""" Tests the FC evaluator, that assumes a ContentEvaluationResult to be present in the evaluatable data"""
from typing import Optional

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint
from unittests.defaults import default_test_format, default_test_version


class TestCerBasedRcEvaluator:
    """Test for the evaluation using the ContentEvaluationResult Based FC Evaluator"""

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
        token_logic_provider: TokenLogicProvider = inject.instance(TokenLogicProvider)  # type:ignore[assignment]
        fc_evalutor = token_logic_provider.get_fc_evaluator(default_test_format, default_test_version)
        if expected_result is not None:
            actual = await fc_evalutor.evaluate_single_format_constraint(condition_key)
            assert actual == expected_result
        else:
            with pytest.raises(NotImplementedError):
                await fc_evalutor.evaluate_single_format_constraint(condition_key)
