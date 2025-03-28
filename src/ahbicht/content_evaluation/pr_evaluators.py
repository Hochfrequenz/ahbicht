"""
Package Repetition (RR) Evaluators are evaluators that check if... tba
"""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ahbicht.condition_node_distinction import REGEX_PACKAGE_REPEATABILITY
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluationContext
from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.models.condition_nodes import ConditionFulfilledValue
from ahbicht.models.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema


class PrEvaluator(Evaluator, ABC):
    """
    tba
    """

    @abstractmethod
    def _get_default_context(self) -> EvaluationContext:
        raise NotImplementedError("Has to be implemented in inheriting class")

    async def evaluate_single_repetition(
        self,
        repetitions: tuple[int, int],
        evaluatable_data: EvaluatableData,
    ) -> ConditionFulfilledValue:
        """
        tba
        """
        result: ConditionFulfilledValue = ConditionFulfilledValue.NEUTRAL  # tba
        return result

    async def evaluate_conditions(
        self,
        repetition_keys: List[str],
        evaluatable_data: EvaluatableData,
    ) -> Dict[str, ConditionFulfilledValue]:
        """
        tba
        """
        tasks: List[asyncio.Task] = []
        for repetition_key in repetition_keys:
            match = REGEX_PACKAGE_REPEATABILITY.match(repetition_key)
            if match:
                repetitions = (int(match.group("n")), int(match.group("m")))
                tasks.append(
                    self.evaluate_single_repetition(repetitions=repetitions, evaluatable_data=evaluatable_data)
                )

        results = await asyncio.gather(*tasks)

        result = dict(zip(repetition_keys, results))
        return result
