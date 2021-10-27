"""
This module parses a given ahb expression like "Muss [59]U([123]O[456]) Soll [53]" or "X [59]U[53]"
using the parsing library lark: https://lark-parser.readthedocs.io/en/latest/
The goal is to separate the requirement indicator (i.e. Muss, Soll, Kann, X, O, U) from the condition expression
and also several modal marks expressions if there are more than one.
"""

from lark import Lark, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF


def parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression: str) -> Tree:
    """
    Parse a given expression as it appears in the AHB with the help of the here defined grammar to a lark tree.
    The goal is to separate the requirement indicator (i.e. Muss/M Soll/S Kann/K, X, O, U) from the condition expression
    and also several expression with modal marks if there are more than one.
    Whitespaces are ignored.

    :param ahb_expression: e.g. 'Muss[45]U[52] Soll[1]'
    :return parsed_tree:
    """

    # pylint: disable=anomalous-backslash-in-string
    grammar = """
    ahb_expression: modal_mark_expression+
                    | prefix_operator_expression
                    | requirement_indicator
                    | modal_mark_expression+ requirement_indicator
    modal_mark_expression: (MODAL_MARK CONDITION_EXPRESSION) -> single_requirement_indicator_expression
    prefix_operator_expression: PREFIX_OPERATOR CONDITION_EXPRESSION -> single_requirement_indicator_expression
    requirement_indicator: PREFIX_OPERATOR | MODAL_MARK
    PREFIX_OPERATOR: "X"i | "O"i | "U"i
    MODAL_MARK: /M(uss)?|S(oll)?|K(ann)?/i
    // Matches if it looks like a condition expression, but does not yet check if it is a syntactically valid one:
    CONDITION_EXPRESSION: /(?!\BU\B)[\[\]\(\)U∧O∨X⊻\d\s]+/i
    """
    # Regarding the negative lookahead in the condition expression regex see examples https://regex101.com/r/6fFHD4/1
    # and CTRL+F for "Mus[2]" in the unittest that fails if you remove the lookahead.
    parser = Lark(grammar, start="ahb_expression")
    try:
        parsed_tree = parser.parse(ahb_expression)
    except (UnexpectedEOF, UnexpectedCharacters, TypeError) as eof:
        raise SyntaxError(
            """Please make sure that the ahb_expression starts with a requirement indicator \
(i.e Muss/M, Soll/S, Kann/K, X, O, U) and the condition expressions consist of only \
the following characters: [ ] ( ) U ∧ O ∨ X ⊻ and digits."""
        ) from eof

    return parsed_tree
