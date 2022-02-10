""" Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung) """
import uuid
from unittest.mock import AsyncMock

import inject
import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.evaluation_results import FormatConstraintEvaluationResult, RequirementConstraintEvaluationResult
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.expressions.hints_provider import HintsProvider

pytestmark = pytest.mark.asyncio


class TestAHBExpressionEvaluation:
    """Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung)"""

    @pytest_asyncio.fixture()
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
            pytest.param("Muss", ModalMark.MUSS, True, False, None, None),
            pytest.param("X", PrefixOperator.X, True, False, None, None),
            pytest.param("Muss[1]", ModalMark.MUSS, True, True, None, None),
            pytest.param("muss[1]", ModalMark.MUSS, True, True, None, None),
            pytest.param("M[1]", ModalMark.MUSS, True, True, None, None),
            pytest.param("m[1]", ModalMark.MUSS, True, True, None, None),
            pytest.param("Soll[1]", ModalMark.SOLL, True, True, None, None),
            pytest.param("soll[1]", ModalMark.SOLL, True, True, None, None),
            pytest.param("S[1]", ModalMark.SOLL, True, True, None, None),
            pytest.param("s[1]", ModalMark.SOLL, True, True, None, None),
            pytest.param("Kann[1]", ModalMark.KANN, True, True, None, None),
            pytest.param("kann[1]", ModalMark.KANN, True, True, None, None),
            pytest.param("K[1]", ModalMark.KANN, True, True, None, None),
            pytest.param("k[1]", ModalMark.KANN, True, True, None, None),
            pytest.param("Muss[2]", ModalMark.MUSS, False, True, None, None),
            pytest.param("Muss[1]Soll[2]", ModalMark.MUSS, True, True, None, None),
            pytest.param("Muss[2]Soll[1]Kann[4]", ModalMark.SOLL, True, True, None, None),
            pytest.param("Muss[2]\tSoll [ 1]  Kann[4\t]", ModalMark.SOLL, True, True, None, None),
            pytest.param("X[1]", PrefixOperator.X, True, True, None, None),
            pytest.param("O[2]", PrefixOperator.O, False, True, None, None),
            pytest.param("U[1]", PrefixOperator.U, True, True, None, None),
            pytest.param("U[1]U[2]", PrefixOperator.U, False, True, None, None),
            pytest.param("X[1]U[2]U[3]O[4]", PrefixOperator.X, False, True, None, None),
            pytest.param("Muss([1]O[2])U[3]Soll[2]Kann[2]O[4]", ModalMark.MUSS, True, True, None, None),
            pytest.param("muss([1]o[2])u[3]soll[2]kann[2]O[4]", ModalMark.MUSS, True, True, None, None),
            pytest.param("Muss[2]Soll[2]", ModalMark.SOLL, False, True, None, None),
            # Neutral value
            pytest.param("Muss[503]", ModalMark.MUSS, True, False, None, "[503]"),
            pytest.param("Soll[902]", ModalMark.SOLL, True, False, "[902]", None),
            pytest.param("Kann[503]U[504]", ModalMark.KANN, True, False, None, "[503]U[504]"),
            # Last modal mark without conditions
            pytest.param("Muss[1]Kann", ModalMark.MUSS, True, True, None, None),
            pytest.param("Muss[2]Kann", ModalMark.KANN, True, True, None, None),
        ],
    )
    async def test_evaluate_valid_ahb_expression(
        self,
        mocker,
        ahb_expression,
        expected_requirement_indicator: RequirementIndicator,
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
            if condition_expression.lower() in ["[1]", " [ 1]  ", "[3]", "([1]o[2])u[3]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=True,
                    format_constraints_expression=None,
                    hints=None,
                )
            if condition_expression.lower() in [
                "[2]",
                "[2]\t",
                "[4]",
                "[4\t]",
                "[1]u[2]",
                "[1]u[2]u[3]o[4]",
                "[2]o[4]",
            ]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=False,
                    requirement_is_conditional=True,
                    format_constraints_expression=None,
                    hints=None,
                )
            if condition_expression.lower() in ["[503]", "[503]u[504]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=False,
                    format_constraints_expression=None,
                    hints=condition_expression,
                )
            if condition_expression.lower() in ["[902]"]:
                return RequirementConstraintEvaluationResult(
                    requirement_constraints_fulfilled=True,
                    requirement_is_conditional=False,
                    format_constraints_expression=condition_expression,
                    hints=None,
                )

        mocker.patch(
            "ahbicht.expressions.ahb_expression_evaluation.requirement_constraint_evaluation",
            side_effect=AsyncMock(side_effect=side_effect_rc_evaluation),
        )
        mocker.patch(
            "ahbicht.expressions.ahb_expression_evaluation.format_constraint_evaluation",
            return_value=AsyncMock(
                side_effect=FormatConstraintEvaluationResult(format_constraints_fulfilled=True, error_message=None)
            ),
        )

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        result = await evaluate_ahb_expression_tree(parsed_tree, entered_input=None)  # type:ignore[arg-type]

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
             * all packages have the form [INTPn..m]
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
    async def test_invalid_ahb_expressions(
        self, expression: str, expected_error: type, expected_error_message: str, setup_and_teardown_injector
    ):
        """Tests that an error is raised when trying to pass invalid values."""

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)

        with pytest.raises(expected_error) as excinfo:  # type: ignore[var-annotated]
            await evaluate_ahb_expression_tree(
                parsed_tree, entered_input=None  # type:ignore[arg-type] # ok because error test
            )

        assert expected_error_message in str(excinfo.value)

    @pytest.mark.parametrize(
        "ahb_expression, content_evaluation_result",
        [
            pytest.param(
                "Muss ([2]O[3])[902][501]",
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
                    packages={},
                ),
            )
        ],
    )
    async def test_all_serializations_work_similar(
        self, ahb_expression: str, content_evaluation_result: ContentEvaluationResult
    ):
        tree_a = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        tree_b = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        # it's OK/expected that the trees look different depending on whether sub expressions are resolved or not
        # but in any case the evaluation result should look the same
        create_and_inject_hardcoded_evaluators(content_evaluation_result)
        evaluation_input = "something has to be here but it's not important what"
        evaluation_result_a = await evaluate_ahb_expression_tree(tree_a, entered_input=evaluation_input)
        evaluation_result_b = await evaluate_ahb_expression_tree(tree_b, entered_input=evaluation_input)
        assert evaluation_result_a == evaluation_result_b
