"""
This module evaluates the parsed ahb expression tree.
The AhbExpressionTransformer defines the rules how the different parts of the parsed tree are handled.

The used terms are defined in the README.md.
"""
from typing import Awaitable, Dict, List, Optional, Union

from lark import Token, Transformer, Tree, v_args
from lark.exceptions import VisitError

from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.expressions.enums import ModalMark, PrefixOperator, RequirementIndicator
from ahbicht.expressions.format_constraint_expression_evaluation import format_constraint_evaluation
from ahbicht.expressions.requirement_constraint_expression_evaluation import requirement_constraint_evaluation
from ahbicht.utility_functions import gather_if_necessary

_str_to_modal_mark_mapping: Dict[str, ModalMark] = {
    "MUSS": ModalMark.MUSS,
    "M": ModalMark.MUSS,
    "KANN": ModalMark.KANN,
    "K": ModalMark.KANN,
    "SOLL": ModalMark.SOLL,
    "S": ModalMark.SOLL,
}


# pylint: disable=no-self-use, invalid-name
# no-self-use: The following methods are not static because it refers to the terminals of the lark grammar.
# invalid-name: That's also the reason why they seemingly violate the naming conventions.
class AhbExpressionTransformer(Transformer):
    """
    Transformer, that evaluates the trees built from the ahb expressions.
    The input are the conditions as defined in the AHBs in the form of ConditionNodes.
    It returns a list of the seperated requirement indicators with
    their respective condition expressions already evaluated to booleans.
    """

    def __init__(self, entered_input: Optional[str]):
        """
        The input are the evaluated format constraint conditions in the form of ConditionNodes.

        :param entered_input: dict(condition_keys, ConditionNode)
        """
        super().__init__()
        self.entered_input = entered_input

    def CONDITION_EXPRESSION(self, condition_expression: Token) -> str:
        """Returns the condition expression."""
        return condition_expression.value

    def PREFIX_OPERATOR(self, prefix_operator: Token) -> PrefixOperator:
        """Returns the prefix operator."""
        return PrefixOperator(prefix_operator.value)

    def MODAL_MARK(self, modal_mark: Token) -> ModalMark:
        """Returns the modal mark."""
        return _str_to_modal_mark_mapping[modal_mark.value.upper()]

    @v_args(inline=True)  # Children are provided as *args instead of a list argument
    def single_requirement_indicator_expression(
        self, requirement_indicator: RequirementIndicator, condition_expression
    ) -> Awaitable[AhbExpressionEvaluationResult]:
        """
        Evaluates the condition expression of the respective requirement indicator expression and returns a list of the
        seperated requirement indicators with their results of the condition check.
        """
        return self._single_requirement_indicator_expression_async(requirement_indicator, condition_expression)

    async def _single_requirement_indicator_expression_async(
        self, requirement_indicator: RequirementIndicator, condition_expression
    ) -> AhbExpressionEvaluationResult:
        """
        See :meth:`single_requirement_indicator_expression_async`
        """
        requirement_constraint_evaluation_result: RequirementConstraintEvaluationResult = (
            await requirement_constraint_evaluation(condition_expression)
        )

        format_constraint_evaluation_result: FormatConstraintEvaluationResult = await format_constraint_evaluation(
            requirement_constraint_evaluation_result.format_constraints_expression, self.entered_input
        )

        result_of_ahb_expression_evaluation: AhbExpressionEvaluationResult = AhbExpressionEvaluationResult(
            requirement_indicator=requirement_indicator,
            requirement_constraint_evaluation_result=requirement_constraint_evaluation_result,
            format_constraint_evaluation_result=format_constraint_evaluation_result,
        )

        return result_of_ahb_expression_evaluation

    @v_args(inline=True)  # Children are provided as *args instead of a list argument
    def requirement_indicator(self, requirement_indicator: RequirementIndicator) -> AhbExpressionEvaluationResult:
        """
        If there is no condition expression but only a requirement indicator,
        all evaluations are automatically set to True.
        """
        return AhbExpressionEvaluationResult(
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
        self,
        list_of_single_requirement_indicator_expressions: List[
            Union[AhbExpressionEvaluationResult, Awaitable[AhbExpressionEvaluationResult]]
        ],
    ) -> Awaitable[AhbExpressionEvaluationResult]:
        """
        Returns the requirement indicator with its condition expressions already evaluated to booleans.
        If there are more than one modal mark the first whose conditions are fulfilled is returned or the
        last of the list if they are all unfulfilled.
        """
        return self._ahb_expression_async(list_of_single_requirement_indicator_expressions)

    async def _ahb_expression_async(
        self,
        list_of_single_requirement_indicator_expressions: List[
            Union[AhbExpressionEvaluationResult, Awaitable[AhbExpressionEvaluationResult]]
        ],
    ) -> AhbExpressionEvaluationResult:
        # the thing is that some user funcs (like e.g. 'requirement_indicator') are not async and there's no reason to
        # make them async. So here we have a list that is mixed: It contains both evaluation results and awaitable
        # evaluation results. The utility function 'gather_if_necessary' accounts for that (see its separate tests).
        results = await gather_if_necessary(list_of_single_requirement_indicator_expressions)
        for single_requirement_indicator_expression in results:
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
        return results[-1]


async def evaluate_ahb_expression_tree(
    parsed_tree: Tree, entered_input: Optional[str]
) -> AhbExpressionEvaluationResult:
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

    return await result
