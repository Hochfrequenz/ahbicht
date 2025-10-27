"""
Schemata for the JSON serialization of expressions.
"""
import sys
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypeAlias, Union

if TYPE_CHECKING or sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    # fixes pydantic.errors.PydanticUserError:
    # Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.12.
    from typing_extensions import TypedDict

from lark import Token, Tree
from pydantic import ConfigDict, PlainSerializer, TypeAdapter

# For both of the serialization behaviours: I don't know anymore WHY we chose to do it that way,
# but at this point we're just maintaining backward compatability in the pydantic world with the marshmallow past.

_TokenDict: TypeAlias = dict[Literal["value", "type"], Any]
_TreeDict: TypeAlias = dict[Literal["children", "type"], Any]


class _TreeOrTokenDictWithToken(TypedDict):
    token: _TokenDict
    tree: None


class _TreeOrTokenDictWithTree(TypedDict):
    token: None
    tree: _TreeDict


_TreeOrTokenDict: TypeAlias = Union[_TreeOrTokenDictWithToken, _TreeOrTokenDictWithTree]


def _serialize_children(t: Union[Tree, Token]) -> Union[_TokenDict, _TreeDict]:
    if isinstance(t, Tree):
        return TREE_ADAPTER.dump_python(t, mode="json")
    if isinstance(t, Token):
        return TOKEN_ADAPTER.dump_python(t, mode="json")
    raise ValueError(f"Unsupported type {t.__class__.__name__}")


def _serialize_tree(tree: Tree) -> _TreeOrTokenDictWithTree:
    return {"token": None, "tree": {"type": tree.data, "children": [_serialize_children(c) for c in tree.children]}}


def _serialize_token(token: Token) -> _TreeOrTokenDictWithToken:
    return {"tree": None, "token": {"value": token.value, "type": token.type}}


TOKEN_ADAPTER: TypeAdapter[Token] = TypeAdapter(
    Annotated[Token, PlainSerializer(_serialize_token)], config=ConfigDict(arbitrary_types_allowed=True)
)

TREE_ADAPTER: TypeAdapter[Tree] = TypeAdapter(
    Annotated[Tree, PlainSerializer(_serialize_tree)], config=ConfigDict(arbitrary_types_allowed=True)
)


def model_dump_tree(
    tree: Tree, mode: Literal["json", "concise", "compress-conditions-only"] = "json"
) -> dict[str, Any]:
    """ahbicht v1 replacement for the removed TreeSchema"""
    result = TREE_ADAPTER.dump_python(tree, mode="json")
    if mode == "json":
        return result["tree"]
    if mode == "concise":
        return _compress(result["tree"])
    if mode == "compress-conditions-only":
        return _compress_condition_keys_only(result["tree"])
    raise ValueError(f"Unsupported mode {mode}")


def _compress_condition_keys_only(data: dict) -> dict:
    """
    a function that merges a condition key node with its only child (a token that has an int value)
    """
    # this has been found heuristically. There's no way to explain it, just follow the test cases.
    # there's probably a much easier way, e.g. by using a separate token schema.
    if "tree" in data and data["tree"] is not None:
        if "type" in data["tree"]:
            if data["tree"]["type"] == "single_requirement_indicator_expression":
                if data["tree"]["children"][0]["token"]["type"] == "MODAL_MARK":
                    modal_mark = data["tree"]["children"][0]["token"]["value"]
                    del data["tree"]["children"][0]
                    data["tree"]["type"] = modal_mark
                elif data["tree"]["children"][0]["token"]["type"] == "PREFIX_OPERATOR":
                    prefix_operator = data["tree"]["children"][0]["token"]["value"]
                    del data["tree"]["children"][0]
                    data["tree"]["type"] = prefix_operator
        if data["tree"]["type"] == "condition":
            return {
                "token": {"value": data["tree"]["children"][0]["token"]["value"], "type": "condition_key"},
                "tree": None,
            }
        if "token" in data and data["token"] is None and "children" in data["tree"]:
            data["tree"]["children"] = [_compress_condition_keys_only(child) for child in data["tree"]["children"]]
    if "type" in data and data["type"] is not None and "children" in data and data["children"] is not None:
        data["children"] = [_compress_condition_keys_only(child) for child in data["children"]]
    return data


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


__all__ = ["model_dump_tree"]
