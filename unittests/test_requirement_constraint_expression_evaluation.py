""" Test for the evaluation of the conditions tests (Mussfeldprüfung) """
from typing import Dict, Optional

import pytest

from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
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
    _rc_1 = RequirementConstraint(condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED)
    _rc_2 = RequirementConstraint(condition_key="2", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED)
    _rc_3 = RequirementConstraint(condition_key="3", conditions_fulfilled=ConditionFulfilledValue.FULFILLED)
    _rc_4 = RequirementConstraint(condition_key="4", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED)
    _rc_101 = RequirementConstraint(condition_key="101", conditions_fulfilled=ConditionFulfilledValue.UNKNOWN)
    _rc_102 = RequirementConstraint(condition_key="102", conditions_fulfilled=ConditionFulfilledValue.UNKNOWN)
    _h_501 = Hint(condition_key="501", hint="[501] Hinweis: Foo")
    _h_502 = Hint(condition_key="502", hint="[502] Hinweis: Bar")
    _fc_950 = UnevaluatedFormatConstraint(condition_key="950")
    _fc_951 = UnevaluatedFormatConstraint(condition_key="951")
    _fc_987 = UnevaluatedFormatConstraint(condition_key="987")
    _fc_988 = UnevaluatedFormatConstraint(condition_key="988")

    @pytest.mark.parametrize(
        "expression, expected_resulting_conditions_fulfilled",
        [
            pytest.param("[1]", True),
            pytest.param("[2]", False),
            pytest.param("[1]U[3]", True),
            pytest.param("[1]U[2]", False),
            pytest.param("[2]U[1]", False),
            pytest.param("[2]U[4]", False),
            pytest.param("[1]O[3]", True),
            pytest.param("[1]O[2]", True),
            pytest.param("[2]O[1]", True),
            pytest.param("[2]O[4]", False),
            pytest.param("[1]X[3]", False),
            pytest.param("[1]X[2]", True),
            pytest.param("[2]X[1]", True),
            pytest.param("[2]X[4]", False),
            # Tests 'and before or'
            pytest.param("[2]U[4]O[1]", True),
            pytest.param("[1]O[2]U[4]", True),
            pytest.param("[2]U[1]O[3]", True),
            pytest.param("[2]O[1]U[3]", True),
            pytest.param("[2]O[1]U[4]", False),
            pytest.param("[1]U[2]U[3]U[1]", False),
            pytest.param("[1]U[3]U[2]U[1]", False),
            # a very long one
            pytest.param("[1]U[2]O[1]U[1]U[2]O[2]O[1]", True),
            # with brackets
            pytest.param("([2]U[4])O[1]", True),
            pytest.param("[2]U([4]O[1])", False),
        ],
    )
    def test_evaluate_condition_expression_with_valid_conditions_fulfilled(
        self, expression: str, expected_resulting_conditions_fulfilled: bool
    ):
        """
        Tests that valid strings are parsed as expected.
        Odd condition_keys are True, even condition_keys are False
        """
        input_values = {"1": self._rc_1, "2": self._rc_2, "3": self._rc_3, "4": self._rc_4}

        parsed_tree = parse_condition_expression_to_tree(expression)

        result: ConditionNode = evaluate_requirement_constraint_tree(parsed_tree, input_values)
        assert result.conditions_fulfilled.value == expected_resulting_conditions_fulfilled

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
                {"1": EvaluatedComposition(conditions_fulfilled=ConditionFulfilledValue.FULFILLED)},
                "Please make sure that the passed values are ConditionNodes of the type RequirementConstraint, "
                "Hint or FormatConstraint.",
            ),
            # no value for [2]
            pytest.param(
                "[1]U[2]",
                {"1": RequirementConstraint(condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED)},
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
            pytest.param("[1]", True, None),
            pytest.param(
                "[1]U[501]", True, "[501] Hinweis: Foo"
            ),  # e.g. [1] Segment ist genau einmal je Vorgang anzugeben,
            # dann mit [501] Hinweis: "Verwendung der ID der Messlokation"
            pytest.param("[501]U[1]", True, "[501] Hinweis: Foo"),
            pytest.param("[2]U[501]", False, None),
            pytest.param("[501]U[502]", "Neutral", "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            pytest.param("[501]O[502]", "Neutral", "[501] Hinweis: Foo oder [502] Hinweis: Bar"),
            pytest.param("[501]X[502]", "Neutral", "Entweder ([501] Hinweis: Foo) oder ([502] Hinweis: Bar)"),
            pytest.param("[1]U[501]O[2]U[502]", True, "[501] Hinweis: Foo"),
            pytest.param("[1]U[501]U[2]U[502]", False, None),
            pytest.param("[1]U[501]U[3]U[502]", True, "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            # two neutral elements combined
            pytest.param("[1]U([501]O[502])", True, "[501] Hinweis: Foo oder [502] Hinweis: Bar"),
            pytest.param("[1]U([501]X[502])", True, "Entweder ([501] Hinweis: Foo) oder ([502] Hinweis: Bar)"),
            pytest.param("[1]U([501]U[502])", True, "[501] Hinweis: Foo und [502] Hinweis: Bar"),
            pytest.param("[2]U([501]O[502])", False, None),
            pytest.param("[2]U([501]X[502])", False, None),
            pytest.param("[2]U([501]U[502])", False, None),
        ],
    )
    def test_hints_with_valid_values(
        self, expression: str, expected_resulting_conditions_fulfilled: bool, expected_resulting_hint: str
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
        result: ConditionNode = evaluate_requirement_constraint_tree(parsed_tree, input_values)

        assert result.conditions_fulfilled.value == expected_resulting_conditions_fulfilled
        assert getattr(result, "hint", None) == expected_resulting_hint

    @pytest.mark.parametrize(
        """expression, expected_resulting_conditions_fulfilled,
        expected_format_constraint_expression, expected_hint_text""",
        [
            pytest.param("[1][987]", True, "[987]", None),  # true boolean + format constraint
            pytest.param("[987][1]", True, "[987]", None),  # format constraint + true boolean
            # true boolean and unfulfilled constraint
            pytest.param("[2][987]", False, None, None),  # false boolean + format constraint
            pytest.param("[987][2]", False, None, None),  # format constraint + false boolean
            pytest.param("([1]O[2])[987]", True, "[987]", None),  # true boolean + format constraint
            pytest.param("[987]([1]O[2])", True, "[987]", None),  # format constraint + true boolean
            pytest.param("[501][987]", "Neutral", "[987]", "[501] Hinweis: Foo"),  # hint + format constraint
            pytest.param("[987][501]", "Neutral", "[987]", "[501] Hinweis: Foo"),  # format constraint + hint
            pytest.param("[987]U[988]", "Neutral", "[987] U [988]", None),  # format constraint U format constraint
            pytest.param("[987]O[988]", "Neutral", "[987] O [988]", None),  # format constraint O format constraint
            pytest.param("[987]X[988]", "Neutral", "[987] X [988]", None),  # format constraint X format constraint
            # two neutral elements combined
            pytest.param("[1]U([987]O[988])", True, "([987] O [988])", None),
        ],
    )
    def test_format_constraints(
        self,
        expression: str,
        expected_resulting_conditions_fulfilled: bool,
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
        result: EvaluatedComposition = evaluate_requirement_constraint_tree(parsed_tree, input_values)
        assert isinstance(result, EvaluatedComposition)
        assert result.conditions_fulfilled.value == expected_resulting_conditions_fulfilled
        assert result.hint == expected_hint_text
        assert result.format_constraints_expression == expected_format_constraint_expression

    @pytest.mark.parametrize(
        """expression, expected_resulting_conditions_fulfilled""",
        [
            # and_composition
            pytest.param("[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[1]U[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]U[1]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[2]U[101]", ConditionFulfilledValue.UNFULFILLED),
            pytest.param("[101]U[2]", ConditionFulfilledValue.UNFULFILLED),
            pytest.param("[501]U[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]U[987]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]U[102]", ConditionFulfilledValue.UNKNOWN),
            # or_composition
            pytest.param("[1]O[101]", ConditionFulfilledValue.FULFILLED),
            pytest.param("[101]O[1]", ConditionFulfilledValue.FULFILLED),
            pytest.param("[2]O[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]O[2]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]O[102]", ConditionFulfilledValue.UNKNOWN),
            # xor_composition
            pytest.param("[1]X[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]X[1]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[2]X[101]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]X[2]", ConditionFulfilledValue.UNKNOWN),
            pytest.param("[101]X[102]", ConditionFulfilledValue.UNKNOWN),
        ],
    )
    def test_unknown_requirement_constraints(self, expression: str, expected_resulting_conditions_fulfilled: bool):
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
        result: EvaluatedComposition = evaluate_requirement_constraint_tree(parsed_tree, input_values)
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
            evaluate_requirement_constraint_tree(parsed_tree, input_values)

        assert """is not implemented as it has no useful result.""" in str(excinfo.value)

    @pytest.mark.parametrize(
        "input_values, expected_evaluated_result",
        [
            pytest.param(
                {
                    "1": RequirementConstraint(
                        condition_key="1", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "2": RequirementConstraint(
                        condition_key="2", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "3": RequirementConstraint(
                        condition_key="3", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "4": RequirementConstraint(
                        condition_key="4", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                },
                EvaluatedComposition(
                    format_constraints_expression="[950]", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                ),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(
                        condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "2": RequirementConstraint(
                        condition_key="2", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "3": RequirementConstraint(
                        condition_key="3", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "4": RequirementConstraint(
                        condition_key="4", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                },
                EvaluatedComposition(
                    format_constraints_expression="[951]", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                ),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(
                        condition_key="1", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "2": RequirementConstraint(
                        condition_key="2", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "3": RequirementConstraint(
                        condition_key="3", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                    "4": RequirementConstraint(
                        condition_key="4", conditions_fulfilled=ConditionFulfilledValue.FULFILLED
                    ),
                },
                EvaluatedComposition(
                    format_constraints_expression="[950] O [951]",
                    conditions_fulfilled=ConditionFulfilledValue.FULFILLED,
                ),
            ),
            pytest.param(
                {
                    "1": RequirementConstraint(
                        condition_key="1", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "2": RequirementConstraint(
                        condition_key="2", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "3": RequirementConstraint(
                        condition_key="3", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                    "4": RequirementConstraint(
                        condition_key="4", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                    ),
                },
                EvaluatedComposition(
                    format_constraints_expression=None, conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED
                ),
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
        actual: EvaluatedComposition = evaluate_requirement_constraint_tree(parsed_tree, input_values)
        assert isinstance(actual, EvaluatedComposition)
        assert actual == expected_evaluated_result
