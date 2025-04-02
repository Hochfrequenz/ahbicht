"""contains the ConditionNodeType enum"""

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
    PACKAGE_REPEATABILITY = "PACKAGE_REPEATABILITY"
    """
    Package Repeatablity for resolved package nodes in tree
    """
