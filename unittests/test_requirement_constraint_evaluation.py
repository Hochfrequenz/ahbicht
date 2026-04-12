"""Test for the requirement constraint evaluation of the condition expressions."""

from typing import Any, Optional

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.expressions.requirement_constraint_expression_evaluation import requirement_constraint_evaluation
from ahbicht.models.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedComposition,
    Hint,
    RequirementConstraint,
    UnevaluatedFormatConstraint,
)
from ahbicht.models.evaluation_results import RequirementConstraintEvaluationResult
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_fc_evaluator,
    empty_default_hints_provider,
    empty_default_package_resolver,
    empty_default_rc_evaluator,
    empty_default_test_data,
)


def _make_context() -> AhbContext:
    return AhbContext(
        rc_evaluator=empty_default_rc_evaluator,
        fc_evaluator=empty_default_fc_evaluator,
        hints_provider=empty_default_hints_provider,
        package_resolver=empty_default_package_resolver,
        evaluatable_data=empty_default_test_data,
    )


class TestRequirementConstraintEvaluation:
    """Test for the evaluation of the condition expression regarding the requirement constraints."""

    _input_values = {
        "1": RequirementConstraint(condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED),
        "2": RequirementConstraint(condition_key="2", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED),
        "3": RequirementConstraint(condition_key="3", conditions_fulfilled=ConditionFulfilledValue.FULFILLED),
        "4": RequirementConstraint(condition_key="4", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED),
        "101": RequirementConstraint(condition_key="101", conditions_fulfilled=ConditionFulfilledValue.UNKNOWN),
        "901": UnevaluatedFormatConstraint(condition_key="901"),
        "902": UnevaluatedFormatConstraint(condition_key="902"),
        "503": Hint(condition_key="503", hint="[503] Hinweis:foo"),
        "504": Hint(condition_key="504", hint="[504] Hinweis:bar"),
    }

    @pytest.mark.parametrize(
        """condition_expression, expected_requirement_constraints_fulfilled,
        expected_requirement_is_conditional, expected_format_constraints_expression, expected_hints""",
        [
            pytest.param("[1]", True, True, None, None),
            pytest.param("[2]", False, True, None, None),
            pytest.param("[2]\t", False, True, None, None),
            pytest.param(" [ 1]  ", True, True, None, None),
            pytest.param("[4\t]", False, True, None, None),
            pytest.param("[1]U[2]", False, True, None, None),
            pytest.param("[1]U[2]U[3]O[4]", False, True, None, None),
            pytest.param("([1]O[2])U[3]", True, True, None, None),
            pytest.param("[2]O[4]", False, True, None, None),
            # Neutral value
            pytest.param("[503]", True, False, None, "[503] Hinweis:foo"),
            pytest.param("[902]", True, False, "[902]", None),
            pytest.param("[503]U[504]", True, False, None, "[503] Hinweis:foo und [504] Hinweis:bar"),
        ],
    )
    async def test_evaluate_valid_ahb_expression(
        self,
        mocker: Any,
        condition_expression: str,
        expected_requirement_constraints_fulfilled: bool,
        expected_requirement_is_conditional: bool,
        expected_format_constraints_expression: Optional[str],
        expected_hints: Optional[str],
    ) -> None:
        """
        Tests that valid ahb expressions are evaluated as expected.
        Odd condition_keys are True, even condition_keys are False
        """
        mocker.patch(
            "ahbicht.expressions.requirement_constraint_expression_evaluation.ConditionNodeBuilder.requirement_content_evaluation_for_all_condition_keys",
            return_value=self._input_values,
        )
        ctx = _make_context()
        requirement_constraint_evaluation_result = await requirement_constraint_evaluation(
            condition_expression=condition_expression, ahb_context=ctx
        )

        assert isinstance(requirement_constraint_evaluation_result, RequirementConstraintEvaluationResult)

        assert (
            requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            == expected_requirement_constraints_fulfilled
        )
        assert (
            requirement_constraint_evaluation_result.requirement_is_conditional == expected_requirement_is_conditional
        )
        assert (
            requirement_constraint_evaluation_result.format_constraints_expression
            == expected_format_constraints_expression
        )
        assert requirement_constraint_evaluation_result.hints == expected_hints

    @pytest.mark.parametrize(
        "condition_expression, input_values, expected_error, expected_error_message",
        [
            pytest.param(
                "[]",
                {"1": "no_boolean"},
                SyntaxError,
                """Please make sure that:
             * all conditions have the form [INT]
             * all packages have the form [INTPn..m]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """,
            ),
            # todo: implement wiederholbarkeiten
            pytest.param(
                "[1]U[2]",
                {"1": "no_boolean", "2": ConditionFulfilledValue.FULFILLED},
                ValueError,
                "Please make sure that the passed values are ConditionNodes.",
            ),
            pytest.param(
                "[1]",
                {"1": EvaluatedComposition(conditions_fulfilled=ConditionFulfilledValue.FULFILLED)},
                ValueError,
                "Please make sure that the passed values are ConditionNodes of the type RequirementConstraint, "
                "Hint or FormatConstraint.",
            ),
            # no value for [2]
            pytest.param(
                "[1]U[2]",
                {"1": RequirementConstraint(condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED)},
                ValueError,
                "Please make sure that the input values contain all necessary condition_keys.",
            ),
        ],
    )
    async def test_evaluate_condition_expression_with_invalid_values(
        self,
        mocker: Any,
        condition_expression: str,
        input_values: dict[str, Any],
        expected_error: type,
        expected_error_message: str,
    ) -> None:
        """Tests that an error is raised when trying to pass invalid values."""
        mocker.patch(
            "ahbicht.expressions.requirement_constraint_expression_evaluation.ConditionNodeBuilder.requirement_content_evaluation_for_all_condition_keys",
            return_value=input_values,
        )
        ctx = _make_context()
        with pytest.raises(expected_error) as excinfo:
            await requirement_constraint_evaluation(condition_expression, ahb_context=ctx)

        assert expected_error_message in str(excinfo.value)
