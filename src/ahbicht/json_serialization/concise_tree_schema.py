"""
Schemata for the JSON serialization of expressions.
"""

from lark import Tree
from marshmallow import post_dump, pre_load

from ahbicht.json_serialization.tree_schema import TreeSchema


class ConciseTreeSchema(TreeSchema):
    """
    A tree schema that leads to significantly more compact output but can only be used for serialization
    (not deserialization)
    """

    # pylint:disable=unused-argument,no-self-use
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
    if "type" in data and "children" in data:  # and data["type"] in {"MODAL_MARK", "condition_key"}:
        return _compress(data["children"][0]["token"]["value"])
    if "type" in data and data["type"] in {"MODAL_MARK"}:
        return data["value"]
    return data
