"""
AHBicht is a lark based parser and evaluation framework for conditions that occur in Anwendungshandbüchern (AHB).
"""
from enum import Enum


class StrEnum(str, Enum):
    """
    An enum class of which each member has a string representation.
    This is a workaround for Python <v3.11 because enum.StrEnum was introduced in Python 3.11.
    """


try:
    from enum import StrEnum as std_lib_strenum

    StrEnum = std_lib_strenum  # type:ignore[misc, assignment]
except ImportError:
    # This import error occurs for python < 3.11
    # We'll live with the fallback class defined above. The unit test for python 3.9-3.11 ensure that this works.
    pass
