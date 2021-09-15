"""
Tests that the parsed trees are JSON serializable
"""
import json

import pytest
from lark import Token, Tree

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
                    "type": "or_composition",
                    "children": [
                        {
                            "string": None,
                            "tree": {"children": [{"string": "53", "tree": None}], "type": "condition_key"},
                        },
                        {
                            "string": None,
                            "tree": {
                                "children": [
                                    {
                                        "string": None,
                                        "tree": {"children": [{"string": "1", "tree": None}], "type": "condition_key"},
                                    },
                                    {
                                        "string": None,
                                        "tree": {"children": [{"string": "2", "tree": None}], "type": "condition_key"},
                                    },
                                ],
                                "type": "and_composition",
                            },
                        },
                    ],
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
