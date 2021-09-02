"""
Module to provide the condition hints from their respective json file
as dictionary with the condition keys as keys and the hint texts as values.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from ahbicht.edifact import EdifactFormat, EdifactFormatVersion


# pylint: disable = too-few-public-methods
class HintsProvider(ABC):
    """
    A Hints Provider provides plain text hints for a given condition number.
    This class provides the hints from the respective json file (defined by EdifactFormatVersion and EdifactFormat)
    as dictionary with the condition keys as keys and the hint texts as values.
    """

    def __init__(self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion):
        self.edifact_format: EdifactFormat = edifact_format
        self.edifact_format_version: EdifactFormatVersion = edifact_format_version

    @abstractmethod
    async def get_hint_text(self, condition_key: str) -> str:
        """
        Get the hint text for the given condition key.
        :param condition_key: e.g. "501"
        :return: the corresponding hint text, e.g. "Data is thought to be interpreted as foo bar."
        """
        raise NotImplementedError("The inheriting class has to implement this method")


class JsonFileHintsProvider(HintsProvider):
    """
    The JsonFileHintsProvider loads hints from a JSON file.
    """

    def __init__(self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, file_path: Path):
        super().__init__(edifact_format, edifact_format_version)
        self._all_hints: Dict[str, str] = self._open_and_load_hint_json(file_path)

    @staticmethod
    def _open_and_load_hint_json(file_path: Path) -> Dict[str, str]:
        """
        Opens the hint json file and loads it into an attribute of the class.
        """
        with open(file_path, encoding="utf-8") as json_infile:
            return json.load(json_infile)

    async def get_hint_text(self, condition_key: str) -> str:
        if condition_key in self._all_hints:
            return self._all_hints[condition_key]
        return ""
