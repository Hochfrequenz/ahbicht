"""
Test the maus provider as a concept and the file based maus provider as an implementation.
"""
import json
from pathlib import Path

import pytest  # type:ignore[import]
from maus import DeepAnwendungshandbuch
from maus.edifact import EdifactFormat, EdifactFormatVersion
from maus.models.anwendungshandbuch import AhbMetaInformation, DeepAnwendungshandbuchSchema

from ahbicht.validation.maus_provider import FileBasedMausProvider, MausProvider

pytestmark = pytest.mark.asyncio


class MyFooBarMausProvider(FileBasedMausProvider):
    """
    A maus provider, just for this test.
    """

    def to_path(
        self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, pruefidentifikator: str
    ) -> Path:
        return Path(f"{edifact_format_version}/{edifact_format}/{pruefidentifikator}_maus.json")


class TestMausProvider:
    """
    Test the file based maus provider
    """

    def test_file_based_maus_provider_not_found(self, tmpdir_factory):
        maus_root_dir = tmpdir_factory.mktemp("test_dir")
        # we just create an empty temporary directory, just for the sake of having a directory
        provider: MausProvider = MyFooBarMausProvider(base_path=maus_root_dir)
        assert provider is not None
        actual = provider.get_maus(
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2104,
            pruefidentifikator="11001",
        )
        assert actual is None  # because nothing was found

    def test_file_based_maus_provider_success(self, tmpdir_factory):
        maus_root_dir = tmpdir_factory.mktemp("test_dir")
        # no we create something more: a directory structure compatible with the above MyFooBarMausProvider
        maus_root_dir.mkdir("FV2104")
        maus_root_dir.mkdir("FV2104/UTILMD")
        # a minimal maus that is serializable and deserializable
        example_maus = DeepAnwendungshandbuch(meta=AhbMetaInformation(pruefidentifikator="11001"), lines=[])
        with open(maus_root_dir / "FV2104/UTILMD/11001_maus.json", "w+") as maus_test_outfile:
            deep_ahb_dict = DeepAnwendungshandbuchSchema().dump(example_maus)  # create a dictionary
            json.dump(deep_ahb_dict, maus_test_outfile)  # dump the dictionary to the file
        provider: MausProvider = MyFooBarMausProvider(base_path=maus_root_dir)
        assert provider is not None
        actual = provider.get_maus(
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2104,
            pruefidentifikator="11001",
        )
        assert actual is not None  # because the file was found
        assert actual == example_maus  # is equivalent to the original because it was read from the file
