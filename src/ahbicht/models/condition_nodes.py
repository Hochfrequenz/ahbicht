"""
This module contains the abstract class ConditionNode, which specifies the nodes of the parsed tree.
The type of the subclass is the decisive factor on how the respective node
is handled in the context of the compositions it is used in.
There are three possible input nodes (RequirementConstraint, Hint and FormatConstraint) and
the EvaluatedComposition node which results from a combination of two nodes (of all possible types).

The used terms are defined in the README_conditions.md.
"""

from enum import Enum
from typing import Optional, TypeVar

# pylint: disable=too-few-public-methods
from pydantic import BaseModel, ConfigDict, model_validator


class ConditionFulfilledValue(str, Enum):
    """
    Possible values to describe the state of a condition
    in the condition_fulfilled attribute of the ConditionNodes.
    """

    #: if condition is fulfilled
    FULFILLED = "FULFILLED"
    #: if condition is not fulfilled
    UNFULFILLED = "UNFULFILLED"
    #: if it cannot be checked if condition is fulfilled (e.g. "Wenn vorhanden")
    UNKNOWN = "UNKNOWN"
    #: a hint or unevaluated format constraint which does not have a status of being fulfilled or not
    NEUTRAL = "NEUTRAL"

    def __str__(self) -> str:
        return self.value

    def __or__(self, other: "ConditionFulfilledValue") -> "ConditionFulfilledValue":
        if other == ConditionFulfilledValue.NEUTRAL:  # todo: the next 8 lines are nearly identical with __and__
            return self
        if self == ConditionFulfilledValue.NEUTRAL:
            return other
        # if any single operand of the or composition is fulfilled, then the entire outcome is fulfilled, regardless
        # of the other operand
        if ConditionFulfilledValue.FULFILLED in (self, other):
            return ConditionFulfilledValue.FULFILLED
        # if no operand is fulfilled, then any single "unknown" leads to an unknown outcome
        if ConditionFulfilledValue.UNKNOWN in (self, other):
            return ConditionFulfilledValue.UNKNOWN
        return ConditionFulfilledValue.UNFULFILLED

    def __and__(self, other: "ConditionFulfilledValue") -> "ConditionFulfilledValue":
        if other == ConditionFulfilledValue.NEUTRAL:  # todo: the next 8 lines are nearly identical with __or__
            return self
        if self == ConditionFulfilledValue.NEUTRAL:
            return other
        # if any single operand in the and_composition is unfulfilled, then the entire outcome is unfulfilled,
        # regardless of the other operand
        if ConditionFulfilledValue.UNFULFILLED in (self, other):
            return ConditionFulfilledValue.UNFULFILLED
        if ConditionFulfilledValue.UNKNOWN in (self, other):
            return ConditionFulfilledValue.UNKNOWN
        if self == ConditionFulfilledValue.FULFILLED and other == ConditionFulfilledValue.FULFILLED:
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    def __xor__(self, other: "ConditionFulfilledValue") -> "ConditionFulfilledValue":
        if other == ConditionFulfilledValue.NEUTRAL:
            return self
        if self == ConditionFulfilledValue.NEUTRAL:
            return other
        if ConditionFulfilledValue.UNKNOWN in (self, other):
            return ConditionFulfilledValue.UNKNOWN
        if self == ConditionFulfilledValue.FULFILLED and other == ConditionFulfilledValue.FULFILLED:
            return ConditionFulfilledValue.UNFULFILLED
        if ConditionFulfilledValue.FULFILLED in (self, other):
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED


class ConditionNode(BaseModel):
    """
    This abstract class specifies the nodes of the parsed tree.
    The type of the subclass is the decisive factor on how the respective node
    is handled in the context of the compositions it is used in.
    """

    model_config = ConfigDict(extra="forbid")
    conditions_fulfilled: ConditionFulfilledValue


# ConditionNodeType_co matches any class inheriting from ConditionNode (in contrast to Type[ConditionNode])
ConditionNode_co = TypeVar("ConditionNode_co", bound=ConditionNode, covariant=True)


class RequirementConstraint(ConditionNode):
    """
    Bedingung, with a requirement constraint, e.g. "falls SG2+IDE+CCI == EHZ"
    """

    condition_key: str


class Hint(ConditionNode):
    """
    A so called 'Hinweis', just a hint, even if it is worded like a condition,
    e.g. "Hinweis: 'Es ist der alte MSB zu verwenden'"
    """

    condition_key: str
    conditions_fulfilled: ConditionFulfilledValue = ConditionFulfilledValue.NEUTRAL
    hint: str  #: an informatory text


class FormatConstraint(ConditionNode):
    """
    This class is the base class of all format constraints. FormatConstraints describe that data have to obey certain
    rules, meaning those conditions with an outcome that does not change whether data are obligatory or not but
    validates existing data.
    """

    condition_key: str


class UnevaluatedFormatConstraint(FormatConstraint):
    """
    This class is the base class of all unevaluated format constraints. They are used in the context of the
    Mussfeldprüfung where the constraints are collected but not evaluated yet.
    """

    conditions_fulfilled: ConditionFulfilledValue = ConditionFulfilledValue.NEUTRAL


class EvaluatedFormatConstraint(BaseModel):
    """
    This class is the base class of all evaluated format constraints. They are used in the context of the
    Mussfeldprüfung after the format constraints are evaluated to see if the format constraint expression is
    fulfilled or not.
    """

    format_constraint_fulfilled: bool
    error_message: Optional[str] = None

    @model_validator(mode="after")
    def _validate_error_message(self) -> "EvaluatedFormatConstraint":
        """
        Validate that error_message is None when format_constraint_fulfilled is True,
        and that error_message is not an empty string.
        """
        if self.format_constraint_fulfilled and self.error_message is not None:
            raise ValueError("error_message must be None when format_constraint_fulfilled is True")
        if self.error_message is not None and self.error_message == "":
            raise ValueError("error_message must not be an empty string")
        return self


# @attrs.define(auto_attribs=True, kw_only=True)
# class EvaluatableFormatConstraint(FormatConstraint):
#     """
#     This class is the base class of all evaluatable format constraints. They are used in the context of the
#     data evaluation (_after_ the Mussfeldprüfung) and can be either True/False or None.
#     """

#     name: str = attrs.field(validator=attrs.validators.instance_of(str))
# e.g. "MaLo-Prüfsummenprüfung" or "OBIS-Format"


# ideas for format constraints:
# + check sum (or more generally: computational evaluation effort) constraint for e.g. MaLo IDs
# + data bound constraints (date must not be further than 16 days in the future)
# + pattern constraint that check data against a regex pattern (e.g. obis)
# + date format constraint ("must obey 'yyyy-mm-dd'")


class EvaluatedComposition(ConditionNode):
    """
    Node which is returned after a composition of two nodes is evaluated.
    """

    hint: Optional[str] = None  #: text from hints/notes
    format_constraints_expression: Optional[str] = None
    """
    an expression that consists of (initially unevaluated) format constraints that the evaluated field needs to obey
    """
