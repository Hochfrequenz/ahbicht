""" Tests the dictionary based FC evaluator"""
from unittest import mock

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.fc_evaluators import DictBasedFcEvaluator
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint

pytestmark = pytest.mark.asyncio


class TestDictBasedFcEvaluator:
    """Test for the evaluation using the Dict Based FC Evaluator"""

    async def test_evaluation(self, mocker):
        hardcoded_results = {
            "1": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
            "2": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong"),
        }
        evaluator = DictBasedFcEvaluator(hardcoded_results)
        assert await evaluator.evaluate_single_format_constraint("1", entered_input="asd") == EvaluatedFormatConstraint(
            format_constraint_fulfilled=True
        )
        assert await evaluator.evaluate_single_format_constraint("2", entered_input="yxc") == EvaluatedFormatConstraint(
            format_constraint_fulfilled=False, error_message="something wrong"
        )
        with pytest.raises(NotImplementedError):
            await evaluator.evaluate_single_format_constraint("3", entered_input="qwe")
        dict_evaluation_spy = mocker.spy(evaluator, "evaluate_single_format_constraint")
        assert await evaluator.evaluate_format_constraints(["1", "2"], entered_input="asd") == hardcoded_results
        dict_evaluation_spy.assert_has_awaits([mock.call("1", "asd"), mock.call("2", "asd")])
