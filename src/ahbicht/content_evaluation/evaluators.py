"""
Evaluators are classes that evaluate AHB conditions, meaning: Based on a condition key and a message they return either
FULFILLED (true), UNFULFILLED (false) or NEUTRAL (None). Their results are used as input for the condition validation of
the entire message.
"""
import inspect
import re
from abc import ABC
from typing import Callable, Dict, Optional

from maus.edifact import EdifactFormat, EdifactFormatVersion


# pylint: disable=too-few-public-methods
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
    _evaluation_method_name_pattern = re.compile(r"^evaluate_(?P<condition_key>\d+)$")

    def __init__(self):
        """
        initializes a cache with all evaluation methods defined in the (child) class
        """
        self._evaluation_methods: Dict[str, Callable] = {}
        for candidate in inspect.getmembers(self, inspect.ismethod):
            # a candidate is a tuple of a string (index 0, name of the method) and the bound method itself (index 1)
            match = Evaluator._evaluation_method_name_pattern.match(candidate[0])
            if match:
                self._evaluation_methods[match.groupdict()["condition_key"]] = candidate[1]

    def get_evaluation_method(self, condition_key: str) -> Optional[Callable]:
        """
        Returns the method that evaluates the condition with key condition_key
        :param condition_key: unique key of the condition, e.g. "59"
        :return: The method that can be used for content_evaluation; None if no such method is implemented.
        """
        if condition_key in self._evaluation_methods:
            return self._evaluation_methods[condition_key]
        return None
