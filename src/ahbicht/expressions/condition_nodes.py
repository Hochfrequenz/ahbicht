"""
This module contains the abstract class ConditionNode, which specifies the nodes of the parsed tree.
The type of the subclass is the decisive factor on how the respective node
is handled in the context of the compositions it is used in.
There are three possible input nodes (RequirementConstraint, Hint and FormatConstraint) and
the EvaluatedComposition node which results from a combination of two nodes (of all possible types).

The used terms are defined in the README_conditions.md.
"""
from abc import ABC
from enum import Enum
from typing import Optional, TypeVar

import attr

# pylint: disable=too-few-public-methods
from marshmallow import Schema, fields, post_load


class ConditionFulfilledValue(str, Enum):
    """
    Possible values to describe the state of a condition
    in the condition_fulfilled attribute of the ConditionNodes.
    """

    FULFILLED = "FULFILLED"  #: if condition is fulfilled
    UNFULFILLED = "UNFULFILLED"  #: if condition is not fulfilled
    UNKNOWN = "UNKNOWN"  #: if it cannot be checked if condition is fulfilled (e.g. "Wenn vorhanden")
    NEUTRAL = (
        "NEUTRAL"  #: a hint or unevaluated format constraint which does not have a status of being fulfilled or not
    )

    def __str__(self):
        return self.value

    def __or__(self, other):
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

    def __and__(self, other):
        if other == ConditionFulfilledValue.NEUTRAL:  # todo: the next 8 lines are nearly identical with __or__
            return self
        if self == ConditionFulfilledValue.NEUTRAL:
            return other
        # if any single operand in the and composition is unfulfilled, then the entire outcome is unfulfilled,
        # regardless of the other operand
        if ConditionFulfilledValue.UNFULFILLED in (self, other):
            return ConditionFulfilledValue.UNFULFILLED
        if ConditionFulfilledValue.UNKNOWN in (self, other):
            return ConditionFulfilledValue.UNKNOWN
        if self == ConditionFulfilledValue.FULFILLED and other == ConditionFulfilledValue.FULFILLED:
            return ConditionFulfilledValue.FULFILLED
        return ConditionFulfilledValue.UNFULFILLED

    def __xor__(self, other):
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


# TConditionNode is a type var that matches any class inheriting from ConditionNode (in contrast to Type[ConditionNode])
TConditionNode = TypeVar("TConditionNode", bound=ConditionNode)


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


class EvaluatedFormatConstraintSchema(Schema):
    """
    A schema to (de)serialize EvaluatedFormatConstraints.
    """

    format_constraint_fulfilled = fields.Boolean(required=True)
    error_message = fields.String(required=False, allow_none=True, dump_default=True)

    # pylint: disable=no-self-use, unused-argument
    @post_load
    def deserialize(self, data, **kwargs) -> EvaluatedFormatConstraint:
        """
        converts the barely typed data dictionary into an actual EvaluatedFormatConstraint
        :param data:
        :param kwargs:
        :return:
        """
        return EvaluatedFormatConstraint(**data)


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

    hint: Optional[str] = attr.ib(default=None)  # text from hints/notes
    format_constraints_expression: Optional[str] = attr.ib(default=None)  # an expression that consists of (initially
    # unevaluated) format constraints that the evaluated field needs to obey
