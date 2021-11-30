"""
This module makes it possible to parse expressions including all their subexpressions, if present.
for example ahb_expressions which contain condition_expressions or condition_expressions which contain packages.
Parsing expressions that are nested into other expressions is refered to as "resolving".
"""

from lark import Transformer, Tree

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


def parse_expression_including_unresolved_subexpressions(expression: str, resolve_packages: bool = False) -> Tree:
    """
    Parses expressions and resolves its subexpressions,
    for example condition_expressions in ahb_expressions or packages in condition_expressions.
    :param expression: a syntactically valid ahb_expression or condition_expression
    :param resolve_packages: if true resolves also the packages in the condition_expressions
    """
    # TOOD: implement packages
    if resolve_packages:
        raise NotImplementedError("Resolving Packages is not implemented yet.")
    try:
        expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)
        resolved_expression_tree = AhbExpressionResolverTransformer().transform(expression_tree)
    except SyntaxError as ahb_syntax_error:
        try:
            resolved_expression_tree = parse_condition_expression_to_tree(expression)
        except SyntaxError as condition_syntax_error:
            # pylint: disable=raise-missing-from
            raise SyntaxError(f"{ahb_syntax_error.msg} {condition_syntax_error.msg}")

    return resolved_expression_tree


# pylint: disable=no-self-use, invalid-name
class AhbExpressionResolverTransformer(Transformer):
    """
    Resolves the condition_expressions inside an ahb_expression.
    """

    def CONDITION_EXPRESSION(self, expression):
        """
        Replacing the expression_condition with its parsed tree.
        """
        condition_tree = parse_condition_expression_to_tree(expression.value)
        return condition_tree
