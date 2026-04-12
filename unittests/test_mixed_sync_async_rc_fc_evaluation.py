"""
Tests that the code can handle RC/FC evaluators that have both async and sync methods.
"""

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluationContext
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_hints_provider,
    empty_default_package_resolver,
    empty_default_test_data,
)


class MixedSyncAsyncRcEvaluator(RcEvaluator):
    """An RC evaluator that has both sync and async methods"""

    edifact_format = default_test_format
    edifact_format_version = default_test_version

    def _get_default_context(self) -> None:  # type: ignore[override]
        return None

    def evaluate_1(self, evaluatable_data: EvaluatableData, context: EvaluationContext) -> ConditionFulfilledValue:  # type: ignore[type-arg]
        assert isinstance(evaluatable_data, EvaluatableData)
        if context is not None:
            assert isinstance(context, EvaluationContext)
        return ConditionFulfilledValue.FULFILLED

    async def evaluate_2(self, evaluatable_data: EvaluatableData, context: EvaluationContext) -> ConditionFulfilledValue:  # type: ignore[type-arg]
        assert isinstance(evaluatable_data, EvaluatableData)
        if context is not None:
            assert isinstance(context, EvaluationContext)
        return ConditionFulfilledValue.UNFULFILLED


class MixedSyncAsyncFcEvaluator(FcEvaluator):
    """An FC Evaluator that has both sync and async methods"""

    edifact_format = default_test_format
    edifact_format_version = default_test_version

    def evaluate_901(self, _: object) -> EvaluatedFormatConstraint:
        return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)

    async def evaluate_902(self, _: object) -> EvaluatedFormatConstraint:
        return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)


class TestMixedSyncAsyncEvaluation:
    @pytest.mark.parametrize(
        "expression, expected_rc_fulfilled, expected_fc_fulfilled",
        [
            pytest.param("Muss ([1][901] X [2][902])", True, True),
            pytest.param("Muss ([1][902] X [2][901])", True, True),
            pytest.param("Muss ([2][902] X [2][901])", False, True),
        ],
    )
    async def test_mixed_async_non_async(
        self, expression: str, expected_rc_fulfilled: bool, expected_fc_fulfilled: bool
    ) -> None:
        fc_evaluator = MixedSyncAsyncFcEvaluator()
        rc_evaluator = MixedSyncAsyncRcEvaluator()
        ctx = AhbContext(
            rc_evaluator=rc_evaluator,
            fc_evaluator=fc_evaluator,
            hints_provider=empty_default_hints_provider,
            package_resolver=empty_default_package_resolver,
            evaluatable_data=empty_default_test_data,
        )
        tree = await parse_expression_including_unresolved_subexpressions(expression)
        evaluation_result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert (
            evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            is expected_rc_fulfilled
        )
        assert (
            evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled is expected_fc_fulfilled
        )
        # When mocker.spy ing on the evaluate_... the inspection inside the rc/fc evaluator fails
        # https://stackoverflow.com/questions/18869141/using-python-mock-to-spy-on-calls-to-an-existing-object
