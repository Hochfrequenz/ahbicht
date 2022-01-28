"""
A module to allow easy distinction between different types of condition nodes (by mapping their integer key)
"""
from enum import Enum


class ConditionNodeType(str, Enum):
    """
    Possible types of condition nodes.
    The value is usually determined using the key of the respective condition node.
    """

    FORMAT_CONSTRAINT = "FORMAT_CONSTRAINT"  #: a format constraint
    REQUIREMENT_CONSTRAINT = "REQUIREMENT_CONSTRAINT"  #: a requirement constraint
    HINT = "HINT"  #: a hint
    PACKAGE = "PACKAGE"  #: a package


def derive_condition_node_type(condition_key: str) -> ConditionNodeType:
    """
    Returns the corresponding type of condition node for a given condition key
    """
    if condition_key.endswith("P"):
        return ConditionNodeType.PACKAGE
        # todo: implement wiederholbarkeiten https://github.com/Hochfrequenz/ahbicht/issues/96
    if 1 <= int(condition_key) <= 499:
        return ConditionNodeType.REQUIREMENT_CONSTRAINT
    if 500 <= int(condition_key) <= 900:
        return ConditionNodeType.HINT
    if 901 <= int(condition_key) <= 999:
        return ConditionNodeType.FORMAT_CONSTRAINT
    raise ValueError("Condition key is not in valid number range.")
