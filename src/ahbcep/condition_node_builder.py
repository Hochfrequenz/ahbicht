"""
Module for taking all the condition keys of a condition expression and building their respective ConditionNodes.
If necessary it evaluates the needed attributes.
"""
import asyncio
from typing import Dict, List, Tuple, Union

from ahbcep.content_evaluation.rc_evaluators import RcEvaluator
from ahbcep.expressions.condition_nodes import Hint, RequirementConstraint, UnevaluatedFormatConstraint
from ahbcep.expressions.hints_provider import HintsProvider


# pylint: disable=no-member, too-few-public-methods
class ConditionNodeBuilder:
    """
    Builds ConditionNodes for the given condition_keys by seperating them into their respective types
    and evaluating the necessary attributes.
    It distinguishes between requirement constraint evaluation and format constraint evaluation.
    """

    def __init__(self, condition_keys: List[str], hints_provider: HintsProvider, rc_evaluator: RcEvaluator):
        self.hints_provider = hints_provider
        self.rc_evaluator = rc_evaluator
        self.condition_keys = condition_keys
        (
            self.requirement_constraints_condition_keys,
            self.hints_condition_keys,
            self.format_constraints_condition_keys,
        ) = self._seperate_condition_keys_into_each_type()

    def _seperate_condition_keys_into_each_type(self) -> Tuple[List[str]]:
        """
        Seperates the list of all condition keys into three lists of their respective types.
        The types are differentiated by their number range.
        See 'Allgemeine Festlegungen' from EDI@Energy.
        """
        requirement_constraints: List[str] = []
        hints: List[str] = []
        format_constraints: List[str] = []
        for condition_key in self.condition_keys:
            if 1 <= int(condition_key) <= 499:
                requirement_constraints.append(condition_key)
            elif 500 <= int(condition_key) <= 900:
                hints.append(condition_key)
            elif 901 <= int(condition_key) <= 999:
                format_constraints.append(condition_key)
            else:
                raise ValueError("Condition key is not in valid number range.")
        return requirement_constraints, hints, format_constraints

    def _build_hint_nodes(self) -> Dict[str, Hint]:
        """Builds Hint nodes from their condition keys by getting all hint texts from the HintsProvider."""
        all_hints: Dict[str, str] = self.hints_provider.all_hints
        evaluated_hints = dict()
        for condition_key in self.hints_condition_keys:
            try:
                evaluated_hints[condition_key] = Hint(condition_key=condition_key, hint=all_hints[condition_key])
            except KeyError as key_err:
                raise KeyError("There seems to be no hint implemented with this condition key.") from key_err
        return evaluated_hints

    def _build_unevaluated_format_constraint_nodes(self) -> Dict[str, UnevaluatedFormatConstraint]:
        """Build unevaluated format constraint nodes."""
        unevaluated_format_constraints = dict()
        for condition_key in self.format_constraints_condition_keys:
            unevaluated_format_constraints[condition_key] = UnevaluatedFormatConstraint(condition_key=condition_key)
        return unevaluated_format_constraints

    def _build_requirement_constraint_nodes(self) -> Dict[str, RequirementConstraint]:
        """
        Build requirement constraint nodes by evaluating the constraints
        with the help of the respective Evaluator.
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        evaluated_conditions_fulfilled_attribute: dict = loop.run_until_complete(
            self.rc_evaluator.evaluate_conditions(self.requirement_constraints_condition_keys)
        )

        evaluated_requirement_constraints = dict()
        for condition_key in self.requirement_constraints_condition_keys:
            evaluated_requirement_constraints[condition_key] = RequirementConstraint(
                condition_key=condition_key,
                conditions_fulfilled=evaluated_conditions_fulfilled_attribute[condition_key],
            )
        return evaluated_requirement_constraints

    def requirement_content_evaluation_for_all_condition_keys(
        self,
    ) -> Dict[str, Union[RequirementConstraint, UnevaluatedFormatConstraint, Hint]]:
        """Gets input nodes for all condition keys."""
        requirement_constraint_nodes = self._build_requirement_constraint_nodes()
        hint_nodes = self._build_hint_nodes()
        unevaluated_format_constraint_nodes = self._build_unevaluated_format_constraint_nodes()
        input_nodes = {**requirement_constraint_nodes, **hint_nodes, **unevaluated_format_constraint_nodes}
        return input_nodes