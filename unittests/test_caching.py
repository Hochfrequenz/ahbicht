import asyncio
import timeit

import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]

from ahbicht.expressions.ahb_expression_parser import _parser as ahb_expr_parser
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import _parser as cond_expr_parser
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


class TestCaching:
    """
    Tests the caching capabilities of both ahb and condition expression parsers
    """

    # test expressions have to be unique per test case because the tests interfere (they share the same "global" cache)

    def test_ahb_expression_cache_performance(self):
        # be careful with performance tests. they naturally behave different on different systems
        ahb_expression = "Muss [7] U [8]"
        calls = 1000
        time_with_cache = timeit.timeit(
            lambda: parse_ahb_expression_to_single_requirement_indicator_expressions(
                ahb_expression, disable_cache=False
            ),
            number=calls,
        )
        time_without_cache = timeit.timeit(
            lambda: parse_ahb_expression_to_single_requirement_indicator_expressions(
                ahb_expression, disable_cache=True
            ),
            number=calls,
        )
        # a 100-fold performance improvement for 1000 calls of a simple expression seems fair
        assert time_with_cache < time_without_cache / 100

    def test_ahb_expression_cache_disabled(self, mocker):
        ahb_expression = "Muss [1] U [2]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")
        for _ in range(100):
            _ = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression, disable_cache=True)
        assert parse_spy.call_count == 100

    def test_ahb_expression_cache_sync(self, mocker):
        ahb_expression = "Muss [3] U [4]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")
        for _ in range(100):
            _ = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        parse_spy.assert_called_once_with(ahb_expression)

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
        for _ in range(100):
            _ = parse_condition_expression_to_tree(cond_expression)
        parse_spy.assert_called_once_with(cond_expression)

    async def test_condition_expression_cache_async(self, mocker):
        # test expression has to be different from the cond_expression in the sync test case because the tests interfere
        cond_expression = "[3] U [4]"
        parse_spy = mocker.spy(cond_expr_parser, "parse")

        async def parsing_task():
            parse_condition_expression_to_tree(cond_expression)

        tasks = [parsing_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        parse_spy.assert_called_once_with(cond_expression)
