"""
Schemata for the JSON serialization of expressions.
"""

from typing import Optional, Union

from lark import Token, Tree
from marshmallow import Schema, fields, post_dump, post_load, pre_dump, pre_load

# in the classes/schemata we don't care about if there aren't enough public versions.
# We also don't care about unused kwargs, or no self-use.
# pylint: disable=too-few-public-methods,unused-argument,no-self-use


class _TokenOrTree:
    """
    A class that is easily serializable as dictionary and allows us to _not_ use the marshmallow-union package.
    """

    def __init__(self, token: Optional[Token] = None, tree: Optional[Tree] = None):
        self.token = token
        self.tree = tree

    token: Optional[Token]
    tree: Optional[Tree]


class _TokenOrTreeSchema(Schema):
    """
    A schema that represents data of the kind Union[str,Tree]
    There is a python package for that: https://github.com/adamboche/python-marshmallow-union
    but is only has 15 stars; not sure if it's worth the dependency
    """

    token = fields.Nested(
        lambda: TokenSchema(), allow_none=True, required=False  # pylint: disable=unnecessary-lambda
    )  # fields.String(dump_default=False, required=False, allow_none=True)
    # disable unnecessary lambda warning because of circular imports
    tree = fields.Nested(
        lambda: TreeSchema(), dump_default=False, required=False, allow_none=True  # pylint: disable=unnecessary-lambda
    )

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
        if "token" in data and data["token"]:
            return data["token"]
        return data

    @pre_dump
    def prepare_tree_for_serialization(self, data, **kwargs) -> _TokenOrTree:
        """
        Create a string of tree object
        :param data:
        :param kwargs:
        :return:
        """
        if isinstance(data, Tree):
            return _TokenOrTree(token=None, tree=data)
        if isinstance(data, Token):
            return _TokenOrTree(token=data, tree=None)
        raise NotImplementedError(f"Data type of {data} is not implemented for JSON serialization")


class TokenSchema(Schema):
    """
    A schema that represents a lark Token and allows (de-)serializing is as JSON
    """

    value = fields.String(dump_default=False, allow_none=True)
    type = fields.String(dump_default=False, data_key="type")

    @post_load
    def deserialize(self, data, **kwargs) -> Token:
        """
        converts the barely typed data dictionary into an actual Tree
        :param data:
        :param kwargs:
        :return:
        """
        return Token(data["type"], data["value"])


class TreeSchema(Schema):
    """
    A schema that represents a lark tree and allows (de-)serializing it as JSON
    """

    data = fields.String(data_key="type")  # for example 'or_composition', 'and_composition', 'condition_key'
    # disable lambda warning. I don't know how to resolve this circular imports
    children = fields.List(fields.Nested(lambda: _TokenOrTreeSchema()))  # pylint: disable=unnecessary-lambda

    @post_load
    def deserialize(self, data, **kwargs) -> Tree:
        """
        converts the barely typed data dictionary into an actual Tree
        :param data:
        :param kwargs:
        :return:
        """
        return Tree(**data)


def _compress(data: dict) -> dict:
    """
    a function that "throws away" unnecessary data.
    The price we pay is that we loose the ability to easily deserialize the result.
    But if we're only interested in a simple tree that's fine.
    """
    if (
        "children" in data
        and "type" in data
        and (data["type"].endswith("_composition") or data["type"].endswith("_expression"))
    ):
        return {data["type"]: [_compress(child) for child in data["children"]]}
    if "tree" in data and "token" in data and data["token"] is None:
        return _compress(data["tree"])
    if "tree" in data and "token" in data and data["tree"] is None:
        return _compress(data["token"])
    if "type" in data and "children" in data:  # and data["type"] in {"MODAL_MARK", "condition"}:
        return _compress(data["children"][0]["token"]["value"])
    if "type" in data and data["type"] in {"MODAL_MARK"}:
        return data["value"]
    return data


class ConciseTreeSchema(TreeSchema):
    """
    A tree schema that leads to significantly more compact output but can only be used for serialization
    (not deserialization)
    """

    @post_dump
    def serialize(self, data, **kwargs) -> dict:
        """
        Serialize as compact/concise tree
        """
        return _compress(data)

    @pre_load
    def deserialize(self, data, **kwargs) -> Tree:
        """
        This is out of scope
        """
        raise NotImplementedError("Deserializing a compact tree is not supported.")
