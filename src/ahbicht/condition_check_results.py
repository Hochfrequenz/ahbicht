"""
This module contains the classes for the evaluation results.
A "result" is the outcome of a evaluation. It requires actual data to be present.
"""

from typing import Optional

import attr

# pylint: disable=too-few-public-methods, no-member


@attr.s(auto_attribs=True, kw_only=True)
class RequirementConstraintEvaluationResult:
    """
    A class for the result of the requirement constraint evaluation.
    """

    requirement_constraints_fulfilled: bool  # true if condition expression in regard to
    # requirement constraints evaluates to true
    requirement_is_conditional: bool  # true if it is dependent on requirement constraints
    format_constraints_expression: str
    hints: str  # Hint text that should be displayed in the frontend, e.g. "[501] Hinweis: 'ID der Messlokation'"


@attr.s(auto_attribs=True, kw_only=True)
class FormatConstraintEvaluationResult:
    """
    A class for the result of the format constraint evaluation.
    """

    format_constraints_fulfilled: bool  # true if data entered obey the format constraint expression
    error_message: Optional[str]  # All error messages that lead to not fulfilling the format constraint expression


@attr.s(auto_attribs=True, kw_only=True)
class ConditionCheckResult:
    """
    A class for the result of the overall condition check.
    """

    requirement_indicator: str  # i.e. "Muss", "Soll", "Kann", "X", "O", "U"
    requirement_constraint_evaluation_result: RequirementConstraintEvaluationResult
    format_constraint_evaluation_result: FormatConstraintEvaluationResult
