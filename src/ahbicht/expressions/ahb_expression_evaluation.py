"""
This module evaluates the parsed ahb expression tree.
The AhbExpressionTransformer defines the rules how the different parts of the parsed tree are handled.

The used terms are defined in the README.md.
"""

from typing import List

from lark import Token, Transformer, Tree, v_args
from lark.exceptions import VisitError

from ahbicht.condition_check_results import (
    ConditionCheckResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions.format_constraint_expression_evaluation import format_constraint_evaluation
from ahbicht.expressions.requirement_constraint_expression_evaluation import requirement_constraint_evaluation


# pylint: disable=no-self-use, invalid-name
class AhbExpressionTransformer(Transformer):
    """
    Transformer, that evaluates the trees built from the ahb expressions.
    The input are the conditions as defined in the AHBs in the form of ConditionNodes.
    It returns a list of the seperated requirement indicators with
    their respective condition expressions already evaluated to booleans.
    """

    def __init__(self, entered_input: str):
        """
        The input are the evaluated format constraint conditions in the form of ConditionNodes.
        :param entered_input: dict(condition_keys, ConditionNode)
        """
        super().__init__()
        self.entered_input = entered_input

    def CONDITION_EXPRESSION(self, condition_expression: Token) -> str:
        """Returns the condition expression."""
        return condition_expression.value

    def PREFIX_OPERATOR(self, prefix_operator: Token) -> str:
        """Returns the prefix operator."""
        return prefix_operator.value

    def MODAL_MARK(self, modal_mark: Token) -> str:
        """Returns the modal mark."""
        return modal_mark.value

    @v_args(inline=True)  # Children are provided as *args instead of a list argument
    def single_requirement_indicator_expression(
        self, requirement_indicator, condition_expression
    ) -> ConditionCheckResult:
        """
        Evaluates the condition expression of the respective requirement indicator expression
        and returns a list of the seperated requirement indicators with
        their results of the condition check.
        """
        requirement_constraint_evaluation_result: RequirementConstraintEvaluationResult = (
            requirement_constraint_evaluation(condition_expression)
        )
        format_constraint_evaluation_result: FormatConstraintEvaluationResult = format_constraint_evaluation(
            requirement_constraint_evaluation_result.format_constraints_expression, self.entered_input
        )

        result_of_condition_check: ConditionCheckResult = ConditionCheckResult(
            requirement_indicator=requirement_indicator,
            requirement_constraint_evaluation_result=requirement_constraint_evaluation_result,
            format_constraint_evaluation_result=format_constraint_evaluation_result,
        )

        return result_of_condition_check

    @v_args(inline=True)  # Children are provided as *args instead of a list argument
    def requirement_indicator(self, requirement_indicator) -> ConditionCheckResult:
        """
        If there is no condition expression but only a requirement indicator,
        all evaluations are automatically set to True.
        """
        return ConditionCheckResult(
            requirement_indicator=requirement_indicator,
            requirement_constraint_evaluation_result=RequirementConstraintEvaluationResult(
                requirement_constraints_fulfilled=True,
                requirement_is_conditional=False,
                format_constraints_expression=None,
                hints=None,
            ),
            format_constraint_evaluation_result=FormatConstraintEvaluationResult(
                format_constraints_fulfilled=True, error_message=None
            ),
        )

    # pylint: disable=(line-too-long)
    def ahb_expression(
        self, list_of_single_requirement_indicator_expressions: List[ConditionCheckResult]
    ) -> ConditionCheckResult:
        """
        Returns the requirement indicator with its condition expressions already evaluated to booleans.
        If there are more than one modal mark the first whose conditions are fulfilled is returned or the
        last of the list if they are all unfulfilled.
        """
        for single_requirement_indicator_expression in list_of_single_requirement_indicator_expressions:
            if (
                single_requirement_indicator_expression.requirement_constraint_evaluation_result.requirement_constraints_fulfilled
            ):
                # if there are more than one modal mark, the requirement is conditional
                # even if the one of modal mark itself is not, e.g. `Muss[1] Kann`
                if len(list_of_single_requirement_indicator_expressions) > 1:
                    single_requirement_indicator_expression.requirement_constraint_evaluation_result.requirement_is_conditional = (
                        True
                    )
                return single_requirement_indicator_expression
        return list_of_single_requirement_indicator_expressions[-1]


def evaluate_ahb_expression_tree(parsed_tree: Tree, entered_input: str) -> ConditionCheckResult:
    """
    Evaluates the tree built from the ahb expressions with the help of the AhbExpressionTransformer.

    :param parsed_tree: Tree
    :param entered_input: the conditions as defined in the AHBs in the form of ConditionNodes
    :return: the result of the overall condition check (including requirement constraints, format constraints,
        several modal marks)
    """
    try:
        result = AhbExpressionTransformer(entered_input).transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc

    return result
