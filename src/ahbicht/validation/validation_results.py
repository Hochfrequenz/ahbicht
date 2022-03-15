"This module contains the classes for the validation results."

from abc import ABC
from typing import Dict, Optional

import attrs
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField  # type:ignore[import]

from ahbicht.validation.validation_values import RequirementValidationValue

# pylint: disable=too-few-public-methods, no-member, no-self-use, unused-argument


@attrs.define(auto_attribs=True, kw_only=True)
class ValidationResult(ABC):
    """Result of the validation"""

    #: In which requirement state is the field and is it filled or not?
    requirement_validation: RequirementValidationValue = attrs.field(
        validator=attrs.validators.instance_of(RequirementValidationValue)
    )
    #: Collected hints
    hints: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)), default=None
    )


class ValidationResultSchema(Schema):
    """
    A schema to (de-)serialize ValidationResult
    """

    requirement_validation = EnumField(RequirementValidationValue)
    hints = fields.String(load_default=None)

    @post_load
    def deserialize(self, data, **kwargs) -> ValidationResult:
        """
        Converts the barely typed data dictionary into an actual ValidationResult
        :param data:
        :param kwargs:
        :return:
        """
        return ValidationResult(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class SegmentLevelValidationResult(ValidationResult):
    """Result of the validation of a segment or segment group"""


class SegmentLevelValidationResultSchema(ValidationResultSchema):
    """
    A schema to (de-)serialize SegmentLevelValidationResult
    """

    @post_load
    def deserialize(self, data, **kwargs) -> SegmentLevelValidationResult:
        """
        Converts the barely typed data dictionary into an actual ValidationResult
        :param data:
        :param kwargs:
        :return:
        """
        return SegmentLevelValidationResult(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class DataElementValidationResult(ValidationResult):
    """Result of the validation of a data element"""

    #: Is the format constraint fulfilled or not?
    format_validation_fulfilled: bool = attrs.field(validator=attrs.validators.instance_of(bool))
    #: possible error message regarding the format constraints
    format_error_message: Optional[str] = attrs.field(
        validator=attrs.validators.optional(attrs.validators.instance_of(str)), default=None
    )
    #: possible qualifiers for value pool data elements
    possible_values: Optional[Dict[str, str]] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.deep_mapping(
                key_validator=attrs.validators.instance_of(str),
                value_validator=attrs.validators.instance_of(str),
                mapping_validator=attrs.validators.instance_of(dict),
            )
        ),
    )


class DataElementValidationResultSchema(ValidationResultSchema):
    """
    A schema to (de-)serialize DataElementValidationResult
    """

    format_validation_fulfilled = fields.Bool()
    format_error_message = fields.String(load_default=None)
    possible_values = fields.Dict(fields.Str, load_default=None)

    @post_load
    def deserialize(self, data, **kwargs) -> DataElementValidationResult:
        """
        Converts the barely typed data dictionary into an actual DataElementValidationResult
        :param data:
        :param kwargs:
        :return:
        """
        return DataElementValidationResult(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class ValidationResultInContext:
    """
    Class to set validation result in context, for example with its discriminator.
    """

    discriminator: str = attrs.field(validator=attrs.validators.instance_of(str))
    validation_result: ValidationResult = attrs.field(validator=attrs.validators.instance_of(ValidationResult))


class ValidationResultInContextSchema(Schema):
    """
    A schema to serialize ValidationResultInContext
    """

    discriminator = fields.String()
    validation_result = fields.Nested(ValidationResultSchema)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> ValidationResultInContext:
        """
        Serializes a ValidationResultDiscriminator
        so that the discriminator is the key and the validation_result the value.
        """
        return ValidationResultInContext(**data)
