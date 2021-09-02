"""
Module to provide the condition hints from their respective json file
as dictionary with the condition keys as keys and the hint texts as values.
"""
import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ahbicht.edifact import EdifactFormat, EdifactFormatVersion

# pylint: disable = too-few-public-methods
from ahbicht.expressions.condition_nodes import Hint


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
    async def get_hint_text(self, condition_key: str) -> Optional[str]:
        """
        Get the hint text for the given condition key.
        :param condition_key: e.g. "501"
        :return: the corresponding hint text, e.g. "Data is thought to be interpreted as foo bar."
        """
        raise NotImplementedError("The inheriting class has to implement this method")

    async def get_hints(self, condition_keys: List[str], raise_key_error: bool = True) -> Dict[str, Hint]:
        """
        Get Hints for given condition keys by asynchronously awaiting all self.get_hint_text at once
        """
        tasks = [self.get_hint_text(ck) for ck in condition_keys]
        results: List[Optional[str]] = await asyncio.gather(*tasks)
        result: Dict[str, Hint] = {}
        for key, value in zip(condition_keys, results):
            if value is None:
                if raise_key_error:
                    raise KeyError(f"There seems to be no hint implemented with condition key '{key}'.")
            else:
                result[key] = Hint(hint=value, condition_key=key)
        return result


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

    async def get_hint_text(self, condition_key: str) -> Optional[str]:
        if not condition_key:
            raise ValueError(f"The condition key must not be None/empty but was '{condition_key}'")
        if condition_key in self._all_hints:
            return self._all_hints[condition_key]
        return None
