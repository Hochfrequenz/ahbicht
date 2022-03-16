"""
This module provides the functions to validate segment groups, segments and data elements.
"""

import asyncio
from typing import Dict, List, Optional

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
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import RequirementValidationValue


async def validate_segment_level(
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
    parent_segment_group_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required: bool = True,
) -> List[ValidationResultInContext]:
    """
    Validates a segment group and the segment groups and segments it contains.
    :param segment_group: the segment_group that should be validated
    :param parent_segment_group_requirement: the requirement of the segment_group's segment_group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the segment group and the segment groups and segments it contains.
    """

    # validation of this segment group
    if parent_segment_group_requirement is RequirementValidationValue.IS_FORBIDDEN:
        segment_group_validation = SegmentLevelValidationResult(
            requirement_validation=RequirementValidationValue.IS_FORBIDDEN
        )
    else:
        segment_group_validation = await get_segment_level_requirement_validation_value(
            segment_group, parent_segment_group_requirement, soll_is_required
        )

    validation_results_in_context = [
        ValidationResultInContext(discriminator=segment_group.discriminator, validation_result=segment_group_validation)
    ]

    tasks = []

    # validation of child_segment_group s
    if segment_group.segment_groups:
        for child_segment_group in segment_group.segment_groups:
            tasks.append(
                validate_segment_group(
                    child_segment_group,
                    segment_group_validation.requirement_validation,
                    soll_is_required,
                )
            )

    # validation of child segments
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
    Validates a segment and the data elements it contains.
    :param segment: the segment that should be validated
    :param segment_group_requirement: the requirement of the segment's parent segment_group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the segment and the data elements it contains
    """

    # validation of this segment
    if segment_group_requirement is RequirementValidationValue.IS_FORBIDDEN:
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

    # validation of this segments data elements
    for data_element in segment.data_elements:
        tasks.append(validate_data_element(data_element, segment_validation.requirement_validation))

    validation_results_in_context_data_elements = await asyncio.gather(*tasks)

    return [*validation_results_in_context, *validation_results_in_context_data_elements]


async def get_segment_level_requirement_validation_value(
    segment_level: SegmentLevel,
    parent_segment_group_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required: bool = True,
) -> SegmentLevelValidationResult:
    """
    Parses and evaluates a segment level expression and maps it to a requirement validation value,
    also depending on a parent segment group requirement if present.
    :param segment_level: the segment or segment group that should be validated
    :param parent_segment_group_requirement: the requirement of the segment level's segment group, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: Validation Result of the data element
    """

    expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(segment_level.ahb_expression)
    evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=None)

    requirement_validation_without_hierarchy = map_requirement_validation_values(
        evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled,
        requirement_indicator=evaluation_result.requirement_indicator,
        soll_is_required=soll_is_required,
    )

    requirement_validation = combine_requirements_of_different_levels(
        parent_level_requirement=parent_segment_group_requirement,
        child_level_requirement=requirement_validation_without_hierarchy,
    )

    return SegmentLevelValidationResult(
        requirement_validation=requirement_validation,
        hints=evaluation_result.requirement_constraint_evaluation_result.hints,
    )


async def validate_data_element(
    data_element: DataElement,
    segment_requirement: RequirementValidationValue,
    soll_is_required=True,
) -> ValidationResultInContext:
    """
    Validates data elements by handing them over to specialized functions for freetext or value pool data elements.
    :param dat_aelement: the data element that should be validated
    :param segment_requirement: the requirement of the data element's parent segment, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: Validation Result of the Data element
    """
    if isinstance(data_element, DataElementFreeText):
        return await validate_data_element_freetext(data_element, segment_requirement, soll_is_required)
    if isinstance(data_element, DataElementValuePool):
        return await validate_data_element_valuepool(data_element, segment_requirement)
    raise NotImplementedError("Unexpected type for data element")


async def validate_data_element_freetext(
    data_element: DataElementFreeText,
    segment_requirement: Optional[RequirementValidationValue] = None,
    soll_is_required=True,
) -> ValidationResultInContext:
    """
    Validates a freetext data element, e.g. 'Dokumentennummer'.
    :param data_element: the data element that should be validated
    :param segment_requirement: the requirement of the data element's parent segment, e.g. IS_REQUIRED
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, if it should be handled like KANN
    :return: Validation Result of the DataElement
    """

    expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(data_element.ahb_expression)
    evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=data_element.entered_input)

    # requirement constraints
    requirement_validation_without_input_without_hierarchy = map_requirement_validation_values(
        evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled,
        evaluation_result.requirement_indicator,
        soll_is_required,
    )
    requirement_validation_without_input = combine_requirements_of_different_levels(
        segment_requirement, requirement_validation_without_input_without_hierarchy
    )

    if data_element.entered_input:
        requirement_validation = RequirementValidationValue(str(requirement_validation_without_input) + "_AND_FILLED")
    else:
        requirement_validation = RequirementValidationValue(str(requirement_validation_without_input) + "_AND_EMPTY")

    return ValidationResultInContext(
        discriminator=data_element.discriminator,
        validation_result=DataElementValidationResult(
            requirement_validation=requirement_validation,
            format_validation_fulfilled=evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled,  # pylint: disable=line-too-long
            format_error_message=evaluation_result.format_constraint_evaluation_result.error_message,
            hints=evaluation_result.requirement_constraint_evaluation_result.hints,
        ),
    )


async def validate_data_element_valuepool(
    data_element: DataElementValuePool,
    segment_requirement: RequirementValidationValue,
) -> ValidationResultInContext:
    """
    Validates a value pool data element which depends on the requirement status of its segment.
    :param data_element: the data element that should be validated
    :param segment_requirement: the requirement of the data element's parent segment, e.g. IS_REQUIRED
    :returns: Validation Result of the DataElement
    """
    possible_values: Dict[str, str] = {}

    # Since the conditions behind the qualifiers only say if this qualifier is possible or not,
    # the overall requirement is inherited from the data element's parent segment.
    # Only exception is if no qualifier is possible, see below
    requirement_validation_data_element = segment_requirement

    if segment_requirement is not RequirementValidationValue.IS_FORBIDDEN:
        # it seems like all single value data elements (except freetext) are just labeled "X"
        if len(data_element.value_pool) == 1:
            possible_values[data_element.value_pool[0].qualifier] = data_element.value_pool[0].meaning
            hints = None
        else:  # len(value_pool) >1
            for value_pool_entry in data_element.value_pool:
                expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(
                    value_pool_entry.ahb_expression
                )
                evaluation_result = await evaluate_ahb_expression_tree(expression_tree, entered_input=None)
                if evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled:
                    possible_values[value_pool_entry.qualifier] = value_pool_entry.meaning
                hints = None  # TODO: Get all hints from possible values

    # if no possible values are found, the requirement is set to forbidden
    # pylint: disable = pointless-statement
    # Case: segment_requirement is required, but no possible values are appended
    if not possible_values:
        requirement_validation_data_element is RequirementValidationValue.IS_FORBIDDEN
        hints = None

    return ValidationResultInContext(
        discriminator=data_element.discriminator,
        validation_result=DataElementValidationResult(
            requirement_validation=requirement_validation_data_element,
            format_validation_fulfilled=True,
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
    if requirement_indicator is ModalMark.SOLL:
        if soll_is_required:
            requirement_indicator = ModalMark.MUSS
        else:
            requirement_indicator = ModalMark.KANN

    if not requirement_constraints_are_fulfilled:
        requirement_validation = RequirementValidationValue.IS_FORBIDDEN
    else:
        if requirement_indicator is ModalMark.MUSS or isinstance(requirement_indicator, PrefixOperator):
            requirement_validation = RequirementValidationValue.IS_REQUIRED
        elif requirement_indicator is ModalMark.KANN:
            requirement_validation = RequirementValidationValue.IS_OPTIONAL

    return requirement_validation


def combine_requirements_of_different_levels(
    parent_level_requirement: Optional[RequirementValidationValue],
    child_level_requirement: RequirementValidationValue,
) -> RequirementValidationValue:
    """
    Combines two requirement values of a parent and child level.
    Requirement status from `segment group` beats `segment` beats `data element`
    Forbidden on parent level is caught beforehand to make further evaluation unnecessary.

    | parent group | child group | result    |
    | ------------ | ----------- | --------- |
    | required     | required    | required  |
    | required     | forbidden   | forbidden |
    | required     | optional    | optional  |
    | optional     | required    | optional  |
    | optional     | forbidden   | forbidden |
    | optional     | optional    | optional  |

    """
    if parent_level_requirement is None:
        return child_level_requirement

    if parent_level_requirement is RequirementValidationValue.IS_REQUIRED:
        return child_level_requirement
    if parent_level_requirement is RequirementValidationValue.IS_OPTIONAL:
        if child_level_requirement is RequirementValidationValue.IS_REQUIRED:
            return RequirementValidationValue.IS_OPTIONAL  # TODO: Let's discuss this (optional/optionalrequired?)
        return child_level_requirement

    raise ValueError("Unexpected parent_level_requirement value")
