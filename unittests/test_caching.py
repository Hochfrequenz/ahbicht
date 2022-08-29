import asyncio
import timeit

import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]

from ahbicht.expressions.ahb_expression_parser import _cache as ahb_expr_cache
from ahbicht.expressions.ahb_expression_parser import _parser as ahb_expr_parser
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import _cache as cond_expr_cache
from ahbicht.expressions.condition_expression_parser import _parser as cond_expr_parser
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


class TestCaching:
    """
    Tests the caching capabilities of both ahb and condition expression parsers
    """

    @pytest.fixture()
    def clear_caches(self):
        ahb_expr_cache.clear()
        cond_expr_cache.clear()

    # test expressions have to be unique per test case because the tests interfere (they share the same "global" cache)

    @pytest.mark.parametrize(
        "ahb_expression",
        [
            pytest.param("Muss [7] U [8]", id="simple expression"),
            pytest.param(
                "Muss [7] U [8] X ([112] O [2343] X [3] U [9]) O ([1] U [2] U ([12] O [13]) O [12 U [222])",
                id="longer expression",
            ),
        ],
    )
    def test_ahb_expression_cache_performance(self, clear_caches, ahb_expression: str):
        # be careful with performance tests. they naturally behave different on different systems
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

        avg_time_per_parsing_with_cache = time_with_cache / calls
        avg_time_per_parsing_without_cache = time_without_cache / calls
        assert avg_time_per_parsing_with_cache < avg_time_per_parsing_without_cache / 100
        # a 100-fold performance improvement for 1000 calls of a simple expression seems fair
        # still, the overall time spent in parsing is not large: the order of magnitude for parsing without cache is 1ms

    def test_ahb_expression_cache_disabled(self, clear_caches, mocker):
        ahb_expression = "Muss [1] U [2]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")
        for _ in range(100):
            _ = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression, disable_cache=True)
        assert parse_spy.call_count == 100

    def test_ahb_expression_cache_sync(self, clear_caches, mocker):
        ahb_expression = "Muss [3] U [4]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")
        for _ in range(100):
            _ = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        parse_spy.assert_called_once_with(ahb_expression)

    async def test_ahb_expression_cache_async(self, clear_caches, mocker):

        ahb_expression = "Muss [5] U [6]"
        parse_spy = mocker.spy(ahb_expr_parser, "parse")

        async def parsing_task():
            parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)

        tasks = [parsing_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        parse_spy.assert_called_once_with(ahb_expression)

    def test_condition_expression_cache_sync(self, clear_caches, mocker):
        cond_expression = "[1] U [2]"
        parse_spy = mocker.spy(cond_expr_parser, "parse")
        for _ in range(100):
            _ = parse_condition_expression_to_tree(cond_expression)
        parse_spy.assert_called_once_with(cond_expression)

    async def test_condition_expression_cache_async(self, clear_caches, mocker):
        # test expression has to be different from the cond_expression in the sync test case because the tests interfere
        cond_expression = "[3] U [4]"
        parse_spy = mocker.spy(cond_expr_parser, "parse")

        async def parsing_task():
            parse_condition_expression_to_tree(cond_expression)

        tasks = [parsing_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        parse_spy.assert_called_once_with(cond_expression)
