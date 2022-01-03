"""
Enums used in AHB and condition expressions.
"""
from enum import Enum, unique
from typing import Dict, Literal, Union

from marshmallow import Schema, fields, post_dump, post_load, pre_load


@unique
class ModalMark(str, Enum):
    """
    A modal mark describes if information are obligatory or not. The German term is "Merkmal".
    The modal marks are defined by the EDI Energy group (see edi-energy.de → Dokumente → Allgemeine Festlegungen).
    The modal mark stands alone or before a condition expression.
    It can be the start of several requirement indicator expressions in one AHB expression.
    """

    MUSS = "MUSS"
    """
    German term for "Must". Is required for the correct structure of the message.
    If the following condition is not fulfilled, the information must not be given ("must not")
    """

    SOLL = "SOLL"
    """
    German term for "Should". Is required for technical reasons.
    Always followed by a condition.
    If the following condition is not fulfilled, the information must not be given.
    """

    KANN = "KANN"
    """
    German term for "Can". Optional
    """


@unique
class PrefixOperator(str, Enum):
    """
    Operator which does not function to combine conditions, but as requirement indicator.
    It stands alone or in front of a condition expression. Please find detailed descriptions of the operators and their
    usage in the "Allgemeine Festlegungen".
    Note that with MaKo2022 introced 2022-04-01 the "O" and "U" prefix operators will be deprecated.
    Refer to the "Allgemeine Festlegungen" valid up to 2022-04-01 for deprecated "O" and "U".
    """

    X = "X"
    """
    The "X" operator. See "Allgemeine Festlegungen" Kapitel 6.8.1. Usually this just means something is required
    or required under circumstances defined in a trailing condition expression.
    It shall be read as "exclusive or" regarding how qualifiers/codes shall be used from a finite set.
    Note that "X" can also be used as "logical exclusive or" (aka "xor") operator in condition expressions.
    The prefix operator works differently from the logical operator in condition expressions!
    The usage of "X" as logical operator is deprecated since 2022-04-01. It will be replaced with the "⊻" symbol.
    """
    O = "O"
    """
    The "O" operator means that at least one out of multiple possible qualifiers/codes has to be given.
    This is typically found when describing ways to contact a market partner (CTA): You can use email or phone or fax
    but you have to provide at least one of the given possibilities.
    The usage of "O" as a prefix operator is deprecated since 2022-04-01.
    Note that "O" can also be used as a "logical or" (aka "lor") operator in condition expressions.
    The prefix operator works differently from the logical operator in condition expressions!
    The usage of "O" as logical operator is also deprecated since 2022-04-01. It will be replaced with the "∨" symbol.
    """
    U = "U"
    """
    The "U" operator means that all provided qualifiers/codes have to be used.
    The usage of "U" as a prefix operator is deprecated since 2022-04-01.
    Note that "U" can also be used as a "logical and" (aka "land") operator in condition expressions.
    The prefix operator works differently from the logical operator in condition expressions!
    The usage of "U" as logical operator is also deprecated since 2022-04-01. It will be replaced with the "∧" symbol.
    """


RequirementIndicator = Union[PrefixOperator, ModalMark]
"""
A Requirement Indicator is either the Merkmal :class:`ModalMark` or the :class:`PrefixOperator` of the
data element/data element group/segment/segment group at which it is used.
"""


# pylint:disable=no-self-use, unused-argument
class RequirementIndicatorSchema(Schema):
    """
    a helper schema because marshmallow does not support something like fields.Union out of the box
    """

    value = fields.String()

    @pre_load
    def pre_load(self, data, **kwargs) -> Dict[Literal["value"], str]:
        """puts the value in an artificial dictionary"""
        return {"value": data}

    @post_load
    def post_load(self, data, **kwargs) -> RequirementIndicator:
        """tries to parse the data as either PrefixOperator or ModalMark"""
        try:
            return ModalMark(data["value"])
        except ValueError:
            return PrefixOperator(data["value"])

    @post_dump
    def post_dump(self, data, **kwargs):
        """
        returns the enum value as upper case
        """
        return data["value"].upper()


class LogicalOperator(str, Enum):
    """
    Logical operators connect two tokens.
    """

    LAND = "U"
    """
    logical AND, also denoted as "∧", used in and_composition
    """

    LOR = "O"
    """
    logical OR, also denoted as "∨", used in or_composition
    """

    XOR = "X"
    """
    logical excluxive OR (XOR), also denoted as "⊻", used in xor_composition
    """
