"""
Module to provide the condition hints from their respective json file
as dictionary with the condition keys as keys and the hint texts as values.
"""
import asyncio
import inspect
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import inject
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider

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

    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("Instantiated %s", self.__class__.__name__)

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
        self.logger.debug("Found %i hints for %s", len(results), ", ".join(result.keys()))
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
        super().__init__()
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


class ContentEvaluationResultBasedHintsProvider(HintsProvider):
    """
    A hints provider that expects the evaluatable data to contain a ContentEvalutionResult as edifact seed.
    Other than the DictBasedHintsProvider the outcome is not dependent on the initialization but on the evaluatable
    data.
    """

    def __init__(self):
        super().__init__()
        self._schema = ContentEvaluationResultSchema()

    async def get_hint_text(self, condition_key: str) -> Optional[str]:
        # the missing second argument to the private method call in the next line should be injected automatically
        return await self._get_hint_text(condition_key)  # pylint:disable=no-value-for-parameter

    @inject.params(evaluatable_data=EvaluatableDataProvider)  # injects what has been bound to the EvaluatableData type
    async def _get_hint_text(self, condition_key: str, evaluatable_data: EvaluatableData) -> Optional[str]:
        content_evaluation_result: ContentEvaluationResult = self._schema.load(evaluatable_data.body)
        try:
            self.logger.debug("Retrieving hint '%s' from Content Evaluation Result", condition_key)
            return content_evaluation_result.hints[condition_key]
        except KeyError as key_error:
            self.logger.debug("Hint '%s' was not contained in the CER", str(key_error))
            return None
