"""
This module parses a condition expression like "[59] U ([123] O [456])" into a tree structur using
the parsing library lark: https://lark-parser.readthedocs.io/en/latest/

The used terms are defined in the README_conditions.md.
"""

from lark import Lark, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF


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
    ?expression: expression "O" expression -> or_composition
                | expression "∨" expression -> or_composition
                | expression "X" expression -> xor_composition
                | expression "⊻" expression -> xor_composition
                | expression "U" expression -> and_composition
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
