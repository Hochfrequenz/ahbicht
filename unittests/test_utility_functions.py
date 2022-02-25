"""
Tests the utility functions.
"""
from typing import Awaitable, List, TypeVar, Union

import pytest  # type:ignore[import]

from ahbicht.mapping_results import Repeatability, parse_repeatability
from ahbicht.utility_functions import gather_if_necessary

pytestmark = pytest.mark.asyncio

T = TypeVar("T")


async def _return_awaitable(arg: T) -> T:
    """returns the argument but is awaitable"""
    return arg


class TestUtilityFunctions:
    @pytest.mark.parametrize(
        "mixed_input, expected_result",
        [
            # only non-awaitables
            pytest.param([], []),
            pytest.param([3, 2, 1], [3, 2, 1]),
            pytest.param(["a", "b", "c"], ["a", "b", "c"]),
            # both awaitables and non-awaitables
            pytest.param(
                ["2", _return_awaitable("3"), "4", "foo", _return_awaitable("bar")], ["2", "3", "4", "foo", "bar"]
            ),
            # only awaitables
            pytest.param([_return_awaitable("a"), _return_awaitable("b")], ["a", "b"]),
        ],
    )
    async def test_gather_if_necessary(self, mixed_input: List[Union[T, Awaitable[T]]], expected_result: List[T]):
        actual = await gather_if_necessary(mixed_input)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "candidate, expected_result",
        [
            pytest.param("0..1", Repeatability(min_occurrences=0, max_occurrences=1)),
            pytest.param("1..1", Repeatability(min_occurrences=1, max_occurrences=1)),
            pytest.param("1..2", Repeatability(min_occurrences=1, max_occurrences=2)),
            pytest.param("71..89", Repeatability(min_occurrences=71, max_occurrences=89)),
        ],
    )
    def test_parse_repeatability(self, candidate: str, expected_result: Repeatability):
        actual = parse_repeatability(candidate)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "invalid_candidate",
        [
            pytest.param("1..0"),
            pytest.param("77..76"),
            pytest.param("0..0"),
            pytest.param("-1..1"),
            pytest.param("bullshit"),
            pytest.param(""),
        ],
    )
    def test_parse_repeatability_failures(self, invalid_candidate):
        with pytest.raises(ValueError):
            _ = parse_repeatability(invalid_candidate)
