"""
This module provides the functions to validate segment groups, segments and data elements.
"""

import asyncio
from typing import Awaitable, Dict, List, Optional

from maus.models.anwendungshandbuch import DeepAnwendungshandbuch
from maus.models.edifact_components import (
    DataElement,
    DataElementDataType,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    SegmentLevel,
)

from ahbicht.content_evaluation import fc_evaluators
from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions import InvalidExpressionError
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.validation import validation_logger
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    SegmentLevelValidationResult,
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import RequirementValidationValue


async def validate_deep_anwendungshandbuch(
    deep_ahb: DeepAnwendungshandbuch, soll_is_required: bool = True
) -> List[ValidationResultInContext]:
    """
    Validates a deep Anwendungshandbuch aka 'MAUS' as provided from the package maus.
    :param deep_ahb: the deep Anwendungshandbuch that should be validated
    :param soll_is_required: true (default) if SOLL should be handled like MUSS, false if it should be handled like KANN
    :return: List of ValidationResultInContext of the deep Anwendungshandbuch
    """

    tasks: List[Awaitable[List[ValidationResultInContext]]] = []

    for segment_group in deep_ahb.lines:
        tasks.append(
            validate_segment_group(
                segment_group=segment_group,
                soll_is_required=soll_is_required,
            )
        )

    validation_results_of_segment_groups: List[List[ValidationResultInContext]] = await asyncio.gather(*tasks)
    deep_ahb_validation_result: List[ValidationResultInContext] = []
    for sublist in validation_results_of_segment_groups:
        for item in sublist:
            deep_ahb_validation_result.append(item)
    validation_logger.debug("Validated %i segment groups", len(deep_ahb_validation_result))
    return deep_ahb_validation_result


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

    raise NotImplementedError("Unexpected type for segment_level")


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

    if segment_group_validation.requirement_validation is not RequirementValidationValue.IS_FORBIDDEN:
        tasks: List[Awaitable[List[ValidationResultInContext]]] = []

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

        validation_results_of_children: List[List[ValidationResultInContext]] = await asyncio.gather(*tasks)

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

    # validate this segments' data elements only if segment is not forbidden
    if segment_validation.requirement_validation is RequirementValidationValue.IS_FORBIDDEN:
        validation_results_in_context_data_elements = []
    else:
        tasks: List[Awaitable[ValidationResultInContext]] = []
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

    expression_tree = await parse_expression_including_unresolved_subexpressions(
        segment_level.ahb_expression, resolve_packages=True
    )
    try:
        evaluation_result = await evaluate_ahb_expression_tree(expression_tree)
    except InvalidExpressionError as invalid_expr_error:
        validation_logger.warning("The expression '%s' is invalid. Returning IS_OPTIONAL", segment_level.ahb_expression)
        return SegmentLevelValidationResult(
            hints=invalid_expr_error.error_message, requirement_validation=RequirementValidationValue.IS_OPTIONAL
        )

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
    :param data_element: the data element that should be validated
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
    expression_tree = await parse_expression_including_unresolved_subexpressions(
        data_element.ahb_expression, resolve_packages=True
    )
    fc_evaluators.text_to_be_evaluated_by_format_constraint.set(data_element.entered_input)
    try:
        evaluation_result = await evaluate_ahb_expression_tree(expression_tree)
    except InvalidExpressionError as invalid_expr_error:
        validation_logger.warning(
            "The expression '%s' @ '%s' is invalid. Returning IS_OPTIONAL",
            data_element.ahb_expression,
            data_element.discriminator,
        )
        return ValidationResultInContext(
            validation_result=DataElementValidationResult(
                requirement_validation=RequirementValidationValue.IS_OPTIONAL,
                format_validation_fulfilled=True,
                format_error_message=None,
                hints=invalid_expr_error.error_message,
                data_element_data_type=DataElementDataType.TEXT,
            ),
            discriminator=data_element.discriminator,
        )

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
    result = DataElementValidationResult(
        requirement_validation=requirement_validation,
        format_validation_fulfilled=evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled,  # pylint: disable=line-too-long
        format_error_message=evaluation_result.format_constraint_evaluation_result.error_message,
        hints=evaluation_result.requirement_constraint_evaluation_result.hints,
        data_element_data_type=DataElementDataType.TEXT,  # set text by default, later check if it might be a date
    )
    if data_element.value_type is not None:
        result.data_element_data_type = data_element.value_type  # this will set the type to DATE, if necessary
    validation_logger.debug(
        "The validation of expression '%s' for the data element with discriminator '%s' resulted in %s",
        data_element.ahb_expression,
        data_element.discriminator,
        str(result),
    )
    return ValidationResultInContext(
        discriminator=data_element.discriminator,
        validation_result=result,
    )


async def validate_data_element_valuepool(
    data_element: DataElementValuePool,
    segment_requirement: RequirementValidationValue,
) -> ValidationResultInContext:
    """
    Validates a value pool data element which depends on the requirement status of its segment.
    :param data_element: the data element that should be validated
    :param segment_requirement: the requirement of the data element's parent segment, e.g. IS_REQUIRED
    :return: Validation Result of the DataElement
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
                expression_tree = await parse_expression_including_unresolved_subexpressions(
                    value_pool_entry.ahb_expression, resolve_packages=True
                )
                try:
                    evaluation_result = await evaluate_ahb_expression_tree(expression_tree)
                except InvalidExpressionError as invalid_expr_error:
                    validation_logger.warning(
                        "The expression '%s' @ '%s' is invalid. Treating value pool entry as optional",
                        value_pool_entry.ahb_expression,
                        data_element.discriminator,
                    )
                    evaluation_result = AhbExpressionEvaluationResult(
                        format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                            format_constraints_fulfilled=True, error_message=None
                        ),
                        requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                            requirement_constraints_fulfilled=True,
                            requirement_is_conditional=True,
                            hints=invalid_expr_error.error_message,
                        ),
                        requirement_indicator=ModalMark.KANN,
                    )
                validation_logger.debug(
                    "The validation of value pool entry %s resulted in %s",
                    str(value_pool_entry),
                    str(evaluation_result),
                )
                if evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled:
                    possible_values[value_pool_entry.qualifier] = value_pool_entry.meaning
                hints = None  # TODO: Get all hints from possible values

    # if no possible values are found, the requirement is set to forbidden
    # pylint: disable = pointless-statement
    # Case: segment_requirement is required, but no possible values are appended
    fc_validation_result: bool = True  # by default Format Constraints are not evaluated for ValuePools
    if not possible_values:
        requirement_validation_data_element is RequirementValidationValue.IS_FORBIDDEN
        hints = None
    else:
        if data_element.entered_input in possible_values:
            requirement_validation_data_element = RequirementValidationValue.IS_REQUIRED_AND_FILLED
        elif data_element.entered_input:
            fc_validation_result = False  # we re-use the fc validation field to mark that the value is unexpected
            requirement_validation_data_element = RequirementValidationValue.IS_REQUIRED_AND_EMPTY
            hints = f"Der Wert '{data_element.entered_input}' ist nicht in: {{{', '.join(possible_values.keys())}}}"
            data_element.entered_input = None  # overwrite the illegal value
        else:
            requirement_validation_data_element = RequirementValidationValue.IS_REQUIRED_AND_EMPTY
    result = DataElementValidationResult(
        requirement_validation=requirement_validation_data_element,
        format_validation_fulfilled=fc_validation_result,
        hints=hints,  # todo: hints might be referenced before assignment
        possible_values=possible_values,
        data_element_data_type=DataElementDataType.VALUE_POOL,
    )
    validation_logger.debug(
        "The validation for the data element with discriminator '%s' resulted in %s",
        data_element.discriminator,
        str(result),
    )
    return ValidationResultInContext(
        discriminator=data_element.discriminator,
        validation_result=result,
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
