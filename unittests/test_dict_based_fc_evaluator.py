""" Tests the dictionary based FC evaluator"""
from typing import Optional
from unittest import mock

import pytest  # type:ignore[import]

from ahbicht.content_evaluation import fc_evaluators
from ahbicht.content_evaluation.fc_evaluators import DictBasedFcEvaluator, FcEvaluator
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint


class TestDictBasedFcEvaluator:
    """Test for the evaluation using the Dict Based FC Evaluator"""

    hardcoded_results = {
        "1": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
        "2": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong"),
    }

    @pytest.fixture()
    def dict_fc_evaluator(self) -> FcEvaluator:
        evaluator = DictBasedFcEvaluator(self.hardcoded_results)
        return evaluator

    @pytest.mark.parametrize(
        "condition_key,text_input, expected_result",
        [
            pytest.param("1", "asd", EvaluatedFormatConstraint(format_constraint_fulfilled=True)),
            pytest.param(
                "2",
                "yxc",
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong"),
            ),
        ],
    )
    async def test_evaluation(
        self,
        condition_key: str,
        text_input: Optional[str],
        expected_result: EvaluatedFormatConstraint,
        dict_fc_evaluator,
    ):
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("asd")
        assert await dict_fc_evaluator.evaluate_single_format_constraint("1") == EvaluatedFormatConstraint(
            format_constraint_fulfilled=True
        )
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("yxc")
        assert await dict_fc_evaluator.evaluate_single_format_constraint("2") == EvaluatedFormatConstraint(
            format_constraint_fulfilled=False, error_message="something wrong"
        )

    async def test_not_implemented(self, dict_fc_evaluator):
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("qwe")
        with pytest.raises(NotImplementedError):
            await dict_fc_evaluator.evaluate_single_format_constraint("3")

    async def test_multithreading_with_same_value(self, dict_fc_evaluator, mocker):
        dict_evaluation_spy = mocker.spy(dict_fc_evaluator, "evaluate_single_format_constraint")
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("asd")
        assert await dict_fc_evaluator.evaluate_format_constraints(["1", "2"]) == self.hardcoded_results
        dict_evaluation_spy.assert_has_awaits([mock.call("1"), mock.call("2")])
