"""
Functions that are not clearly related to another module
"""
import asyncio
import inspect
from typing import Awaitable, Callable, List, TypeVar, Union

from lark import Tree

from ahbicht.expressions import parsing_logger

Result = TypeVar("Result")


async def gather_if_necessary(results_and_awaitable_results: List[Union[Result, Awaitable[Result]]]) -> List[Result]:
    """
    Await the awaitables, pass the un-awaitable results
    :param results_and_awaitable_results: heterogenous list of both Ts and Awaitable[T]s.
    :return: list of T in the same order as in the input param.
    """
    awaitable_indexes = [n for n, x in enumerate(results_and_awaitable_results) if inspect.isawaitable(x)]
    awaited_results = await asyncio.gather(*[x for x in results_and_awaitable_results if inspect.isawaitable(x)])
    result: List[Result] = []
    awaited_results_index = 0
    for index, obj in enumerate(results_and_awaitable_results):
        if index in awaitable_indexes:
            result.append(awaited_results[awaited_results_index])
            awaited_results_index += 1
        else:
            # we are sure obj is of type T
            result.append(obj)  # type:ignore[arg-type]
    return result


_CACHE_LOG_LEVEL = 5
"""
This is a custom log level, which is smaller than debug: https://docs.python.org/3/library/logging.html#logging-levels
We use it to log cache accesses but not spam at log level DEBUG.
"""


def tree_copy(lru_cached_parsing_func: Callable[[str], Tree]):
    """
    A decorator that returns copy of the cached result from the lru_cached_parsing_func.
    Rationale: We want to cache the tree for various expressions because this is definitely faster than re-parsing it.
    But we don't want the same instance of the tree to be returned over and over again, because the calling code might
    modify the tree and (if we always returned the same instance) might also modify the cache entry. We don't want this.
    The tree_copy decorator is used together shall be used with a @lru_cached function. It returns a copy of the cached
    value instead of the same instance.
    :param lru_cached_parsing_func: A function that parses a string to a tree which is decorated with @lru_cache.
    :return: the decorated function that always returns a copy of the cached result instead of the same instance
    """

    def decorated(*args, **kwargs):
        cache_size_before_parsing = lru_cached_parsing_func.cache_info().currsize
        tree_result: Tree = lru_cached_parsing_func(*args, **kwargs)
        cache_size_after_parsing = lru_cached_parsing_func.cache_info().currsize
        if cache_size_after_parsing == cache_size_before_parsing:
            parsing_logger.log(_CACHE_LOG_LEVEL, "The parsed tree for '%s' has been loaded from the cache", args[0])
        return tree_result.copy()

    return decorated
