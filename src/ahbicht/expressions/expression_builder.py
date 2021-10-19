"""
Module to create expressions from scratch.
"""
import re
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, Union

from ahbicht.expressions.condition_nodes import (
    EvaluatedComposition,
    EvaluatedFormatConstraint,
    Hint,
    UnevaluatedFormatConstraint,
)

TSupportedNodes = TypeVar("TSupportedNodes")


class ExpressionBuilder(Generic[TSupportedNodes], ABC):
    """
    Class that helps to create expression strings. It separates the logical operation (connect two conditions with a
    logical operator) from the implementation which might differ depending on the condition type and other
    circumstances.
    """

    @abstractmethod
    def get_expression(self) -> Optional[str]:
        """
        Returns the expression string or none if there is no expression.
        :return:
        """
        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def land(self, other: TSupportedNodes):
        """
        connects the expression with a logical and (LAND)
        :param other: condition or expression to be connected to the expression
        :return:
        """
        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def lor(self, other: TSupportedNodes):
        """
        connects the expression with a logical or (LOR)
        :param other: condition or expression to be connected to the expression
        :return:
        """
        raise NotImplementedError("Has to be implemented by inheriting class.")

    @abstractmethod
    def xor(self, other: TSupportedNodes):
        """
        connects the expression with an exclusive or (XOR)
        :param other: condition or expression to be connected to the expression
        :return:
        """
        raise NotImplementedError("Has to be implemented by inheriting class.")


TFCExpressionBuilderArgument = Union[
    EvaluatedComposition, UnevaluatedFormatConstraint, Optional[str]
]  # node types that are supported by the FormatConstraintExpressionBuilder


class FormatConstraintExpressionBuilder(ExpressionBuilder[TFCExpressionBuilderArgument]):
    """
    Class to create expressions that consists of FormatConstraints
    """

    _one_key_surrounded_by_brackets_pattern = re.compile(r"\((?P<body>\[\d+\])\)")  # https://regex101.com/r/IauOei/1

    # (?P<group_name>...) is a named group: https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups

    def __init__(self, init_condition_or_expression: TFCExpressionBuilderArgument):
        """
        Start with a plain expression
        :param init_condition_or_expression: initial format constraint or existing expression
        """
        self._expression: Optional[str] = None
        if isinstance(init_condition_or_expression, UnevaluatedFormatConstraint):
            # the condition key of the token in expression '[42]' is only '42'
            # so the get a valid expression, we add the square brackets
            self._expression = f"[{init_condition_or_expression.condition_key}]"
        elif (
            isinstance(init_condition_or_expression, EvaluatedComposition)
            and init_condition_or_expression.format_constraints_expression
        ):
            self._expression = init_condition_or_expression.format_constraints_expression
        elif isinstance(init_condition_or_expression, str):
            self._expression = f"{init_condition_or_expression}"

    def get_expression(self) -> Optional[str]:
        # could add simplifications here
        return self._expression

    def land(self, other: TFCExpressionBuilderArgument) -> ExpressionBuilder:
        return self._connect("U", other)

    def lor(self, other: TFCExpressionBuilderArgument) -> ExpressionBuilder:
        return self._connect("O", other)

    def xor(self, other: TFCExpressionBuilderArgument) -> ExpressionBuilder:
        return self._connect("X", other)

    def _connect(self, operator_character: str, other: TFCExpressionBuilderArgument):
        """
        Connect the existing expression and the other part.
        :param operator_character: "X", "U" or "O"
        :param other:
        :return:
        """
        if self._expression:
            prefix = f"({self._expression}) {operator_character}"
        else:
            prefix = ""
        if isinstance(other, UnevaluatedFormatConstraint):
            self._expression = f"{prefix} [{other.condition_key}]"
        elif isinstance(other, EvaluatedComposition) and other.format_constraints_expression:
            self._expression = f"{prefix} ({other.format_constraints_expression})"
        elif isinstance(other, str):
            self._expression = f"{prefix} ({other})"
        if self._expression:
            self._expression = self._expression.strip()
            self._expression = self._one_key_surrounded_by_brackets_pattern.sub(r"\g<body>", self._expression)
        return self


THExpressionBuilderArgument = Union[Hint, Optional[str]]  # node types supported by the HintExpressionBuilder


class HintExpressionBuilder(ExpressionBuilder[THExpressionBuilderArgument]):
    """
    Allows to connect hints with logical operations.
    """

    @staticmethod
    def get_hint_text(hinty_object: THExpressionBuilderArgument) -> Optional[str]:
        """
        get the hint from a Hint instance or plain string
        :param hinty_object:
        :return: hint if there is any, None otherwise
        """
        if hinty_object is None:
            return None
        if isinstance(hinty_object, str):
            return hinty_object
        return getattr(hinty_object, "hint", None)

    def __init__(self, init_condition: THExpressionBuilderArgument):
        """
        Initialize by providing either a Hint Node or a hint string
        """
        self._expression = HintExpressionBuilder.get_hint_text(init_condition)

    def get_expression(self) -> Optional[str]:
        return self._expression

    def land(self, other: THExpressionBuilderArgument) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression += f" und {HintExpressionBuilder.get_hint_text(other)}"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self

    def lor(self, other: THExpressionBuilderArgument) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression += f" oder {HintExpressionBuilder.get_hint_text(other)}"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self

    def xor(self, other: THExpressionBuilderArgument) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression = f"Entweder ({self._expression}) oder ({HintExpressionBuilder.get_hint_text(other)})"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self


TFEMExpressionBuilderArgument = (
    EvaluatedFormatConstraint  # node types supported by the FormatErrorMessageExpressionBuilder
)


class FormatErrorMessageExpressionBuilder(ExpressionBuilder[TFEMExpressionBuilderArgument]):
    """
    Class to build the error messages for the format constraint evaluation.
    """

    def __init__(self, init_condition: TFEMExpressionBuilderArgument):
        self._expression = init_condition.error_message
        self.format_constraint_fulfilled = init_condition.format_constraint_fulfilled

    def get_expression(self) -> Optional[str]:
        return self._expression

    def land(self, other: TFEMExpressionBuilderArgument) -> ExpressionBuilder:
        if other.format_constraint_fulfilled is True:
            self._expression = self._expression
        else:
            if self._expression is None:
                self._expression = other.error_message
            else:
                self._expression = f"'{self._expression}' und '{other.error_message}'"
        return self

    def lor(self, other: TFEMExpressionBuilderArgument) -> ExpressionBuilder:
        if self.format_constraint_fulfilled is False and other.format_constraint_fulfilled is False:
            self._expression = f"'{self._expression}' oder '{other.error_message}'"
        else:
            self._expression = None
        return self

    def xor(self, other: TFEMExpressionBuilderArgument) -> ExpressionBuilder:
        if self.format_constraint_fulfilled is False and other.format_constraint_fulfilled is False:
            self._expression = f"Entweder '{self._expression}' oder '{other.error_message}'"
        elif self.format_constraint_fulfilled is True and other.format_constraint_fulfilled is True:
            self._expression = "Zwei exklusive Formatdefinitionen dürfen nicht gleichzeitig erfüllt sein"
            # pylint: disable=fixme
            # TODO: Do we need to know which one? It's probably more work than benefit.
        else:
            self._expression = None
        return self
