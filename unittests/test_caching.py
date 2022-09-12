import asyncio
from itertools import product
from typing import List

import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]
from lark import Tree

from ahbicht.expressions.ahb_expression_parser import _parser as ahb_expr_parser
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import _parser as cond_expr_parser
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


class TestCaching:
    """
    Tests the caching capabilities of both ahb and condition expression parsers
    """

    def test_ahb_expression_cache_sync(self, mocker):
        ahb_expression = "Muss [3] U [4]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")
        tree_instances: List[Tree] = []
        number_of_calls: int = 100
        for _ in range(number_of_calls):
            tree_instance = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
            tree_instances.append(tree_instance)
        parse_spy.assert_called_once_with(ahb_expression)
        # The following assertion is to make sure that each cached call actually returns a new instance of a lark tree.
        # We do not want the same instance to be returned and eventually be modified over and over again.
        number_of_distinct_instances: int = (
            len(tree_instances)
            * len(tree_instances)
            / len([1 for x, y in product(tree_instances, tree_instances) if x is y])
        )
        assert number_of_distinct_instances == number_of_calls

    async def test_ahb_expression_cache_async(self, mocker):

        ahb_expression = "Muss [5] U [6]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")

        async def parsing_task():
            parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)

        tasks = [parsing_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        parse_spy.assert_called_once_with(ahb_expression)

    def test_condition_expression_cache_sync(self, mocker):
        cond_expression = "[1] U [2]"
        parse_spy = mocker.spy(cond_expr_parser, "parse")
        tree_instances: List[Tree] = []
        number_of_calls: int = 100
        for _ in range(number_of_calls):
            tree_instance = parse_condition_expression_to_tree(cond_expression)
            tree_instances.append(tree_instance)
        parse_spy.assert_called_once_with(cond_expression)
        number_of_distinct_instances: int = (
            len(tree_instances)
            * len(tree_instances)
            / len([1 for x, y in product(tree_instances, tree_instances) if x is y])
        )
        assert number_of_distinct_instances == number_of_calls

    async def test_condition_expression_cache_async(self, mocker):
        # test expression has to be different from the cond_expression in the sync test case because the tests interfere
        cond_expression = "[3] U [4]"
        parse_spy = mocker.spy(cond_expr_parser, "parse")

        async def parsing_task():
            parse_condition_expression_to_tree(cond_expression)

        tasks = [parsing_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        parse_spy.assert_called_once_with(cond_expression)
