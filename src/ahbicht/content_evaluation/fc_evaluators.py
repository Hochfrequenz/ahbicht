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
from typing import Coroutine, Dict, List, Optional

from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.content_evaluation.german_strom_and_gas_tag import has_no_utc_offset, is_xtag_limit
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint


# pylint: disable=no-self-use
class FcEvaluator(Evaluator, ABC):
    """
    Base of all Format Constraint (FC) evaluators.
    To implement a content_evaluation create or update an inheriting class that has edifact_format and
    edifact_format_version set accordingly. Then create a method named "evaluate_123" where "123" is the condition key
    of the condition it evaluates.
    """

    def evaluate_931(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        Assert that the entered input is parsable as datetime with explicit UTC offset.
        Then assert that the UTC offset is exactly +00:00.
        Be aware of the fact that asserting on a fixed offset when both datetime + offset are given will not lead to any
        truly meaningful results.
        We implement it for compatability but don't encourage you to actively write any conditions that use it.
        """
        return has_no_utc_offset(entered_input)

    def evaluate_932(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        Assert that the entered input is the start/end of a german "Stromtag" (during central european daylight saving
        time).
        We ship this predefined method to evaluate the format constraints which are being introduced by expanding
        "time conditions" (UB1/UB3) in the :class:`expression_resolver.TimeConditionTransformer`.
        """
        return is_xtag_limit(entered_input, "Strom")

    # Attentive readers will notice, that 933 does exactly the same thing as 932; Also 935 does the same thing as 934.
    # This is because, from a data perspective, it's totally irrelevant if we're communicating a datetime with
    # +1h or +2h UTC offset as long as _any_ offset is given. Two distinctive format constraints are just ..., ok.
    # The authors of the AHBs probably had good intentions, when they introduced two different format constraints for
    # both German "winter" (CET/MEZ) and "summer time" (CEST/MESZ).
    # The road to hell is paved with good intentions.

    def evaluate_933(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        Assert that the entered input is the start/end of a german "Stromtag" (during central european standard time).
        We ship this predefined method to evaluate the format constraints which are being introduced by expanding
        "time conditions" (UB1/UB3) in the :class:`expression_resolver.TimeConditionTransformer`.
        """
        return is_xtag_limit(entered_input, "Strom")

    def evaluate_934(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        Assert that the entered input is the start/end of a german "Gastag" (during central european daylight saving
        time).
        We ship this predefined method to evaluate the format constraints which are being introduced by expanding
        "time conditions" (UB2/UB3) in the :class:`expression_resolver.TimeConditionTransformer`.
        """
        return is_xtag_limit(entered_input, "Gas")

    def evaluate_935(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        Assert that the entered input is the start/end of a german "Gastag" (during central european standard time).
        We ship this predefined method to evaluate the format constraints which are being introduced by expanding
        "time conditions" (UB2/UB3) in the :class:`expression_resolver.TimeConditionTransformer`.
        """
        return is_xtag_limit(entered_input, "Gas")

    async def evaluate_single_format_constraint(
        self, condition_key: str, entered_input: Optional[str]
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
        self, condition_keys: List[str], entered_input: Optional[str]
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
        self, condition_key: str, entered_input: Optional[str]
    ) -> EvaluatedFormatConstraint:
        try:
            return self._results[condition_key]
        except KeyError as key_error:
            raise NotImplementedError(f"No result was provided for {condition_key}.") from key_error
