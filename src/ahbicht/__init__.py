"""
AHBicht is a lark based parser and evaluation framework for conditions that occur in Anwendungshandbüchern (AHB).
"""
from typing import Type

StrEnum: Type
try:
    from enum import StrEnum as std_lib_strenum

    StrEnum = std_lib_strenum
except ImportError:
    # this import error occurs for python < 3.11
    from enum import Enum

    class SelfDefinedStrEnum(str, Enum):
        pass

    StrEnum = SelfDefinedStrEnum
