""" Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung) """
import uuid
from typing import List
from unittest.mock import AsyncMock

import inject
import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.evaluator_factory import create_and_inject_hardcoded_evaluators
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_hints_provider,
    empty_default_rc_evaluator,
    iterating_rc_evaluator,
    return_empty_dummy_evaluatable_data,
)


class TestAHBExpressionEvaluation:
    """Test for the evaluation of the ahb expression conditions tests (Mussfeldprüfung)"""

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector(self):
        inject.clear_and_configure(
            lambda binder: binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([empty_default_hints_provider, empty_default_rc_evaluator]),
            ).bind_to_provider(EvaluatableDataProvider, return_empty_dummy_evaluatable_data)
        )
        yield
        inject.clear()

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector_without_evaluatable_data_provider(self):
        inject.clear_and_configure(
            lambda binder: binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([empty_default_hints_provider, empty_default_rc_evaluator]),
            )
            # similar to the fixture above but without the evaluatable data provider => leads to injection errors
        )
        yield
        inject.clear()

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector_with_iterating_rc_evaluator(self):
        inject.clear_and_configure(
            lambda binder: binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([empty_default_hints_provider, iterating_rc_evaluator]),
            ).bind_to_provider(EvaluatableDataProvider, return_empty_dummy_evaluatable_data)
        )
        yield
        inject.clear()

    async def test_evaluation_under_cache(self, setup_and_teardown_injector_with_iterating_rc_evaluator):
        """
        This test is to show that the content evaluation is _not_ affected by the cache, meaning it's still possible
        to get different outcomes for the same expression even if it has been evaluated once already.
        This is a very basic assertion but not always given.
        """
        expression = "Muss [1] U [2]"
        evaluation_results: List[AhbExpressionEvaluationResult] = []
        for _ in range(9):
            # see iterating_rc_evaluator for the behaviour of 1 and 2. Both iterate
            # 1: (true, false, true, false, ...)
            # 2: (true, true, false, false, true, true, false, false, ...)
            # --------------------------
            #   1   |   2   | [1] U [2]
            # true  | true  | true
            # false | true  | false
            # true  | false | false
            # false | false | false
            # true  | true  | true
            # ... repeat
            tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)
            evaluation_result = await evaluate_ahb_expression_tree(tree)
            evaluation_results.append(evaluation_result)
        overall_results = [
            x.requirement_constraint_evaluation_result.requirement_constraints_fulfilled for x in evaluation_results
        ]
        assert overall_results == [True, False, False, False, True, False, False, False, True]

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
        result = await evaluate_ahb_expression_tree(parsed_tree)

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
        self, expression: str, expected_error: type, expected_error_message: str, setup_and_teardown_injector
    ):
        """Tests that an error is raised when trying to pass invalid values."""

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(expression)

        with pytest.raises(expected_error) as excinfo:  # type: ignore[var-annotated]
            await evaluate_ahb_expression_tree(parsed_tree)

        assert expected_error_message in str(excinfo.value)

    async def test_missing_bind_to_provider_error(self, setup_and_teardown_injector_without_evaluatable_data_provider):
        """Tests that a meaningful error raised when the user forgot to setup bind_to_provider"""

        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions("Muss [1] U [2]")
        with pytest.raises(AttributeError) as excinfo:  # type: ignore[var-annotated]
            await evaluate_ahb_expression_tree(parsed_tree)
        assert "Are you sure you called .bind_to_provider" in str(excinfo.value)

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
        try:
            create_and_inject_hardcoded_evaluators(
                content_evaluation_result,
                evaluatable_data_provider=return_empty_dummy_evaluatable_data,
                edifact_format=default_test_format,
                edifact_format_version=default_test_version,
            )
            evaluation_result_a = await evaluate_ahb_expression_tree(tree_a)
            evaluation_result_b = await evaluate_ahb_expression_tree(tree_b)
            assert evaluation_result_a == evaluation_result_b
        finally:
            inject.clear()

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
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)
        try:
            create_and_inject_hardcoded_evaluators(
                content_evaluation_result,
                evaluatable_data_provider=return_empty_dummy_evaluatable_data,
                edifact_format=default_test_format,
                edifact_format_version=default_test_version,
            )
            evaluation_result = await evaluate_ahb_expression_tree(tree)
            assert evaluation_result is not None
        finally:
            inject.clear()
