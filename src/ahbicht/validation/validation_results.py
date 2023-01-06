"This module contains the classes for the validation results."

from abc import ABC
from typing import Any, Dict, List, Optional, Union

import attrs
import maus.models.edifact_components
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField  # type:ignore[import]

from ahbicht.validation.validation_values import RequirementValidationValue

# pylint: disable=too-few-public-methods, no-member, unused-argument


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


class ValidationResultAttributesSchema(Schema):
    """
    A schema to pass on the attributes of ValidationResult
    """

    requirement_validation = EnumField(RequirementValidationValue)
    hints = fields.String(load_default=None)


class ValidationResultSchema(ValidationResultAttributesSchema):
    """
    A schema to (de-)serialize ValidationResult
    """

    @post_load
    def deserialize(self, data, **kwargs) -> ValidationResult:
        """
        Converts the barely typed data dictionary into an actual ValidationResult
        :param data:
        :param kwargs:
        :return:
        """
        return ValidationResult(**data)

    def dump(self, obj, **kwargs) -> Union[Any, list]:
        """
        A way to dump the subclasses DataElementValidationResult and SegmentLevelValidationResult
        of ValidationResult
        :param obj:
        :param kwargs:
        :return:
        """
        if isinstance(obj, DataElementValidationResult):
            return DataElementValidationResultSchema().dump(obj)
        if isinstance(obj, SegmentLevelValidationResult):
            return SegmentLevelValidationResultSchema().dump(obj)
        raise NotImplementedError(f"Data type of {obj} is not implemented for JSON serialization")


@attrs.define(auto_attribs=True, kw_only=True)
class SegmentLevelValidationResult(ValidationResult):
    """Result of the validation of a segment or segment group"""


class SegmentLevelValidationResultSchema(ValidationResultAttributesSchema):
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
    data_element_data_type: Optional[maus.models.edifact_components.DataElementDataType] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(maus.models.edifact_components.DataElementDataType)
        ),
    )
    """
    describes the type of the original data element that has been validated
    """


class DataElementValidationResultSchema(ValidationResultAttributesSchema):
    """
    A schema to (de-)serialize DataElementValidationResult
    """

    format_validation_fulfilled = fields.Bool()
    format_error_message = fields.String(load_default=None)
    possible_values = fields.Dict(fields.Str, load_default=None)
    data_element_data_type = EnumField(
        maus.models.edifact_components.DataElementDataType, required=False, load_default=None
    )

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

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> ValidationResultInContext:
        """
        Serializes a ValidationResultDiscriminator
        so that the discriminator is the key and the validation_result the value.
        """
        return ValidationResultInContext(**data)


@attrs.define(auto_attribs=True, kw_only=True)
class ListOfValidationResultInContext:
    """
    Class to set validation result in context, for example with its discriminator.
    This class is basically a wrapper around the list to have one place where the methods operating on the list do live.
    """

    validation_results: List[ValidationResultInContext] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(ValidationResultInContext),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )

    def replace_edi_domain_paths_with_application_domain_paths(
        self, edi_domain_to_application_domain_mappings: Dict[str, str]
    ) -> None:
        """
        replaces the edi domain discriminators in the list of validation results with the respective
        values from the application domain if present

        :param edi_domain_to_application_domain_mappings: dictionary with edi domain paths as keys
            and application domain paths as values, for example ediseed to bo4e mapping:
            "$[Dokument][0]['Transaktionsgrund']": "$['transaktionsdaten']['transaktionsgrund']"
        :return:
        """
        for validation_result in self.validation_results:
            if validation_result.discriminator.startswith("$"):
                edi_seed_path = validation_result.discriminator
                if edi_seed_path in edi_domain_to_application_domain_mappings:
                    bo4e_path = edi_domain_to_application_domain_mappings[edi_seed_path]
                    validation_result.discriminator = bo4e_path

    def filter_for_data_element_validation_results(self) -> None:
        """
        Filters the lost of validation results for only DataElementValidationResults
        """
        self.validation_results = list(
            filter(lambda vr: isinstance(vr.validation_result, DataElementValidationResult), self.validation_results)
        )

    @staticmethod
    def _is_boneycomb_path_result(validation_result_in_context: ValidationResultInContext) -> bool:
        return (
            "stammdaten" in validation_result_in_context.discriminator
            or "transaktionsdaten" in validation_result_in_context.discriminator
        )

    def filter_for_boneycomb_path_results(self) -> None:
        """
        Filters the list of validation results for those that have a boneycomb path as discriminator
        """
        self.validation_results = list(filter(self._is_boneycomb_path_result, self.validation_results))


class ListOfValidationResultInContextSchema(Schema):
    """
    A schema to deserialize ListOfValidationResultInContext
    """

    validation_results = fields.List(fields.Nested(ValidationResultInContextSchema))

    # pylint:disable=unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> ListOfValidationResultInContext:
        """
        Deserializes a ValidationResultDiscriminator
        """
        return ListOfValidationResultInContext(**data)
