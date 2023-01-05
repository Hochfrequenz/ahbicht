import asyncio
from contextvars import ContextVar
from logging import LogRecord
from typing import List

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


class SomethingInjectable:
    """
    This class is used by one of our custom Evaluators.
    The evaluators a bit fragile because of https://github.com/ivankorobkov/python-inject/issues/77
    This means you _cannot_ use inject.attr(...) in your custom evaluators
    """

    pass


class MweRcEvaluator(EmptyDefaultRcEvaluator):
    # do _not_use inject.attr! It breaks in the inspection inside the Evaluator __init__ method

    def evaluate_1(self, evaluatable_data, context):
        seed = evaluatable_data.body
        if "foo" in seed and seed["foo"] == "bar":
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    async def evaluate_2(self, evaluatable_data, context):
        # an async method, just for the sake of it
        seed = evaluatable_data.body
        if "asd" in seed and seed["asd"] == "yxc":
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    def evaluate_3(self, _, __):
        something_injected = inject.instance(SomethingInjectable)  # this is fine (other than inject.attr, see above)
        assert isinstance(something_injected, SomethingInjectable)
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


current_evaluatable_data: ContextVar[EvaluatableData] = ContextVar("current_evaluatable_data")


def get_current_evaluatable_data() -> EvaluatableData:
    return current_evaluatable_data.get()


class TestIntegrationMwe:
    """
    Contains an integration tests that show a full minimal working example (meaning: no mocks at all).
    If any tests break, then first fix all other tests and run these tests last.
    """

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
            ).bind_to_provider(EvaluatableDataProvider, get_current_evaluatable_data)
        )
        yield
        inject.clear()

    async def test_integration(self, setup_and_teardown_injector, caplog):
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
                                    entered_input=None,
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

        async def first_evaluation():
            current_evaluatable_data.set(
                EvaluatableData(
                    body={"foo": "bar", "asd": "yxc"},
                    edifact_format=default_test_format,
                    edifact_format_version=default_test_version,
                )
            )
            return await validate_deep_anwendungshandbuch(maus)

        async def second_evaluation():
            current_evaluatable_data.set(
                EvaluatableData(
                    body={"foo": "baz", "asd": "qwe"},
                    edifact_format=default_test_format,
                    edifact_format_version=default_test_version,
                )
            )  # use a different message under test to trigger different outcomes
            # you can set a breakpoint in evaluate_1 and evaluate_2 to manually verify the different data they access
            return await validate_deep_anwendungshandbuch(maus)

        results1, results2 = await asyncio.gather(*[first_evaluation(), second_evaluation()])
        assert results2 is not None
        assert results1 != results2  # this shows, that the evaluatable data used are indeed different in each call
        log_entries: List[LogRecord] = caplog.records
        assert len([le for le in log_entries if le.message.startswith("The requirement constraint")]) == 12
        assert len([le for le in log_entries if le.message.startswith("The format constraint")]) == 1
