"""
Tests the hints provider module.
"""
from ahbicht.edifact import EdifactFormat, EdifactFormatVersion
from ahbicht.expressions.hints_provider import HintsProvider


class TestHintsProvider:
    """Test Class for HintsProvider"""

    def test_initiating_hints_provider(self):
        """Tests if hints provider is initiated correctly."""
        hints_provider = HintsProvider(
            edifact_format=EdifactFormat.UTILMD, edifact_format_version=EdifactFormatVersion.FV2104
        )
        assert hints_provider.edifact_format == EdifactFormat.UTILMD
        assert hints_provider.edifact_format_version == EdifactFormatVersion.FV2104
        assert hints_provider.all_hints["583"] == "[583] Hinweis: Verwendung der ID der Marktlokation"
