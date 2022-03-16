"""
Tests that the parsed trees are JSON serializable
"""
import json
import uuid
from typing import List, TypeVar

import pytest  # type:ignore[import]
from marshmallow import Schema, ValidationError
from maus.edifact import EdifactFormat

from ahbicht.content_evaluation.categorized_key_extract import CategorizedKeyExtract, CategorizedKeyExtractSchema
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResult,
    AhbExpressionEvaluationResultSchema,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)
from ahbicht.expressions.enums import ModalMark
from ahbicht.mapping_results import (
    ConditionKeyConditionTextMapping,
    ConditionKeyConditionTextMappingSchema,
    PackageKeyConditionExpressionMapping,
    PackageKeyConditionExpressionMappingSchema,
)
from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    DataElementValidationResultSchema,
    SegmentLevelValidationResult,
    SegmentLevelValidationResultSchema,
    ValidationResultInContext,
    ValidationResultInContextSchema,
)
from ahbicht.validation.validation_values import RequirementValidationValue

T = TypeVar("T")

pytestmark = pytest.mark.asyncio


def _test_serialization_roundtrip(serializable_object: T, schema: Schema, expected_json_dict: dict) -> T:
    """
    Serializes the serializable_object using the provided schema,
    asserts, that the result is equal to the expected_json_dict
    then deserializes it again and asserts on equality with the original serializable_object
    :returns the deserialized_object
    """
    json_string = schema.dumps(serializable_object)
    assert json_string is not None
    actual_json_dict = json.loads(json_string)
    assert actual_json_dict == expected_json_dict
    deserialized_object = schema.loads(json_data=json_string)
    assert isinstance(deserialized_object, type(serializable_object))
    assert deserialized_object == serializable_object
    return deserialized_object


class TestJsonSerialization:
    """
    This class tests the serialization of all objects except for trees.
    """

    @pytest.mark.parametrize(
        "evaluated_format_constraint, expected_json_dict",
        [
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                {"format_constraint_fulfilled": True, "error_message": None},
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something is wrong"),
                {"format_constraint_fulfilled": False, "error_message": "something is wrong"},
            ),
        ],
    )
    def test_evaluated_format_constraint_serialization(
        self, evaluated_format_constraint: EvaluatedFormatConstraint, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(
            evaluated_format_constraint, EvaluatedFormatConstraintSchema(), expected_json_dict
        )

    @pytest.mark.parametrize(
        "invalid_content_evaluation_result_dict",
        [
            pytest.param({}, id="empty dict"),
            pytest.param({"format_constraints": {}, "hints": {}}, id="missing requirement constraints"),
            pytest.param({"requirement_constraints": {}, "hints": {}}, id="missing format_constraints"),
        ],
    )
    def test_validation_errors_on_content_evaluation_result_deserialization(
        self, invalid_content_evaluation_result_dict: dict
    ):
        schema = ContentEvaluationResultSchema()
        with pytest.raises(ValidationError):
            schema.load(invalid_content_evaluation_result_dict)

    @pytest.mark.parametrize(
        "content_evaluation_result, expected_json_dict",
        [
            pytest.param(
                ContentEvaluationResult(
                    hints={"501": "foo", "502": "bar", "503": None},
                    format_constraints={
                        "901": EvaluatedFormatConstraint(
                            format_constraint_fulfilled=False, error_message="something is wrong"
                        ),
                        "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                    },
                    requirement_constraints={
                        "1": ConditionFulfilledValue.NEUTRAL,
                        "2": ConditionFulfilledValue.FULFILLED,
                        "3": ConditionFulfilledValue.UNFULFILLED,
                        "4": ConditionFulfilledValue.UNKNOWN,
                    },
                    packages={"123P": "[17] U [18]"},
                    id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
                ),
                {
                    "hints": {"501": "foo", "502": "bar", "503": None},
                    "format_constraints": {
                        "902": {"format_constraint_fulfilled": True, "error_message": None},
                        "901": {"format_constraint_fulfilled": False, "error_message": "something is wrong"},
                    },
                    "requirement_constraints": {"1": "NEUTRAL", "2": "FULFILLED", "3": "UNFULFILLED", "4": "UNKNOWN"},
                    "packages": {"123P": "[17] U [18]"},
                    "id": "d106f335-f663-4d14-9636-4f43a883ad26",
                },
            ),
        ],
    )
    def test_content_evaluation_result_serialization(
        self, content_evaluation_result: ContentEvaluationResult, expected_json_dict: dict
    ):
        for rc_evaluation_result in content_evaluation_result.requirement_constraints.values():
            assert isinstance(rc_evaluation_result, ConditionFulfilledValue)
        deserialized_object = _test_serialization_roundtrip(
            content_evaluation_result, ContentEvaluationResultSchema(), expected_json_dict
        )
        for rc_evaluation_result in deserialized_object.requirement_constraints.values():
            assert isinstance(rc_evaluation_result, ConditionFulfilledValue)
        for rc_evaluation_result in content_evaluation_result.requirement_constraints.values():
            assert isinstance(rc_evaluation_result, ConditionFulfilledValue)

    def test_content_evaluation_result_without_packages_may_can_deserialized(self):
        json_dict = {
            "hints": {"501": "foo", "502": "bar", "503": None},
            "format_constraints": {
                "902": {"format_constraint_fulfilled": True, "error_message": None},
                "901": {"format_constraint_fulfilled": False, "error_message": "something is wrong"},
            },
            "requirement_constraints": {"1": "NEUTRAL", "2": "FULFILLED", "3": "UNFULFILLED", "4": "UNKNOWN"},
            "packages": None,
            "id": "d106f335-f663-4d14-9636-4f43a883ad26",
        }
        cer = ContentEvaluationResultSchema().load(json_dict)
        assert cer is not None
        assert cer.packages is None

    @pytest.mark.parametrize(
        "ahb_expression_evaluation_result, expected_json_dict",
        [
            pytest.param(
                AhbExpressionEvaluationResult(
                    requirement_indicator=ModalMark.MUSS,
                    format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                        error_message="hello", format_constraints_fulfilled=False
                    ),
                    requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                        hints="foo bar",
                        requirement_constraints_fulfilled=True,
                        requirement_is_conditional=True,
                        format_constraints_expression="[asd]",
                    ),
                ),
                {
                    "requirement_indicator": "MUSS",
                    "format_constraint_evaluation_result": {
                        "format_constraints_fulfilled": False,
                        "error_message": "hello",
                    },
                    "requirement_constraint_evaluation_result": {
                        "hints": "foo bar",
                        "requirement_is_conditional": True,
                        "requirement_constraints_fulfilled": True,
                        "format_constraints_expression": "[asd]",
                    },
                },
            ),
            pytest.param(
                AhbExpressionEvaluationResult(
                    requirement_indicator=ModalMark.MUSS,
                    format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                        error_message="hello", format_constraints_fulfilled=False
                    ),
                    requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                        hints="foo bar",
                        requirement_constraints_fulfilled=True,
                        requirement_is_conditional=True,
                        format_constraints_expression="[asd]",
                    ),
                ),
                {
                    "format_constraint_evaluation_result": {
                        "error_message": "hello",
                        "format_constraints_fulfilled": False,
                    },
                    "requirement_constraint_evaluation_result": {
                        "format_constraints_expression": "[asd]",
                        "hints": "foo bar",
                        "requirement_constraints_fulfilled": True,
                        "requirement_is_conditional": True,
                    },
                    "requirement_indicator": "MUSS",
                },
            ),
            pytest.param(
                AhbExpressionEvaluationResult(
                    requirement_indicator=ModalMark.MUSS,
                    format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                        format_constraints_fulfilled=False
                    ),
                    requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                        requirement_constraints_fulfilled=True,
                        requirement_is_conditional=True,
                    ),
                ),
                {
                    "format_constraint_evaluation_result": {
                        "error_message": None,
                        "format_constraints_fulfilled": False,
                    },
                    "requirement_constraint_evaluation_result": {
                        "format_constraints_expression": None,
                        "hints": None,
                        "requirement_constraints_fulfilled": True,
                        "requirement_is_conditional": True,
                    },
                    "requirement_indicator": "MUSS",
                },
                id="Minimal example",
            ),
        ],
    )
    def test_ahb_expression_evaluation_result_serialization(
        self, ahb_expression_evaluation_result: AhbExpressionEvaluationResult, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(
            ahb_expression_evaluation_result, AhbExpressionEvaluationResultSchema(), expected_json_dict
        )

    @pytest.mark.parametrize(
        "validation_result, expected_json_dict",
        [
            pytest.param(
                SegmentLevelValidationResult(
                    requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                ),
                {
                    "requirement_validation": "IS_FORBIDDEN_AND_EMPTY",
                    "hints": "foo",
                },
            ),
            pytest.param(
                SegmentLevelValidationResult(requirement_validation=RequirementValidationValue.IS_FORBIDDEN),
                {
                    "requirement_validation": "IS_FORBIDDEN",
                    "hints": None,
                },
            ),
        ],
    )
    def test_segment_level_validation_result_serialization(
        self, validation_result: SegmentLevelValidationResult, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(validation_result, SegmentLevelValidationResultSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "validation_result, expected_json_dict",
        [
            pytest.param(
                DataElementValidationResult(
                    requirement_validation=RequirementValidationValue.IS_FORBIDDEN,
                    format_validation_fulfilled=True,
                ),
                {
                    "requirement_validation": "IS_FORBIDDEN",
                    "hints": None,
                    "format_validation_fulfilled": True,
                    "format_error_message": None,
                    "possible_values": None,
                },
            ),
            pytest.param(
                DataElementValidationResult(
                    requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_FILLED,
                    hints="foo",
                    format_validation_fulfilled=False,
                    format_error_message="bar",
                ),
                {
                    "requirement_validation": "IS_REQUIRED_AND_FILLED",
                    "hints": "foo",
                    "format_validation_fulfilled": False,
                    "format_error_message": "bar",
                    "possible_values": None,
                },
            ),
            pytest.param(
                DataElementValidationResult(
                    requirement_validation=RequirementValidationValue.IS_REQUIRED,
                    hints="foo",
                    format_validation_fulfilled=True,
                    format_error_message=None,
                    possible_values={"A1": "Ich bin A1", "A2": "Ich bin A2", "Z3": "Ich bin Z3"},
                ),
                {
                    "requirement_validation": "IS_REQUIRED",
                    "hints": "foo",
                    "format_validation_fulfilled": True,
                    "format_error_message": None,
                    "possible_values": {"A1": "Ich bin A1", "A2": "Ich bin A2", "Z3": "Ich bin Z3"},
                },
            ),
        ],
    )
    def test_data_element_validation_result_serialization(
        self, validation_result: DataElementValidationResult, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(validation_result, DataElementValidationResultSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "validation_result_in_context, expected_json_dict",
        [
            pytest.param(
                ValidationResultInContext(
                    discriminator="foo",
                    validation_result=SegmentLevelValidationResult(
                        requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                    ),
                ),
                {
                    "discriminator": "foo",
                    "validation_result": {
                        "requirement_validation": "IS_FORBIDDEN_AND_EMPTY",
                        "hints": "foo",
                    },
                },
            ),
        ],
    )
    def test_validation_result_in_context_serialization(
        self, validation_result_in_context: ValidationResultInContext, expected_json_dict: dict
    ):
        json_string = ValidationResultInContextSchema().dumps(validation_result_in_context)
        assert json_string is not None
        actual_json_dict = json.loads(json_string)
        assert actual_json_dict == expected_json_dict

    @pytest.mark.parametrize(
        "list_of_validation_result_in_context, expected_json_dict",
        [
            pytest.param(
                [
                    ValidationResultInContext(
                        discriminator="foo",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                        ),
                    ),
                    ValidationResultInContext(
                        discriminator="bar",
                        validation_result=SegmentLevelValidationResult(
                            requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                        ),
                    ),
                ],
                [
                    {
                        "discriminator": "foo",
                        "validation_result": {
                            "requirement_validation": "IS_FORBIDDEN_AND_EMPTY",
                            "hints": "foo",
                        },
                    },
                    {
                        "discriminator": "bar",
                        "validation_result": {
                            "requirement_validation": "IS_REQUIRED",
                            "hints": "bar",
                        },
                    },
                ],
            ),
        ],
    )
    def test_list_of_validation_result_in_context_serialization(
        self,
        list_of_validation_result_in_context: List[ValidationResultInContext],
        expected_json_dict: dict,
    ):
        json_string = ValidationResultInContextSchema().dumps(list_of_validation_result_in_context, many=True)
        assert json_string is not None
        actual_json_dict = json.loads(json_string)
        assert actual_json_dict == expected_json_dict

    @pytest.mark.parametrize(
        "condition_key_condition_text_mapping, expected_json_dict",
        [
            pytest.param(
                ConditionKeyConditionTextMapping(
                    edifact_format=EdifactFormat.UTILMD,
                    condition_key="123",
                    condition_text="Blablabla",
                ),
                {"edifact_format": "UTILMD", "condition_key": "123", "condition_text": "Blablabla"},
            ),
        ],
    )
    def test_condition_key_condition_text_mapping_serialization(
        self, condition_key_condition_text_mapping: ConditionKeyConditionTextMapping, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(
            condition_key_condition_text_mapping, ConditionKeyConditionTextMappingSchema(), expected_json_dict
        )

    @pytest.mark.parametrize(
        "package_key_condition_expression_mapping, expected_json_dict",
        [
            pytest.param(
                PackageKeyConditionExpressionMapping(
                    edifact_format=EdifactFormat.UTILMD,
                    package_key="123P",
                    package_expression="[1] U [2] O [3]",
                ),
                {"edifact_format": "UTILMD", "package_key": "123P", "package_expression": "[1] U [2] O [3]"},
            ),
        ],
    )
    def test_package_key_condition_expression_mapping_serialization(
        self, package_key_condition_expression_mapping: PackageKeyConditionExpressionMapping, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(
            package_key_condition_expression_mapping, PackageKeyConditionExpressionMappingSchema(), expected_json_dict
        )

    @pytest.mark.parametrize(
        "categorized_key_extract, expected_json_dict",
        [
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=["501", "502", "503"],
                    format_constraint_keys=["901", "902"],
                    requirement_constraint_keys=["1", "2", "3", "4"],
                    package_keys=["17P"],
                    time_condition_keys=["UB1", "UB2"],
                ),
                {
                    "hint_keys": ["501", "502", "503"],
                    "format_constraint_keys": ["901", "902"],
                    "requirement_constraint_keys": ["1", "2", "3", "4"],
                    "package_keys": ["17P"],
                    "time_condition_keys": ["UB1", "UB2"],
                },
            ),
        ],
    )
    def test_categorized_key_extract_serialization(
        self, categorized_key_extract: CategorizedKeyExtract, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(categorized_key_extract, CategorizedKeyExtractSchema(), expected_json_dict)
