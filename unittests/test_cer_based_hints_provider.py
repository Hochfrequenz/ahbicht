""" Tests the HintsProvider, that assumes a ContentEvaluationResult to be present in the evaluatable data"""
from typing import Optional

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
from unittests.defaults import default_test_format, default_test_version


class TestCerBasedHintsProvider:
    """Test for the evaluation using the ContentEvaluationResult Based Hints Provider"""

    @pytest.mark.parametrize(
        "inject_cer_evaluators",
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
    async def test_evaluation(self, condition_key: str, expected_result: Optional[str], inject_cer_evaluators):
        token_logic_provider: TokenLogicProvider = inject.instance(TokenLogicProvider)  # type:ignore[assignment]
        hints_provider = token_logic_provider.get_hints_provider(default_test_format, default_test_version)
        actual = await hints_provider.get_hint_text(condition_key)
        assert actual == expected_result
