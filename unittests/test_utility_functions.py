"""
Tests the utility functions.
"""
from typing import Awaitable, List, TypeVar, Union

import pytest  # type:ignore[import]

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
