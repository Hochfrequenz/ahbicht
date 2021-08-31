"""
Module to provide the condition hints from their respective json file
as dictionary with the condition keys as keys and the hint texts as values.
"""

import json
from pathlib import Path
from typing import Dict

from ahbicht.edifact import EdifactFormat, EdifactFormatVersion


# pylint: disable = too-few-public-methods
class HintsProvider:
    """
    This class provides the hints from the respective json file (defined by EdifactFormatVersion and EdifactFormat)
    as dictionary with the condition keys as keys and the hint texts as values.
    """

    def __init__(self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion):
        self.edifact_format: EdifactFormat = edifact_format
        self.edifact_format_version: EdifactFormatVersion = edifact_format_version
        self.all_hints = self.open_and_load_hint_json()

    def open_and_load_hint_json(self) -> Dict[str, str]:
        """Opens the hint json file and loads it into an attribute of the class."""
        directory_path = Path(__file__).parent.parent
        file_name = f"Hints_{str(self.edifact_format_version)}_{str(self.edifact_format)}.json"
        path_to_hint_json = directory_path / "resources_condition_hints" / str(self.edifact_format_version) / file_name

        with open(path_to_hint_json, encoding="utf-8") as json_infile:
            return json.load(json_infile)
