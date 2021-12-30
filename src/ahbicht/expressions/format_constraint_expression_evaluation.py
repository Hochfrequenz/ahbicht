"""
This module evaluates the format constraint expression tree using EvaluatedFormatConstraints.
The FormatConstraintTransformer defines the rules how the different parts and nodes
of the format constraint expression tree are handled.

The used terms are defined in the README_conditions.md.
"""

from typing import Dict, List, Mapping, Optional

import inject
from lark import Token, Tree, v_args
from lark.exceptions import VisitError

from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.evaluation_results import FormatConstraintEvaluationResult
from ahbicht.expressions.base_transformer import BaseTransformer
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint
from ahbicht.expressions.expression_builder import FormatErrorMessageExpressionBuilder


# pylint: disable=no-self-use
@v_args(inline=True)  # Children are provided as *args instead of a list argument
# pylint:disable=inherit-non-class
class FormatConstraintTransformer(BaseTransformer[EvaluatedFormatConstraint, EvaluatedFormatConstraint]):
    """
    Transformer that evaluates the trees built from the format constraint expressions.
    The input are the evaluated format constraint conditions in the form of EvaluatedFormatConstraints.
    The return value is an EvaluatedFormatConstraint whose attribute `format_constraint_fulfilled` describes whether
    the format constraint expression is fulfilled or not.
    """

    def and_composition(
        self, left: EvaluatedFormatConstraint, right: EvaluatedFormatConstraint
    ) -> EvaluatedFormatConstraint:
        """Evaluates logical and_composition"""

        resulting_format_constraint_fulfilled = left.format_constraint_fulfilled and right.format_constraint_fulfilled
        error_message = FormatErrorMessageExpressionBuilder(left).land(right).get_expression()

        return EvaluatedFormatConstraint(
            format_constraint_fulfilled=resulting_format_constraint_fulfilled, error_message=error_message
        )

    def or_composition(
        self, left: EvaluatedFormatConstraint, right: EvaluatedFormatConstraint
    ) -> EvaluatedFormatConstraint:
        """Evaluates logical (inclusive) or_composition"""

        resulting_format_constraint_fulfilled = left.format_constraint_fulfilled or right.format_constraint_fulfilled
        error_message = FormatErrorMessageExpressionBuilder(left).lor(right).get_expression()

        return EvaluatedFormatConstraint(
            format_constraint_fulfilled=resulting_format_constraint_fulfilled, error_message=error_message
        )

    def xor_composition(
        self, left: EvaluatedFormatConstraint, right: EvaluatedFormatConstraint
    ) -> EvaluatedFormatConstraint:
        """Evaluates exclusive xor_composition"""

        resulting_format_constraint_fulfilled = left.format_constraint_fulfilled ^ right.format_constraint_fulfilled
        error_message = FormatErrorMessageExpressionBuilder(left).xor(right).get_expression()

        return EvaluatedFormatConstraint(
            format_constraint_fulfilled=resulting_format_constraint_fulfilled, error_message=error_message
        )


def evaluate_format_constraint_tree(
    parsed_tree: Tree, input_values: Mapping[str, EvaluatedFormatConstraint]
) -> EvaluatedFormatConstraint:
    """
    Evaluates the tree built from the format constraint expressions with the help of the FormatConstraintTransformer.

    :param parsed_tree: Tree
    :param input_values: dict(condition_key, EvaluatedFormatConstraint)
        :return: EvaluatedFormatConstraint
    """
    if not all(isinstance(input_value, EvaluatedFormatConstraint) for input_value in input_values.values()):
        raise ValueError(f"Please make sure that the passed values are {EvaluatedFormatConstraint.__name__}s.")
    try:
        result = FormatConstraintTransformer(input_values).transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc

    return result


async def format_constraint_evaluation(
    format_constraints_expression: Optional[str], entered_input: str
) -> FormatConstraintEvaluationResult:
    """
    Evaluation of the format constraint expression.
    """
    error_message: Optional[str] = None
    format_constraints_fulfilled: bool
    if not format_constraints_expression:
        format_constraints_fulfilled = True
    else:
        parsed_tree_fc: Tree = parse_condition_expression_to_tree(format_constraints_expression)
        all_evaluatable_format_constraint_keys: List[str] = [
            t.value for t in parsed_tree_fc.scan_values(lambda v: isinstance(v, Token))  # type:ignore[attr-defined]
        ]
        input_values: Dict[str, EvaluatedFormatConstraint] = await _build_evaluated_format_constraint_nodes(
            all_evaluatable_format_constraint_keys, entered_input
        )
        resulting_evaluated_format_constraint_node: EvaluatedFormatConstraint = evaluate_format_constraint_tree(
            parsed_tree_fc, input_values
        )
        format_constraints_fulfilled = resulting_evaluated_format_constraint_node.format_constraint_fulfilled
        error_message = resulting_evaluated_format_constraint_node.error_message  # pylint:disable=no-member

    return FormatConstraintEvaluationResult(
        format_constraints_fulfilled=format_constraints_fulfilled, error_message=error_message
    )


async def _build_evaluated_format_constraint_nodes(
    evaluatable_format_constraint_keys: List[str], entered_input: str
) -> Dict[str, EvaluatedFormatConstraint]:
    """Build evaluated format constraint nodes."""

    evaluator: FcEvaluator = inject.instance(FcEvaluator)
    evaluated_format_constraints = await evaluator.evaluate_format_constraints(
        evaluatable_format_constraint_keys, entered_input
    )
    return evaluated_format_constraints
