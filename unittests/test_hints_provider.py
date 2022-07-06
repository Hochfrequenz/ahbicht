"""
Tests the hints provider module.
"""
import asyncio
import datetime
from logging import LogRecord
from typing import List

import pytest  # type:ignore[import]
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.expressions.hints_provider import HintsProvider, JsonFileHintsProvider


class Dummy1sHintsProvider(HintsProvider):
    """a hints provider that takes 1s for each (dummy) hint text"""

    async def get_hint_text(self, _: str):
        await asyncio.sleep(1)
        return "foo"


class DummyAsyncHintsProvider(HintsProvider):
    """a hints provider that has an async get_hint_text_method"""

    async def get_hint_text(self, _: str):
        return "foo"


class DummySyncHintsProvider(HintsProvider):
    """a hints provider that has a sync get_hint_text_method"""

    def get_hint_text(self, _: str):
        return "foo"


class TestHintsProvider:
    """Test Class for JsonFileHintsProvider"""

    @pytest.mark.datafiles("./unittests/provider_test_files/example_hints_file.json")
    async def test_initiating_hints_provider(self, datafiles):
        """Tests if hints provider is initiated correctly."""
        path_to_hint_json = datafiles / "example_hints_file.json"
        hints_provider = JsonFileHintsProvider(
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2104,
            file_path=path_to_hint_json,
        )
        assert hints_provider.edifact_format == EdifactFormat.UTILMD
        assert hints_provider.edifact_format_version == EdifactFormatVersion.FV2104
        assert await hints_provider.get_hint_text("583") == "[583] Hinweis: Verwendung der ID der Marktlokation"

    async def test_concurrent_hint_text_resolving(self):
        """
        Tests that the get_hint_text methods are evaluated concurrently
        :return:
        """
        hints_provider = Dummy1sHintsProvider()
        dummy_keys = ["1", "2", "3"]
        start = datetime.datetime.now()
        await hints_provider.get_hints(dummy_keys)
        end = datetime.datetime.now()
        assert (end - start).total_seconds() < len(dummy_keys)

    async def test_sync_hint_text_resolving(self, caplog):
        hints_provider = DummySyncHintsProvider()
        dummy_keys = ["1", "2", "3"]
        await hints_provider.get_hints(dummy_keys)
        log_entries: List[LogRecord] = caplog.records
        assert len(log_entries) == 2
        assert log_entries[0].message == "Instantiated DummySyncHintsProvider"
        assert log_entries[1].message == "Found 3 hints for 1, 2, 3"

    async def test_async_hint_text_resolving(self):
        hints_provider = DummyAsyncHintsProvider()
        dummy_keys = ["1", "2", "3"]
        await hints_provider.get_hints(dummy_keys)
