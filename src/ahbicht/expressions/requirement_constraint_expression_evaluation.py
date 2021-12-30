"""
This module evaluates the parsed condition expression tree regarding the requirement constraints using ConditionNodes.
The RequirementConstraintTransformer defines the rules how the different parts and nodes
of the condition expression tree are handled.

The used terms are defined in the README_conditions.md.
"""

from typing import List, Literal, Mapping, Type, Union

from lark import Token, Tree, v_args
from lark.exceptions import VisitError

from ahbicht.condition_node_builder import ConditionNodeBuilder, TRCTransformerArgument
from ahbicht.evaluation_results import RequirementConstraintEvaluationResult
from ahbicht.expressions.base_transformer import BaseTransformer
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    ConditionNode,
    EvaluatedComposition,
    FormatConstraint,
    Hint,
    RequirementConstraint,
    UnevaluatedFormatConstraint,
)
from ahbicht.expressions.expression_builder import FormatConstraintExpressionBuilder, HintExpressionBuilder


# pylint: disable=no-self-use
@v_args(inline=True)  # Children are provided as *args instead of a list argument
# pylint:disable=inherit-non-class
class RequirementConstraintTransformer(BaseTransformer[TRCTransformerArgument, EvaluatedComposition]):
    """
    Transformer that evaluates the trees built from the condition expressions regarding the requirement constraints.
    The input are the conditions as defined in the AHBs in the form of ConditionNodes.
    In the case of a Bedingung/RequirementConstraint already evaluated for the single condition.
    Hints are evaluated as neutral element in the boolean logic: and_composition: True, or_composition: False.

    After two nodes are evaluated in a composition, the resulting node has the node type EvalutatedComposition.
    The return value is a ConditionNode whose attribute `conditions_fulfilled` describes whether it is a required field,
    its hints are the gathered hints and its `format_constraint_expression` contains the gathered format constraints
    for the field in a newly build expression.
    """

    def and_composition(self, left: TRCTransformerArgument, right: TRCTransformerArgument) -> EvaluatedComposition:
        """Evaluates logical and_composition"""

        # if one of the nodes is neutral the condition_fulfilled.value of the other one is the resulting one
        evaluated_composition = EvaluatedComposition(
            conditions_fulfilled=left.conditions_fulfilled & right.conditions_fulfilled
        )

        # Hints are added if the branch is true or neutral
        if evaluated_composition.conditions_fulfilled != ConditionFulfilledValue.UNFULFILLED:
            evaluated_composition.hint = (
                HintExpressionBuilder(getattr(left, "hint", None)).land(getattr(right, "hint", None)).get_expression()
            )
        evaluated_composition.format_constraints_expression = (
            FormatConstraintExpressionBuilder(left).land(right).get_expression()
        )

        return evaluated_composition

    def _or_xor_composition(
        self, left: ConditionNode, right: ConditionNode, composition: Literal["or_composition", "xor_composition"]
    ):
        """
        Determine the condition_fulfilled attribute for or_/xor_compostions.
        """
        # combining a hint with a format constraint in an or_/xor_composition has no useful result
        if (isinstance(left, Hint) and isinstance(right, UnevaluatedFormatConstraint)) or (
            isinstance(right, Hint) and isinstance(left, UnevaluatedFormatConstraint)
        ):
            raise NotImplementedError(
                f"Combining a {left.__class__} and a {right.__class__} in an"
                f"{composition} is not implemented as it has no useful result."
            )

        # combining a neutral element with a boolean value in an or_/xor_composition has no useful result
        if (
            left.conditions_fulfilled == ConditionFulfilledValue.NEUTRAL
            and right.conditions_fulfilled != ConditionFulfilledValue.NEUTRAL
            or (
                right.conditions_fulfilled == ConditionFulfilledValue.NEUTRAL
                and left.conditions_fulfilled != ConditionFulfilledValue.NEUTRAL
            )
        ):
            raise NotImplementedError(
                "Combining a neutral element with a boolean value in an"
                f"{composition} is not implemented as it has no useful result."
            )
        if composition == "or_composition":
            resulting_conditions_fulfilled = left.conditions_fulfilled | right.conditions_fulfilled
        elif composition == "xor_composition":
            resulting_conditions_fulfilled = left.conditions_fulfilled ^ right.conditions_fulfilled
        evaluated_composition = EvaluatedComposition(conditions_fulfilled=resulting_conditions_fulfilled)
        return evaluated_composition

    def or_composition(self, left: ConditionNode, right: ConditionNode) -> EvaluatedComposition:
        """Evaluates logical (inclusive) or_composition"""

        evaluated_composition = self._or_xor_composition(left, right, "or_composition")

        evaluated_composition.format_constraints_expression = (
            # todo: ask annika why the case of "invalid arguments" never happens here...
            FormatConstraintExpressionBuilder(left)  # type:ignore[arg-type]
            .lor(right)  # type:ignore[arg-type]
            .get_expression()
        )
        evaluated_composition.hint = (
            HintExpressionBuilder(getattr(left, "hint", None)).lor(getattr(right, "hint", None)).get_expression()
        )

        return evaluated_composition

    def xor_composition(self, left: ConditionNode, right: ConditionNode) -> EvaluatedComposition:
        """Evaluates exclusive xor_composition"""

        evaluated_composition = self._or_xor_composition(left, right, "xor_composition")

        evaluated_composition.format_constraints_expression = (
            # todo: ask annika why the case of "invalid arguments" never happens here...
            FormatConstraintExpressionBuilder(left)  # type:ignore[arg-type]
            .xor(right)  # type:ignore[arg-type]
            .get_expression()
        )
        evaluated_composition.hint = (
            HintExpressionBuilder(getattr(left, "hint", None)).xor(getattr(right, "hint", None)).get_expression()
        )

        return evaluated_composition

    def _then_also(
        self,
        format_constraint: UnevaluatedFormatConstraint,
        other_condition: Type[ConditionNode],
    ) -> EvaluatedComposition:
        """
        Evaluates a boolean condition with a format constraint. The functions name indicates its behaviour:
        If the `condition_fulfilled` attribute is true, the format constraint has to be fulfilled, too.
        But it is not directly evaluated but only attached to the evaluated composition such that we keep
        a strict separation of the Mussfeldprüfung itself and evaluation of format constraints on fields
        that have been marked obligatory by the (previously run) Mussfeldprüfung but do not affect
        the result of the Mussfeldprüfung.
        (Things that are obligatory, are obligatory regardless of the format constraints.)

        :param format_constraint: a format constraint
        :param other_condition: a requirement constraint or hint
        :return:
        """
        if other_condition.conditions_fulfilled != ConditionFulfilledValue.NEUTRAL:
            evaluated_composition = EvaluatedComposition(conditions_fulfilled=other_condition.conditions_fulfilled)
            format_constraint_is_required = other_condition.conditions_fulfilled == ConditionFulfilledValue.FULFILLED
        elif isinstance(other_condition, Hint):
            evaluated_composition = EvaluatedComposition(
                conditions_fulfilled=ConditionFulfilledValue.NEUTRAL, hint=other_condition.hint
            )
            format_constraint_is_required = True
        else:
            raise NotImplementedError(
                f"Combining Conditions of type {other_condition.__class__} with a "
                f"{format_constraint.__class__} is not implemented."
            )
        if format_constraint_is_required:
            evaluated_composition.format_constraints_expression = (
                FormatConstraintExpressionBuilder(format_constraint).land(other_condition).get_expression()
            )

        return evaluated_composition

    def then_also_composition(self, left: Type[ConditionNode], right: Type[ConditionNode]) -> EvaluatedComposition:
        """
        A "then also" composition is typically used for format constraints.
        It connects an evaluable expression with a format constraint.
        If the `conditions_fulfilled` attribute evaluates to true,
        then also the attached format constraint has to be fulfilled.
        """
        # pylint: disable=protected-access
        if isinstance(left, UnevaluatedFormatConstraint):
            return self._then_also(format_constraint=left, other_condition=right)
        return self._then_also(
            format_constraint=right,  # type:ignore[arg-type]
            # #because typically format constraints are "attached" to the right side of an expression
            other_condition=left,
        )  # this might raise the NotImplementedError


def evaluate_requirement_constraint_tree(
    parsed_tree: Tree, input_values: Mapping[str, TRCTransformerArgument]
) -> EvaluatedComposition:
    """
    Evaluates the tree built from the expressions with the help of the ConditionsTransformer.

    :param parsed_tree: Tree
    :param input_values: dict(condition_key, ConditionNode)
        :return: EvaluatedComposition
    """
    if not all(isinstance(input_value, ConditionNode) for input_value in input_values.values()):
        raise ValueError("Please make sure that the passed values are ConditionNodes.")
    if not all(
        isinstance(input_value, (RequirementConstraint, Hint, FormatConstraint))
        for input_value in input_values.values()
    ):
        raise ValueError(
            """Please make sure that the passed values are ConditionNodes \
of the type RequirementConstraint, Hint or FormatConstraint."""
        )
    try:
        result = RequirementConstraintTransformer(input_values).transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc

    return result


async def requirement_constraint_evaluation(
    condition_expression: Union[str, Tree]
) -> RequirementConstraintEvaluationResult:
    """
    Evaluation of the condition expression in regard to the requirement conditions (rc).
    The condition expression can either be a string that still needs to be parsed as condition expression or a tree
    that has already been parsed.
    """
    if isinstance(condition_expression, str):
        parsed_tree_rc: Tree = parse_condition_expression_to_tree(condition_expression)
    else:
        parsed_tree_rc = condition_expression

    # get all condition keys from tree
    all_condition_keys: List[str] = [
        t.value for t in parsed_tree_rc.scan_values(lambda v: isinstance(v, Token))  # type: ignore[attr-defined]
    ]
    condition_node_builder = ConditionNodeBuilder(all_condition_keys)
    input_nodes = await condition_node_builder.requirement_content_evaluation_for_all_condition_keys()

    resulting_condition_node: EvaluatedComposition = evaluate_requirement_constraint_tree(parsed_tree_rc, input_nodes)

    requirement_constraints_fulfilled: bool = (
        resulting_condition_node.conditions_fulfilled == ConditionFulfilledValue.FULFILLED
    )
    requirement_is_conditional = True
    if resulting_condition_node.conditions_fulfilled == ConditionFulfilledValue.NEUTRAL:  # pylint:disable=no-member
        requirement_constraints_fulfilled = True
        requirement_is_conditional = False
    if resulting_condition_node.conditions_fulfilled == ConditionFulfilledValue.UNKNOWN:  # pylint:disable=no-member
        raise NotImplementedError("It is unknown if the conditions are fulfilled due to missing information.")

    format_constraints_expression = getattr(resulting_condition_node, "format_constraints_expression", None)
    if isinstance(resulting_condition_node, UnevaluatedFormatConstraint):
        format_constraints_expression = f"[{resulting_condition_node.condition_key}]"
    hints = getattr(resulting_condition_node, "hint", None)

    requirement_constraint_evaluation_result = RequirementConstraintEvaluationResult(
        requirement_constraints_fulfilled=requirement_constraints_fulfilled,
        hints=hints,
        format_constraints_expression=format_constraints_expression,
        requirement_is_conditional=requirement_is_conditional,
    )

    return requirement_constraint_evaluation_result
