import asyncio
from typing import Dict, Optional

from ahbicht.content_evaluation import fc_evaluators
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint


class _MyFcEvaluator(FcEvaluator):
    def _evaluate_has_length(self, entered_input: Optional[str], length: int) -> EvaluatedFormatConstraint:
        """
        check if input is length character long
        """
        if not entered_input:
            return EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="Input is None or Empty")
        if len(entered_input) == length:
            return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)
        return EvaluatedFormatConstraint(
            format_constraint_fulfilled=False,
            error_message=f"Input has length {len(entered_input)} but expected {length}",
        )

    def evaluate_1(self, entered_input: Optional[str]):
        """
        check if input is 1 character long
        """
        return self._evaluate_has_length(entered_input, 1)

    def evaluate_2(self, entered_input: Optional[str]):
        """
        check if input is 2 characters long
        """
        return self._evaluate_has_length(entered_input, 2)

    async def evaluate_3(self, entered_input: Optional[str]):
        """
        check if input is 3 character long
        """
        return self._evaluate_has_length(entered_input, 3)

    async def evaluate_4(self, entered_input: Optional[str]):
        """
        check if input is 4 character long
        """
        return self._evaluate_has_length(entered_input, 4)


def _build_expectations(actual_length: int) -> Dict[str, EvaluatedFormatConstraint]:
    result = {}
    for length in range(1, 5):
        error_message: Optional[str]
        if actual_length == 0:
            error_message = "Input is None or Empty"
        elif actual_length == length:
            error_message = None
        else:
            error_message = f"Input has length {actual_length} but expected {length}"

        value = EvaluatedFormatConstraint(
            format_constraint_fulfilled=length == actual_length, error_message=error_message
        )
        result.update({str(length): value})
    return result


class TestFormatConstraintsContextVar:
    """Tests that the context variable used by the FC Evaluators works as designed"""

    async def test_context_var_is_context_sensitive(self):
        evaluator = _MyFcEvaluator()
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set("something to confuse the evaluation?")

        async def first_evaluation():
            fc_evaluators.text_to_be_evaluated_by_format_constraint.set("a")
            assert await evaluator.evaluate_format_constraints(["1", "2", "3", "4"]) == _build_expectations(1)

        async def second_evaluation():
            fc_evaluators.text_to_be_evaluated_by_format_constraint.set("bb")
            assert await evaluator.evaluate_format_constraints(["1", "2", "3", "4"]) == _build_expectations(2)

        async def third_evaluation():
            fc_evaluators.text_to_be_evaluated_by_format_constraint.set("ccc")
            assert await evaluator.evaluate_format_constraints(["1", "2", "3", "4"]) == _build_expectations(3)

        async def forth_evaluation():
            fc_evaluators.text_to_be_evaluated_by_format_constraint.set("dddd")
            assert await evaluator.evaluate_format_constraints(["1", "2", "3", "4"]) == _build_expectations(4)

        await asyncio.gather(*[first_evaluation(), second_evaluation(), third_evaluation(), forth_evaluation()])
