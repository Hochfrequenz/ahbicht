"""Tests the Evaluator Factory"""

import uuid
from typing import Optional

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from ahbicht.models.enums import ModalMark, RequirementIndicator
from unittests.defaults import default_test_format, default_test_version


class TestEvaluatorFactory:
    """Tests, that evaluators are created correctly via AhbContext"""

    @pytest.mark.parametrize(
        "content_evaluation_result",
        [
            ContentEvaluationResult(
                hints={"501": "foo"},
                format_constraints={
                    "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                },
                requirement_constraints={
                    "1": ConditionFulfilledValue.FULFILLED,  # <-- from resolving the 123P package
                    "2": ConditionFulfilledValue.FULFILLED,
                    "3": ConditionFulfilledValue.UNFULFILLED,
                },
                packages={"123P": "[1]"},
                id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
            )
        ],
    )
    @pytest.mark.parametrize(
        "expression, expected_requirement_indicator, expected_format_constraint_result, expected_in_hints",
        [
            pytest.param("Muss ([2] O [3])[902]U[501]", ModalMark.MUSS, True, "foo"),
            pytest.param("Muss [2] O [3][902]U[501]", ModalMark.MUSS, True, None),
            pytest.param("Muss [2] O [3][902]U[501]U[123P]", ModalMark.MUSS, True, None, id="with package"),
        ],
    )
    async def test_correct_context(
        self,
        content_evaluation_result: ContentEvaluationResult,
        expression: str,
        expected_requirement_indicator: RequirementIndicator,
        expected_format_constraint_result: bool,
        expected_in_hints: Optional[str],
    ) -> None:
        ctx = AhbContext.from_content_evaluation_result(
            content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        tree = await parse_expression_including_unresolved_subexpressions(
            expression=expression, resolve_packages=True, ahb_context=ctx
        )
        assert tree is not None
        expression_evaluation_result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert (
            expression_evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            is True
        )
        assert expression_evaluation_result.requirement_indicator == expected_requirement_indicator
        assert (
            expression_evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled
            is expected_format_constraint_result
        )
        if expected_in_hints is not None:
            assert (
                expected_in_hints
                in expression_evaluation_result.requirement_constraint_evaluation_result.hints  # type: ignore[operator]
            )
        else:
            assert expression_evaluation_result.requirement_constraint_evaluation_result.hints is None
