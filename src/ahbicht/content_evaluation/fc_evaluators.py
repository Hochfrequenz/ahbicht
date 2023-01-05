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
from contextvars import ContextVar
from typing import Callable, Coroutine, Dict, List, Optional

import inject

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.content_evaluation.german_strom_and_gas_tag import has_no_utc_offset, is_xtag_limit
from ahbicht.evaluation_results import FormatConstraintEvaluationResult
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint

text_to_be_evaluated_by_format_constraint: ContextVar[Optional[str]] = ContextVar(
    "text_to_be_evaluated_by_format_constraint", default=None
)
"""
This context variable holds the text that is to be analysed/evaluated by the format constraint evaluator.
It will always return the "correct" value in your context. You only have to manually set this context variable if you're
evaluating an expression outside the validation framework.
The conceptual difference to the EvaluatableData which are dependency injected using the EvaluatableDataProvider is,
that the data evaluated in a format constraint (via the context variable) vary over the time span of one validation run.
The EvaluatableData are stable in that regard.
"""

# The idea behind the context variable is to avoid passing the string/text to be evaluated by FC evaluators through many
# layers of code (including lark classes like transformers where we formerly had the string as constructor argument).
# Now it needs to be set once and only once when the entered input is determined (e.g. when reading user input).
# Then we can forget about it, it does not bloat our function signatures (where in >90% of the cases it has just been
# forwarded to the next layer of code).
# The context variable also greatly simplifies the debugging/error analysis.
# Instead of tracing the entered input all the way down from the ahbicht API to the FC Evaluator method,
# you now just need to watch the two places in the code where the values are actually set:
# 1. in the ahbicht code base in the validation
# 2. in custom code using ahbicht(?)
# The single evaluation methods of the FC evaluators (e.g. "def evaluate_987") are still provided with the value as a
# usual function argument to prevent the methods from needing to access the context variable themselves.


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

    async def evaluate_single_format_constraint(self, condition_key: str) -> EvaluatedFormatConstraint:
        """
        Evaluates the format constraint with the given key.
        :param condition_key: key of the condition, e.g. "950"
        :return: If the format constraint is fulfilled and an optional error_message.
        """
        text_to_be_evaluated = text_to_be_evaluated_by_format_constraint.get()
        evaluation_method = self.get_evaluation_method(condition_key)
        if evaluation_method is None:
            raise NotImplementedError(f"There is no content_evaluation method for format constraint '{condition_key}'")
        result: EvaluatedFormatConstraint
        if inspect.iscoroutinefunction(evaluation_method):
            result = await evaluation_method(text_to_be_evaluated)
        else:
            result = evaluation_method(text_to_be_evaluated)
        try:
            if result.format_constraint_fulfilled is False and result.error_message is None:
                result.error_message = f"Condition [{condition_key}] has to be fulfilled."
        except AttributeError as attribute_error:
            if isinstance(result, FormatConstraintEvaluationResult):
                # explicitly raise error with meaningful message, because this is really hard to distinguish for users
                raise ValueError(
                    "A FcEvaluator shall return EvaluatedFormatConstraints, _not_ FormatConstraintEvaluationResults"
                ) from attribute_error
            raise attribute_error
        self.logger.debug(
            "The format constraint %s with input '%s' evaluated to %s", condition_key, text_to_be_evaluated, str(result)
        )
        return result

    async def evaluate_format_constraints(self, condition_keys: List[str]) -> Dict[str, EvaluatedFormatConstraint]:
        """
        Evaluate the entered_input in regard to all the formats provided in condition_keys.
        """
        tasks: List[Coroutine] = [
            self.evaluate_single_format_constraint(condition_key) for condition_key in condition_keys
        ]
        results: List[EvaluatedFormatConstraint] = await asyncio.gather(*tasks)

        result: Dict[str, EvaluatedFormatConstraint] = dict(zip(condition_keys, results))
        return result


class DictBasedFcEvaluator(FcEvaluator):
    """
    A format constraint evaluator that is initialized with a prefilled dictionary on time of creation.
    Once initialized the outcome of the evaluation won't change anymore.
    """

    def __init__(self, results: Dict[str, EvaluatedFormatConstraint]):
        """
        Initialize with a dictionary that contains all the format constraint evaluation results.
        :param results:
        """
        super().__init__()
        self._results: Dict[str, EvaluatedFormatConstraint] = results

    # pylint: disable=unused-argument
    async def evaluate_single_format_constraint(self, condition_key: str) -> EvaluatedFormatConstraint:
        try:
            return self._results[condition_key]
        except KeyError as key_error:
            raise NotImplementedError(f"No result was provided for {condition_key}.") from key_error

    def get_evaluation_method(self, condition_key: str) -> Optional[Callable]:
        """
        Returns the method that evaluates the condition with key condition_key
        :param condition_key: unique key of the condition, e.g. "59"
        :return: The method that can be used for content_evaluation; None if no such method is implemented.
        """
        return self.get_evaluation_method(condition_key)


class ContentEvaluationResultBasedFcEvaluator(FcEvaluator):
    """
    A format constraint evaluator that expects the evaluatable data to contain a ContentEvalutionResult as edifact seed.
    Other than the DictBasedFcEvaluator the outcome is not dependent on the initialization but on the evaluatable data.
    """

    def __init__(self):
        super().__init__()
        self._schema = ContentEvaluationResultSchema()

    async def evaluate_single_format_constraint(self, condition_key: str) -> EvaluatedFormatConstraint:
        # the missing second argument to the private method call in the next line should be injected automatically
        return await self._evaluate_single_format_constraint(condition_key)  # pylint:disable=no-value-for-parameter

    @inject.params(evaluatable_data=EvaluatableDataProvider)  # injects what has been bound to the EvaluatableData type
    async def _evaluate_single_format_constraint(
        self, condition_key: str, evaluatable_data: EvaluatableData
    ) -> EvaluatedFormatConstraint:
        content_evaluation_result: ContentEvaluationResult = self._schema.load(evaluatable_data.body)
        try:
            self.logger.debug("Retrieving key %s' from Content Evaluation Result", condition_key)
            return content_evaluation_result.format_constraints[condition_key]
        except KeyError as key_error:
            raise NotImplementedError(f"No result was provided for {condition_key}.") from key_error

    def get_evaluation_method(self, condition_key: str) -> Optional[Callable]:
        async def evaluation_method():
            return await self.evaluate_single_format_constraint(condition_key)

        return evaluation_method
