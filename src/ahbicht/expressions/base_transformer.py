"""
This module implements the base class for the condition check Transformers
that evaluate trees build from the condition_expression_parser.
"""

from abc import ABC, abstractmethod
from typing import Generic, Mapping, TypeVar

from lark import Token, Transformer, v_args

# All non-abstract transformers obey the following generic type constraints:
#   1. The methods of each transformer all have the same accepted argument type ("TSupportedArgumentNodeType").
#       This type is arbitrary but fixed per Transformer.
#   2. Also, all the methods of one transformer return objects of the same type ("TSupportedReturnType").
TSupportedArgumentNodeType = TypeVar("TSupportedArgumentNodeType")  # bound=ConditionNode)
# bound does not work because:
# error: Type argument "ahbicht.expressions.condition_nodes.EvaluatedFormatConstraint" of "BaseTransformer" must be a
# subtype of "ahbicht.expressions.condition_nodes.ConditionNode"  [type-var]
TSupportedReturnType = TypeVar("TSupportedReturnType")


@v_args(inline=True)  # Children are provided as *args instead of a list argument
class BaseTransformer(Transformer, ABC, Generic[TSupportedArgumentNodeType, TSupportedReturnType]):
    """
    Transformer that evaluates the trees built from the format constraint expressions.
    The input are the evaluated format constraint conditions in the form of ConditionNodes.

    After two nodes are evaluated in a composition, the resulting node has the node type EvalutatedComposition.
    The return value is a ConditionNode whose attribute `format_constraint_fulfilled` describes whether
    the format constraint expression is fulfiled or not.
    """

    def __init__(self, input_values: Mapping[str, TSupportedArgumentNodeType]):
        """
        The input are the evaluated format constraint conditions in the form of ConditionNodes.
        :param input_values: something that maps a condition key (str) onto an argument
        """
        super().__init__()
        self.input_values = input_values

    def condition(self, token: Token) -> TSupportedArgumentNodeType:
        """Returns ConditionNode of rule 'condition'"""
        try:
            condition_key = self.input_values[token.value]
        except KeyError as key_err:
            raise ValueError(
                "Please make sure that the input values contain all necessary condition_keys."
            ) from key_err
        return condition_key

    def package(self, token: Token) -> TSupportedArgumentNodeType:
        """Returns ConditionNode of rule package"""
        try:
            package_key = self.input_values[token.value]
        except KeyError as key_err:
            raise ValueError("Please make sure that the input values contain all necessary package_keys.") from key_err
        return package_key

    @abstractmethod
    def and_composition(
        self, left: TSupportedArgumentNodeType, right: TSupportedArgumentNodeType
    ) -> TSupportedReturnType:
        """Evaluates logical and_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def or_composition(
        self, left: TSupportedArgumentNodeType, right: TSupportedArgumentNodeType
    ) -> TSupportedReturnType:
        """Evaluates logical (inclusive) or_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def xor_composition(
        self, left: TSupportedArgumentNodeType, right: TSupportedArgumentNodeType
    ) -> TSupportedReturnType:
        """Evaluates exclusive xor_composition"""

        raise NotImplementedError("Has to be implemented by inheriting class.")
