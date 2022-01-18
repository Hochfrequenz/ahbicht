"""
Tests that the code can handle RC/FC evaluators that have both async and sync methods.
"""
from unittest import mock

import inject
import pytest  # type:ignore[import]

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator, RcEvaluator
from ahbicht.edifact import EdifactFormat, EdifactFormatVersion
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.expressions.hints_provider import DictBasedHintsProvider, HintsProvider

pytestmark = pytest.mark.asyncio


class MixedSyncAsyncRcEvaluator(RcEvaluator):
    """An RC evaluator that has both sync and async methods"""

    edifact_format = EdifactFormat.UTILMD
    edifact_format_version = EdifactFormatVersion.FV2104

    def _get_default_context(self):
        return None  # type:ignore[return-value]

    def evaluate_1(self, _):
        return ConditionFulfilledValue.FULFILLED

    async def evaluate_2(self, _):
        return ConditionFulfilledValue.UNFULFILLED


class MixedSyncAsyncFcEvaluator(FcEvaluator):
    """An FC Evaluator that has both sync and async methods"""

    edifact_format = EdifactFormat.UTILMD
    edifact_format_version = EdifactFormatVersion.FV2104

    def evaluate_901(self, _):
        return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)

    async def evaluate_902(self, _):
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
    ):
        fc_evaluator = MixedSyncAsyncFcEvaluator()
        rc_evaluator = MixedSyncAsyncRcEvaluator(EvaluatableData(edifact_seed={}))
        inject.clear_and_configure(
            lambda binder: binder.bind(RcEvaluator, rc_evaluator)  # type:ignore[arg-type]
            .bind(FcEvaluator, fc_evaluator)
            .bind(HintsProvider, DictBasedHintsProvider({}))
        )
        evaluation_input = "something has to be here but it's not important what"
        tree = parse_expression_including_unresolved_subexpressions(expression)
        evaluation_result = await evaluate_ahb_expression_tree(tree, entered_input=evaluation_input)
        assert (
            evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            is expected_rc_fulfilled
        )
        assert (
            evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled is expected_fc_fulfilled
        )
        # When mocker.spy ing on the evaluate_... the inspection inside the rc/fc evaluator fails
        # https://stackoverflow.com/questions/18869141/using-python-mock-to-spy-on-calls-to-an-existing-object
