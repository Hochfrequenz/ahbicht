"""
This module contains classes that are returned by mappers, meaning they contain a mapping.
"""
import re
from typing import Match, Optional

import attrs
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField  # type:ignore[import]
from maus.edifact import EdifactFormat


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True)
class ConditionKeyConditionTextMapping:
    """
    maps a condition from a specified EDIFACT format onto a text as it is found in the AHB.
    """

    edifact_format: EdifactFormat = attrs.field(
        validator=attrs.validators.instance_of(EdifactFormat)
    )  #: the format in which the condition is used; e.g. 'UTILMD'
    condition_key: str = attrs.field(
        validator=attrs.validators.instance_of(str)
    )  #: the key of the condition without square brackets; e.g. '78'
    condition_text: Optional[str] = attrs.field(default=None)
    """
    the description of the condition as in the AHB; None if unknown;
    e.g. 'Wenn SG4 STS+7++E02 (Transaktionsgrund: Einzug/Neuanlage)  nicht vorhanden'.
    """


class ConditionKeyConditionTextMappingSchema(Schema):
    """
    A schema to (de-)serialize :class:`.ConditionKeyConditionTextMapping` s
    """

    edifact_format = EnumField(EdifactFormat)
    condition_key = fields.String()
    condition_text = fields.String(load_default=None)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> ConditionKeyConditionTextMapping:
        """
        Converts the barely typed data dictionary into an actual :class:`.ConditionKeyConditionTextMapping`
        """
        return ConditionKeyConditionTextMapping(**data)


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True)
class PackageKeyConditionExpressionMapping:
    """
    maps a package key from a specified EDIFACT format onto a (not yet parsed) condition expression as it is found in
    the AHB.
    """

    edifact_format: EdifactFormat = attrs.field(
        validator=attrs.validators.instance_of(EdifactFormat)
    )  #: the format in which the package is used; e.g. 'UTILMD'
    package_key: str = attrs.field(
        validator=attrs.validators.instance_of(str)
    )  #: the key of the package without square brackets but with trailing P; e.g. '10P'
    package_expression: Optional[str] = attrs.field(
        default=None
    )  #: the expression for which the package is a shortcut; None if unknown e.g. '[20] ∧ [244]'

    def has_been_resolved_successfully(self) -> bool:
        """
        return true iff the package has been resolved successfully
        """
        return self.package_expression is not None


class PackageKeyConditionExpressionMappingSchema(Schema):
    """
    A schema to (de-)serialize :class:`.PackageKeyConditionExpressionMapping` s
    """

    edifact_format = EnumField(EdifactFormat)
    package_key = fields.String()
    package_expression = fields.String(load_default=None)

    # pylint:disable=unused-argument,no-self-use
    @post_load
    def deserialize(self, data, **kwargs) -> PackageKeyConditionExpressionMapping:
        """
        Converts the barely typed data dictionary into an actual :class:`.PackageKeyConditionExpressionMapping`
        """
        return PackageKeyConditionExpressionMapping(**data)


# pylint:disable=unused-argument
def check_max_greater_or_equal_than_min(instance: "Repeatability", attribute, value):
    """
    assert that 0<=min<max and not both min and max are 0
    """
    if not 0 <= instance.min_occurrences <= instance.max_occurrences:
        raise ValueError(f"0≤n≤m is not fulfilled for n={instance.min_occurrences}, m={instance.max_occurrences}")
    if instance.min_occurrences == instance.max_occurrences == 0:
        raise ValueError("not both min and max occurrences must be 0")


# pylint:disable=too-few-public-methods
@attrs.define(auto_attribs=True, kw_only=True)
class Repeatability:
    """
    describes how often a segment/code must be used when a "repeatability" is provided with packages
    """

    min_occurrences: int = attrs.field(
        validator=attrs.validators.and_(attrs.validators.instance_of(int), check_max_greater_or_equal_than_min)
    )
    """
    how often the segment/code has to be repeated (lower, inclusive bound); may be 0 for optional packages
    """

    max_occurrences: int = attrs.field(
        validator=attrs.validators.and_(attrs.validators.instance_of(int), check_max_greater_or_equal_than_min)
    )
    """
    how often the segment/coode may be repeated at most (upper, inclusive bound).
    This is inclusive meaning that [123P0..1] leads to max_occurrences==1
    """

    def is_optional(self) -> bool:
        """
        returns true if the package used together with this repeatability is optional
        """
        return self.min_occurrences == 0


_repeatability_pattern = re.compile(r"^(?P<min>\d+)\.{2}(?P<max>\d+)$")  #: a pattern to match "n..m" repeatabilities


def parse_repeatability(repeatability_string: str) -> Repeatability:
    """
    parses the given string as repeatability; e.g. `17..23` is parsed as min=17, max=23
    """
    match: Optional[Match[str]] = _repeatability_pattern.match(repeatability_string)
    if match is None:
        raise ValueError(f"The given string '{repeatability_string}' could not be parsed as repeatability")
    min_repeatability = int(match["min"])
    max_repeatability = int(match["max"])
    return Repeatability(min_occurrences=min_repeatability, max_occurrences=max_repeatability)
