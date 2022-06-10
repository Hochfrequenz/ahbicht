"""
Contains the evaluator provider.
This is basically just a separate module to avoid cyclic imports.
"""
from abc import ABC, abstractmethod
from typing import Dict, List

from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator


class EvaluatorProvider(ABC):
    """
    An Evaluator provider is a class that can provide you with the correct evaluator for your use case.
    """

    @abstractmethod
    def get_rc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> RcEvaluator:
        """
        returns an appropriate RC Evaluator for the given edifact_format and edifact_format_version.
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")

    @abstractmethod
    def get_fc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> FcEvaluator:
        """
        returns an appropriate FC Evaluator for the given edifact_format and edifact_format_version.
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")


class ListBasedEvaluatorProvider(EvaluatorProvider):
    """
    An EvaluatorProvider that is instantiated with a list of evaluators.
    """

    @staticmethod
    def _to_key(edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> str:
        """
        because a tuple for format and format version is not hashable / usuable as key in a dict this methods
        converts them to a unique and hashable string
        """
        # we don't care what the key is, it just has to be unique and consistent
        return f"{edifact_format}-{format_version}"

    def __init__(self, evaluators: List[Evaluator]):
        self._rc_evaluators: Dict[str, RcEvaluator] = {}
        self._fc_evaluators: Dict[str, FcEvaluator] = {}
        for evaluator in evaluators:
            key = ListBasedEvaluatorProvider._to_key(evaluator.edifact_format, evaluator.edifact_format_version)
            if isinstance(evaluator, RcEvaluator):
                self._rc_evaluators[key] = evaluator
            elif isinstance(evaluator, FcEvaluator):
                self._fc_evaluators[key] = evaluator
            else:
                raise ValueError(f"The type of '{evaluator}' is not supported. Expected either RC or FC evaluator")

    def get_fc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> FcEvaluator:
        try:
            return self._fc_evaluators[ListBasedEvaluatorProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No FC Evaluator has been registered for {edifact_format} in {format_version}"
            ) from key_error

    def get_rc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> RcEvaluator:
        try:
            return self._rc_evaluators[ListBasedEvaluatorProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No RC Evaluator has been registered for {edifact_format} in {format_version}"
            ) from key_error
