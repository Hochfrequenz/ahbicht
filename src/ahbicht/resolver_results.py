"""
This module contains classes that are returned by resolvers, meaning the contain a mapping.
"""
from typing import Optional

import attr
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField  # type:ignore[import]

from ahbicht.edifact import EdifactFormat


@attr.s(auto_attribs=True, kw_only=True)
class ConditionTextMapping:
    """
    maps a condition from a specified EDIFACAT format onto a text as it is found in the AHB.
    """

    edifact_format: EdifactFormat = attr.ib(
        validator=attr.validators.instance_of(EdifactFormat)
    )  #: the format in which the condition is used; f.e. 'UTILMD'
    condition_key: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )  #: the key of the condition without square brackets; f.e. '78'
    condition_text: Optional[str] = attr.ib(
        default=None
    )  #: the description of the condition as in the AHB; None if unknown; f.e. 'Wenn SG4 STS+7++E02 (Transaktionsgrund: Einzug/Neuanlage)  nicht vorhanden'.


class ConditionTextMappingSchema(Schema):
    """
    A schema to (de-)serialize :class:`.ConditionTextMapping`s
    """

    edifact_format = EnumField(EdifactFormat)
    condition_key = fields.String()
    condition_text = fields.String(missing=None)

    @post_load
    def deserialize(self, data, **kwargs) -> ConditionTextMapping:
        """
        Converts the barely typed data dictionary into an actual :class:`.ConditionTextMapping`
        """
        return ConditionTextMapping(**data)


@attr.s(auto_attribs=True, kw_only=True)
class PackageConditionExpressionMapping:
    """
    maps a package key from a specified EDIFACT format onto a (not yet parsed) condition expression as it is found in
    the AHB.
    """

    edifact_format: EdifactFormat = attr.ib(
        validator=attr.validators.instance_of(EdifactFormat)
    )  #: the format in which the package is used; f.e. 'UTILMD'
    package_key: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )  #: the key of the package without square brackets but with trailing P; f.e. '10P'
    package_expression: Optional[str] = attr.ib(
        default=None
    )  #: the expression for which the package is a shortcut; None if unknown f.e. '[20] ∧ [244]'


class PackageConditionExpressionMappingSchema(Schema):
    """
    A schema to (de-)serialize :class:`.ConditionTextMapping`s
    """

    edifact_format = EnumField(EdifactFormat)
    package_key = fields.String()
    package_expression = fields.String(missing=None)

    @post_load
    def deserialize(self, data, **kwargs) -> PackageConditionExpressionMapping:
        """
        Converts the barely typed data dictionary into an actual :class:`.ConditionTextMapping`
        """
        return PackageConditionExpressionMapping(**data)
