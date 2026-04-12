"""Tests the HintsProvider, that assumes a ContentEvaluationResult to be present in the evaluatable data"""

from typing import Optional

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from unittests.defaults import default_test_format, default_test_version


class TestCerBasedHintsProvider:
    """Test for the evaluation using the ContentEvaluationResult Based Hints Provider"""

    @pytest.mark.parametrize(
        "ahb_context_from_cer",
        [
            pytest.param(
                ContentEvaluationResult(
                    format_constraints={},
                    requirement_constraints={},
                    hints={"501": "Hello", "502": "World"},
                )
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "condition_key, expected_result",
        [
            pytest.param("501", "Hello"),
            pytest.param("502", "World"),
            pytest.param("503", None),
        ],
    )
    async def test_evaluation(
        self, condition_key: str, expected_result: Optional[str], ahb_context_from_cer: AhbContext
    ) -> None:
        hints_provider = ahb_context_from_cer.hints_provider
        actual = await hints_provider.get_hint_text(condition_key)
        assert actual == expected_result
