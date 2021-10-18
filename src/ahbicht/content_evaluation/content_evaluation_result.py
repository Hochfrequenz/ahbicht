"""
This module contains a class to store _all_ kinds of content evaluation results.
"""
from typing import Dict, Optional
from uuid import UUID

import attr
from marshmallow import Schema, fields, post_dump, post_load, pre_dump

from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)

# pylint: disable=too-few-public-methods, no-self-use, unused-argument


@attr.s(auto_attribs=True)
class ContentEvaluationResult:
    """
    A class that holds the results of a full content evaluation (meaning all hints, requirement constraints and
    format constraints have been evaluated)
    """

    hints: Dict[str, Optional[str]]  # maps the key of a hint (e.g. "501" to a hint text)
    format_constraints: Dict[
        str, EvaluatedFormatConstraint
    ]  # maps the key of a format constraint to the respective evaluation result
    requirement_constraints: Dict[
        str, ConditionFulfilledValue
    ]  # maps the key of a requirement_constraint to the respective evaluation result
    id: Optional[UUID] = None  # optional guid


class ContentEvaluationResultSchema(Schema):
    """
    A schema to (de)serialize ContentEvaluationResults
    """

    hints = fields.Dict(keys=fields.String(allow_none=False), values=fields.String(allow_none=True), required=True)
    format_constraints = fields.Dict(
        keys=fields.String(allow_none=False),
        values=fields.Nested(EvaluatedFormatConstraintSchema, allow_none=False, required=True),
    )
    requirement_constraints = fields.Dict(
        keys=fields.String(allow_none=False), values=fields.String(allow_none=True), required=True
    )
    id = fields.UUID(required=False, dump_default=False)

    @post_load
    def deserialize(self, data, **kwargs) -> ContentEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual ContentEvaluationResult
        :param data:
        :param kwargs:
        :return:
        """
        result = ContentEvaluationResult(**data)
        for rc_key, rc_value in result.requirement_constraints.items():
            if not isinstance(rc_value, ConditionFulfilledValue):
                for enum_value in ConditionFulfilledValue:
                    if str(rc_value).upper() == enum_value.name:
                        result.requirement_constraints[rc_key] = ConditionFulfilledValue(enum_value.value)
                        break
        return result

    @post_dump
    def post_process_serialized_tree(self, data, **kwargs):
        """
        Create a string of tree object
        :param data:
        :param kwargs:
        :return:
        """
        if data and "requirement_constraints" in data:
            rc_constraints = data["requirement_constraints"]
            for rc_key in list(rc_constraints.keys()):
                if rc_constraints[rc_key].startswith("ConditionFulfilledValue."):
                    rc_constraints[rc_key] = rc_constraints[rc_key].split(".")[1]
        return data
