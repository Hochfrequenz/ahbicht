"""
This module implements the base class for the condition check Transformers
that evaluate trees build from the condition_expression_parser.
"""

from abc import ABC, abstractmethod
from typing import Dict

from lark import Token, Transformer, v_args

from ahbicht.expressions.condition_nodes import ConditionNode


@v_args(inline=True)  # Children are provided as *args instead of a list argument
class BaseTransformer(Transformer, ABC):
    """
    Transformer that evaluates the trees built from the format constraint expressions.
    The input are the evaluated format constraint conditions in the form of ConditionNodes.

    After two nodes are evaluated in a composition, the resulting node has the node type EvalutatedComposition.
    The return value is a ConditionNode whose attribute `format_constraint_fulfilled` describes whether
    the format constraint expression is fulfiled or not.
    """

    def __init__(self, input_values: Dict[str, ConditionNode]):
        """
        The input are the evaluated format constraint conditions in the form of ConditionNodes.
        :param input_values: dict(condition_keys, ConditionNode)
        """
        super().__init__()
        self.input_values = input_values

    def condition_key(self, token: Token) -> str:
        """Returns ConditionNode of condition_key"""
        try:
            condition_key = self.input_values[token.value]
        except KeyError as key_err:
            raise ValueError(
                "Please make sure that the input values contain all necessary condition_keys."
            ) from key_err
        return condition_key

    @abstractmethod
    def and_composition(self, left: ConditionNode, right: ConditionNode) -> ConditionNode:
        """Evaluates logical and_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def or_composition(self, left: ConditionNode, right: ConditionNode) -> ConditionNode:
        """Evaluates logical (inclusive) or_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def xor_composition(self, left: ConditionNode, right: ConditionNode) -> ConditionNode:
        """Evaluates exclusive xor_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")
