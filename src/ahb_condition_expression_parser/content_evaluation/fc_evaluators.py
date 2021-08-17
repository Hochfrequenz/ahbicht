"""
Evaluators are classes that evaluate AHB conditions, meaning here for format constraints: Based on a condition key and
the entered input they return either True or False and for the latter an additional error message.
Their results are used as input for the condition validation of the entire format constraint expression.

Hochfrequenz, 2021-06
"""
import asyncio
from abc import ABC
from typing import Callable, Coroutine, Dict, List

from ahb_condition_expression_parser.content_evaluation.evaluators import Evaluator
from ahb_condition_expression_parser.expressions.condition_nodes import EvaluatedFormatConstraint


# pylint: disable=no-self-use
class FcEvaluator(Evaluator, ABC):
    """
    Base of all Format Constraint (FC) evaluators.
    To implement a content_evaluation create or update an inheriting class that has edifact_format and
    edifact_format_version set accordingly. Then create a method named "evaluate_123" where "123" is the condition key
    of the condition it evaluates.
    """

    async def evaluate_single_format_constraint(
        self, condition_key: str, entered_input: str
    ) -> EvaluatedFormatConstraint:
        """
        Evaluates the format constraint with the given key.
        :param condition_key: key of the condition, e.g. "950"
        :param entered_input: the entered input whose format should be checked, e.g. "12345678913"
        :return: If the format constraint is fulfilled and an optional error_message.
        """
        evaluation_method: Callable = self.get_evaluation_method(condition_key)
        if evaluation_method is None:
            raise NotImplementedError(f"There is no content_evaluation method for format constraint '{condition_key}'")
        result: EvaluatedFormatConstraint = await evaluation_method(entered_input)

        # Fallback error message if there is no error message even though format constraint isn't fulfilled
        if result.format_constraint_fulfilled is False and result.error_message is None:
            result.error_message = f"Bedingung [{condition_key}] muss erfüllt werden."

        return result

    async def evaluate_format_constraints(
        self, condition_keys: List[str], entered_input: str
    ) -> Dict[str, EvaluatedFormatConstraint]:
        """
        Evaluate the entered_input in regard to all the formats provided in condition_keys.
        """
        tasks: List[Coroutine] = [
            self.evaluate_single_format_constraint(condition_key, entered_input) for condition_key in condition_keys
        ]
        results: EvaluatedFormatConstraint = await asyncio.gather(*tasks)

        result: Dict[str, EvaluatedFormatConstraint] = dict(zip(condition_keys, results))
        return result
