"""
Tests the hints provider module.
"""
import pytest

from ahbicht.edifact import EdifactFormat, EdifactFormatVersion
from ahbicht.expressions.hints_provider import JsonFileHintsProvider

pytestmark = pytest.mark.asyncio


class TestHintsProvider:
    """Test Class for JsonFileHintsProvider"""

    @pytest.mark.datafiles("./unittests/resources_condition_hints/FV2104/Hints_FV2104_UTILMD.json")
    async def test_initiating_hints_provider(self, datafiles):
        """Tests if hints provider is initiated correctly."""
        path_to_hint_json = datafiles / "Hints_FV2104_UTILMD.json"
        hints_provider = JsonFileHintsProvider(
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2104,
            file_path=path_to_hint_json,
        )
        assert hints_provider.edifact_format == EdifactFormat.UTILMD
        assert hints_provider.edifact_format_version == EdifactFormatVersion.FV2104
        assert await hints_provider.get_hint_text("583") == "[583] Hinweis: Verwendung der ID der Marktlokation"
