"""
This module parses a condition expression like "[59] U ([123] O [456])" into a tree structur using
the parsing library lark: https://lark-parser.readthedocs.io/en/latest/

The used terms are defined in the README_conditions.md.
"""
from typing import List, Union

from lark import Lark, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF

from ahbicht.condition_node_distinction import ConditionNodeType, derive_condition_node_type
from ahbicht.content_evaluation.categorized_key_extract import CategorizedKeyExtract


def parse_condition_expression_to_tree(condition_expression: str) -> Tree:
    """
    Parse a given condition expression with the help of the here defined grammar to a lark tree.
    The grammar starts with condition keys, e.g. [45] and combines them with
    and _/or_compositions corresponding to U/O operators or without an operator (then_also_composition).
    It follows the boolean logic 'brackets before `then_also` before `and` before `xor` before `or`'.
    Whitespaces are ignored.

    :param condition_expression: str, e.g. '[45]U[502]O[1][906]'
    :return parsed_tree: Tree
    """

    grammar = """
    ?expression: expression "O"i expression -> or_composition
                | expression "∨" expression -> or_composition
                | expression "X"i expression -> xor_composition
                | expression "⊻" expression -> xor_composition
                | expression "U"i expression -> and_composition
                | expression "∧" expression -> and_composition
                | expression expression -> then_also_composition
                | brackets
                | condition_key
    ?brackets: "(" expression ")"
    condition_key: "[" INT "]"

    %import common.INT
    %import common.WS
    %ignore WS  // WS = whitespace
    """

    parser = Lark(grammar, start="expression")
    try:
        parsed_tree = parser.parse(condition_expression)
    except (UnexpectedEOF, UnexpectedCharacters, TypeError) as eof:
        raise SyntaxError(
            """Please make sure that:
             * all conditions have the form [INT]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """
        ) from eof

    return parsed_tree


def extract_categorized_keys_from_tree(
    tree_or_list: Union[Tree, List[str]], sanitize: bool = False
) -> CategorizedKeyExtract:
    """
    find different types of condition nodes inside the given tree or list of keys.
    The types are differentiated by their number range.
    See 'Allgemeine Festlegungen' from EDI@Energy.
    """
    result = CategorizedKeyExtract(
        format_constraint_keys=[], requirement_constraint_keys=[], hint_keys=[], package_keys=[]
    )
    condition_keys: List[str]
    if isinstance(tree_or_list, list):
        condition_keys = tree_or_list
    elif isinstance(tree_or_list, Tree):
        condition_keys = [
            x.value  # type:ignore[attr-defined]
            for x in tree_or_list.scan_values(
                lambda token: token.type == "INT"  # type:ignore[union-attr]
            )
        ]
    else:
        raise ValueError(f"{tree_or_list} is neither a list nor a {Tree.__name__}")
    for condition_key in condition_keys:
        condition_node_type = derive_condition_node_type(condition_key)
        if condition_node_type is ConditionNodeType.REQUIREMENT_CONSTRAINT:
            result.requirement_constraint_keys.append(condition_key)
        elif condition_node_type is ConditionNodeType.HINT:
            result.hint_keys.append(condition_key)
        elif condition_node_type is ConditionNodeType.FORMAT_CONSTRAINT:
            result.format_constraint_keys.append(condition_key)
        elif condition_node_type is ConditionNodeType.PACKAGE:
            result.package_keys.append(condition_key)
        else:
            raise NotImplementedError(f"The type '{condition_node_type}' is not implemented yet.")
    if sanitize:
        result.sanitize()
    return result


def extract_categorized_keys(condition_expression: str) -> CategorizedKeyExtract:
    """
    Parses the given condition expression and returns CategorizedKeyExtract as a template for content
    evaluation.
    """
    tree = parse_condition_expression_to_tree(condition_expression)
    return extract_categorized_keys_from_tree(tree, sanitize=True)
