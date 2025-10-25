"""
This module contains a class to store _all_ kinds of content evaluation results.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr

from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint


# pylint: disable=too-few-public-methods, unused-argument
class ContentEvaluationResult(BaseModel):
    """
    A class that holds the results of a full content evaluation (meaning all hints, requirement constraints and
    format constraints have been evaluated)
    """

    hints: dict[str, Optional[str]] = Field(default_factory=dict)  #: maps the key of a hint (e.g. "501" to a hint text)

    #: maps the key of a format constraint to the respective evaluation result
    format_constraints: dict[str, EvaluatedFormatConstraint]
    #: maps the key of a requirement_constraint to the respective evaluation result
    requirement_constraints: dict[str, ConditionFulfilledValue]

    packages: Optional[dict[constr(pattern=r"^\d+P$"), str]] = Field(default=None)  # type:ignore[valid-type]
    """
    maps the key of a package (e.g. '123') to the respective expression (e.g. '[1] U ([2] O [3])'
    """

    # pylint:disable=invalid-name
    #: optional guid
    id: Optional[UUID] = Field(default=None)


__all__ = ["ContentEvaluationResult"]
