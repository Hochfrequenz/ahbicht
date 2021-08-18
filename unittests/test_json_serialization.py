"""
Tests that the parsed trees are JSON serializable
"""
import json

import pytest
from lark import Token, Tree


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
        json_string = json.dumps(tree)
        assert json_string is not None
