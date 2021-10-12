""" Tests the Evaluator Factory"""
import uuid

import pytest

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint

pytestmark = pytest.mark.asyncio


class TestEvaluatorFactory:
    """Tests, that evaluators are created and injected correctly"""

    @pytest.fixture()
    def setup_and_teardown_injector(self):
        content_eval_result = ContentEvaluationResult(
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
        create_and_inject_hardcoded_evaluators(content_eval_result)

    def test_correct_injection(self, setup_and_teardown_injector):
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions("Muss ([2] O [3])[902]U[501]")
        expression_evaluation_result = evaluate_ahb_expression_tree(tree, entered_input="hello")
        assert (
            expression_evaluation_result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            is True
        )
        assert expression_evaluation_result.requirement_indicator == "Muss"
        assert expression_evaluation_result.format_constraint_evaluation_result.format_constraints_fulfilled is True
        assert "foo" in expression_evaluation_result.requirement_constraint_evaluation_result.hints
