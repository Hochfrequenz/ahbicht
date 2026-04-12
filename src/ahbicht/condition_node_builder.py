"""
Module for taking all the condition keys of a condition expression and building their respective ConditionNodes.
If necessary it evaluates the needed attributes.
"""

from typing import Any, Union

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.models.condition_nodes import Hint, RequirementConstraint, UnevaluatedFormatConstraint

# TRCTransformerArgument is a union of nodes that are already evaluated from a Requirement Constraint (RC) perspective.
# The Format Constraints (FC) might still be unevaluated. That's why the return type used in the
# RequirementConstraintTransformer is always an EvaluatedComposition.
TRCTransformerArgument = Union[RequirementConstraint, UnevaluatedFormatConstraint, Hint]  # pylint:disable=invalid-name


# pylint: disable=no-member, too-few-public-methods


class ConditionNodeBuilder:
    """
    Builds ConditionNodes for the given condition_keys by separating them into their respective types
    and evaluating the necessary attributes.
    It distinguishes between requirement constraint evaluation and format constraint evaluation.
    """

    def __init__(self, condition_keys: list[str], ahb_context: AhbContext) -> None:
        self._ahb_context = ahb_context
        self.condition_keys = condition_keys
        (
            self.requirement_constraints_condition_keys,
            self.hints_condition_keys,
            self.format_constraints_condition_keys,
        ) = self._seperate_condition_keys_into_each_type()

    def _seperate_condition_keys_into_each_type(self) -> tuple[list[str], list[str], list[str]]:
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

    async def _build_hint_nodes(self) -> dict[str, Hint]:
        """Builds Hint nodes from their condition keys by getting all hint texts from the HintsProvider."""
        return await self._ahb_context.hints_provider.get_hints(self.hints_condition_keys)

    def _build_unevaluated_format_constraint_nodes(self) -> dict[str, UnevaluatedFormatConstraint]:
        """Build unevaluated format constraint nodes."""
        unevaluated_format_constraints: dict[str, UnevaluatedFormatConstraint] = {}
        for condition_key in self.format_constraints_condition_keys:
            unevaluated_format_constraints[condition_key] = UnevaluatedFormatConstraint(condition_key=condition_key)
        return unevaluated_format_constraints

    async def _build_requirement_constraint_nodes(
        self,
        evaluatable_data: EvaluatableData[Any],
    ) -> dict[str, RequirementConstraint]:
        """
        Build requirement constraint nodes by evaluating the constraints
        with the help of the respective Evaluator.
        """
        rc_evaluator = self._ahb_context.rc_evaluator
        evaluated_conditions_fulfilled_attribute = await rc_evaluator.evaluate_conditions(
            condition_keys=self.requirement_constraints_condition_keys, evaluatable_data=evaluatable_data
        )
        evaluated_requirement_constraints: dict[str, RequirementConstraint] = {}
        for condition_key in self.requirement_constraints_condition_keys:
            evaluated_requirement_constraints[condition_key] = RequirementConstraint(
                condition_key=condition_key,
                conditions_fulfilled=evaluated_conditions_fulfilled_attribute[condition_key],
            )
        return evaluated_requirement_constraints

    async def requirement_content_evaluation_for_all_condition_keys(self) -> dict[str, TRCTransformerArgument]:
        """Gets input nodes for all condition keys."""
        evaluatable_data = self._ahb_context.evaluatable_data
        requirement_constraint_nodes = await self._build_requirement_constraint_nodes(evaluatable_data=evaluatable_data)
        hint_nodes = await self._build_hint_nodes()
        unevaluated_format_constraint_nodes = self._build_unevaluated_format_constraint_nodes()
        input_nodes: dict[str, TRCTransformerArgument] = {
            **requirement_constraint_nodes,
            **hint_nodes,
            **unevaluated_format_constraint_nodes,
        }
        return input_nodes
