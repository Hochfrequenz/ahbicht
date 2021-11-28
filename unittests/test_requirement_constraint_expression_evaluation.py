""" Test for the evaluation of the conditions tests (Mussfeldprüfung) """
from typing import Dict, Optional

import pytest  # type:ignore[import]

from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue as cfv
from ahbicht.expressions.condition_nodes import (
    ConditionNode,
    EvaluatedComposition,
    Hint,
    RequirementConstraint,
    UnevaluatedFormatConstraint,
)
from ahbicht.expressions.requirement_constraint_expression_evaluation import evaluate_requirement_constraint_tree


class TestRequirementConstraintEvaluation:
    """Test for the evaluation of the conditions tests (Mussfeldprüfung)"""

    # some valid nodes for easier referencing
    _rc_1 = RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.FULFILLED)
    _rc_2 = RequirementConstraint(condition_key="2", conditions_fulfilled=cfv.UNFULFILLED)
    _rc_3 = RequirementConstraint(condition_key="3", conditions_fulfilled=cfv.FULFILLED)
    _rc_4 = RequirementConstraint(condition_key="4", conditions_fulfilled=cfv.UNFULFILLED)
    _rc_101 = RequirementConstraint(condition_key="101", conditions_fulfilled=cfv.UNKNOWN)
    _rc_102 = RequirementConstraint(condition_key="102", conditions_fulfilled=cfv.UNKNOWN)
    _h_501 = Hint(condition_key="501", hint="[501] Hinweis: Foo")
    _h_502 = Hint(condition_key="502", hint="[502] Hinweis: Bar")
    _fc_950 = UnevaluatedFormatConstraint(condition_key="950")
    _fc_951 = UnevaluatedFormatConstraint(condition_key="951")
    _fc_987 = UnevaluatedFormatConstraint(condition_key="987")
    _fc_988 = UnevaluatedFormatConstraint(condition_key="988")

    @pytest.mark.parametrize(
        "expression, expected_resulting_conditions_fulfilled",
        [
            pytest.param("[1]", cfv.FULFILLED),
            pytest.param("[2]", cfv.UNFULFILLED),
            pytest.param("[1]U[3]", cfv.FULFILLED),
            pytest.param("[1]U[2]", cfv.UNFULFILLED),
            pytest.param("[2]U[1]", cfv.UNFULFILLED),
            pytest.param("[2]U[4]", cfv.UNFULFILLED),
            pytest.param("[1]O[3]", cfv.FULFILLED),
            pytest.param("[1]O[2]", cfv.FULFILLED),
            pytest.param("[2]O[1]", cfv.FULFILLED),
            pytest.param("[2]O[4]", cfv.UNFULFILLED),
            pytest.param("[1]X[3]", cfv.UNFULFILLED),
            pytest.param("[1]X[2]", cfv.FULFILLED),
            pytest.param("[2]X[1]", cfv.FULFILLED),
            pytest.param("[2]X[4]", cfv.UNFULFILLED),
            # Tests 'and before or'
            pytest.param("[2]U[4]O[1]", cfv.FULFILLED),
            pytest.param("[1]O[2]U[4]", cfv.FULFILLED),
            pytest.param("[2]U[1]O[3]", cfv.FULFILLED),
            pytest.param("[2]O[1]U[3]", cfv.FULFILLED),
            pytest.param("[2]O[1]U[4]", cfv.UNFULFILLED),
            pytest.param("[1]U[2]U[3]U[1]", cfv.UNFULFILLED),
            pytest.param("[1]U[3]U[2]U[1]", cfv.UNFULFILLED),
            # a very long one
            pytest.param("[1]U[2]O[1]U[1]U[2]O[2]O[1]", cfv.FULFILLED),
            # with brackets
            pytest.param("([2]U[4])O[1]", cfv.FULFILLED),
            pytest.param("[2]U([4]O[1])", cfv.UNFULFILLED),
        ],
    )
    def test_evaluate_condition_expression_with_valid_conditions_fulfilled(
        self, expression: str, expected_resulting_conditions_fulfilled: cfv
    ):
        """
        Tests that valid strings are parsed as expected.
        Odd condition_keys are True, even condition_keys are False
        """
        input_values = {"1": self._rc_1, "2": self._rc_2, "3": self._rc_3, "4": self._rc_4}

        parsed_tree = parse_condition_expression_to_tree(expression)

        result: ConditionNode = evaluate_requirement_constraint_tree(parsed_tree, input_values)
        assert result.conditions_fulfilled == expected_resulting_conditions_fulfilled

    @pytest.mark.parametrize(
        "expression, input_values, expected_error",
        [
            pytest.param("[1]", {"1": "no_boolean"}, "Please make sure that the passed values are ConditionNodes."),
            pytest.param(
                "[1]U[2]",
                {"1": "no_boolean", "2": True},
                "Please make sure that the passed values are ConditionNodes.",
            ),
            pytest.param(
                "[1]",
                {"1": EvaluatedComposition(conditions_fulfilled=cfv.FULFILLED)},
                "Please make sure that the passed values are ConditionNodes of the type RequirementConstraint, "
                "Hint or FormatConstraint.",
            ),
            # no value for [2]
            pytest.param(
                "[1]U[2]",
                {"1": RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.FULFILLED)},
                "Please make sure that the input values contain all necessary condition_keys.",
            ),
        ],
    )
    def test_evaluate_condition_expression_with_invalid_values(
        self, expression: str, input_values: dict, expected_error: str
    ):
        """Tests that an error is raised when trying to pass invalid values."""
        parsed_tree = parse_condition_expression_to_tree(expression)

        with pytest.raises(ValueError) as excinfo:
            evaluate_requirement_constraint_tree(parsed_tree, input_values)

        assert expected_error in str(excinfo.value)

    @pytest.mark.parametrize(
        "expression, expected_resulting_conditions_fulfilled, expected_resulting_hint",
        [
            pytest.param("[1]", cfv.FULFILLED, None),
            pytest.param(
                "[1]U[501]", cfv.FULFILLED, "[501] Hinweis: Foo"
            ),  # e.g. [1] Segment ist genau einmal je Vorgang anzugeben,
            # dann mit [501] Hinweis: "Verwendung der ID der Messlokation"
            pytest.param("[501]U[1]", cfv.FULFILLED, "[501] Hinweis: Foo"),
            pytest.param("[2]U[501]", cfv.UNFULFILLED, None),
            pytest.param("[501]U[502]", cfv.NEUTRAL, "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            pytest.param("[501]O[502]", cfv.NEUTRAL, "[501] Hinweis: Foo oder [502] Hinweis: Bar"),
            pytest.param(
                "[501]X[502]",
                cfv.NEUTRAL,
                "Entweder ([501] Hinweis: Foo) oder ([502] Hinweis: Bar)",
            ),
            pytest.param("[1]U[501]O[2]U[502]", cfv.FULFILLED, "[501] Hinweis: Foo"),
            pytest.param("[1]U[501]U[2]U[502]", cfv.UNFULFILLED, None),
            pytest.param("[1]U[501]U[3]U[502]", cfv.FULFILLED, "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            # two neutral elements combined
            pytest.param("[1]U([501]O[502])", cfv.FULFILLED, "[501] Hinweis: Foo oder [502] Hinweis: Bar"),
            pytest.param(
                "[1]U([501]X[502])",
                cfv.FULFILLED,
                "Entweder ([501] Hinweis: Foo) oder ([502] Hinweis: Bar)",
            ),
            pytest.param("[1]U([501]U[502])", cfv.FULFILLED, "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            pytest.param("[2]U([501]O[502])", cfv.UNFULFILLED, None),
            pytest.param("[2]U([501]X[502])", cfv.UNFULFILLED, None),
            pytest.param("[2]U([501]U[502])", cfv.UNFULFILLED, None),
        ],
    )
    def test_hints_with_valid_values(
        self,
        expression: str,
        expected_resulting_conditions_fulfilled: cfv,
        expected_resulting_hint: str,
    ):
        """Test valid expressions with Hints/Hinweise."""

        input_values = {
            "1": self._rc_1,
            "2": self._rc_2,
            "3": self._rc_3,
            "501": self._h_501,
            "502": self._h_502,
        }

        parsed_tree = parse_condition_expression_to_tree(expression)
        result: ConditionNode = evaluate_requirement_constraint_tree(parsed_tree, input_values)  # type:ignore[arg-type]

        assert result.conditions_fulfilled == expected_resulting_conditions_fulfilled
        assert getattr(result, "hint", None) == expected_resulting_hint

    @pytest.mark.parametrize(
        """expression, expected_resulting_conditions_fulfilled,
        expected_format_constraint_expression, expected_hint_text""",
        [
            pytest.param("[1][987]", cfv.FULFILLED, "[987]", None),  # true boolean + format constraint
            pytest.param("[987][1]", cfv.FULFILLED, "[987]", None),  # format constraint + true boolean
            # true boolean and unfulfilled constraint
            pytest.param("[2][987]", cfv.UNFULFILLED, None, None),  # false boolean + format constraint
            pytest.param("[987][2]", cfv.UNFULFILLED, None, None),  # format constraint + false boolean
            pytest.param("([1]O[2])[987]", cfv.FULFILLED, "[987]", None),  # true boolean + format constraint
            pytest.param("[987]([1]O[2])", cfv.FULFILLED, "[987]", None),  # format constraint + true boolean
            pytest.param("[501][987]", cfv.NEUTRAL, "[987]", "[501] Hinweis: Foo"),  # hint + format constraint
            pytest.param("[987][501]", cfv.NEUTRAL, "[987]", "[501] Hinweis: Foo"),  # format constraint + hint
            pytest.param("[987]U[988]", cfv.NEUTRAL, "[987] U [988]", None),  # format constraint U format constraint
            pytest.param("[987]O[988]", cfv.NEUTRAL, "[987] O [988]", None),  # format constraint O format constraint
            pytest.param("[987]X[988]", cfv.NEUTRAL, "[987] X [988]", None),  # format constraint X format constraint
            # two neutral elements combined
            pytest.param("[1]U([987]O[988])", cfv.FULFILLED, "([987] O [988])", None),
        ],
    )
    def test_format_constraints(
        self,
        expression: str,
        expected_resulting_conditions_fulfilled: cfv,
        expected_format_constraint_expression: Optional[str],
        expected_hint_text: Optional[str],
    ):
        """Test valid expressions with Format Constraints"""

        input_values = {
            "1": self._rc_1,
            "2": self._rc_2,
            "501": self._h_501,
            "987": self._fc_987,
            "988": self._fc_988,
        }
        parsed_tree = parse_condition_expression_to_tree(expression)
        result: EvaluatedComposition = evaluate_requirement_constraint_tree(
            parsed_tree, input_values  # type:ignore[arg-type]
        )
        assert isinstance(result, EvaluatedComposition)
        assert result.conditions_fulfilled == expected_resulting_conditions_fulfilled
        assert result.hint == expected_hint_text
        assert result.format_constraints_expression == expected_format_constraint_expression

    @pytest.mark.parametrize(
        """expression, expected_resulting_conditions_fulfilled""",
        [
            # and_composition
            pytest.param("[101]", cfv.UNKNOWN),
            pytest.param("[1]U[101]", cfv.UNKNOWN),
            pytest.param("[101]U[1]", cfv.UNKNOWN),
            pytest.param("[2]U[101]", cfv.UNFULFILLED),
            pytest.param("[101]U[2]", cfv.UNFULFILLED),
            pytest.param("[501]U[101]", cfv.UNKNOWN),
            pytest.param("[101]U[987]", cfv.UNKNOWN),
            pytest.param("[101]U[102]", cfv.UNKNOWN),
            # or_composition
            pytest.param("[1]O[101]", cfv.FULFILLED),
            pytest.param("[101]O[1]", cfv.FULFILLED),
            pytest.param("[2]O[101]", cfv.UNKNOWN),
            pytest.param("[101]O[2]", cfv.UNKNOWN),
            pytest.param("[101]O[102]", cfv.UNKNOWN),
            # xor_composition
            pytest.param("[1]X[101]", cfv.UNKNOWN),
            pytest.param("[101]X[1]", cfv.UNKNOWN),
            pytest.param("[2]X[101]", cfv.UNKNOWN),
            pytest.param("[101]X[2]", cfv.UNKNOWN),
            pytest.param("[101]X[102]", cfv.UNKNOWN),
        ],
    )
    def test_unknown_requirement_constraints(self, expression: str, expected_resulting_conditions_fulfilled: cfv):
        """Test valid expressions with unnkown requirement constraints"""

        input_values = {
            "1": self._rc_1,
            "2": self._rc_2,
            "101": self._rc_101,
            "102": self._rc_102,
            "501": self._h_501,
            "987": self._fc_987,
        }
        parsed_tree = parse_condition_expression_to_tree(expression)
        result: EvaluatedComposition = evaluate_requirement_constraint_tree(
            parsed_tree, input_values  # type:ignore[arg-type]
        )
        assert isinstance(result, ConditionNode)
        assert result.conditions_fulfilled == expected_resulting_conditions_fulfilled

    @pytest.mark.parametrize(
        "expression",
        [
            # or_composition
            pytest.param("[1]O[502]"),
            pytest.param("[502]O[1]"),
            pytest.param("[2]O[501]"),
            pytest.param("[501]O[2]"),
            pytest.param("[1]O[987]"),
            pytest.param("[987]O[1]"),
            pytest.param("[988]O[2]"),
            pytest.param("[2]O[988]"),
            ## unknown requirement constraint
            pytest.param("[501]O[101]"),
            pytest.param("[101]O[987]"),
            ## hint and format constraint
            pytest.param("[988]O[502]"),
            pytest.param("[501]O[987]"),
            ## neutral evaluated composition
            pytest.param("[1]O([501]U[502])"),
            pytest.param("[1]O([987]O[988])"),
            pytest.param("[1]O([987]X[988])"),
            # xor_composition
            pytest.param("[1]X[502]"),
            pytest.param("[502]X[1]"),
            pytest.param("[2]X[501]"),
            pytest.param("[501]X[2]"),
            pytest.param("[1]X[987]"),
            pytest.param("[987]X[1]"),
            pytest.param("[988]X[2]"),
            pytest.param("[2]X[988]"),
            ## unknown requirement constraint
            pytest.param("[501]X[101]"),
            pytest.param("[101]X[987]"),
            ## hint and format constraint
            pytest.param("[988]X[502]"),
            pytest.param("[501]X[987]"),
            ## neutral evaluated composition
            pytest.param("[1]X([501]U[502])"),
            pytest.param("[1]X([987]O[988])"),
            pytest.param("[1]X([987]X[988])"),
        ],
    )
    def test_hints_and_formats_with_invalid_or_xor_composition(self, expression: str):
        """Test invalid expressions with invalid or/xor_compositions."""

        input_values = {
            "1": self._rc_1,
            "2": self._rc_2,
            "101": self._rc_101,
            "501": self._h_501,
            "502": self._h_502,
            "987": self._fc_987,
            "988": self._fc_988,
        }

        parsed_tree = parse_condition_expression_to_tree(expression)

        with pytest.raises(NotImplementedError) as excinfo:
            evaluate_requirement_constraint_tree(parsed_tree, input_values)  # type:ignore[arg-type]

        assert """is not implemented as it has no useful result.""" in str(excinfo.value)

    @pytest.mark.parametrize(
        "input_values, expected_evaluated_result",
        [
            pytest.param(
                {
                    "1": RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.UNFULFILLED),
                    "2": RequirementConstraint(condition_key="2", conditions_fulfilled=cfv.FULFILLED),
                    "3": RequirementConstraint(condition_key="3", conditions_fulfilled=cfv.UNFULFILLED),
                    "4": RequirementConstraint(condition_key="4", conditions_fulfilled=cfv.FULFILLED),
                },
                EvaluatedComposition(format_constraints_expression="[950]", conditions_fulfilled=cfv.FULFILLED),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.FULFILLED),
                    "2": RequirementConstraint(condition_key="2", conditions_fulfilled=cfv.UNFULFILLED),
                    "3": RequirementConstraint(condition_key="3", conditions_fulfilled=cfv.FULFILLED),
                    "4": RequirementConstraint(condition_key="4", conditions_fulfilled=cfv.UNFULFILLED),
                },
                EvaluatedComposition(format_constraints_expression="[951]", conditions_fulfilled=cfv.FULFILLED),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.FULFILLED),
                    "2": RequirementConstraint(condition_key="2", conditions_fulfilled=cfv.FULFILLED),
                    "3": RequirementConstraint(condition_key="3", conditions_fulfilled=cfv.FULFILLED),
                    "4": RequirementConstraint(condition_key="4", conditions_fulfilled=cfv.FULFILLED),
                },
                EvaluatedComposition(
                    format_constraints_expression="[950] O [951]",
                    conditions_fulfilled=cfv.FULFILLED,
                ),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(condition_key="1", conditions_fulfilled=cfv.UNFULFILLED),
                    "2": RequirementConstraint(condition_key="2", conditions_fulfilled=cfv.UNFULFILLED),
                    "3": RequirementConstraint(condition_key="3", conditions_fulfilled=cfv.UNFULFILLED),
                    "4": RequirementConstraint(condition_key="4", conditions_fulfilled=cfv.UNFULFILLED),
                },
                EvaluatedComposition(format_constraints_expression=None, conditions_fulfilled=cfv.UNFULFILLED),
            ),
        ],
    )
    def test_format_constraints_example_from_allgemeine_festlegungen(
        self,
        input_values: Dict[str, ConditionNode],
        expected_evaluated_result: EvaluatedComposition,
    ):
        """Test the example from allgemeine Festlegungen"""
        input_values["950"] = self._fc_950
        input_values["951"] = self._fc_951
        parsed_tree = parse_condition_expression_to_tree("([950] ([2] U [4])) O ([951] ([1] U [3]))")
        actual: EvaluatedComposition = evaluate_requirement_constraint_tree(
            parsed_tree, input_values  # type:ignore[arg-type]
        )
        assert isinstance(actual, EvaluatedComposition)
        assert actual == expected_evaluated_result
