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
    async def test_mixed_async_non_async(self):
        inject.clear_and_configure(
            lambda binder: binder.bind(RcEvaluator, MixedSyncAsyncRcEvaluator(EvaluatableData(edifact_seed={})))
            .bind(FcEvaluator, MixedSyncAsyncFcEvaluator())
            .bind(HintsProvider, DictBasedHintsProvider({}))
        )
        evaluation_input = "something has to be here but it's not important what"
        tree = parse_expression_including_unresolved_subexpressions("Muss ([1] X [2])[901][902]")
        evaluation_result = await evaluate_ahb_expression_tree(tree, entered_input=evaluation_input)
        assert evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is True
        assert evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled is True
