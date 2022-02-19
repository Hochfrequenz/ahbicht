import uuid

import pytest  # type:ignore[import]
from maus.models.edifact_components import DataElementFreeText, DataElementValuePool, Segment, SegmentGroup

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.expressions.enums import ModalMark, PrefixOperator
from ahbicht.validation.validation import (
    combine_requirements_of_different_levels,
    map_requirement_validation_values,
    validate_dataelement_freetext,
    validate_dataelement_valuepool,
    validate_root_segment_level,
    validate_segment,
    validate_segment_group,
)
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    SegmentLevelValidationResult,
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import FormatValidationValue, RequirementValidationValue

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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
        result = await validate_root_segment_level(segment_level)
        assert result == expected_validation_result

    @pytest.mark.parametrize(
        "segment_group, higher_segment_group_requirement, expected_validation_result",
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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        ),
                    ),
                ],
            ),
        ],
    )
    async def test_validate_segment_group(
        self,
        segment_group,
        higher_segment_group_requirement,
        expected_validation_result,
        inject_content_evaluation_result,
    ):
        result = await validate_segment_group(segment_group, higher_segment_group_requirement)
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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Auszug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
        "dataelement, segment_requirement, expected_validation",
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
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
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
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_NOT_FULFILLED,
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
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                    ),
                ),
            ),
        ],
    )
    async def test_validate_dataelement_freetext(
        self, dataelement, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_dataelement_freetext(dataelement, segment_requirement)
        assert result == expected_validation

    @pytest.mark.parametrize(
        "dataelement, segment_requirement, expected_validation",
        [
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1", data_element_id="1234", value_pool={"A1": "X", "A2": "X", "A3": "X"}
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        possible_values=["A1", "A2", "A3"],
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1", data_element_id="1234", value_pool={"A1": "X", "A2": "X", "A3": "X"}
                ),
                RequirementValidationValue.IS_FORBIDDEN,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN,
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        possible_values=[],
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1", data_element_id="1234", value_pool={"A1": "X[2]", "A2": "X[3]", "A3": "X"}
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        possible_values=["A1", "A3"],
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1", data_element_id="1234", value_pool={"A1": "X[2]", "A2": "X[3][501]", "A3": "X"}
                ),
                RequirementValidationValue.IS_FORBIDDEN,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN,
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        possible_values=[],
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(discriminator="SG1", data_element_id="1234", value_pool={"A1": "X"}),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        format_validation=FormatValidationValue.FORMAT_CONSTRAINTS_ARE_FULFILLED,
                        possible_values=["A1"],
                    ),
                ),
            ),
        ],
    )
    async def test_validate_dataelement_valuepool(
        self, dataelement, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_dataelement_valuepool(dataelement, segment_requirement)
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

    @pytest.mark.parametrize(
        "higher_level_requirement, lower_level_requirement, expected_requirement",
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
        self, higher_level_requirement, lower_level_requirement, expected_requirement
    ):
        combined_requirement = combine_requirements_of_different_levels(
            higher_level_requirement, lower_level_requirement
        )
        assert combined_requirement == expected_requirement

    def test_combine_requirements_of_different_levels_error(self):
        with pytest.raises(ValueError) as excinfo:
            _ = combine_requirements_of_different_levels(
                higher_level_requirement=RequirementValidationValue.IS_FORBIDDEN,
                lower_level_requirement=RequirementValidationValue.IS_OPTIONAL,  # does not matter
            )

        assert "Unexpected higher_level_requirement value" in str(excinfo.value)
