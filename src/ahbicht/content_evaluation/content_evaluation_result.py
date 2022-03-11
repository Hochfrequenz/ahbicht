"""
This module contains a class to store _all_ kinds of content evaluation results.
"""

from typing import Dict, Optional
from uuid import UUID

import attrs
from marshmallow import Schema, fields, post_load

from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)


# pylint: disable=too-few-public-methods, no-self-use, unused-argument
@attrs.define(auto_attribs=True)
class ContentEvaluationResult:
    """
    A class that holds the results of a full content evaluation (meaning all hints, requirement constraints and
    format constraints have been evaluated)
    """

    #: maps the key of a hint (e.g. "501" to a hint text)
    hints: Dict[str, Optional[str]] = attrs.field(
        validator=attrs.validators.deep_mapping(
            key_validator=attrs.validators.instance_of(str),
            value_validator=attrs.validators.optional(attrs.validators.instance_of(str)),
        )
    )

    #: maps the key of a format constraint to the respective evaluation result
    format_constraints: Dict[str, EvaluatedFormatConstraint] = attrs.field(
        validator=attrs.validators.deep_mapping(
            key_validator=attrs.validators.instance_of(str),
            value_validator=attrs.validators.instance_of(EvaluatedFormatConstraint),
        )
    )
    #: maps the key of a requirement_constraint to the respective evaluation result
    requirement_constraints: Dict[str, ConditionFulfilledValue] = attrs.field(
        validator=attrs.validators.deep_mapping(
            key_validator=attrs.validators.instance_of(str),
            value_validator=attrs.validators.instance_of(ConditionFulfilledValue),
        )
    )

    packages: Optional[Dict[str, str]] = attrs.field(  # Union[str, ConditionFulfilledValue]]
        validator=attrs.validators.optional(
            attrs.validators.deep_mapping(  # type: ignore[arg-type]
                key_validator=attrs.validators.and_(
                    attrs.validators.instance_of(str),
                    attrs.validators.matches_re(r"^\d+P$"),  # this is to avoid someone passes '123' instead of '123P'
                ),
                # todo: implement wiederholbarkeiten
                value_validator=attrs.validators.instance_of(str),
            )
        ),
        default=None,
    )
    """
    maps the key of a package (e.g. '123') to the respective expression (e.g. '[1] U ([2] O [3])'
    """

    # pylint:disable=invalid-name
    #: optional guid
    id: Optional[UUID] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(UUID)), default=None
    )


class ContentEvaluationResultSchema(Schema):
    """
    A schema to (de)serialize ContentEvaluationResults
    """

    hints = fields.Dict(keys=fields.String(allow_none=False), values=fields.String(allow_none=True), required=True)
    format_constraints = fields.Dict(
        keys=fields.String(allow_none=False),
        values=fields.Nested(EvaluatedFormatConstraintSchema, allow_none=False, required=True),
        required=True,
    )
    requirement_constraints = fields.Dict(
        keys=fields.String(allow_none=False), values=fields.String(allow_none=False), required=True
    )
    packages = fields.Dict(
        keys=fields.String(allow_none=False),
        values=fields.String(allow_none=False),
        required=False,
        load_default={},
        allow_none=True,
    )
    id = fields.UUID(required=False, dump_default=False, load_default=None)

    @post_load
    def deserialize(self, data, **kwargs) -> ContentEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual ContentEvaluationResult
        """
        if "requirement_constraints" in data:
            # because of attrs.validators.deep_iterable this parsing step has to happen before binding to the instance
            for rc_key, rc_value in data["requirement_constraints"].items():
                if not isinstance(rc_value, ConditionFulfilledValue):
                    for enum_value in ConditionFulfilledValue:
                        if str(rc_value).upper() == enum_value.value:
                            data["requirement_constraints"][rc_key] = ConditionFulfilledValue(enum_value.value)
                            break
        result = ContentEvaluationResult(**data)
        return result
