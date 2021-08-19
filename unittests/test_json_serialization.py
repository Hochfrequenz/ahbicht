"""
Tests that the parsed trees are JSON serializable
"""
import json
from typing import Union

import pytest
from lark import Token, Tree
from marshmallow import Schema, fields, post_load, pre_dump

# todo: move the schemas to elsewhere / out of the test


class StrOrTreeSchema(Schema):
    """
    A schema that represents data of the kind Union[str,Tree]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    string = fields.String()
    tree = fields.Nested(lambda: TreeSchema())

    @post_load
    def deserialize(self, data, **kwargs) -> Union[str, Tree]:
        if "tree" in data:
            return data["tree"]
        elif "string" in data:
            return data["string"]
        else:
            raise NotImplementedError("not implemented")

    @pre_dump
    def to_camelcase(self, data, **kwargs):
        """convert to lower camelCase"""
        if isinstance(data, Tree):
            self.tree = data
        elif isinstance(data, str):
            self.string = data
        else:
            raise NotImplementedError("not implemented")
        return self


class TreeSchema(Schema):
    """
    A schema that represents a lark Tree
    """

    data = fields.String(data_key="composition")  # for example 'or_composition', 'and_composition', 'xor_composition'
    children = fields.List(fields.Nested(lambda: StrOrTreeSchema()))
    _meta = fields.Raw()

    class Meta:
        json_module = json


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
        assert deserialized_tree == tree
