"""
MAUS s (plural of MAUS) are data structures which are structurally equivalent to the maus.DeepAnwendungshandbuch.
For more information see the MAUS repo and its documentation: https://github.com/Hochfrequenz/mig_ahb_utility_stack/
A MAUS Provider is a class that returns MAUS s' from what ever data source the implementation prefers.
The MAUS provider is supposed to be used with dependency injection.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from maus import DeepAnwendungshandbuch
from maus.edifact import EdifactFormat, EdifactFormatVersion
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema

# pylint:disable=too-few-public-methods


class MausProvider(ABC):
    """
    A MausProvider is a class that provides MAUS' (Deep Anwendungshandbuch) to calling code.
    """

    @abstractmethod
    def get_maus(
        self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, pruefidentifikator: str
    ) -> Optional[DeepAnwendungshandbuch]:
        """
        Return a MAUS for the given parameters. returns None if the requested MAUS is not available.
        """
        raise NotImplementedError("Has to be implemented in inheriting class")


class FileBasedMausProvider(MausProvider):
    """
    A MAUS provider that uses the file system to retrieve MAUS s.
    """

    def __init__(self, base_path: Path, encoding: str = "utf-8"):
        """
        initialize by providing a base path relative to which the MAUS s can be found.
        """
        self.base_path: Path = base_path
        self._encoding = encoding

    @abstractmethod
    def to_path(
        self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, pruefidentifikator: str
    ) -> Path:
        """
        returns the path of the maus file relative to the given parameters.
        """
        raise NotImplementedError("Has to be implemented in inheriting class")

    def get_maus(
        self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, pruefidentifikator: str
    ) -> Optional[DeepAnwendungshandbuch]:
        relative_path = self.to_path(edifact_format, edifact_format_version, pruefidentifikator)
        full_path: Path = self.base_path / relative_path
        try:
            with open(full_path, "r", encoding=self._encoding) as maus_infile:
                file_content_json = json.load(maus_infile)
                maus = DeepAnwendungshandbuchSchema().load(file_content_json)
        except FileNotFoundError:
            return None
        return maus
