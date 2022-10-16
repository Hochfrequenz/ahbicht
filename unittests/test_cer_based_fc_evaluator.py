""" Tests the FC evaluator, that assumes a ContentEvaluationResult to be present in the evaluatable data"""
from unittest import mock

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.fc_evaluators import ContentEvaluationResultBasedFcEvaluator, FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import ContentEvaluationResultBasedRcEvaluator, RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from unittests.defaults import EmptyDefaultRcEvaluator, store_content_evaluation_result_in_evaluatable_data


class TestCerBasedRcEvaluator:
    """Test for the evaluation using the ContentEvaluationResult Based FC Evaluator"""

    @pytest.fixture
    def inject_cer_evaluators(self, request: SubRequest):
        # indirect parametrization: https://stackoverflow.com/a/33879151/10009545
        content_evaluation_result: ContentEvaluationResult = request.param
        assert isinstance(content_evaluation_result, ContentEvaluationResult)
        fc_evaluator = ContentEvaluationResultBasedFcEvaluator()

        def get_evaluatable_data():
            return store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)

        def configure(binder):
            binder.bind(TokenLogicProvider, SingletonTokenLogicProvider([EmptyDefaultRcEvaluator(), fc_evaluator]))
            binder.bind_to_provider(EvaluatableDataProvider, get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

    @pytest.mark.parametrize(
        "inject_cer_evaluators",
        [
            pytest.param(
                ContentEvaluationResult(
                    format_constraints={
                        "1": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
                        "2": EvaluatedFormatConstraint(
                            format_constraint_fulfilled=False, error_message="something wrong"
                        ),
                    },
                    requirement_constraints={},
                    hints={},
                )
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "condition_key, expected_result",
        [
            pytest.param("1", EvaluatedFormatConstraint(format_constraint_fulfilled=True)),
            pytest.param(
                "2",
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong"),
            ),
        ],
    )
    async def test_evaluation(
        self, condition_key: str, expected_result: EvaluatedFormatConstraint, inject_cer_evaluators
    ):
        fc_evalutor: FcEvaluator = inject.instance(FcEvaluator)
        actual = await fc_evalutor.evaluate_single_format_constraint(condition_key)
        assert actual == expected_result

    async def test_not_implemented(self, dict_fc_evaluator):
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("qwe")
        with pytest.raises(NotImplementedError):
            await dict_fc_evaluator.evaluate_single_format_constraint("3")
