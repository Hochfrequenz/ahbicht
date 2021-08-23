from typing import Union

from lark import Token, Tree
from marshmallow import Schema, fields, post_load, pre_dump


class _StringOrTree:
    """
    A class that is easily serializable as dictionary and allows us to _not_ use the marshmallow-union package.
    """

    def __init__(self, string: str = None, tree: Tree = None):
        self.string = string
        self.tree = tree

    string: str
    tree: Tree


class _StrOrTreeSchema(Schema):
    """
    A schema that represents data of the kind Union[str,Tree]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    string = fields.String(dump_default=False, required=False, allow_none=True)
    tree = fields.Nested(lambda: TreeSchema(), dump_default=False, required=False, allow_none=True)

    @post_load
    def deserialize(self, data, **kwargs) -> Union[str, Tree, Token]:
        """
        convert a dictionary back to a string, Tree or Token
        :param data:
        :param kwargs:
        :return:
        """
        if "tree" in data and data["tree"]:
            if not isinstance(data["tree"], Tree):
                return Tree(**data["tree"])
            return data["tree"]
        elif "string" in data and data["string"]:
            return Token("INT", data["string"])
        return data

    @pre_dump
    def prepare_tree_for_serialization(self, data, **kwargs) -> _StringOrTree:
        """
        Create a string of tree object
        :param data:
        :param kwargs:
        :return:
        """
        if isinstance(data, Tree):
            return _StringOrTree(string=None, tree=data)
        elif isinstance(data, str):
            return _StringOrTree(string=data, tree=None)
        raise NotImplementedError(f"Data type of {data} is not implemented for JSON serialization")


class TreeSchema(Schema):
    """
    A schema that represents a lark tree and allows (de-)serializing it as JSON
    """

    data = fields.String(data_key="type")  # for example 'or_composition', 'and_composition', 'condition_key'
    children = fields.List(fields.Nested(lambda: _StrOrTreeSchema()))

    @post_load
    def deserialize(self, data, **kwargs) -> Tree:
        return Tree(**data)