"""
This module contains the classes for the evaluation results.
A "result" is the outcome of a evaluation. It requires actual data to be present.
"""

from typing import Optional

import attr

# pylint: disable=too-few-public-methods, no-member, no-self-use, unused-argument
from marshmallow import Schema, fields, post_load


@attr.s(auto_attribs=True, kw_only=True)
class RequirementConstraintEvaluationResult:
    """
    A class for the result of the requirement constraint evaluation.
    """

    requirement_constraints_fulfilled: bool  # true if condition expression in regard to
    # requirement constraints evaluates to true
    requirement_is_conditional: bool  # true if it is dependent on requirement constraints

    format_constraints_expression: Optional[str] = attr.ib(default=None)
    hints: Optional[str] = attr.ib(default=None)  # Hint text that should be displayed in the frontend,
    # e.g. "[501] Hinweis: 'ID der Messlokation'"


class RequirementConstraintEvaluationResultSchema(Schema):
    """
    A schema to (de-)serialize RequirementConstraintEvaluationResult
    """

    requirement_constraints_fulfilled = fields.Boolean()
    requirement_is_conditional = fields.Boolean()

    format_constraints_expression = fields.String(load_default=None)
    hints = fields.String(load_default=None)

    @post_load
    def deserialize(self, data, **kwargs) -> RequirementConstraintEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual RequirementConstraintEvaluationResult
        :param data:
        :param kwargs:
        :return:
        """
        return RequirementConstraintEvaluationResult(**data)


@attr.s(auto_attribs=True, kw_only=True)
class FormatConstraintEvaluationResult:
    """
    A class for the result of the format constraint evaluation.
    """

    format_constraints_fulfilled: bool  # true if data entered obey the format constraint expression

    error_message: Optional[str] = attr.ib(
        default=None
    )  # All error messages that lead to not fulfilling the format constraint expression


class FormatConstraintEvaluationResultSchema(Schema):
    """
    A class to (de-)serialize FormatConstraintEvaluationResult
    """

    format_constraints_fulfilled = fields.Boolean()
    error_message = fields.String(allow_none=True, missing=None)

    @post_load
    def deserialize(self, data, **kwargs) -> FormatConstraintEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual FormatConstraintEvaluationResult
        :param data:
        :param kwargs:
        :return:
        """
        return FormatConstraintEvaluationResult(**data)


@attr.s(auto_attribs=True, kw_only=True)
class AhbExpressionEvaluationResult:
    """
    A class for the result of the overall condition check.
    """

    requirement_indicator: str  # i.e. "Muss", "M", "Soll", "S", "Kann", "K", "X", "O", "U"
    requirement_constraint_evaluation_result: RequirementConstraintEvaluationResult
    format_constraint_evaluation_result: FormatConstraintEvaluationResult


class AhbExpressionEvaluationResultSchema(Schema):
    """
    A schema to (de-)serialize AhbExpressionEvaluationResults
    """

    requirement_indicator = fields.String(required=True, allow_none=True)
    requirement_constraint_evaluation_result = fields.Nested(RequirementConstraintEvaluationResultSchema())
    format_constraint_evaluation_result = fields.Nested(FormatConstraintEvaluationResultSchema())

    @post_load
    def deserialize(self, data, **kwargs) -> AhbExpressionEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual AhbExpressionEvaluationResult
        :param data:
        :param kwargs:
        :return:
        """
        return AhbExpressionEvaluationResult(**data)