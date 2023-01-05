import uuid
from itertools import product
from typing import List

import inject
import pytest  # type:ignore[import]
from maus.models.anwendungshandbuch import AhbMetaInformation, DeepAnwendungshandbuch
from maus.models.edifact_components import (
    DataElementDataType,
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.validation.validation import (
    combine_requirements_of_different_levels,
    map_requirement_validation_values,
    validate_data_element_freetext,
    validate_data_element_valuepool,
    validate_deep_anwendungshandbuch,
    validate_segment,
    validate_segment_group,
    validate_segment_level,
)
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    SegmentLevelValidationResult,
    ValidationResultInContext,
    ListOfValidationResultInContext,
)
from ahbicht.validation.validation_values import RequirementValidationValue

# TODO: Add testcases for segment_requirement is None & soll_is_required = False
from unittests.defaults import default_test_format, default_test_version, empty_default_test_data

# lovric = list_of_validation_result_in_context


class TestValidationResults:
    @pytest.mark.parametrize(
        "lovric_actual, edi_seed_to_bo4e_mappings, lovric_expected",
        [
            pytest.param(
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['Transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['EdiFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
                {
                    "$['Transaktionsgrund']": "$['transaktionsdaten']['transaktionsgrund']",
                    "$['EdiFoo']": "$['stammdaten'][0]['applicationFoo']",
                },
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    async def test_lovric_replace_edi_seed_paths_with_bo4e_paths(
        self, lovric_actual: ListOfValidationResultInContext, edi_seed_to_bo4e_mappings, lovric_expected
    ):
        lovric_actual.replace_edi_seed_paths_with_bo4e_paths(edi_seed_to_bo4e_mappings)
        assert lovric_actual == lovric_expected
