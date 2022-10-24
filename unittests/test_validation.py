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
)
from ahbicht.validation.validation_values import RequirementValidationValue

# TODO: Add testcases for segment_requirement is None & soll_is_required = False
from unittests.defaults import default_test_format, default_test_version, empty_default_test_data


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

        def eval_data_provider():
            return empty_default_test_data

        create_and_inject_hardcoded_evaluators(
            content_evaluation_result=content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
            evaluatable_data_provider=eval_data_provider,
        )
        yield
        inject.clear()

    @pytest.mark.parametrize(
        "deep_ahb, expected_validation_result",
        [
            pytest.param(
                DeepAnwendungshandbuch(
                    meta=AhbMetaInformation(pruefidentifikator="12345"),
                    lines=[
                        SegmentGroup(
                            discriminator="root",
                            ahb_expression="X",
                            segments=[
                                Segment(
                                    discriminator="UNH",
                                    ahb_expression="X",
                                    data_elements=[
                                        DataElementFreeText(
                                            discriminator="Nachrichten-Startsegment",
                                            ahb_expression="X",
                                            entered_input=None,
                                            data_element_id="1234",
                                        )
                                    ],
                                )
                            ],
                        ),
                        SegmentGroup(
                            discriminator="SG4",
                            ahb_expression="X",
                            segments=[
                                Segment(
                                    discriminator="FOO",
                                    ahb_expression="X",
                                    data_elements=[
                                        DataElementValuePool(
                                            discriminator="SG4->FOO->0333",
                                            value_pool=[
                                                ValuePoolEntry(
                                                    qualifier="E01",
                                                    meaning="Das andere",
                                                    ahb_expression="X[3]",
                                                ),
                                                ValuePoolEntry(
                                                    qualifier="E02",
                                                    meaning="Das Eine",
                                                    ahb_expression="X[2]",
                                                ),
                                            ],
                                            data_element_id="0333",
                                            entered_input=None,
                                        )
                                    ],
                                )
                            ],
                            segment_groups=[
                                SegmentGroup(
                                    discriminator="SG5",
                                    ahb_expression="X[3]",
                                    segments=[
                                        Segment(
                                            discriminator="BAR",
                                            ahb_expression="X",
                                            data_elements=[
                                                DataElementFreeText(
                                                    discriminator="Die fünfte Gruppe",
                                                    ahb_expression="X",
                                                    entered_input=None,
                                                    data_element_id="1234",
                                                )
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                [
                    ValidationResultInContext(
                        discriminator="root",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="UNH",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="Nachrichten-Startsegment",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                            data_element_data_type=DataElementDataType.TEXT,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG4",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG5",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_FORBIDDEN
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="FOO",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG4->FOO->0333",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                            possible_values={"E02": "Das Eine"},
                            data_element_data_type=DataElementDataType.VALUE_POOL,
                        ),
                    ),
                ],
            ),
        ],
    )
    async def test_validate_deep_ahb(
        self,
        deep_ahb,
        expected_validation_result,
        inject_content_evaluation_result,
    ):
        result = await validate_deep_anwendungshandbuch(deep_ahb)
        assert result == expected_validation_result

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
                                    value_type=DataElementDataType.DATETIME,
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
                                            value_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
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
                            value_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
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
                                    value_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
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
                            value_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
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
                            value_type=DataElementDataType.DATETIME,
                        ),
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Auszug",
                            data_element_id="1235",
                            ahb_expression="M[2]",
                            entered_input="",
                            value_type=DataElementDataType.DATETIME,
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
                            data_element_data_type=DataElementDataType.DATETIME,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Auszug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                            format_validation_fulfilled=True,
                            data_element_data_type=DataElementDataType.DATETIME,
                        ),
                    ),
                ],
            ),
            pytest.param(
                Segment(
                    ahb_expression="Muss[2]O[501]",
                    discriminator="SG10 Datum",
                    data_elements=[
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Einzug",
                            data_element_id="1234",
                            ahb_expression="M[2]",
                            entered_input="",
                            value_type=DataElementDataType.DATETIME,
                        ),
                        DataElementFreeText(
                            discriminator="SG10 - Datum - Auszug",
                            data_element_id="1235",
                            ahb_expression="M[2]",
                            entered_input="",
                            value_type=DataElementDataType.DATETIME,
                        ),
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                [
                    ValidationResultInContext(
                        discriminator="SG10 Datum",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_OPTIONAL,
                            hints="Combining a neutral element 'Hint(condition_key='501', conditions_fulfilled=<ConditionFulfilledValue.NEUTRAL: 'NEUTRAL'>, hint='foo')' with a boolean value RequirementConstraint(condition_key='2', conditions_fulfilled=<ConditionFulfilledValue.FULFILLED: 'FULFILLED'>) in an or_composition is not implemented as it has no useful result. This is probably an error in the AHB itself.",
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Einzug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_OPTIONAL_AND_EMPTY,
                            format_validation_fulfilled=True,
                            data_element_data_type=DataElementDataType.DATETIME,
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="SG10 - Datum - Auszug",
                        validation_result=DataElementValidationResult(
                            requirement_validation=RequirementValidationValue.IS_OPTIONAL_AND_EMPTY,
                            format_validation_fulfilled=True,
                            data_element_data_type=DataElementDataType.DATETIME,
                        ),
                    ),
                ],
                id="invalid ahb expression",
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
                        data_element_data_type=DataElementDataType.TEXT,
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
                        data_element_data_type=DataElementDataType.TEXT,
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
                        data_element_data_type=DataElementDataType.TEXT,
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
                        data_element_data_type=DataElementDataType.TEXT,
                    ),
                ),
            ),
            pytest.param(
                DataElementFreeText(
                    discriminator="SG1", ahb_expression="M[3]O[501]", entered_input="bar", data_element_id="1234"
                ),
                RequirementValidationValue.IS_OPTIONAL,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_OPTIONAL,
                        format_validation_fulfilled=True,
                        data_element_data_type=DataElementDataType.TEXT,
                        hints="Combining a neutral element 'Hint(condition_key='501', conditions_fulfilled=<ConditionFulfilledValue.NEUTRAL: 'NEUTRAL'>, hint='foo')' with a boolean value RequirementConstraint(condition_key='3', conditions_fulfilled=<ConditionFulfilledValue.UNFULFILLED: 'UNFULFILLED'>) in an or_composition is not implemented as it has no useful result. This is probably an error in the AHB itself.",
                    ),
                ),
            ),
        ],
    )
    async def test_validate_data_element_freetext(
        self, caplog, data_element, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_data_element_freetext(data_element, segment_requirement)
        assert result == expected_validation
        validation_log_entries = [record for record in caplog.records if record.name == "ahbicht.validation"]
        assert len(validation_log_entries) > 0
        first_log_message = validation_log_entries[0].message
        assert first_log_message.startswith("The validation of expression") or first_log_message.startswith(
            "The expression '"
        )

    @pytest.mark.parametrize(
        "data_element, segment_requirement, expected_validation",
        [
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input=None,
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
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A2": "Ich bin A2", "A3": "Ich bin A3"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
                id="required value pool with empty input",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input=None,
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
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
                id="forbidden value pool with empty input",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input=None,
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
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A3": "Ich bin A3"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
                id="required value pool and empty input",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input="A2",
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
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                        format_validation_fulfilled=False,
                        possible_values={"A1": "Ich bin A1", "A3": "Ich bin A3"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                        hints="Der Wert 'A2' ist nicht in: {A1, A3}",
                    ),
                ),
                id="required value pool and illegal input",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input=None,
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
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input="A1",
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
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_FILLED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
                id="only one expected input (could this be filled automatically?)",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input="A1",
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
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_FILLED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A2": "Ich bin A2", "A3": "Ich bin A3"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                    ),
                ),
                id="required value pool and correct input",
            ),
            pytest.param(
                DataElementValuePool(
                    discriminator="SG1",
                    data_element_id="1234",
                    entered_input="A3",
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
                            ahb_expression="X [2] O [501]",  # <-- well formed but invalid
                        ),
                    ],
                ),
                RequirementValidationValue.IS_REQUIRED,
                ValidationResultInContext(
                    discriminator="SG1",
                    validation_result=DataElementValidationResult(
                        requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_FILLED,
                        format_validation_fulfilled=True,
                        possible_values={"A1": "Ich bin A1", "A2": "Ich bin A2", "A3": "Ich bin A3"},
                        data_element_data_type=DataElementDataType.VALUE_POOL,
                        hints=None,
                    ),
                ),
                id="invalid ahb expression",
            ),
        ],
    )
    async def test_validate_data_element_valuepool(
        self, caplog, data_element, segment_requirement, expected_validation, inject_content_evaluation_result
    ):
        result = await validate_data_element_valuepool(data_element, segment_requirement)
        assert result == expected_validation
        validation_log_entries = [record for record in caplog.records if record.name == "ahbicht.validation"]
        assert len(validation_log_entries) > 0

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
