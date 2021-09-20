"""
Tests that the parsed trees are JSON serializable
"""
import json

import pytest
from lark import Token, Tree

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.json_serialization.tree_schema import TreeSchema


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
        json_string = TreeSchema().dumps(tree)
        assert json_string is not None
        actual_json_dict = json.loads(json_string)
        assert actual_json_dict == expected_json_dict
        deserialized_tree = TreeSchema().loads(json_data=json_string)
        assert isinstance(deserialized_tree, Tree)
        assert deserialized_tree == tree

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
        json_string = TreeSchema().dumps(tree)
        assert json_string is not None
        actual_json_dict = json.loads(json_string)
        assert actual_json_dict == expected_json_dict
        deserialized_tree = TreeSchema().loads(json_data=json_string)
        assert isinstance(deserialized_tree, Tree)
        assert deserialized_tree == tree
