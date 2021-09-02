""" Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung) """

from unittest.mock import AsyncMock

import inject
import pytest

from ahbicht.condition_check_results import FormatConstraintEvaluationResult, RequirementConstraintEvaluationResult
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.hints_provider import HintsProvider


class TestAHBExpressionEvaluation:
    """Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung)"""

    @pytest.fixture()
    def setup_and_teardown_injector(self):
        inject.clear_and_configure(
            lambda binder: binder.bind(HintsProvider, AsyncMock(wraps=HintsProvider)).bind(
                RcEvaluator, AsyncMock(wraps=RcEvaluator)
            )
        )
        yield
        inject.clear()

    @pytest.mark.parametrize(
        """ahb_expression, expected_requirement_indicator, expected_requirement_constraints_fulfilled,
        expected_requirement_is_conditional, expected_format_constraints_expression, expected_hints""",
        [
            pytest.param("Muss", "Muss", True, False, None, None),
            pytest.param("X", "X", True, False, None, None),
            pytest.param("Muss[1]", "Muss", True, True, None, None),
            pytest.param("Muss[2]", "Muss", False, True, None, None),
            pytest.param("Muss[1]Soll[2]", "Muss", True, True, None, None),
            pytest.param("Muss[2]Soll[1]Kann[4]", "Soll", True, True, None, None),
            pytest.param("Muss[2]\tSoll [ 1]  Kann[4\t]", "Soll", True, True, None, None),
            pytest.param("X[1]", "X", True, True, None, None),
            pytest.param("O[2]", "O", False, True, None, None),
            pytest.param("U[1]", "U", True, True, None, None),
            pytest.param("U[1]U[2]", "U", False, True, None, None),
            pytest.param("X[1]U[2]U[3]O[4]", "X", False, True, None, None),
            pytest.param("Muss([1]O[2])U[3]Soll[2]Kann[2]O[4]", "Muss", True, True, None, None),
            pytest.param("Muss[2]Soll[2]", "Soll", False, True, None, None),
            # Neutral value
            pytest.param("Muss[503]", "Muss", True, False, None, "[503]"),
            pytest.param("Soll[902]", "Soll", True, False, "[902]", None),
            pytest.param("Kann[503]U[504]", "Kann", True, False, None, "[503]U[504]"),
            # Last modal mark without conditions
            pytest.param("Muss[1]Kann", "Muss", True, True, None, None),
            pytest.param("Muss[2]Kann", "Kann", True, True, None, None),
        ],
    )
    def test_evaluate_valid_ahb_expression(
        self,
        mocker,
        ahb_expression,
        expected_requirement_indicator,
        expected_requirement_constraints_fulfilled,
        expected_requirement_is_conditional,
        expected_format_constraints_expression,
        expected_hints,
    ):
        """
        Tests that valid ahb expressions are evaluated as expected.
        Odd condition_keys are True, even condition_keys are False
        """

        def side_effect_rc_evaluation(condition_expression):
            if condition_expression in ["[1]", " [ 1]  ", "[3]", "([1]O[2])U[3]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=True,
                    format_constraints_expression=None,
                    hints=None,
                )
            if condition_expression in ["[2]", "[2]\t", "[4]", "[4\t]", "[1]U[2]", "[1]U[2]U[3]O[4]", "[2]O[4]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=False,
                    requirement_is_conditional=True,
                    format_constraints_expression=None,
                    hints=None,
                )
            if condition_expression in ["[503]", "[503]U[504]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=False,
                    format_constraints_expression=None,
                    hints=condition_expression,
                )
            if condition_expression in ["[902]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=False,
                    format_constraints_expression=condition_expression,
                    hints=None,
                )

        mocker.patch(
            "ahbicht.expressions.ahb_expression_evaluation.requirement_constraint_evaluation",
            side_effect=side_effect_rc_evaluation,
        )
        mocker.patch(
            "ahbicht.expressions.ahb_expression_evaluation.format_constraint_evaluation",
            return_value=FormatConstraintEvaluationResult(format_constraints_fulfilled=True, error_message=None),
        )

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        result = evaluate_ahb_expression_tree(parsed_tree, entered_input=None)

        assert result.requirement_indicator == expected_requirement_indicator
        assert (
            result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            == expected_requirement_constraints_fulfilled
        )
        assert (
            result.requirement_constraint_evaluation_result.requirement_is_conditional
            == expected_requirement_is_conditional
        )
        assert (
            result.requirement_constraint_evaluation_result.format_constraints_expression
            == expected_format_constraints_expression
        )
        assert result.requirement_constraint_evaluation_result.hints == expected_hints

    @pytest.mark.parametrize(
        "expression, expected_error, expected_error_message",
        [
            pytest.param(
                "Muss[]",
                SyntaxError,
                """Please make sure that:
             * all conditions have the form [INT]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """,
            ),
            pytest.param(
                "Soll[1001]",
                ValueError,
                """Condition key is not in valid number range.""",
            ),
        ],
    )
    def test_invalid_ahb_expressions(
        self, expression: str, expected_error: type, expected_error_message: str, setup_and_teardown_injector
    ):
        """Tests that an error is raised when trying to pass invalid values."""

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)

        with pytest.raises(expected_error) as excinfo:
            evaluate_ahb_expression_tree(parsed_tree, entered_input=None)

        assert expected_error_message in str(excinfo.value)
