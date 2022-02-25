"""
This module makes it possible to parse expressions including all their subexpressions, if present.
for example ahb_expressions which contain condition_expressions or condition_expressions which contain packages.
Parsing expressions that are nested into other expressions is referred to as "resolving".
"""
import asyncio
import inspect
from typing import Awaitable, List, Optional, Union

import inject
from lark import Token, Transformer, Tree
from lark.exceptions import VisitError

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.package_expansion import PackageResolver
from ahbicht.mapping_results import Repeatability, parse_repeatability


async def parse_expression_including_unresolved_subexpressions(
    expression: str, resolve_packages: bool = False
) -> Tree[Token]:
    """
    Parses expressions and resolves its subexpressions,
    for example condition_expressions in ahb_expressions or packages in condition_expressions.
    :param expression: a syntactically valid ahb_expression or condition_expression
    :param resolve_packages: if true resolves also the packages in the condition_expressions
    """
    try:
        expression_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)
        resolved_expression_tree = AhbExpressionResolverTransformer().transform(expression_tree)
        if resolve_packages:
            # the condition expression inside the ahb expression has to be resolved before trying to resolve packages
            resolved_expression_tree = await expand_packages(resolved_expression_tree)
    except SyntaxError as ahb_syntax_error:
        try:
            resolved_expression_tree = parse_condition_expression_to_tree(expression)
        except SyntaxError as condition_syntax_error:
            # pylint: disable=raise-missing-from
            raise SyntaxError(f"{ahb_syntax_error.msg} {condition_syntax_error.msg}")
    return resolved_expression_tree


async def expand_packages(parsed_tree: Tree) -> Tree[Token]:
    """
    Replaces all the "short" packages in parser_tree with the respective "long" condition expressions
    """
    try:
        result = PackageExpansionTransformer().transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc
    result = await _replace_sub_coroutines_with_awaited_results(result)
    return result


async def _replace_sub_coroutines_with_awaited_results(tree: Union[Tree, Awaitable[Tree]]) -> Tree[Token]:
    """
    awaits all coroutines inside the tree and replaces the coroutines with their respective awaited result.
    returns an updated tree
    """
    result: Tree
    if inspect.isawaitable(tree):
        result = await tree
    else:
        # if the tree type hint is correct this is always a tree if it's not awaitable
        result = tree  # type:ignore[assignment]
    # todo: check why lark type hints state the return value of scan_values is always Iterator[str]
    sub_results = await asyncio.gather(*result.scan_values(asyncio.iscoroutine))  # type:ignore[call-overload]
    for coro, sub_result in zip(result.scan_values(asyncio.iscoroutine), sub_results):
        for sub_tree in result.iter_subtrees():
            for child_index, child in enumerate(sub_tree.children):
                if child == coro:
                    sub_tree.children[child_index] = sub_result
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

    def package(self, tokens: List[Token]) -> Awaitable[Tree]:
        """
        try to resolve the package using the injected PackageResolver
        """
        # The grammar guarantees that there is always exactly 1 package_key token/terminal.
        # But the repeatability token is optional, so the list repeatability_tokens might contain 0 or 1 entries
        # They all come in the same `tokens` list which we split in the following two lines.
        package_key_token = [t for t in tokens if t.type == "PACKAGE_KEY"][0]
        repeatability_tokens = [t for t in tokens if t.type == "REPEATABILITY"]
        # pylint: disable=unused-variable
        # we parse the repeatability, but we don't to anything with it, yet.
        repeatability: Optional[Repeatability]
        if len(repeatability_tokens) == 1:
            repeatability = parse_repeatability(repeatability_tokens[0].value)
        else:
            repeatability = None
        return self._package_async(package_key_token)

    async def _package_async(self, package_key_token: Token) -> Tree[Token]:
        resolved_package = await self._resolver.get_condition_expression(package_key_token.value)
        if not resolved_package.has_been_resolved_successfully():
            raise NotImplementedError(
                f"The package '{package_key_token.value}' could not be resolved by {self._resolver}"
            )
        # the package_expression is not None because that's the definition of "has been resolved successfully"
        tree_result = parse_condition_expression_to_tree(resolved_package.package_expression)  # type:ignore[arg-type]
        return tree_result
