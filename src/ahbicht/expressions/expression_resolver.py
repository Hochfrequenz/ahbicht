"""
This module makes it possible to parse expressions including all their subexpressions, if present.
for example ahb_expressions which contain condition_expressions or condition_expressions which contain packages.
Parsing expressions that are nested into other expressions is refered to as "resolving".
"""
import asyncio
from typing import List

import inject
from lark import Token, Transformer, Tree
from lark.exceptions import VisitError

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.package_expansion import PackageResolver


def parse_expression_including_unresolved_subexpressions(expression: str, resolve_packages: bool = False) -> Tree:
    """
    Parses expressions and resolves its subexpressions,
    for example condition_expressions in ahb_expressions or packages in condition_expressions.
    :param expression: a syntactically valid ahb_expression or condition_expression
    :param resolve_packages: if true resolves also the packages in the condition_expressions
    """
    try:
        expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)
        if resolve_packages:
            expression_tree = expand_packages(expression_tree)
        resolved_expression_tree = AhbExpressionResolverTransformer().transform(expression_tree)
    except SyntaxError as ahb_syntax_error:
        try:
            resolved_expression_tree = parse_condition_expression_to_tree(expression)
        except SyntaxError as condition_syntax_error:
            # pylint: disable=raise-missing-from
            raise SyntaxError(f"{ahb_syntax_error.msg} {condition_syntax_error.msg}")
    return resolved_expression_tree


def expand_packages(parsed_tree: Tree) -> Tree:
    """
    Replaces all the "short" packages in parser_tree with the respective "long" condition expressions
    """
    try:
        result = PackageExpansionTransformer().transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc

    return result


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


# pylint: disable=no-self-use, invalid-name
class PackageExpansionTransformer(Transformer):
    """
    The PackageExpansionTransformer expands packages inside a tree to condition expressions by using a PackageResolver.
    """

    def __init__(self):
        super().__init__()
        self._resolver: PackageResolver = inject.instance(PackageResolver)

    def package(self, token: List[Token]):
        """
        try to resolve the package using the injected PackageResolver
        :param token:
        :return:
        """
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        resolved_package = loop.run_until_complete(self._resolver.get_condition_expression(token[0].value))
        if resolved_package is None:
            raise NotImplementedError(f"The package '{token[0].value}' could not be resolved by {self._resolver}")
        return parse_condition_expression_to_tree(resolved_package)
