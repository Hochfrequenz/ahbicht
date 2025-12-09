"""Tests for creating different condition nodes that are used in the parsed tree."""

import pytest
from pydantic import ValidationError

from ahbicht.models.condition_nodes import (
    ConditionFulfilledValue,
    ConditionNode,
    EvaluatedComposition,
    EvaluatedFormatConstraint,
    Hint,
    RequirementConstraint,
)


class TestConditionNodes:
    """Test for creating different condition nodes that are used in the parsed tree."""

    @pytest.mark.parametrize(
        "cfv, equivalent_string",
        [
            pytest.param(
                ConditionFulfilledValue.FULFILLED,
                "FULFILLED",
            ),
        ],
    )
    def test_condition_fulfilled_value_equality(self, cfv: ConditionFulfilledValue, equivalent_string: str):
        """For mypy we had to replace some enum comparisons. This test is to ensure that everything works as expected"""
        assert cfv == ConditionFulfilledValue.FULFILLED

    @pytest.mark.parametrize(
        "condition_node_arguments, expected_error_message",
        [
            pytest.param(
                {"conditions_fulfilled": ConditionFulfilledValue.FULFILLED},
                "Field required",
            ),
            pytest.param(
                {
                    "condition_key": "1",
                    "conditions_fulfilled": ConditionFulfilledValue.FULFILLED,
                    "hint": "foo",
                },
                "Extra inputs are not permitted",
            ),
            pytest.param(
                {
                    "condition_key": "1",
                    "conditions_fulfilled": "no_ConditionFulfilledValue",
                },
                f"Input should be 'FULFILLED', 'UNFULFILLED', 'UNKNOWN' or 'NEUTRAL'",
            ),
        ],
    )
    def test_invalid_requirement_constraint(self, condition_node_arguments, expected_error_message):
        """Tests if requirements for RequirementConstraints are working as expected."""
        with pytest.raises(ValidationError) as excinfo:
            RequirementConstraint(**condition_node_arguments)
        assert expected_error_message in str(excinfo.value)

    def test_valid_hint(self):
        """Tests the creation of a valid Hint node."""
        actual_node = Hint(condition_key="501", hint="[501] Hinweis: Foo")

        assert isinstance(actual_node, ConditionNode)
        assert isinstance(actual_node, Hint)
        assert actual_node.condition_key == "501"
        assert actual_node.hint == "[501] Hinweis: Foo"

    @pytest.mark.parametrize(
        "hint_node_arguments, expected_error_message",
        [
            pytest.param(
                {"hint": "[501] Hinweis: Foo"},
                "Field required",
            ),
            pytest.param(
                {"condition_key": "1"},
                "Field required",
            ),
            pytest.param(
                {
                    "condition_key": "501",
                    "hint": "[501] Hinweis: Foo",
                    "format": "bar",
                },
                "Extra inputs are not permitted",
            ),
            pytest.param(
                {"condition_key": "501", "hint": None},
                "Input should be a valid string",
            ),
        ],
    )
    def test_invalid_hint(self, hint_node_arguments, expected_error_message):
        """Tests if requirements for Hints are working as expected."""

        with pytest.raises(ValidationError) as excinfo:
            Hint(**hint_node_arguments)
        assert expected_error_message in str(excinfo.value)

    def test_valid_evaluated_composition(self):
        """Tests the creation of a valid EvaluatedComposition."""
        # Minimal example:
        minimal_node = EvaluatedComposition(conditions_fulfilled=ConditionFulfilledValue.FULFILLED)

        assert isinstance(minimal_node, ConditionNode)
        assert isinstance(minimal_node, EvaluatedComposition)
        assert minimal_node.conditions_fulfilled == ConditionFulfilledValue.FULFILLED

        maximal_node = EvaluatedComposition(
            conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED,
            hint="[501] Hinweis: Foo",
        )

        assert isinstance(maximal_node, ConditionNode)
        assert isinstance(maximal_node, EvaluatedComposition)
        assert maximal_node.conditions_fulfilled == ConditionFulfilledValue.UNFULFILLED
        assert maximal_node.hint == "[501] Hinweis: Foo"

    @pytest.mark.parametrize(
        "resulting_node_arguments, expected_error_message",
        [
            pytest.param(
                {},
                "Field required",
            ),
            pytest.param(
                {
                    "condition": "501",
                    "conditions_fulfilled": True,
                },
                "Extra inputs are not permitted",
            ),
            pytest.param(
                {
                    "conditions_fulfilled": "no_ConditionFulfilledValue",
                },
                f"Input should be 'FULFILLED",
            ),
        ],
    )
    def test_invalid_evaluated_composition(self, resulting_node_arguments, expected_error_message):
        """Tests if requirements for Hints are working as expected."""
        with pytest.raises(ValidationError) as excinfo:
            EvaluatedComposition(**resulting_node_arguments)
        assert expected_error_message in str(excinfo.value)

    @pytest.mark.parametrize(
        "format_constraint_arguments, expected_error_message",
        [
            pytest.param(
                {"format_constraint_fulfilled": True, "error_message": "some error"},
                "error_message must be None when format_constraint_fulfilled is True",
            ),
            pytest.param(
                {"format_constraint_fulfilled": True, "error_message": ""},
                "error_message must be None when format_constraint_fulfilled is True",
            ),
            pytest.param(
                {"format_constraint_fulfilled": False, "error_message": ""},
                "error_message must not be an empty string",
            ),
        ],
    )
    def test_invalid_evaluated_format_constraint(self, format_constraint_arguments, expected_error_message):
        """Tests that EvaluatedFormatConstraint validates error_message correctly."""
        with pytest.raises(ValidationError) as excinfo:
            EvaluatedFormatConstraint(**format_constraint_arguments)
        assert expected_error_message in str(excinfo.value)

    def test_valid_evaluated_format_constraint(self):
        """Tests valid EvaluatedFormatConstraint instances."""
        # fulfilled with no error message
        fulfilled = EvaluatedFormatConstraint(format_constraint_fulfilled=True)
        assert fulfilled.format_constraint_fulfilled is True
        assert fulfilled.error_message is None

        # not fulfilled with error message
        not_fulfilled = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="something wrong")
        assert not_fulfilled.format_constraint_fulfilled is False
        assert not_fulfilled.error_message == "something wrong"

        # not fulfilled with no error message (allowed)
        not_fulfilled_no_msg = EvaluatedFormatConstraint(format_constraint_fulfilled=False)
        assert not_fulfilled_no_msg.format_constraint_fulfilled is False
        assert not_fulfilled_no_msg.error_message is None
