"""
This module manages EDIFACT related stuff. It's basically a helper module to avoid stringly typed parameters.
"""
import re
from typing import Dict, Optional

import aenum

pruefidentifikator_pattern = re.compile(r"^[1-9]\d{4}$")


# pylint: disable=too-few-public-methods
class EdifactFormat(aenum.Enum):
    """
    existing EDIFACT formats
    """

    _init_ = "value string"
    APERAK = 99, "APERAK"
    IFTSTA = 21, "IFTSTA"  # Multimodaler Statusbericht
    INSRPT = 23, "INSRPT"  # Prüfbericht
    INVOIC = 31, "INVOIC"  # invoice
    MSCONS = 13, "MSCONS"  # meter readings
    ORDERS = 17, "ORDERS"  # orders
    ORDRSP = 19, "ORDRSP"  # orders response
    PRICAT = 21, "PRICAT"  # price catalogue
    QUOTES = 15, "QUOTES"  # quotes
    REMADV = 33, "REMADV"  # zahlungsavis
    REQOTE = 35, "REQOTE"  # request quote
    UTILMD = 11, "UTILMD"  # utilities master data
    UTILTS = 25, "UTILTS"  # formula

    def __str__(self):
        return self.string


_leading_digits_format_map: Dict[str, EdifactFormat] = {
    "99": EdifactFormat.APERAK,
    "21": EdifactFormat.IFTSTA,
    "23": EdifactFormat.INSRPT,
    "31": EdifactFormat.INVOIC,
    "13": EdifactFormat.MSCONS,
    "17": EdifactFormat.ORDERS,
    "19": EdifactFormat.ORDRSP,
    "27": EdifactFormat.PRICAT,
    "15": EdifactFormat.QUOTES,
    "33": EdifactFormat.REMADV,
    "35": EdifactFormat.REQOTE,
    "11": EdifactFormat.UTILMD,
    "25": EdifactFormat.UTILTS,
}


class EdifactFormatVersion(aenum.Enum):
    """
    One format version refers to the period in which an AHB is valid.
    """

    _init_ = "value string"
    FV2104 = 2104, "FV2104"  # valid since 2021-04-01
    FV2110 = 2110, "FV2110"  # valid from 2021-10-01 onwards
    FV2204 = 2204, "FV2204"  # valid from 2022-04-01 onwards ("MaKo 2022")

    def __str__(self):
        return self.string


def pruefidentifikator_to_format(pruefidentifikator: str) -> Optional[EdifactFormat]:
    """
    returns the format corresponding to a given pruefi
    :param pruefidentifikator:
    :return: matching EDIFACT format or None
    """
    if not pruefidentifikator:
        raise ValueError("The pruefidentifikator must not be falsy")
    if not pruefidentifikator_pattern.match(pruefidentifikator):
        raise ValueError(f"The pruefidentifikator '{pruefidentifikator}' is invalid.")
    try:
        return _leading_digits_format_map[pruefidentifikator[:2]]
    except KeyError:
        return None
