""" Tests the HintsProvider, that assumes a ContentEvaluationResult to be present in the evaluatable data"""
from typing import Optional

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.hints_provider import ContentEvaluationResultBasedHintsProvider
from unittests.defaults import (
    EmptyDefaultFcEvaluator,
    EmptyDefaultRcEvaluator,
    default_test_format,
    default_test_version,
    store_content_evaluation_result_in_evaluatable_data,
)


class TestCerBasedRcEvaluator:
    """Test for the evaluation using the ContentEvaluationResult Based Hints Provider"""

    @pytest.fixture
    def inject_cer_evaluators(self, request: SubRequest):
        # indirect parametrization: https://stackoverflow.com/a/33879151/10009545
        content_evaluation_result: ContentEvaluationResult = request.param
        assert isinstance(content_evaluation_result, ContentEvaluationResult)
        hints_provider = ContentEvaluationResultBasedHintsProvider()
        hints_provider.edifact_format = default_test_format
        hints_provider.edifact_format_version = default_test_version

        def get_evaluatable_data():
            return store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)

        def configure(binder):
            binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([EmptyDefaultRcEvaluator(), EmptyDefaultFcEvaluator(), hints_provider]),
            )
            binder.bind_to_provider(EvaluatableDataProvider, get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

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
