""" Tests the dictionary based RC evaluator"""
from unittest import mock

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue

pytestmark = pytest.mark.asyncio


class TestDictBasedRcEvaluator:
    """Test for the evaluation using the Dict Based RC Evaluator"""

    async def test_evaluation(self, mocker):
        hardcoded_results = {
            "1": ConditionFulfilledValue.NEUTRAL,
            "2": ConditionFulfilledValue.UNFULFILLED,
            "3": ConditionFulfilledValue.FULFILLED,
            "4": ConditionFulfilledValue.UNKNOWN,
        }
        evaluator = DictBasedRcEvaluator(hardcoded_results)
        assert await evaluator.evaluate_single_condition("1") == ConditionFulfilledValue.NEUTRAL
        assert await evaluator.evaluate_single_condition("2") == ConditionFulfilledValue.UNFULFILLED
        assert await evaluator.evaluate_single_condition("3") == ConditionFulfilledValue.FULFILLED
        assert await evaluator.evaluate_single_condition("4") == ConditionFulfilledValue.UNKNOWN
        with pytest.raises(NotImplementedError):
            await evaluator.evaluate_single_condition("5")

        single_condition_spy = mocker.spy(evaluator, "evaluate_single_condition")
        assert await evaluator.evaluate_conditions(["1", "2", "3", "4"]) == hardcoded_results
        single_condition_spy.assert_has_awaits(
            [mock.call("1", None), mock.call("2", None), mock.call("3", None), mock.call("4", None)]
        )
