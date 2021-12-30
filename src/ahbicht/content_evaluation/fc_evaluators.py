"""
A format constraint (FC) evaluator is an evaluator for format constraints.
Think of stuff like:
* strings that should match an OBIS regex
* MarktlokationsIDs having correct check sums
* pre/post decimal values having specific ranges
Other than requirement constraints format constraints do not affect if data are required at all, but instead only
validate already required data.
"""
import asyncio
import inspect
from abc import ABC
from typing import Coroutine, Dict, List

from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint


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
        evaluation_method = self.get_evaluation_method(condition_key)
        if evaluation_method is None:
            raise NotImplementedError(f"There is no content_evaluation method for format constraint '{condition_key}'")
        result: EvaluatedFormatConstraint
        if inspect.iscoroutinefunction(evaluation_method):
            result = await evaluation_method(entered_input)
        else:
            result = evaluation_method(entered_input)
        # Fallback error message if there is no error message even though format constraint isn't fulfilled
        if result.format_constraint_fulfilled is False and result.error_message is None:
            result.error_message = f"Condition [{condition_key}] has to be fulfilled."

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
        results: List[EvaluatedFormatConstraint] = await asyncio.gather(*tasks)

        result: Dict[str, EvaluatedFormatConstraint] = dict(zip(condition_keys, results))
        return result


class DictBasedFcEvaluator(FcEvaluator):
    """
    A format constraint evaluator that is initialized with a prefilled dictionary.
    """

    def __init__(self, results: Dict[str, EvaluatedFormatConstraint]):
        """
        Initialize with a dictionary that contains all the format constraint evaluation results.
        :param results:
        """
        self._results: Dict[str, EvaluatedFormatConstraint] = results

    # pylint: disable=unused-argument
    async def evaluate_single_format_constraint(
        self, condition_key: str, entered_input: str
    ) -> EvaluatedFormatConstraint:
        try:
            return self._results[condition_key]
        except KeyError as key_error:
            raise NotImplementedError(f"No result was provided for {condition_key}.") from key_error
