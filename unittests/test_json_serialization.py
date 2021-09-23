"""
Tests that the parsed trees are JSON serializable
"""
import json
import uuid

import pytest
from lark import Token, Tree
from marshmallow import Schema

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)
from ahbicht.json_serialization.tree_schema import TreeSchema


def _test_serialization_roundtrip(serializable_object, schema: Schema, expected_json_dict: dict):
    """
    serializes the serializable_object using the provided schema,
    asserts, that the result is equal to the expected_json_dict
    then deserializes it again and asserts on equality with the original serializable_object
    """
    json_string = schema.dumps(serializable_object)
    assert json_string is not None
    actual_json_dict = json.loads(json_string)
    assert actual_json_dict == expected_json_dict
    deserialized_object = schema.loads(json_data=json_string)
    assert isinstance(deserialized_object, type(serializable_object))
    assert deserialized_object == serializable_object


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
        _test_serialization_roundtrip(content_evaluation_result, ContentEvaluationResultSchema(), expected_json_dict)
