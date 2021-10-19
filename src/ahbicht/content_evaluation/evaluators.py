"""
Evaluators are classes that evaluate AHB conditions, meaning: Based on a condition key and a message they return either
FULFILLED (true), UNFULFILLED (false) or NEUTRAL (None). Their results are used as input for the condition validation of
the entire message.
"""
import inspect
from abc import ABC
from typing import Callable, Optional

from ahbicht.edifact import EdifactFormat, EdifactFormatVersion


# pylint: disable=no-self-use, too-few-public-methods
class Evaluator(ABC):
    """
    Base of all evaluators.
    To implement a content_evaluation create or update an inheriting class that has edifact_format and
    edifact_format_version set accordingly. Then create a method named "evaluate_123" where "123" is the condition key
    of the condition it evaluates.
    """

    # define some common attributes. They will be needed to find the correct validator for each use case.
    edifact_format: EdifactFormat = NotImplementedError(  # type:ignore[assignment]
        "The inheriting class needs to define a format to which it is applicable."
    )

    edifact_format_version: EdifactFormatVersion = NotImplementedError(  # type:ignore[assignment]
        "The inheriting class needs to define a format version."
    )

    def get_evaluation_method(self, condition_key: str) -> Optional[Callable]:
        """
        Returns the method that evaluates the condition with key condition_key
        :param condition_key: unique key of the condition, e.g. "59"
        :return: The method that can be used for content_evaluation; None if no such method is implemented.
        """
        for candidate in inspect.getmembers(self, inspect.ismethod):
            # a candidate is a tuple of a string (index 0, name of the method) and the bound method itself (index 1)
            if candidate[0] == f"evaluate_{condition_key}":
                return candidate[1]
        return None
