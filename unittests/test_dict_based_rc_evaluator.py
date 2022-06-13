""" Tests the dictionary based RC evaluator"""
from unittest import mock

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue
from unittests.defaults import empty_default_test_data


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
        dummy_eval_data = empty_default_test_data
        assert (
            await evaluator.evaluate_single_condition("1", evaluatable_data=dummy_eval_data)
            == ConditionFulfilledValue.NEUTRAL
        )
        assert (
            await evaluator.evaluate_single_condition("2", evaluatable_data=dummy_eval_data)
            == ConditionFulfilledValue.UNFULFILLED
        )
        assert (
            await evaluator.evaluate_single_condition("3", evaluatable_data=dummy_eval_data)
            == ConditionFulfilledValue.FULFILLED
        )
        assert (
            await evaluator.evaluate_single_condition("4", evaluatable_data=dummy_eval_data)
            == ConditionFulfilledValue.UNKNOWN
        )
        with pytest.raises(NotImplementedError):
            await evaluator.evaluate_single_condition("5", evaluatable_data=dummy_eval_data)

        single_condition_spy = mocker.spy(evaluator, "evaluate_single_condition")

        assert (
            await evaluator.evaluate_conditions(["1", "2", "3", "4"], evaluatable_data=dummy_eval_data)
            == hardcoded_results
        )
        single_condition_spy.assert_has_awaits(
            [
                mock.call("1", dummy_eval_data, None),
                mock.call("2", dummy_eval_data, None),
                mock.call("3", dummy_eval_data, None),
                mock.call("4", dummy_eval_data, None),
            ]
        )
