import inject
import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]
from maus import (
    DataElementFreeText,
    DataElementValuePool,
    DeepAnwendungshandbuch,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)
from maus.models.anwendungshandbuch import AhbMetaInformation

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.validation.validation import validate_deep_anwendungshandbuch
from unittests.defaults import (
    DefaultHintsProvider,
    DefaultPackageResolver,
    EmptyDefaultFcEvaluator,
    EmptyDefaultRcEvaluator,
    default_test_format,
    default_test_version,
)

pytestmark = pytest.mark.asyncio


class MweRcEvaluator(EmptyDefaultRcEvaluator):
    def evaluate_1(self, evaluatable_data, context):
        seed = evaluatable_data.edifact_seed
        if "foo" in seed and seed["foo"] == "bar":
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    async def evaluate_2(self, evaluatable_data, context):
        # an async method, just for the sake of it
        seed = evaluatable_data.edifact_seed
        if "asd" in seed and seed["asd"] == "yxc":
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    def evaluate_3(self, _, __):
        return ConditionFulfilledValue.UNFULFILLED


class MweFcEvaluator(EmptyDefaultFcEvaluator):
    def evaluate_998(self, entered_input):
        """fantasy FC: input must be all upper case"""
        if not entered_input:
            return EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="Input must not be empty")
        if entered_input.to_upper() == entered_input:
            return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)
        return EvaluatedFormatConstraint(
            format_constraint_fulfilled=False, error_message=f"Input '{entered_input}' is not all upper case"
        )


def get_eval_data():
    return TestIntegrationMwe.message_under_test


class TestIntegrationMwe:
    """
    Contains an integration tests that show a full minimal working example (meaning: no mocks at all).
    If any tests break, then first fix all other tests and run these tests last.
    """

    message_under_test: EvaluatableData = EvaluatableData(
        edifact_seed={"foo": "bar", "asd": "yxc"},
        edifact_format=default_test_format,
        edifact_format_version=default_test_version,
    )

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector(self):
        fc_evaluator = MweFcEvaluator()
        rc_evaluator = MweRcEvaluator()
        hints_provider = DefaultHintsProvider({"567": "Hallo Welt"})
        package_resolver = DefaultPackageResolver({"4P": "[1] U [2]"})
        inject.clear_and_configure(
            lambda binder: binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([fc_evaluator, rc_evaluator, hints_provider, package_resolver]),
            ).bind_to_provider(EvaluatableDataProvider, get_eval_data)
        )
        yield
        inject.clear()

    async def test_integration(self, setup_and_teardown_injector):
        maus = DeepAnwendungshandbuch(
            meta=AhbMetaInformation(pruefidentifikator="12345"),
            lines=[
                SegmentGroup(
                    discriminator="root",
                    ahb_expression="X[4P]",
                    segments=[
                        Segment(
                            discriminator="UNH",
                            ahb_expression="X",
                            data_elements=[
                                DataElementFreeText(
                                    discriminator="Nachrichten-Startsegment",
                                    ahb_expression="X[998][567]",
                                    entered_input=None,
                                    data_element_id="1234",
                                )
                            ],
                        )
                    ],
                ),
                SegmentGroup(
                    discriminator="SG4",
                    ahb_expression="X",
                    segments=[
                        Segment(
                            discriminator="FOO",
                            ahb_expression="X",
                            data_elements=[
                                DataElementValuePool(
                                    discriminator="SG4->FOO->0333",
                                    value_pool=[
                                        ValuePoolEntry(
                                            qualifier="E01",
                                            meaning="Das andere",
                                            ahb_expression="X[4P]",
                                        ),
                                        ValuePoolEntry(
                                            qualifier="E02",
                                            meaning="Das Eine",
                                            ahb_expression="X[3]",
                                        ),
                                    ],
                                    data_element_id="0333",
                                )
                            ],
                        )
                    ],
                    segment_groups=[
                        SegmentGroup(
                            discriminator="SG5",
                            ahb_expression="X[2]",
                            segments=[
                                Segment(
                                    discriminator="BAR",
                                    ahb_expression="X",
                                    data_elements=[
                                        DataElementFreeText(
                                            discriminator="Die fünfte Gruppe",
                                            ahb_expression="X",
                                            entered_input=None,
                                            data_element_id="1234",
                                        )
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
        results = await validate_deep_anwendungshandbuch(maus)
        assert results is not None  # no detailed assertions here
        TestIntegrationMwe.message_under_test = EvaluatableData(
            edifact_seed={"foo": "baz", "asd": "qwe"},
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )  # change the message under test to trigger different outcomes
        results2 = await validate_deep_anwendungshandbuch(maus)
        assert results2 is not None
        assert results != results2
