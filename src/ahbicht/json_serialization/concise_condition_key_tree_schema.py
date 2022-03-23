"""
Schemata for the JSON serialization of expressions.
"""
from lark import Tree
from marshmallow import post_dump, pre_load

from ahbicht.json_serialization.tree_schema import TreeSchema


class ConciseConditionKeyTreeSchema(TreeSchema):
    """
    A tree schema that merges condition key values and their single child
    (not deserialization)
    """

    # pylint:disable=unused-argument,no-self-use
    @post_dump
    def serialize(self, data, **kwargs) -> dict:
        """
        Serialize as compact/concise tree
        """
        return _compress_condition_keys_only(data)

    @pre_load
    def deserialize(self, data, **kwargs) -> Tree:
        """
        This is out of scope
        """
        raise NotImplementedError("Deserializing a compact tree is not supported.")


def _compress_condition_keys_only(data: dict) -> dict:
    """
    a function that merges a condition key node with its only child (a token that has an int value)
    """
    # this has been found heuristically. There's no way to explain it, just follow the test cases.
    # there's probably a much easier way, e.g. by using a separate token schema.
    if (
        "tree" in data
        and "type" in data["tree"]
        and data["tree"]["type"] == "single_requirement_indicator_expression"
        and data["tree"]["children"][0]["token"]["type"] == "MODAL_MARK"
    ):
        modal_mark = data["tree"]["children"][0]["token"]["value"]
        del data["tree"]["children"][0]
        data["tree"]["type"] = modal_mark
    if "tree" in data and data["tree"] is not None and data["tree"]["type"] == "condition":
        return {
            "token": {"value": data["tree"]["children"][0]["token"]["value"], "type": "condition_key"},
            "tree": None,
        }
    if (
        "token" in data
        and data["token"] is None
        and "tree" in data
        and data["tree"] is not None
        and "children" in data["tree"]
    ):
        data["tree"]["children"] = [_compress_condition_keys_only(child) for child in data["tree"]["children"]]
    if "type" in data and data["type"] is not None and "children" in data and data["children"] is not None:
        data["children"] = [_compress_condition_keys_only(child) for child in data["children"]]
    return data
