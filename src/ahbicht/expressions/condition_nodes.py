"""
This module contains the abstract class ConditionNode, which specifies the nodes of the parsed tree.
The type of the subclass is the decisive factor on how the respective node
is handled in the context of the compositions it is used in.
There are three possible input nodes (RequirementConstraint, Hint and FormatConstraint) and
the EvaluatedComposition node which results from a combination of two nodes (of all possible types).

The used terms are defined in the README_conditions.md.
"""
from abc import ABC
from typing import Optional

import attr
from aenum import Enum

# pylint: disable=too-few-public-methods


class ConditionFulfilledValue(Enum):
    """
    Possible values to describe the state of a condition
    in the condition_fulfilled attribute of the ConditionNodes.
    """

    FULFILLED = True  # if condition is fulfilled
    UNFULFILLED = False  # if condition is not fulfilled
    UNKNOWN = None  # if it cannot be checked if condition is fulfilled (e.g. "Wenn vorhanden")
    NEUTRAL = "Neutral"  # a hint or unevaluated format constraint which do not have a status of being fulfilled or not


@attr.s(auto_attribs=True, kw_only=True)
class ConditionNode(ABC):
    """
    This abstract class specifies the nodes of the parsed tree.
    The type of the subclass is the decisive factor on how the respective node
    is handled in the context of the compositions it is used in.
    """

    conditions_fulfilled: ConditionFulfilledValue = attr.ib(
        validator=attr.validators.instance_of(ConditionFulfilledValue)
    )


@attr.s(auto_attribs=True, kw_only=True)
class ConditionKeyNodeMixin(ABC):
    """
    Nodes that have a condition key.
    """

    condition_key: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True, kw_only=True)
class RequirementConstraint(ConditionNode, ConditionKeyNodeMixin):
    """
    Bedingung, with a requirement constraint, e.g. "falls SG2+IDE+CCI == EHZ"
    """


@attr.s(auto_attribs=True, kw_only=True)
class Hint(ConditionNode, ConditionKeyNodeMixin):
    """
    A so called 'Hinweis', just a hint, even if it is worded like a condition,
    e.g. "Hinweis: 'Es ist der alte MSB zu verwenden'"
    """

    conditions_fulfilled: ConditionFulfilledValue = ConditionFulfilledValue.NEUTRAL
    hint: str = attr.ib(validator=attr.validators.instance_of(str))  # an informatory text


@attr.s(auto_attribs=True, kw_only=True)
class FormatConstraint(ConditionNode, ConditionKeyNodeMixin):
    """
    This class is the base class of all format constraints. FormatConstraints describe that data have to obey certain
    rules, meaning those conditions with an outcome that does not change whether data are obligatory or not but
    validates existing data.
    """


@attr.s(auto_attribs=True, kw_only=True)
class UnevaluatedFormatConstraint(FormatConstraint):
    """
    This class is the base class of all unevaluated format constraints. They are used in the context of the
    Mussfeldprüfung where the constraints are collected but not evaluated yet.
    """

    conditions_fulfilled: ConditionFulfilledValue = ConditionFulfilledValue.NEUTRAL


@attr.s(auto_attribs=True)
class EvaluatedFormatConstraint:
    """
    This class is the base class of all evaluated format constraints. They are used in the context of the
    Mussfeldprüfung after the format constraints are evaluated to see if the format constraint expression is
    fulfilled or not.
    """

    format_constraint_fulfilled: bool = attr.ib(validator=attr.validators.instance_of(bool))
    error_message: Optional[str] = attr.ib(default=None)


# @attr.s(auto_attribs=True, kw_only=True)
# class EvaluatableFormatConstraint(FormatConstraint):
#     """
#     This class is the base class of all evaluatable format constraints. They are used in the context of the
#     data evaluation (_after_ the Mussfeldprüfung) and can be either True/False or None.
#     """

#     name: str = attr.ib(validator=attr.validators.instance_of(str))  # e.g. "MaLo-Prüfsummenprüfung" or "OBIS-Format"


# ideas for format constraints:
# + check sum (or more generally: computational evaluation effort) constraint for e.g. MaLo IDs
# + data bound constraints (date must not be further than 16 days in the future)
# + pattern constraint that check data against a regex pattern (e.g. obis)
# + date format constraint ("must obey 'yyyy-mm-dd'")


@attr.s(auto_attribs=True, kw_only=True)
class EvaluatedComposition(ConditionNode):
    """
    Node which is returned after a composition of two nodes is evaluated.
    """

    hint: str = attr.ib(default=None)  # text from hints/notes
    format_constraints_expression: Optional[str] = attr.ib(default=None)  # an expression that consists of (initially
    # unevaluated) format constraints that the evaluated field needs to obey
