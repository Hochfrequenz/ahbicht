"""
Tests that the parsed trees are JSON serializable
"""
import json
import uuid
from typing import TypeVar

import pytest  # type:ignore[import]
from lark import Token, Tree
from marshmallow import Schema, ValidationError

from ahbicht.content_evaluation.categorized_key_extract import CategorizedKeyExtract, CategorizedKeyExtractSchema
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.edifact import EdifactFormat
from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResult,
    AhbExpressionEvaluationResultSchema,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)
from ahbicht.expressions.enums import ModalMark, RequirementIndicator
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.json_serialization.tree_schema import ConciseTreeSchema, TreeSchema
from ahbicht.mapping_results import (
    ConditionKeyConditionTextMapping,
    ConditionKeyConditionTextMappingSchema,
    PackageKeyConditionExpressionMapping,
    PackageKeyConditionExpressionMappingSchema,
)

T = TypeVar("T")


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
    @pytest.mark.parametrize(
        "tree, expected_json_dict",
        [
            pytest.param(
                Tree(
                    "or_composition",
                    [
                        Tree("condition_key", [Token("INT", "53")]),
                        Tree(
                            "and_composition",
                            [Tree("condition_key", [Token("INT", "1")]), Tree("condition_key", [Token("INT", "2")])],
                        ),
                    ],
                ),
                {
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "children": [{"token": {"type": "INT", "value": "53"}, "tree": None}],
                                "type": "condition_key",
                            },
                        },
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {
                                        "token": None,
                                        "tree": {
                                            "children": [{"token": {"type": "INT", "value": "1"}, "tree": None}],
                                            "type": "condition_key",
                                        },
                                    },
                                    {
                                        "token": None,
                                        "tree": {
                                            "children": [{"token": {"type": "INT", "value": "2"}, "tree": None}],
                                            "type": "condition_key",
                                        },
                                    },
                                ],
                                "type": "and_composition",
                            },
                        },
                    ],
                    "type": "or_composition",
                },
            )
        ],
    )
    def test_tree_serialization(self, tree: Tree, expected_json_dict: dict):
        _test_serialization_roundtrip(tree, TreeSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "condition_string, expected_json_dict",
        [
            pytest.param(
                "Muss [2] U ([3] O [4])[901] U [555]",
                {
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {"token": {"type": "MODAL_MARK", "value": "Muss"}, "tree": None},
                                    {
                                        "token": {
                                            "type": "CONDITION_EXPRESSION",
                                            "value": " [2] U ([3] O [4])[901] U [555]",
                                        },
                                        "tree": None,
                                    },
                                ],
                                "type": "single_requirement_indicator_expression",
                            },
                        }
                    ],
                    "type": "ahb_expression",
                },
            )
        ],
    )
    def test_single_requirement_indicator_expression_serialization(
        self, condition_string: str, expected_json_dict: dict
    ):
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(condition_string)
        _test_serialization_roundtrip(tree, TreeSchema(), expected_json_dict)

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
                    id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
                ),
                {
                    "hints": {"501": "foo", "502": "bar", "503": None},
                    "format_constraints": {
                        "902": {"format_constraint_fulfilled": True, "error_message": None},
                        "901": {"format_constraint_fulfilled": False, "error_message": "something is wrong"},
                    },
                    "requirement_constraints": {"1": "NEUTRAL", "2": "FULFILLED", "3": "UNFULFILLED", "4": "UNKNOWN"},
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
                ),
                {
                    "hint_keys": ["501", "502", "503"],
                    "format_constraint_keys": ["901", "902"],
                    "requirement_constraint_keys": ["1", "2", "3", "4"],
                    "package_keys": ["17P"],
                },
            ),
        ],
    )
    def test_categorized_key_extract_serialization(
        self, categorized_key_extract: CategorizedKeyExtract, expected_json_dict: dict
    ):
        _test_serialization_roundtrip(categorized_key_extract, CategorizedKeyExtractSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "condition_expression, expected_compact_json_dict",
        [
            pytest.param(
                "[1] U ([2] O [3])[901]",
                {"and_composition": ["1", {"then_also_composition": [{"or_composition": ["2", "3"]}, "901"]}]},
            ),
            pytest.param(
                "[3] U ([2] O [3] U [77] X [99][502])[901]",
                {
                    "and_composition": [
                        "3",
                        {
                            "then_also_composition": [
                                {
                                    "or_composition": [
                                        "2",
                                        {
                                            "xor_composition": [
                                                {"and_composition": ["3", "77"]},
                                                {"then_also_composition": ["99", "502"]},
                                            ]
                                        },
                                    ]
                                },
                                "901",
                            ]
                        },
                    ]
                },
            ),
        ],
    )
    def test_concise_tree_serialization_behaviour_for_condition_expressions(
        self, condition_expression: str, expected_compact_json_dict: dict
    ):
        tree = parse_condition_expression_to_tree(condition_expression)
        json_dict = ConciseTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict

    @pytest.mark.parametrize(
        "ahb_expression, expected_compact_json_dict",
        [
            pytest.param(
                "Muss [1] U ([2] O [3])[901]",
                {
                    "ahb_expression": [
                        {
                            "single_requirement_indicator_expression": [
                                "Muss",
                                {
                                    "and_composition": [
                                        "1",
                                        {"then_also_composition": [{"or_composition": ["2", "3"]}, "901"]},
                                    ]
                                },
                            ]
                        }
                    ]
                },
            ),
            pytest.param(
                "Soll [3] U ([2] O [3] U [77] X [99][502])[901] Kann [43]",
                {
                    "ahb_expression": [
                        {
                            "single_requirement_indicator_expression": [
                                "Soll",
                                {
                                    "and_composition": [
                                        "3",
                                        {
                                            "then_also_composition": [
                                                {
                                                    "or_composition": [
                                                        "2",
                                                        {
                                                            "xor_composition": [
                                                                {"and_composition": ["3", "77"]},
                                                                {"then_also_composition": ["99", "502"]},
                                                            ]
                                                        },
                                                    ]
                                                },
                                                "901",
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                        {"single_requirement_indicator_expression": ["Kann", "43"]},
                    ]
                },
            ),
        ],
    )
    def test_concise_tree_serialization_behaviour_for_ahb_expressions(
        self, ahb_expression: str, expected_compact_json_dict: dict
    ):
        tree = parse_expression_including_unresolved_subexpressions(ahb_expression)
        json_dict = ConciseTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict
