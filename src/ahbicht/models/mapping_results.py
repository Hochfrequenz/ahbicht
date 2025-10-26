"""
This module contains classes that are returned by mappers, meaning they contain a mapping.
"""

import math
from typing import Literal, Optional, Self, Union

from efoli import EdifactFormat
from pydantic import BaseModel, model_validator


# pylint:disable=too-few-public-methods
class ConditionKeyConditionTextMapping(BaseModel):
    """
    maps a condition from a specified EDIFACT format onto a text as it is found in the AHB.
    """

    edifact_format: EdifactFormat  #: the format in which the condition is used; e.g. 'UTILMD'
    condition_key: str  #: the key of the condition without square brackets; e.g. '78'
    condition_text: Optional[str] = None
    """
    the description of the condition as in the AHB; None if unknown;
    e.g. 'Wenn SG4 STS+7++E02 (Transaktionsgrund: Einzug/Neuanlage)  nicht vorhanden'.
    """


# pylint:disable=too-few-public-methods
class PackageKeyConditionExpressionMapping(BaseModel):
    """
    maps a package key from a specified EDIFACT format onto a (not yet parsed) condition expression as it is found in
    the AHB.
    """

    edifact_format: EdifactFormat  #: the format in which the package is used; e.g. 'UTILMD'
    package_key: str  #: the key of the package without square brackets but with trailing P; e.g. '10P'
    package_expression: Optional[str] = None
    """the expression for which the package is a shortcut; None if unknown e.g. '[20] ∧ [244]'"""

    def has_been_resolved_successfully(self) -> bool:
        """
        return true iff the package has been resolved successfully
        """
        return self.package_expression is not None


def check_max_greater_or_equal_than_min(instance: "Repeatability"):
    """
    assert that 0<=min<max and not both min and max are 0
    """
    max_occurrences = math.inf if instance.max_occurrences == "n" else instance.max_occurrences
    if not 0 <= instance.min_occurrences <= max_occurrences:
        raise ValueError(f"0≤n≤m is not fulfilled for n={instance.min_occurrences}, m={max_occurrences}")
    if instance.min_occurrences == max_occurrences == 0:
        raise ValueError("not both min and max occurrences must be 0")


# pylint:disable=too-few-public-methods
class Repeatability(BaseModel):
    """
    describes how often a segment/code must be used when a "repeatability" is provided with packages
    """

    min_occurrences: int
    """
    how often the segment/code has to be repeated (lower, inclusive bound); may be 0 for optional packages
    """

    max_occurrences: Union[int, Literal["n"]]
    """
    how often the segment/code may be repeated at most (upper, inclusive bound).
    This is inclusive meaning that [123P0..1] leads to max_occurrences==1
    """

    @model_validator(mode="after")
    def _check__repeatability_values(self) -> Self:
        if self.max_occurrences == "n":
            return self
        check_max_greater_or_equal_than_min(self)
        return self

    def is_optional(self) -> bool:
        """
        returns true if the package used together with this repeatability is optional
        """
        return self.min_occurrences == 0
