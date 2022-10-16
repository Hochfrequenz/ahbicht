""" Tests the FC evaluator, that assumes a ContentEvaluationResult to be present in the evaluatable data"""
from typing import Optional

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.fc_evaluators import ContentEvaluationResultBasedFcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint
from unittests.defaults import (
    EmptyDefaultRcEvaluator,
    default_test_format,
    default_test_version,
    store_content_evaluation_result_in_evaluatable_data,
)


class TestCerBasedRcEvaluator:
    """Test for the evaluation using the ContentEvaluationResult Based FC Evaluator"""

    @pytest.fixture
    def inject_cer_evaluators(self, request: SubRequest):
        # indirect parametrization: https://stackoverflow.com/a/33879151/10009545
        content_evaluation_result: ContentEvaluationResult = request.param
        assert isinstance(content_evaluation_result, ContentEvaluationResult)
        fc_evaluator = ContentEvaluationResultBasedFcEvaluator()
        fc_evaluator.edifact_format = default_test_format
        fc_evaluator.edifact_format_version = default_test_version

        def get_evaluatable_data():
            return store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)

        def configure(binder):
            binder.bind(TokenLogicProvider, SingletonTokenLogicProvider([EmptyDefaultRcEvaluator(), fc_evaluator]))
            binder.bind_to_provider(EvaluatableDataProvider, get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

    @pytest.mark.parametrize(
        "inject_cer_evaluators",
        [
            pytest.param(
                ContentEvaluationResult(
                    format_constraints={
                        "1": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
                        "2": EvaluatedFormatConstraint(
                            format_constraint_fulfilled=False, error_message="something wrong"
                        ),
                    },
                    requirement_constraints={},
                    hints={},
                )
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "condition_key, expected_result",
        [
            pytest.param("1", EvaluatedFormatConstraint(format_constraint_fulfilled=True)),
            pytest.param(
                "2",
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong"),
            ),
            pytest.param(
                "789",
                None,
            ),
        ],
    )
    async def test_evaluation(
        self, condition_key: str, expected_result: Optional[EvaluatedFormatConstraint], inject_cer_evaluators
    ):
        token_logic_provider: TokenLogicProvider = inject.instance(TokenLogicProvider)
        fc_evalutor = token_logic_provider.get_fc_evaluator(default_test_format, default_test_version)
        if expected_result is not None:
            actual = await fc_evalutor.evaluate_single_format_constraint(condition_key)
            assert actual == expected_result
        else:
            with pytest.raises(NotImplementedError):
                await fc_evalutor.evaluate_single_format_constraint(condition_key)
