"""
Requirement Constraint (RC) Evaluators are evaluators that check if data are required under given circumstances.
Typical usecases are for example
* you must only provide a Gerätenummer if the Transaktionsgrund is e.g. 'E08'
* you must only provide an Ausbaudatum if the meter is being removed e.g. 'Z02'
"""
import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluationContext
from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue

# pylint: disable=no-self-use


class RcEvaluator(Evaluator, ABC):
    """
    Base class of all Requirement Constraint (RC) evaluators.
    To implement a content_evaluation create or update an inheriting class that has edifact_format and
    edifact_format_version set accordingly. Then create a method named "evaluate_123" where "123" is the condition key
    of the condition it evaluates.
    """

    def __init__(self, evaluatable_data: EvaluatableData):
        """
        Instantiate any evaluator by providing some evaluatable data from a message.
        :param evaluatable_data:
        """
        if not evaluatable_data:
            raise ValueError("Evaluatable data have to be provided to any evaluator.")
        self.evaluatable_data = evaluatable_data

    @abstractmethod
    def _get_default_context(self) -> EvaluationContext:
        raise NotImplementedError("Has to be implemented in inheriting class")

    async def evaluate_single_condition(
        self, condition_key: str, context: Optional[EvaluationContext] = None
    ) -> ConditionFulfilledValue:
        """
        Evaluates the condition with the given key.
        :param context: optional content_evaluation context, if not the default context will be used
        :param condition_key: key of the condition, e.g. "78"
        :return:
        """
        evaluation_method = self.get_evaluation_method(condition_key)
        if evaluation_method is None:
            raise NotImplementedError(f"There is no content_evaluation method for condition '{condition_key}'")
        if context is None:
            context = self._get_default_context()
        if inspect.iscoroutinefunction(evaluation_method):
            return await evaluation_method(context)
        return evaluation_method(context)

    async def evaluate_conditions(
        self, condition_keys: List[str], condition_keys_with_context: Optional[Dict[str, EvaluationContext]] = None
    ) -> Dict[str, ConditionFulfilledValue]:
        """
        Validate all the conditions provided in condition_keys in their respective context.
        """
        if condition_keys_with_context is None:
            tasks = [self.evaluate_single_condition(condition_key, None) for condition_key in condition_keys]
        else:
            tasks = []
            for condition_key in condition_keys:
                if condition_key not in condition_keys_with_context:
                    tasks.append(self.evaluate_single_condition(condition_key, None))
                else:
                    tasks.append(
                        self.evaluate_single_condition(condition_key, condition_keys_with_context[condition_key])
                    )

        results = await asyncio.gather(*tasks)

        result = dict(zip(condition_keys, results))
        return result


class DictBasedRcEvaluator(RcEvaluator):
    """
    A requirement constraint evaluator that is initialized with a prefilled dictionary.
    """

    def __init__(self, results: Dict[str, ConditionFulfilledValue]):
        """
        Initialize with a dictionary that contains all the requirement constraint evaluation results.
        :param results:
        """
        super().__init__(evaluatable_data=EvaluatableData(edifact_seed=results))
        self._results: Dict[str, ConditionFulfilledValue] = results

    def _get_default_context(self) -> EvaluationContext:
        raise NotImplementedError()

    # pylint:disable=unused-argument
    async def evaluate_single_condition(
        self, condition_key: str, context: Optional[EvaluationContext] = None
    ) -> ConditionFulfilledValue:
        try:
            return self._results[condition_key]
        except KeyError as key_error:
            raise NotImplementedError(f"No result was provided for condition '{condition_key}'.") from key_error
