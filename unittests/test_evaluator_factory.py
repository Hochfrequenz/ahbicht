""" Tests the Evaluator Factory"""
import uuid
from typing import Optional

import pytest
from _pytest.fixtures import SubRequest

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint

pytestmark = pytest.mark.asyncio


class TestEvaluatorFactory:
    """Tests, that evaluators are created and injected correctly"""

    @pytest.fixture
    def inject_content_evaluation_result(self, request: SubRequest):
        # indirect parametrization: https://stackoverflow.com/a/33879151/10009545
        content_evaluation_result = request.param
        create_and_inject_hardcoded_evaluators(content_evaluation_result=content_evaluation_result)

    @pytest.mark.parametrize(
        "inject_content_evaluation_result",
        [
            ContentEvaluationResult(
                hints={"501": "foo"},
                format_constraints={
                    "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                },
                requirement_constraints={
                    "2": ConditionFulfilledValue.FULFILLED,
                    "3": ConditionFulfilledValue.UNFULFILLED,
                },
                id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "expression, expected_requirement_indicator, expected_format_constraint_result, expected_in_hints",
        [
            pytest.param("Muss ([2] O [3])[902]U[501]", "Muss", True, "foo"),
            pytest.param("Muss [2] O [3][902]U[501]", "Muss", True, None),
        ],
    )
    def test_correct_injection(
        self,
        inject_content_evaluation_result,
        expression: str,
        expected_requirement_indicator: str,
        expected_format_constraint_result: bool,
        expected_in_hints: Optional[str],
    ):
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression=expression)
        assert tree is not None
        expression_evaluation_result = evaluate_ahb_expression_tree(tree, entered_input="hello")
        assert (
            expression_evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            is True
        )
        assert expression_evaluation_result.requirement_indicator == expected_requirement_indicator
        assert (
            expression_evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled
            is expected_format_constraint_result
        )
        if expected_in_hints:
            assert expected_in_hints in expression_evaluation_result.requirement_constraint_evaluation_result.hints
        else:
            assert expression_evaluation_result.requirement_constraint_evaluation_result.hints is None
