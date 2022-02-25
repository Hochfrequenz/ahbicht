"""
Module to provide the condition hints from their respective json file
as dictionary with the condition keys as keys and the hint texts as values.
"""
import asyncio
import inspect
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from maus.edifact import EdifactFormat, EdifactFormatVersion

# pylint: disable = too-few-public-methods
from ahbicht.expressions.condition_nodes import Hint


class HintsProvider(ABC):
    """
    A Hints Provider provides plain text hints for a given condition number.
    This class provides the hints from the respective json file (defined by EdifactFormatVersion and EdifactFormat)
    as dictionary with the condition keys as keys and the hint texts as values.
    """

    edifact_format: EdifactFormat = NotImplementedError(  # type:ignore[assignment]
        "The inheriting class needs to define a format to which it is applicable."
    )

    edifact_format_version: EdifactFormatVersion = NotImplementedError(  # type:ignore[assignment]
        "The inheriting class needs to define a format version."
    )

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
        results: List[Optional[str]]
        if inspect.iscoroutinefunction(self.get_hint_text):
            tasks = [self.get_hint_text(ck) for ck in condition_keys]
            results = await asyncio.gather(*tasks)
        else:
            results = [self.get_hint_text(ck) for ck in condition_keys]  # type:ignore[misc]
        result: Dict[str, Hint] = {}
        for key, value in zip(condition_keys, results):
            if value is None:
                if raise_key_error:
                    raise KeyError(f"There seems to be no hint implemented with condition key '{key}'.")
            else:
                result[key] = Hint(hint=value, condition_key=key)
        return result


class DictBasedHintsProvider(HintsProvider):
    """
    A Hints Provider that is based on hardcoded values from a dictionary
    """

    def __init__(self, results: Mapping[str, Optional[str]]):
        """
        Initialize with a dictionary that contains all the Hinweis texts.
        :param results:
        """
        self._all_hints: Mapping[str, Optional[str]] = results

    async def get_hint_text(self, condition_key: str) -> Optional[str]:
        if not condition_key:
            raise ValueError(f"The condition key must not be None/empty but was '{condition_key}'")
        if condition_key in self._all_hints:
            return self._all_hints[condition_key]
        return None


class JsonFileHintsProvider(DictBasedHintsProvider):
    """
    The JsonFileHintsProvider loads hints from a JSON file.
    """

    def __init__(self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, file_path: Path):
        super().__init__(self._open_and_load_hint_json(file_path))
        self.edifact_format = edifact_format
        self.edifact_format_version = edifact_format_version

    @staticmethod
    def _open_and_load_hint_json(file_path: Path) -> Dict[str, str]:
        """
        Opens the hint json file and loads it into an attribute of the class.
        """
        with open(file_path, encoding="utf-8") as json_infile:
            return json.load(json_infile)
