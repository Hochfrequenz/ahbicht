"""
This module contains classes that are returned by mappers, meaning they contain a mapping.
"""
from typing import Optional

import attr
from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField  # type:ignore[import]

from ahbicht.edifact import EdifactFormat


# pylint:disable=too-few-public-methods
@attr.s(auto_attribs=True, kw_only=True)
class ConditionKeyConditionTextMapping:
    """
    maps a condition from a specified EDIFACT format onto a text as it is found in the AHB.
    """

    edifact_format: EdifactFormat = attr.ib(
        validator=attr.validators.instance_of(EdifactFormat)
    )  #: the format in which the condition is used; f.e. 'UTILMD'
    condition_key: str = attr.ib(
        validator=attr.validators.instance_of(str)
    )  #: the key of the condition without square brackets; f.e. '78'
    condition_text: Optional[str] = attr.ib(
        default=None
        # pylint:disable=line-too-long
    )  #: the description of the condition as in the AHB; None if unknown; f.e. 'Wenn SG4 STS+7++E02 (Transaktionsgrund: Einzug/Neuanlage)  nicht vorhanden'.


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
@attr.s(auto_attribs=True, kw_only=True)
class PackageKeyConditionExpressionMapping:
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
