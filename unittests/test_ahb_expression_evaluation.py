"""Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung)"""

import uuid
from unittest.mock import AsyncMock

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from ahbicht.models.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.models.evaluation_results import (
    AhbExpressionEvaluationResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_hints_provider,
    empty_default_rc_evaluator,
    empty_default_test_data,
)


def _make_ahb_context(
    rc=None,
    fc=None,
    hints=None,
    packages=None,
) -> AhbContext:
    """Helper to build an AhbContext from a ContentEvaluationResult."""
    cer = ContentEvaluationResult(
        requirement_constraints=rc or {},
        format_constraints=fc or {},
        hints=hints or {},
        packages=packages or {},
    )
    return AhbContext.from_content_evaluation_result(
        cer,
        edifact_format=default_test_format,
        edifact_format_version=default_test_version,
    )


class TestAHBExpressionEvaluation:
    """Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung)"""

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

        def side_effect_rc_evaluation(condition_expression, ahb_context=None):
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
            side_effect=AsyncMock(
                return_value=FormatConstraintEvaluationResult(format_constraints_fulfilled=True, error_message=None)
            ),
        )

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        ctx = _make_ahb_context()
        result = await evaluate_ahb_expression_tree(parsed_tree, ahb_context=ctx)

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
    async def test_not_wellformed_ahb_expressions(
        self, expression: str, expected_error: type, expected_error_message: str
    ):
        """Tests that an error is raised when trying to pass invalid values."""
        ctx = _make_ahb_context()
        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)

        with pytest.raises(expected_error) as excinfo:  # type: ignore[var-annotated]
            await evaluate_ahb_expression_tree(parsed_tree, ahb_context=ctx)

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
        ctx = AhbContext.from_content_evaluation_result(
            content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        tree_a = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        tree_b = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        # it's OK/expected that the trees look different depending on whether sub expressions are resolved or not
        # but in any case the evaluation result should look the same
        evaluation_result_a = await evaluate_ahb_expression_tree(tree_a, ahb_context=ctx)
        evaluation_result_b = await evaluate_ahb_expression_tree(tree_b, ahb_context=ctx)
        assert evaluation_result_a == evaluation_result_b

    @pytest.mark.parametrize(
        "ahb_expression, content_evaluation_result",
        [
            pytest.param(
                "Muss [901][1] X [902][2]",
                ContentEvaluationResult(
                    hints={"501": "foo"},
                    format_constraints={
                        "901": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                        "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                    },
                    requirement_constraints={
                        "1": ConditionFulfilledValue.FULFILLED,
                        "2": ConditionFulfilledValue.UNFULFILLED,
                    },
                    id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
                    packages={},
                ),
            ),
            pytest.param(
                "Muss [901][1] X [902][2]",
                ContentEvaluationResult(
                    hints={"501": "foo"},
                    format_constraints={
                        "902": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                        "901": EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                    },
                    requirement_constraints={
                        "2": ConditionFulfilledValue.FULFILLED,
                        "1": ConditionFulfilledValue.UNFULFILLED,
                    },
                    id=uuid.UUID("d106f335-f663-4d14-9636-4f43a883ad26"),
                    packages={},
                ),
            ),
        ],
    )
    async def test_valid_expression_evaluation(
        self, ahb_expression: str, content_evaluation_result: ContentEvaluationResult
    ):
        ctx = AhbContext.from_content_evaluation_result(
            content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        evaluation_result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert evaluation_result is not None

    @pytest.mark.parametrize(
        "ahb_expression, content_evaluation_result, expected",
        [
            pytest.param(
                "Soll [1]",
                ContentEvaluationResult(
                    hints={},
                    format_constraints={},
                    requirement_constraints={
                        "1": ConditionFulfilledValue.UNKNOWN,
                    },
                    id=uuid.UUID("9bdc494b-8e61-440b-a15d-eb5630916969"),
                    packages={},
                ),
                AhbExpressionEvaluationResult(
                    requirement_indicator=ModalMark.SOLL,
                    requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                        requirement_constraints_fulfilled=None,
                        requirement_is_conditional=None,
                        format_constraints_expression=None,
                        hints=None,
                    ),
                    format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                        format_constraints_fulfilled=True
                    ),
                ),
            ),
            pytest.param(
                "Muss [1]",
                ContentEvaluationResult(
                    hints={},
                    format_constraints={},
                    requirement_constraints={
                        "1": ConditionFulfilledValue.UNKNOWN,
                    },
                    id=uuid.UUID("ba79e51c-6b74-44ed-ad53-66fba828b1b8"),
                    packages={},
                ),
                AhbExpressionEvaluationResult(
                    requirement_indicator=ModalMark.MUSS,
                    requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                        requirement_constraints_fulfilled=None,
                        requirement_is_conditional=None,
                        format_constraints_expression=None,
                        hints=None,
                    ),
                    format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                        format_constraints_fulfilled=True
                    ),
                ),
            ),
        ],
    )
    async def test_no_not_implemented_error_is_raised_for_unknown_nodes(
        self,
        ahb_expression: str,
        content_evaluation_result: ContentEvaluationResult,
        expected: AhbExpressionEvaluationResult,
    ):
        ctx = AhbContext.from_content_evaluation_result(
            content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        evaluation_result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert evaluation_result is not None
        assert evaluation_result == expected

    async def test_nested_xor_format_constraint_error_message(self):
        """
        Test that nested XOR expressions with multiple unfulfilled format constraints
        produce properly formatted error messages using parentheses instead of nested quotes.
        """
        ahb_expression = "X [950] X [951] X [950]"

        content_evaluation_result = ContentEvaluationResult(
            hints={
                "521": "Hinweis: Verwendung der ID der Marktlokation",
                "522": "Hinweis: Verwendung der ID der Messlokation",
                "523": "Hinweis: Verwendung der ID der Tranche",
            },
            format_constraints={
                "950": EvaluatedFormatConstraint(
                    format_constraint_fulfilled=False, error_message="Formatbedingung nicht erfüllt"
                ),
                "951": EvaluatedFormatConstraint(
                    format_constraint_fulfilled=False, error_message="Formatbedingung nicht erfüllt"
                ),
            },
            requirement_constraints={
                "6": ConditionFulfilledValue.FULFILLED,
                "7": ConditionFulfilledValue.FULFILLED,
                "15": ConditionFulfilledValue.FULFILLED,
                "26": ConditionFulfilledValue.UNFULFILLED,
            },
            id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
            packages={},
        )

        ctx = AhbContext.from_content_evaluation_result(
            content_evaluation_result,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        evaluation_result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)

        assert evaluation_result is not None
        assert evaluation_result.format_constraint_evaluation_result is not None
        error_message = evaluation_result.format_constraint_evaluation_result.error_message
        assert error_message is not None
        assert "(" in error_message
        assert ")" in error_message
        assert error_message == (
            "Entweder (Entweder 'Formatbedingung nicht erfüllt' oder 'Formatbedingung nicht erfüllt') "
            "oder 'Formatbedingung nicht erfüllt'"
        )


class TestAhbExpressionEvaluationWithAhbContext:
    """
    End-to-end tests using AhbContext.
    This proves the full pipeline works without the global DI container.
    """

    async def test_simple_muss_fulfilled(self):
        """Muss [1] where [1] is FULFILLED -> requirement_indicator=MUSS, fulfilled=True"""
        ctx = _make_ahb_context(
            rc={"1": ConditionFulfilledValue.FULFILLED},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [1]")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_indicator == ModalMark.MUSS
        assert result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is True

    async def test_simple_muss_unfulfilled(self):
        """Muss [1] where [1] is UNFULFILLED -> fulfilled=False"""
        ctx = _make_ahb_context(
            rc={"1": ConditionFulfilledValue.UNFULFILLED},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [1]")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is False

    async def test_and_composition_with_format_constraint(self):
        """Muss [1] U [2][901] -- RC fulfilled, FC fulfilled"""
        ctx = _make_ahb_context(
            rc={"1": ConditionFulfilledValue.FULFILLED, "2": ConditionFulfilledValue.FULFILLED},
            fc={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=True)},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [1] U [2][901]")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is True
        assert result.format_constraint_evaluation_result.format_constraints_fulfilled is True

    async def test_or_composition(self):
        """Muss [1] O [2] -- one fulfilled -> fulfilled"""
        ctx = _make_ahb_context(
            rc={"1": ConditionFulfilledValue.UNFULFILLED, "2": ConditionFulfilledValue.FULFILLED},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [1] O [2]")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is True

    async def test_with_hints(self):
        """Muss [501] -- hint key, always neutral -> fulfilled with hint text"""
        ctx = _make_ahb_context(
            hints={"501": "Hinweis 501"},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [501]")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_constraint_evaluation_result.requirement_constraints_fulfilled is True
        assert result.requirement_constraint_evaluation_result.hints == "Hinweis 501"

    async def test_modal_mark_fallthrough(self):
        """Muss [1] Kann -- first unfulfilled, falls through to Kann"""
        ctx = _make_ahb_context(
            rc={"1": ConditionFulfilledValue.UNFULFILLED},
        )
        tree = await parse_expression_including_unresolved_subexpressions("Muss [1] Kann")
        result = await evaluate_ahb_expression_tree(tree, ahb_context=ctx)
        assert result.requirement_indicator == ModalMark.KANN
