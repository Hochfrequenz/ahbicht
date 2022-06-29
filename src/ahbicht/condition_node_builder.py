"""
Module for taking all the condition keys of a condition expression and building their respective ConditionNodes.
If necessary it evaluates the needed attributes.
"""
import sys
from typing import Dict, List, Tuple, Union

import inject

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.expressions.condition_nodes import Hint, RequirementConstraint, UnevaluatedFormatConstraint

# TRCTransformerArgument is a union of nodes that are already evaluated from a Requirement Constraint (RC) perspective.
# The Format Constraints (FC) might still be unevaluated. That's why the return type used in the
# RequirementConstraintTransformer is always an EvaluatedComposition.
TRCTransformerArgument = Union[RequirementConstraint, UnevaluatedFormatConstraint, Hint]


# pylint: disable=no-member, too-few-public-methods


class ConditionNodeBuilder:
    """
    Builds ConditionNodes for the given condition_keys by separating them into their respective types
    and evaluating the necessary attributes.
    It distinguishes between requirement constraint evaluation and format constraint evaluation.
    """

    def __init__(self, condition_keys: List[str]):
        self.token_logic_provider: TokenLogicProvider = inject.instance(TokenLogicProvider)  # type:ignore[assignment]
        self.condition_keys = condition_keys
        (
            self.requirement_constraints_condition_keys,
            self.hints_condition_keys,
            self.format_constraints_condition_keys,
        ) = self._seperate_condition_keys_into_each_type()

    def _seperate_condition_keys_into_each_type(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Separates the list of all condition keys into three lists of their respective types.
        """
        categorized_keys = extract_categorized_keys_from_tree(self.condition_keys)
        # note: if you remove duplicate keys or sort the keys, you'll have failing tests
        return (
            categorized_keys.requirement_constraint_keys,
            categorized_keys.hint_keys,
            categorized_keys.format_constraint_keys,
        )

    @inject.params(evaluatable_data=EvaluatableDataProvider)  # injects what has been bound to the EvaluatableData type
    # search for binder.bind_to_provider(EvaluatableDataProvider, your_function_that_returns_evaluatable_data_goes_here)
    async def _build_hint_nodes(self, evaluatable_data: EvaluatableData) -> Dict[str, Hint]:
        """Builds Hint nodes from their condition keys by getting all hint texts from the HintsProvider."""
        hints_provider = self.token_logic_provider.get_hints_provider(
            evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
        )
        return await hints_provider.get_hints(self.hints_condition_keys)

    def _build_unevaluated_format_constraint_nodes(self) -> Dict[str, UnevaluatedFormatConstraint]:
        """Build unevaluated format constraint nodes."""
        unevaluated_format_constraints: Dict[str, UnevaluatedFormatConstraint] = {}
        for condition_key in self.format_constraints_condition_keys:
            unevaluated_format_constraints[condition_key] = UnevaluatedFormatConstraint(condition_key=condition_key)
        return unevaluated_format_constraints

    @inject.params(evaluatable_data=EvaluatableDataProvider)  # injects what has been bound to the EvaluatableData type
    # search for binder.bind_to_provider(EvaluatableDataProvider, your_function_that_returns_evaluatable_data_goes_here)
    async def _build_requirement_constraint_nodes(
        self, evaluatable_data: EvaluatableData
    ) -> Dict[str, RequirementConstraint]:
        """
        Build requirement constraint nodes by evaluating the constraints
        with the help of the respective Evaluator.
        """
        rc_evaluator = self.token_logic_provider.get_rc_evaluator(
            evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
        )
        evaluated_conditions_fulfilled_attribute = await rc_evaluator.evaluate_conditions(
            condition_keys=self.requirement_constraints_condition_keys, evaluatable_data=evaluatable_data
        )
        evaluated_requirement_constraints: Dict[str, RequirementConstraint] = {}
        for condition_key in self.requirement_constraints_condition_keys:
            evaluated_requirement_constraints[condition_key] = RequirementConstraint(
                condition_key=condition_key,
                conditions_fulfilled=evaluated_conditions_fulfilled_attribute[condition_key],
            )
        return evaluated_requirement_constraints

    async def requirement_content_evaluation_for_all_condition_keys(self) -> Dict[str, TRCTransformerArgument]:
        """Gets input nodes for all condition keys."""
        try:
            requirement_constraint_nodes = (
                await self._build_requirement_constraint_nodes()  # pylint:disable=no-value-for-parameter
            )
            # the missing value should be injected automatically
        except AttributeError as attribute_error:
            # the 'name' attribute of the Attribute error has been added in Python3.10
            # https://docs.python.org/3/library/exceptions.html#AttributeError
            if (sys.version_info.minor < 10 or attribute_error.name == "edifact_format") and attribute_error.args[
                0
            ].startswith("'EvaluatableDataProvider' object has no attribute"):
                # This means the injection was not set up correctly.
                # Instead of the EvaluatableDataProvider being called (which would return EvaluatableData),
                # an instance of the EvaluatableDataProvider itself was instantiated.
                # Most likely you're missing binder.bind_to_provider(EvaluatableDataProvider, callable_goes_here)
                attribute_error.args = (
                    attribute_error.args[0] + ". Are you sure you called .bind_to_provider before?",
                )
            raise  # re-raise with an eventually slightly modified error message
        hint_nodes = await self._build_hint_nodes()  # pylint:disable=no-value-for-parameter
        unevaluated_format_constraint_nodes = self._build_unevaluated_format_constraint_nodes()
        input_nodes: Dict[str, TRCTransformerArgument] = {
            **requirement_constraint_nodes,
            **hint_nodes,
            **unevaluated_format_constraint_nodes,
        }
        return input_nodes
