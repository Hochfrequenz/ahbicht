"""
A module to allow easy distinction between different types of condition nodes (by mapping their integer key)
"""
from ahbicht import StrEnum


class ConditionNodeType(StrEnum):
    """
    Possible types of condition nodes.
    The value is usually determined using the key of the respective condition node.
    For the descriptions of the different types see also the README.
    """

    FORMAT_CONSTRAINT = "FORMAT_CONSTRAINT"
    """
    A Format Constraint (FC) is what edi@energy refers to as "Formatbedingung".
    Other than requirement constraints (RC) format constraints do not refer to a data constellation in the edifact
    message as a whole (or at least parts of it) but to the value used at the place where the format constraint is used.
    """
    REQUIREMENT_CONSTRAINT = "REQUIREMENT_CONSTRAINT"
    """
    A Requirement Constraint (RC) is what edi@energy refers to as "Voraussetzung".
    It describes a data constellation that might (or might not) occur in a edifact message.
    """
    HINT = "HINT"
    """
    A Hint is a node whose text/description starts with "Hinweis". It's a text that cannot be interpreted automatically.
    """
    PACKAGE = "PACKAGE"
    """
    A package is an abbreviation for an expression.
    """
    REPEATABILITY_CONSTRAINT = "REPEATABILITY_CONSTRAINT"
    """
    Repeatability Constraints are what edi@energy refers to as "Wiederholbarkeiten".
    They describe how often you may insert segment (groups) into a message (e.g. min. 1 but max 10 times).
    """


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
