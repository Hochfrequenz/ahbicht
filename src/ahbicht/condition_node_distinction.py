"""
A module to allow easy distinction between different types of condition nodes (by mapping their integer key)
"""

from ahbicht.models.condition_node_type import ConditionNodeType


def derive_condition_node_type(condition_key: str) -> ConditionNodeType:
    """
    Returns the corresponding type of condition node for a given condition key
    """
    if condition_key.endswith("P"):
        return ConditionNodeType.PACKAGE
    if 1 <= int(condition_key) <= 499:
        return ConditionNodeType.REQUIREMENT_CONSTRAINT
    if 500 <= int(condition_key) <= 900:
        return ConditionNodeType.HINT
    if 901 <= int(condition_key) <= 999:
        return ConditionNodeType.FORMAT_CONSTRAINT
    if 2000 <= int(condition_key) <= 2499:
        return ConditionNodeType.REPEATABILITY_CONSTRAINT
    raise ValueError("Condition key is not in valid number range.")
