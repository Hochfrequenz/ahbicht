"""
Functions that are not clearly related to another module
"""
import asyncio
import inspect
from typing import Awaitable, List, TypeVar, Union

TResult = TypeVar("TResult")


async def gather_if_necessary(results_and_awaitable_results: List[Union[TResult, Awaitable[TResult]]]) -> List[TResult]:
    """
    Await the awaitables, pass the un-awaitable results
    :param results_and_awaitable_results: heterogenous list of both Ts and Awaitable[T]s.
    :return: list of T in the same order as in the input param.
    """
    awaitable_indexes = [n for n, x in enumerate(results_and_awaitable_results) if inspect.isawaitable(x)]
    awaited_results = await asyncio.gather(*[x for x in results_and_awaitable_results if inspect.isawaitable(x)])
    result: List[TResult] = []
    awaited_results_index = 0
    for index, obj in enumerate(results_and_awaitable_results):
        if index in awaitable_indexes:
            result.append(awaited_results[awaited_results_index])
            awaited_results_index += 1
        else:
            # we are sure obj is of type T
            result.append(obj)  # type:ignore[arg-type]
    return result
