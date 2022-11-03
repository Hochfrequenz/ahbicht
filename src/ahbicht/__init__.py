"""
AHBicht is a lark based parser and evaluation framework for conditions that occur in Anwendungshandbüchern (AHB).
"""
import sys
from enum import Enum

if sys.version_info.major == 3 and sys.version_info.minor >= 11:
    from enum import StrEnum

    # We have to use the builtin / std lib enum.StrEnum in Python >= 3.11, because the behaviour of (str,Enum) changed:
    # class Foo(str, Enum):
    #     MEMBER = "MEMBER"
    # f"{a_str_enum_member}" results in "MEMBER" for Python < v3.11 but "Foo.MEMBER" in Python >= v3.11
    # Using the old (str, Enum) in Python 3.11 causes errors e.g. in the ExpressionBuilders.
else:

    class StrEnum(str, Enum):  # type:ignore[no-redef]
        """
        An enum class of which each member has a string representation.
        This is a workaround for Python <v3.11 because enum.StrEnum was introduced in Python 3.11.
        """

        # We'll live with this  class for Python <v3.11. The unit test for python 3.9-3.11 ensure that this works.
