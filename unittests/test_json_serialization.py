"""
Tests that the parsed trees are JSON serializable
"""
import json

import pytest
from lark import Token, Tree

from ahbicht.json_serialization.tree_schema import TreeSchema


class TestJsonSerialization:
    @pytest.mark.parametrize(
        "tree",
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
                )
            )
        ],
    )
    def test_tree_serialization(self, tree: Tree):
        tree_dict: dict = TreeSchema().dump(tree)
        assert len(tree_dict.keys()) > 0
        json_string = json.dumps(tree_dict)
        assert json_string is not None
        deserialized_tree = TreeSchema().loads(json_data=json_string)
        assert isinstance(deserialized_tree, Tree)
        assert deserialized_tree == tree
