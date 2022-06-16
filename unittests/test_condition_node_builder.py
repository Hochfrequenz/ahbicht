""" Tests for Class Condition Node Builder"""
from pathlib import Path

import inject
import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]

from ahbicht.condition_node_builder import ConditionNodeBuilder
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider, EvaluationContext
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    Hint,
    RequirementConstraint,
    UnevaluatedFormatConstraint,
)
from ahbicht.expressions.hints_provider import JsonFileHintsProvider
from unittests.defaults import default_test_format, default_test_version, return_empty_dummy_evaluatable_data


class DummyRcEvaluator(RcEvaluator):
    """
    a dummy requirement constraint evaluator to be used in the test
    """

    def _get_default_context(self) -> EvaluationContext:
        return None  # type:ignore[return-value]

    edifact_format = default_test_format
    edifact_format_version = default_test_version


class TestConditionNodeBuilder:
    _edifact_format = default_test_format
    _edifact_format_version = default_test_version

    _h_583 = Hint(condition_key="583", hint="[583] Hinweis: Verwendung der ID der Marktlokation")
    _h_584 = Hint(condition_key="584", hint="[584] Hinweis: Verwendung der ID der Messlokation")
    _ufc_955 = UnevaluatedFormatConstraint(condition_key="955")
    _ufc_907 = UnevaluatedFormatConstraint(condition_key="907")

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector(self):
        _hints_provider = JsonFileHintsProvider(
            TestConditionNodeBuilder._edifact_format,
            TestConditionNodeBuilder._edifact_format_version,
            file_path=Path("unittests/provider_test_files/example_hints_file.json"),
        )
        inject.clear_and_configure(
            lambda binder: binder.bind(
                TokenLogicProvider, SingletonTokenLogicProvider([_hints_provider, DummyRcEvaluator()])
            ).bind_to_provider(EvaluatableDataProvider, return_empty_dummy_evaluatable_data)
        )
        yield
        inject.clear()

    def test_initiating_condition_node_builder(self, setup_and_teardown_injector):
        """Tests if condition node builder is initiated correctly."""

        condition_keys = ["501", "12", "903"]
        condition_node_builder = ConditionNodeBuilder(condition_keys)

        assert condition_node_builder.condition_keys == condition_keys
        assert condition_node_builder.requirement_constraints_condition_keys == ["12"]
        assert condition_node_builder.hints_condition_keys == ["501"]
        assert condition_node_builder.format_constraints_condition_keys == ["903"]

    def test_invalid_initiating_condition_node_builder(self, setup_and_teardown_injector):
        """Test that correct error is shown if condition keys are out of range."""
        condition_keys = ["5", "1011"]

        with pytest.raises(ValueError) as excinfo:
            _ = ConditionNodeBuilder(condition_keys)

        assert "Condition key is not in valid number range." in str(excinfo.value)

    async def test_build_hint_nodes(self, setup_and_teardown_injector):
        """Tests that hint nodes are build correctly."""
        condition_keys = ["584", "583"]
        condition_node_builder = ConditionNodeBuilder(condition_keys)
        hint_nodes = await condition_node_builder._build_hint_nodes()
        excepted_hints_nodes = {"583": self._h_583, "584": self._h_584}
        assert hint_nodes == excepted_hints_nodes

    async def test_invalid_hint_nodes(self, setup_and_teardown_injector):
        """Tests that correct error is shown, when hint is not implemented."""
        condition_keys = ["500"]
        # it is possible that a hint with [500] will be implemented in the future as not all hints are collected yet.
        # If test fails, look up if hint exist. And if hint list is completed take one that does not exist.
        condition_node_builder = ConditionNodeBuilder(condition_keys)
        with pytest.raises(KeyError) as excinfo:
            _ = await condition_node_builder._build_hint_nodes()

        assert "There seems to be no hint implemented with condition key '500'." in str(excinfo.value)

    def test_build_unevaluated_format_constraint_nodes(self, setup_and_teardown_injector):
        """Tests that unevaluated format constraints nodes are build correctly."""
        condition_keys = ["907", "955"]
        condition_node_builder = ConditionNodeBuilder(condition_keys)
        unevaluated_fc_nodes = condition_node_builder._build_unevaluated_format_constraint_nodes()
        expected_unevaluated_fc_nodes = {"907": self._ufc_907, "955": self._ufc_955}
        assert unevaluated_fc_nodes == expected_unevaluated_fc_nodes

    @pytest.mark.parametrize(
        "expected_conditions_fulfilled_11, expected_conditions_fulfilled_78",
        [
            pytest.param(ConditionFulfilledValue.FULFILLED, ConditionFulfilledValue.UNKNOWN),
            pytest.param(ConditionFulfilledValue.UNFULFILLED, ConditionFulfilledValue.NEUTRAL),
        ],
    )
    async def test_build_requirement_constraint_nodes(
        self, mocker, expected_conditions_fulfilled_11, expected_conditions_fulfilled_78, setup_and_teardown_injector
    ):
        """Tests that requirement constraint nodes are build correctly."""

        mocker.patch(
            "ahbicht.content_evaluation.rc_evaluators.RcEvaluator.evaluate_single_condition",
            side_effect=[expected_conditions_fulfilled_11, expected_conditions_fulfilled_78],
        )

        condition_keys = ["11", "78"]
        condition_node_builder = ConditionNodeBuilder(condition_keys)

        evaluated_requirement_constraints = await condition_node_builder._build_requirement_constraint_nodes()

        expected_requirement_constraints = {
            "11": RequirementConstraint(condition_key="11", conditions_fulfilled=expected_conditions_fulfilled_11),
            "78": RequirementConstraint(condition_key="78", conditions_fulfilled=expected_conditions_fulfilled_78),
        }
        assert evaluated_requirement_constraints == expected_requirement_constraints

    async def test_requirement_evaluation_for_all_condition_keys(self, mocker, setup_and_teardown_injector):
        mocker.patch(
            "ahbicht.content_evaluation.rc_evaluators.RcEvaluator.evaluate_single_condition",
            side_effect=[ConditionFulfilledValue.FULFILLED, ConditionFulfilledValue.UNFULFILLED],
        )

        condition_keys = ["78", "907", "11", "583"]
        condition_node_builder = ConditionNodeBuilder(condition_keys)

        evaluated_requirement_constraints = (
            await condition_node_builder.requirement_content_evaluation_for_all_condition_keys()
        )

        expected_input_nodes = {
            "11": RequirementConstraint(condition_key="11", conditions_fulfilled=ConditionFulfilledValue.UNFULFILLED),
            "78": RequirementConstraint(condition_key="78", conditions_fulfilled=ConditionFulfilledValue.FULFILLED),
            "583": self._h_583,
            "907": self._ufc_907,
        }
        assert evaluated_requirement_constraints == expected_input_nodes
