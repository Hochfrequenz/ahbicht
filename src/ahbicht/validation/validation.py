"""
This module provides the functions to validate segment group, segments and data elements.
"""

import asyncio
from typing import Optional, List

from maus.models.edifact_components import (
    DataElement,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    SegmentLevel,
)

from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    SegmentLevelValidationResult,
    ValidationResult,
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import FormatValidationValue, RequirementValidationValue

# pylint: disable=too-few-public-methods, no-member, no-self-use, unused-argument


async def validate_root_segment_level(
    segment_level: SegmentLevel,
    soll_is_required: bool = True,
) -> List[ValidationResultInContext]:
    """
    Validates the root segment group or segment and its children by handing them
    over to specialized functions for each kind.
    :param segment_level: the segment group or segment that should be validated
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the segment or segment group including its children
    """
    if isinstance(segment_level, SegmentGroup):
        return await validate_segment_group(segment_group=segment_level, soll_is_required=soll_is_required)

    if isinstance(segment_level, Segment):
        return await validate_segment(segment=segment_level, soll_is_required=soll_is_required)

    raise NotImplementedError("Unexpected type for segement_level")


async def validate_segment_group(
    segment_group: SegmentGroup,
    higher_segment_group_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required: bool = True,
) -> List[ValidationResultInContext]:
    """
    Validates a segment group and its containing segment groups and segments.
    :param segment_group: the segment_group that should be validated
    :param higher_segment_group_requirement: the requirement of the segment_group's segment_group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the segment group
    """

    # validation of this segment group
    if higher_segment_group_requirement == RequirementValidationValue.IS_FORBIDDEN:
        segment_group_validation = SegmentLevelValidationResult(
            requirement_validation=RequirementValidationValue.IS_FORBIDDEN
        )
    else:
        segment_group_validation = await get_segment_level_requirement_validation_value(
            segment_group, higher_segment_group_requirement, soll_is_required
        )

    validation_results_in_context = [
        ValidationResultInContext(discriminator=segment_group.discriminator, validation_result=segment_group_validation)
    ]

    tasks = []

    # validation of lower segment_groups
    if segment_group.segment_groups:
        for lower_segment_group in segment_group.segment_groups:
            tasks.append(
                validate_segment_group(
                    lower_segment_group,
                    segment_group_validation.requirement_validation,
                    soll_is_required,
                )
            )

    # validation of lower segments
    if segment_group.segments:
        for segment in segment_group.segments:
            tasks.append(
                validate_segment(
                    segment,
                    segment_group_validation.requirement_validation,
                    soll_is_required,
                )
            )

    validation_results_of_children = await asyncio.gather(*tasks)

    for sublist in validation_results_of_children:
        for item in sublist:
            validation_results_in_context.append(item)

    return validation_results_in_context


async def validate_segment(
    segment: Segment,
    segment_group_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required: bool = True,
) -> List[ValidationResultInContext]:
    """
    Validates a segment and its containing dataelements
    :param segment: the segment that should be validated
    :param segment_group_requirement: the requirement of the segment's segment_group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the segment and its containing dataelements
    """

    # validation of this segment
    if segment_group_requirement == RequirementValidationValue.IS_FORBIDDEN:
        segment_validation = SegmentLevelValidationResult(
            requirement_validation=RequirementValidationValue.IS_FORBIDDEN
        )
    else:
        segment_validation = await get_segment_level_requirement_validation_value(
            segment, segment_group_requirement, soll_is_required
        )

    validation_results_in_context = [
        ValidationResultInContext(discriminator=segment.discriminator, validation_result=segment_validation)
    ]

    tasks = []

    # validation of this segments dataelements
    for dataelement in segment.data_elements:
        tasks.append(validate_dataelement(dataelement, segment_validation.requirement_validation))

    validation_results_in_context_dataelements = await asyncio.gather(*tasks)

    return [*validation_results_in_context, *validation_results_in_context_dataelements]


async def get_segment_level_requirement_validation_value(
    segment_level: SegmentLevel,
    higher_segment_group_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required: bool = True,
) -> SegmentLevelValidationResult:
    """
    Parses and evaluates a segment level expression and maps it to a requirement validation value,
    also depending on a higher segment group requirement if present.
    :param segment_level: the segment or segment group that should be validated
    :param higher_segment_group_requirement: the requirement of the segment level's segment group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: Validation Result of the Dataelement
    """

    expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(segment_level.ahb_expression)
    evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=None)

    requirement_validation_without_hierarchy = map_requirement_validation_values(
        evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled,
        requirement_indicator=evaluation_result.requirement_indicator,
        soll_is_required=soll_is_required,
    )

    requirement_validation = combine_requirements_of_different_levels(
        higher_level_requirement=higher_segment_group_requirement,
        lower_level_requirement=requirement_validation_without_hierarchy,
    )

    return SegmentLevelValidationResult(
        requirement_validation=requirement_validation,
        hints=evaluation_result.requirement_constraint_evaluation_result.hints,
    )


async def validate_dataelement(
    dataelement: DataElement,
    segment_requirement: RequirementValidationValue,
    soll_is_required=True,
) -> ValidationResult:
    """
    Validates data elements by handing them over to specialized functions for freetext or value pool dataelements.
    :param dataelement: the dataelement that should be validated
    :param segment_requirement: the requirement of the dataelement's segment, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: Validation Result of the Data element
    """
    if isinstance(dataelement, DataElementFreeText):
        return await validate_dataelement_freetext(dataelement, segment_requirement, soll_is_required)
    if isinstance(dataelement, DataElementValuePool):
        return await validate_dataelement_valuepool(dataelement, segment_requirement)
    raise NotImplementedError("Unexpected type for dataelement")


async def validate_dataelement_freetext(
    dataelement: DataElementFreeText,
    segment_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required=True,
) -> DataElementValidationResult:
    """
    Validates a freetext dataelement, e.g. 'Dokumentennummer'.
    :param dataelement: the dataelement that should be validated
    :param segment_requirement: the requirement of the dataelement's segment, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, if it should be handled like KANN
    :return: Validation Result of the Dataelement
    """

    expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(dataelement.ahb_expression)
    evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=dataelement.entered_input)

    # requirement constraints
    requirement_validation_without_input_without_hierachry = map_requirement_validation_values(
        evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled,
        evaluation_result.requirement_indicator,
        soll_is_required,
    )
    requirement_validation_without_input = combine_requirements_of_different_levels(
        segment_requirement, requirement_validation_without_input_without_hierachry
    )

    # format constraints
    if evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled:
        format_validation = FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED
    else:
        format_validation = FormatValidationValue.FORMAT_CONSTRAINTS_ARE_NOT_FULFILLED

    if dataelement.entered_input:
        requirement_validation = RequirementValidationValue(str(requirement_validation_without_input) + "_AND_FILLED")
    else:
        requirement_validation = RequirementValidationValue(str(requirement_validation_without_input) + "_AND_EMPTY")

    return ValidationResultInContext(
        discriminator=dataelement.discriminator,
        validation_result=DataElementValidationResult(
            requirement_validation=requirement_validation,
            format_validation=format_validation,
            format_error_message=evaluation_result.format_constraint_evaluation_result.error_message,
            hints=evaluation_result.requirement_constraint_evaluation_result.hints,
        ),
    )


async def validate_dataelement_valuepool(
    dataelement: DataElementValuePool,
    segment_requirement: RequirementValidationValue,
) -> DataElementValidationResult:
    """
    Validates a value pool data element which depends on the requirement status of its segment.
    :param dataelement: the dataelement that should be validated
    :param segment_requirement: the requirement of the dataelement's segment, e.g. IS_REQUIRED
    :returns: Validation Result of the Dataelement
    """
    possible_values = []

    # Since the conditions behind the qualifiers only say if this qualifier is possible or not,
    # the overall requirement is inherited from the dataelement's segment.
    # Only exception is if no dataelement is possible, see below
    requirement_validation_dataelement = segment_requirement

    if segment_requirement != RequirementValidationValue.IS_FORBIDDEN:
        # it seems like all single value dataelements (except freetext) are just labeled "X"
        if len(dataelement.value_pool) == 1:
            possible_values = list(dataelement.value_pool)
            hints = None
        # value pool > 1
        else:
            for qualifier, expression in dataelement.value_pool.items():
                expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)
                evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=None)
                if evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled:
                    possible_values.append(qualifier)
                hints = None  # TODO: Get all hints from possible values

    # if no possible values are found, the requirement is set to forbidden
    # pylint: disable = pointless-statement
    # Case: segment_requirement is required, but no possible values are appended
    if not possible_values:
        requirement_validation_dataelement == RequirementValidationValue.IS_FORBIDDEN
        hints = None

    return ValidationResultInContext(
        discriminator=dataelement.discriminator,
        validation_result=DataElementValidationResult(
            requirement_validation=requirement_validation_dataelement,
            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
            hints=hints,  # todo: hints might be referenced before assignment
            possible_values=possible_values,
        ),
    )


def map_requirement_validation_values(
    requirement_constraints_are_fulfilled: bool,
    requirement_indicator: RequirementIndicator,
    soll_is_required: bool = True,
) -> RequirementValidationValue:
    """
    Returns requirement validation value according to the requirement indicator
    and whether the requirements constraints are fulfilled.
    :param requirement_constraints_are_fulfilled: true if requirement constraints are fulfilled
    :param requirement_indicator: requirement indicator, e.g MUSS, SOLL, KANN, X, O, U
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: mapped requirement validation value
    """

    # sets soll according to soll_is_required
    if requirement_indicator == ModalMark.SOLL:
        if soll_is_required:
            requirement_indicator = ModalMark.MUSS
        else:
            requirement_indicator = ModalMark.KANN

    if not requirement_constraints_are_fulfilled:
        requirement_validation = RequirementValidationValue.IS_FORBIDDEN
    else:
        if requirement_indicator == ModalMark.MUSS or isinstance(requirement_indicator, PrefixOperator):
            requirement_validation = RequirementValidationValue.IS_REQUIRED
        elif requirement_indicator == ModalMark.KANN:
            requirement_validation = RequirementValidationValue.IS_OPTIONAL

    return requirement_validation


def combine_requirements_of_different_levels(
    higher_level_requirement: Optional[RequirementValidationValue],
    lower_level_requirement: RequirementValidationValue,
) -> RequirementValidationValue:
    """
    Combines two requirement values of a higher and lower level.
    Requirement status from `segment group` beats `segment` beats `data element`
    Forbidden is catched beforehand to make further evaluation unnecessary.

    | Higher group | lower group | result    |
    | ------------ | ----------- | --------- |
    | required     | required    | required  |
    | required     | forbidden   | forbidden |
    | required     | optional    | optional  |
    | optional     | required    | optional  |
    | optional     | forbidden   | forbidden |
    | optional     | optional    | optional  |

    """
    if higher_level_requirement is None:
        return lower_level_requirement

    if higher_level_requirement == RequirementValidationValue.IS_REQUIRED:
        return lower_level_requirement
    if higher_level_requirement == RequirementValidationValue.IS_OPTIONAL:
        if lower_level_requirement == RequirementValidationValue.IS_REQUIRED:
            return RequirementValidationValue.IS_OPTIONAL  # TODO: Let's discuss this (optional/optionalrequired?)
        return lower_level_requirement

    raise ValueError("Unexpected higher_level_requirement value")
