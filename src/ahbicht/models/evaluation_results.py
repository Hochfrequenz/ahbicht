"""
This module contains the classes for the evaluation results.
A "result" is the outcome of an evaluation. It requires actual data to be present.
"""

# pylint: disable=too-few-public-methods, no-member,  unused-argument
from typing import Optional

from pydantic import BaseModel

from ahbicht.models.enums import RequirementIndicator


class RequirementConstraintEvaluationResult(BaseModel):
    """
    A class for the result of the requirement constraint evaluation.
    """

    #: true if condition expression in regard to requirement constraints evaluates to true
    requirement_constraints_fulfilled: Optional[bool]
    #: true if it is dependent on requirement constraints; None if there are unknown condition nodes left
    requirement_is_conditional: Optional[bool]

    format_constraints_expression: Optional[str] = None
    #: Hint text that should be displayed in the frontend, e.g. "[501] Hinweis: 'ID der Messlokation'"
    hints: Optional[str] = None


class FormatConstraintEvaluationResult(BaseModel):
    """
    A class for the result of the format constraint evaluation.
    """

    #: true if data entered obey the format constraint expression
    format_constraints_fulfilled: bool

    #: All error messages that lead to not fulfilling the format constraint expression
    error_message: Optional[str] = None


class AhbExpressionEvaluationResult(BaseModel):
    """
    A class for the result of an ahb expression evaluation.
    """

    requirement_indicator: RequirementIndicator  # i.e. "Muss", "M", "Soll", "S", "Kann", "K", "X", "O", "U"
    requirement_constraint_evaluation_result: RequirementConstraintEvaluationResult
    format_constraint_evaluation_result: FormatConstraintEvaluationResult
