"""
This module parses a condition expression like "[59] U ([123] O [456])" into a tree structur using
the parsing library lark: https://lark-parser.readthedocs.io/en/latest/

The used terms are defined in the README_conditions.md.
"""
# pylint:disable=cyclic-import
import re
from typing import List, Literal, Union

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
                | package
                | condition_key
    ?brackets: "(" expression ")"
    package: "[" INT "P]"
    condition_key: "[" INT "]"

    %import common.INT
    %import common.WS
    %ignore WS  // WS = whitespace
    """
    # todo: add wiederholbarkeiten https://github.com/Hochfrequenz/ahbicht/issues/96
    parser = Lark(grammar, start="expression")
    try:
        parsed_tree = parser.parse(condition_expression)
    except (UnexpectedEOF, UnexpectedCharacters, TypeError) as eof:
        raise SyntaxError(
            """Please make sure that:
             * all conditions have the form [INT]
             * all packages have the form [INTP]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """
        ) from eof
    # todo: implement wiederholbarkeiten
    return parsed_tree


def _get_rules(rule_name: Literal["package", "condition_key"], tree: Tree) -> List[str]:
    """
    This is an ugly workaround to extract all the rule tokens from the given tree.
    There has to be a better way of doing this.
    The rule name can either be "condition_key" or "package"
    """
    expr = r"^Tree\(Token\('RULE', 'rule_name'\), \[Token\('INT', '(?P<key>\d+)'\)\]\)$".replace("rule_name", rule_name)
    pattern = re.compile(expr)  # https://regex101.com/r/R8IQRJ/1
    result: List[str] = []
    for stringified_sub_tree in (str(sub_tree) for sub_tree in tree.iter_subtrees_topdown()):
        # todo: this is super ugly but I didn't find any better way to extract the data. todo: ask in lark issues.
        match = pattern.match(stringified_sub_tree)
        if match:
            result.append(match.groupdict()["key"])
    return result


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
        condition_keys = _get_rules("condition_key", tree_or_list)
        package_keys = [package_key + "P" for package_key in _get_rules("package", tree_or_list)]
        result.package_keys = package_keys
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
        # As of now the packages are extracted separately via their rule, not by analyzing the key.
        #
        # elif condition_node_type is ConditionNodeType.PACKAGE:
        #    result.package_keys.append(condition_key)
        else:
            raise NotImplementedError(f"The type '{condition_node_type}' is not implemented yet.")
    if sanitize:
        result.sanitize()
    return result


async def extract_categorized_keys(condition_expression: str, resolve_packages: bool = False) -> CategorizedKeyExtract:
    """
    Parses the given condition expression and returns CategorizedKeyExtract as a template for content
    evaluation.
    """
    # because of
    # ImportError: cannot import name 'parse_condition_expression_to_tree' from partially initialized module
    # 'ahbicht.expressions.condition_expression_parser' (most likely due to a circular import)
    # pylint: disable=import-outside-toplevel
    from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions

    tree = await parse_expression_including_unresolved_subexpressions(
        condition_expression, resolve_packages=resolve_packages
    )
    return extract_categorized_keys_from_tree(tree, sanitize=True)
