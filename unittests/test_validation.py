import uuid
from itertools import product
from typing import List

import pytest  # type:ignore[import]
from maus.models.edifact_components import (
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
    validate_segment,
    validate_segment_group,
    validate_segment_level,
)
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    SegmentLevelValidationResult,
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import RequirementValidationValue

pytestmark = pytest.mark.asyncio

# TODO: Add testcases for segment_requirement is None & soll_is_required = False


class TestValidation:
    @pytest.fixture
    def inject_content_evaluation_result(self):
        content_evaluation_result = ContentEvaluationResult(
            hints={"501": "foo"},
            format_constraints={
                "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                "903": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="Format error 903"),
            },
            requirement_constraints={
                "2": ConditionFulfilledValue.FULFILLED,
                "3": ConditionFulfilledValue.UNFULFILLED,
            },
            id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
        )

        create_and_inject_hardcoded_evaluators(content_evaluation_result=content_evaluation_result)

    @pytest.mark.parametrize(
        "segment_level, expected_validation_result",
        [
            pytest.param(
                SegmentGroup(
                    ahb_expression="Muss[2]",
                    discriminator="SG10",
                    segments=[
                        Segment(
                            ahb_expression="Muss[2]",
                            discriminator="SG10 - Datum",
                            data_elements=[
                                DataElementFreeText(
                                    discriminator="SG10 - Datum - Einzug",
                                    data_element_id="1234",
                                    ahb_expression="M[2]",
                                    entered_input="",
                                )
                            ],
                        )
                    ],
                    segment_groups=[
                        SegmentGroup(
                            ahb_expression="Muss",
                            discriminator="SG11",
                            segments=[
                                Segment(
                                    ahb_expression="Muss[2]",
                                    discriminator="SG11 - Datum",
                                    data_elements=[
                                        DataElementFreeText(
                                            discriminator="SG11 - Datum - Auszug",
                                            data_element_id="1235",
                                            ahb_expression="M[2]",
                                            entered_input="",
                                        )
                                    ],
                                )
                            ],
                            segment_groups=None,
                        )
                    ],
                ),
                [
                    ValidationResultInContext(
                        discriminator="SG10",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG11",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG11 - Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG11 - Datum - Auszug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                ],
            ),
            pytest.param(
                Segment(
                    ahb_expression="Muss[2]",
                    discriminator="SG10 - Datum",
                    data_elements=[
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Einzug",
                            data_element_id="1234",
                            ahb_expression="M[2]",
                            entered_input="",
                        )
                    ],
                ),
                [
                    ValidationResultInContext(
                        discriminator="SG10 - Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                ],
            ),
        ],
    )
    async def test_validate_root_segment_level(
        self,
        segment_level,
        expected_validation_result,
        inject_content_evaluation_result,
    ):
        result = await validate_segment_level(segment_level)
        assert result == expected_validation_result

    @pytest.mark.parametrize(
        "segment_group, parent_segment_group_requirement, expected_validation_result",
        [
            pytest.param(
                SegmentGroup(
                    ahb_expression="Muss[2]",
                    discriminator="SG10",
                    segments=[
                        Segment(
                            ahb_expression="Muss[2]",
                            discriminator="SG10 - Datum",
                            data_elements=[
                                DataElementFreeText(
                                    discriminator="SG10 - Datum - Einzug",
                                    data_element_id="1234",
                                    ahb_expression="M[2]",
                                    entered_input="",
                                )
                            ],
                        )
                    ],
                    segment_groups=[],
                ),
                RequirementValidationValue.IS_REQUIRED,
                [
                    ValidationResultInContext(
                        discriminator="SG10",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                ],
            ),
        ],
    )
    async def test_validate_segment_group(
        self,
        segment_group,
        parent_segment_group_requirement,
        expected_validation_result,
        inject_content_evaluation_result,
    ):
        result = await validate_segment_group(segment_group, parent_segment_group_requirement)
        assert result == expected_validation_result

    @pytest.mark.parametrize(
        "segment, segment_group_requirement, expected_validation_result",
        [
            pytest.param(
                Segment(
                    ahb_expression="Muss[2]",
                    discriminator="SG10 Datum",
                    data_elements=[
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Einzug",
                            data_element_id="1234",
                            ahb_expression="M[2]",
                            entered_input="",
                        )
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                [
                    ValidationResultInContext(
                        discriminator="SG10 Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                ],
            ),
            pytest.param(
                Segment(
                    ahb_expression="Muss[2]",
                    discriminator="SG10 Datum",
                    data_elements=[
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Einzug",
                            data_element_id="1234",
                            ahb_expression="M[2]",
                            entered_input="",
                        ),
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Auszug",
                            data_element_id="1235",
                            ahb_expression="M[2]",
                            entered_input="",
                        ),
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                [
                    ValidationResultInContext(
                        discriminator="SG10 Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Auszug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                        ),
                    ),
                ],
            ),
        ],
    )
    async def test_validate_segment(
        self, segment, segment_group_requirement, expected_validation_result, inject_content_evaluation_result
    ):
        result = await validate_segment(segment, segment_group_requirement)
        assert result == expected_validation_result

    @pytest.mark.parametrize(
        "data_element, segment_requirement, expected_validation",
        [
            pytest.param(
                DataElementFreeText(
                    discriminator="SG1", ahb_expression="X", entered_input="bar", data_element_id="1234"
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_FILLED,
                        format_validation_fulfilled=True,
                    ),
                ),
            ),
            pytest.param(
                DataElementFreeText(discriminator="SG1", ahb_expression="X", entered_input="", data_element_id="1234"),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                        format_validation_fulfilled=True,
                    ),
                ),
            ),
            pytest.param(
                DataElementFreeText(
                    discriminator="SG1", ahb_expression="M[903][2]U[501]", entered_input="", data_element_id="1234"
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                        format_validation_fulfilled=False,
                        format_error_message="Format error 903",
                        hints="foo",
                    ),
                ),
            ),
            pytest.param(
                DataElementFreeText(
                    discriminator="SG1", ahb_expression="M[902][3]U[501]", entered_input="bar", data_element_id="1234"
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_FILLED,
                        format_validation_fulfilled=True,
                    ),
                ),
            ),
        ],
    )
    async def test_validate_data_element_freetext(
        self, data_element, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_data_element_freetext(data_element, segment_requirement)
        assert result == expected_validation

    @pytest.mark.parametrize(
        "data_element, segment_requirement, expected_validation",
        [
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="A1",
                            meaning="Ich bin A1",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="A2",
                            meaning="Ich bin A2",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="A3",
                            meaning="Ich bin A3",
                            ahb_expression="X",
                        ),
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A2": "Ich bin A2", "A3": "Ich bin A3"},
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="A1",
                            meaning="Ich bin A1",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="A2",
                            meaning="Ich bin A2",
                            ahb_expression="X",
                        ),
                        ValuePoolEntry(
                            qualifier="A3",
                            meaning="Ich bin A3",
                            ahb_expression="X",
                        ),
                    ],
                ),
                RequirementValidationValue.IS_FORBIDDEN,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN,
                        format_validation_fulfilled=True,
                        possible_values={},
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="A1",
                            meaning="Ich bin A1",
                            ahb_expression="X[2]",
                        ),
                        ValuePoolEntry(
                            qualifier="A2",
                            meaning="Ich bin A2",
                            ahb_expression="X[3]",
                        ),
                        ValuePoolEntry(
                            qualifier="A3",
                            meaning="Ich bin A3",
                            ahb_expression="X",
                        ),
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A3": "Ich bin A3"},
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="A1",
                            meaning="Ich bin A1",
                            ahb_expression="X[2]",
                        ),
                        ValuePoolEntry(
                            qualifier="A2",
                            meaning="Ich bin A2",
                            ahb_expression="X[3][501]",
                        ),
                        ValuePoolEntry(
                            qualifier="A3",
                            meaning="Ich bin A3",
                            ahb_expression="X",
                        ),
                    ],
                ),
                RequirementValidationValue.IS_FORBIDDEN,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN,
                        format_validation_fulfilled=True,
                        possible_values={},
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    value_pool=[
                        ValuePoolEntry(
                            qualifier="A1",
                            meaning="Ich bin A1",
                            ahb_expression="X",
                        )
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1"},
                    ),
                ),
            ),
        ],
    )
    async def test_validate_data_element_valuepool(
        self, data_element, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_data_element_valuepool(data_element, segment_requirement)
        assert result == expected_validation

    @pytest.mark.parametrize(
        "requirement_constraints_are_fulfilled, requirement_indicator, expected_requirement_validation_value",
        [
            pytest.param(
                False,
                ModalMark.MUSS,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
            pytest.param(
                True,
                ModalMark.MUSS,
                RequirementValidationValue.IS_REQUIRED,
            ),
            pytest.param(
                True,
                ModalMark.SOLL,
                RequirementValidationValue.IS_REQUIRED,
            ),
            pytest.param(
                False,
                ModalMark.SOLL,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
            pytest.param(
                True,
                ModalMark.KANN,
                RequirementValidationValue.IS_OPTIONAL,
            ),
            pytest.param(
                True,
                PrefixOperator.X,
                RequirementValidationValue.IS_REQUIRED,
            ),
            pytest.param(
                False,
                PrefixOperator.X,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
        ],
    )
    def test_map_requirement_validation_values(
        self, requirement_constraints_are_fulfilled, requirement_indicator, expected_requirement_validation_value
    ):
        requirement_validation_value = map_requirement_validation_values(
            requirement_constraints_are_fulfilled, requirement_indicator
        )
        assert requirement_validation_value == expected_requirement_validation_value

    @pytest.mark.parametrize(
        "requirement_constraints_are_fulfilled, requirement_indicator, expected_requirement_validation_value",
        [
            pytest.param(
                False,
                ModalMark.SOLL,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
            pytest.param(
                True,
                ModalMark.SOLL,
                RequirementValidationValue.IS_OPTIONAL,
            ),
            pytest.param(
                True,
                ModalMark.MUSS,
                RequirementValidationValue.IS_REQUIRED,
            ),
            pytest.param(
                False,
                ModalMark.MUSS,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
        ],
    )
    def test_map_requirement_validation_values_soll_not_required(
        self, requirement_constraints_are_fulfilled, requirement_indicator, expected_requirement_validation_value
    ):
        requirement_validation_value = map_requirement_validation_values(
            requirement_constraints_are_fulfilled, requirement_indicator, soll_is_required=False
        )
        assert requirement_validation_value == expected_requirement_validation_value

    def test_map_requirement_validation_values_all_cases_are_covered(self):
        """
        A fuzzing test to make sure all possible input values are mapped
        """
        requirement_indicators: List[RequirementIndicator] = [x for x in ModalMark] + [x for x in PrefixOperator]
        for rcs_fulfilled, requirement_indicator, soll_is_required in product(
            [True, False], requirement_indicators, [True, False]
        ):
            result = map_requirement_validation_values(rcs_fulfilled, requirement_indicator, soll_is_required)
            assert result is not None
            assert isinstance(result, RequirementValidationValue)

    @pytest.mark.parametrize(
        "parent_level_requirement, child_level_requirement, expected_requirement",
        [
            pytest.param(
                RequirementValidationValue.IS_REQUIRED,
                RequirementValidationValue.IS_REQUIRED,
                RequirementValidationValue.IS_REQUIRED,
            ),
            pytest.param(
                RequirementValidationValue.IS_REQUIRED,
                RequirementValidationValue.IS_OPTIONAL,
                RequirementValidationValue.IS_OPTIONAL,
            ),
            pytest.param(
                RequirementValidationValue.IS_REQUIRED,
                RequirementValidationValue.IS_FORBIDDEN,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
            pytest.param(
                RequirementValidationValue.IS_OPTIONAL,
                RequirementValidationValue.IS_REQUIRED,
                RequirementValidationValue.IS_OPTIONAL,
            ),
            pytest.param(
                RequirementValidationValue.IS_OPTIONAL,
                RequirementValidationValue.IS_OPTIONAL,
                RequirementValidationValue.IS_OPTIONAL,
            ),
            pytest.param(
                RequirementValidationValue.IS_OPTIONAL,
                RequirementValidationValue.IS_FORBIDDEN,
                RequirementValidationValue.IS_FORBIDDEN,
            ),
        ],
    )
    def test_combine_requirements_of_different_levels(
        self, parent_level_requirement, child_level_requirement, expected_requirement
    ):
        combined_requirement = combine_requirements_of_different_levels(
            parent_level_requirement, child_level_requirement
        )
        assert combined_requirement == expected_requirement

    def test_combine_requirements_of_different_levels_error(self):
        with pytest.raises(ValueError) as excinfo:
            _ = combine_requirements_of_different_levels(
                parent_level_requirement=RequirementValidationValue.IS_FORBIDDEN,
                child_level_requirement=RequirementValidationValue.IS_OPTIONAL,  # does not matter
            )

        assert "Unexpected parent_level_requirement value" in str(excinfo.value)
