"""
Module for taking all the condition keys of a condition expression and building their respective ConditionNodes.
If necessary it evaluates the needed attributes.
"""
from typing import Dict, List, Tuple, Union

import inject

from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.expressions.condition_nodes import Hint, RequirementConstraint, UnevaluatedFormatConstraint
from ahbicht.expressions.hints_provider import HintsProvider

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
        self.hints_provider: HintsProvider = inject.instance(HintsProvider)  # type:ignore[assignment]
        self.rc_evaluator: RcEvaluator = inject.instance(RcEvaluator)  # type:ignore[assignment]
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

    async def _build_hint_nodes(self) -> Dict[str, Hint]:
        """Builds Hint nodes from their condition keys by getting all hint texts from the HintsProvider."""
        return await self.hints_provider.get_hints(self.hints_condition_keys)

    def _build_unevaluated_format_constraint_nodes(self) -> Dict[str, UnevaluatedFormatConstraint]:
        """Build unevaluated format constraint nodes."""
        unevaluated_format_constraints: Dict[str, UnevaluatedFormatConstraint] = {}
        for condition_key in self.format_constraints_condition_keys:
            unevaluated_format_constraints[condition_key] = UnevaluatedFormatConstraint(condition_key=condition_key)
        return unevaluated_format_constraints

    async def _build_requirement_constraint_nodes(self) -> Dict[str, RequirementConstraint]:
        """
        Build requirement constraint nodes by evaluating the constraints
        with the help of the respective Evaluator.
        """

        evaluated_conditions_fulfilled_attribute = await self.rc_evaluator.evaluate_conditions(
            condition_keys=self.requirement_constraints_condition_keys
        )
        evaluated_requirement_constraints: Dict[str, RequirementConstraint] = {}
        for condition_key in self.requirement_constraints_condition_keys:
            evaluated_requirement_constraints[condition_key] = RequirementConstraint(
                condition_key=condition_key,
                conditions_fulfilled=evaluated_conditions_fulfilled_attribute[condition_key],
            )
        return evaluated_requirement_constraints

    async def requirement_content_evaluation_for_all_condition_keys(
        self,
    ) -> Dict[str, TRCTransformerArgument]:
        """Gets input nodes for all condition keys."""
        requirement_constraint_nodes = await self._build_requirement_constraint_nodes()
        hint_nodes = await self._build_hint_nodes()
        unevaluated_format_constraint_nodes = self._build_unevaluated_format_constraint_nodes()
        input_nodes: Dict[str, TRCTransformerArgument] = {
            **requirement_constraint_nodes,
            **hint_nodes,
            **unevaluated_format_constraint_nodes,
        }
        return input_nodes
