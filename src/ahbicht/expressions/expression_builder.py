"""
Module to create expressions from scratch.
"""
import re
from abc import ABC, abstractmethod
from typing import Generic, Optional, Protocol, Type, TypeVar, Union

from ahbicht.expressions.condition_nodes import (
    ConditionNode,
    EvaluatedComposition,
    EvaluatedFormatConstraint,
    Hint,
    RequirementConstraint,
    UnevaluatedFormatConstraint,
)
from ahbicht.expressions.enums import LogicalOperator

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


TEffectiveFCExpressionBuilderArguments = Union[
    EvaluatedComposition, UnevaluatedFormatConstraint, Optional[str]
]  # node types that have an effect on the built format constraint expression

TUneffectiveFCExpressionBuilderArguments = Union[
    RequirementConstraint, EvaluatedComposition, Hint, Type[ConditionNode]
]  # node types that are formally accepted as argument but don't
# have any effect. Instead of checking which nodes contain format constraints all are put into the
# FormatConstraintExpressionBuilder, but it only has an effect on those with format constraints.
# Note that EvaluatedComposition is in both classes since they can have format constraints but don't have to.

TSupportedFCExpressionBuilderArguments = Union[
    TEffectiveFCExpressionBuilderArguments, TUneffectiveFCExpressionBuilderArguments
]


class FormatConstraintExpressionBuilder(ExpressionBuilder[TSupportedFCExpressionBuilderArguments]):
    """
    Class to create expressions that consists of FormatConstraints
    """

    _one_key_surrounded_by_brackets_pattern = re.compile(r"\((?P<body>\[\d+\])\)")  # https://regex101.com/r/IauOei/1

    # (?P<group_name>...) is a named group: https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups

    def __init__(self, init_condition_or_expression: TSupportedFCExpressionBuilderArguments):
        """
        Start with a plain expression
        :param init_condition_or_expression: initial format constraint or existing expression
        """
        self._expression: Optional[str]
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
        elif isinstance(init_condition_or_expression, (RequirementConstraint, EvaluatedComposition, Hint)):
            # requirement constraints and hints don't have any effect on the a newly built
            # format constraint expression
            # also evaluated compositions that don't have a format constraint expression
            self._expression = None
        else:
            # we should never come here
            self._expression = None

    def get_expression(self) -> Optional[str]:
        # could add simplifications here
        return self._expression

    def land(self, other: TSupportedFCExpressionBuilderArguments) -> ExpressionBuilder:
        return self._connect(LogicalOperator.LAND, other)

    def lor(self, other: TSupportedFCExpressionBuilderArguments) -> ExpressionBuilder:
        return self._connect(LogicalOperator.LOR, other)

    def xor(self, other: TSupportedFCExpressionBuilderArguments) -> ExpressionBuilder:
        return self._connect(LogicalOperator.XOR, other)

    def _connect(self, operator_character: LogicalOperator, other: TSupportedFCExpressionBuilderArguments):
        """
        Connect the existing expression and the other part.

        :param operator_character: "X", "U" or "O"
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
        elif isinstance(other, (RequirementConstraint, EvaluatedComposition, Hint)):
            # other types than the above don't affect the newly built format constraint expression (no effect, explicit)
            pass
        else:
            # all other types also have no effect (no effect, implicit)
            pass  # we should never come here
        if self._expression:
            self._expression = self._expression.strip()
            self._expression = self._one_key_surrounded_by_brackets_pattern.sub(r"\g<body>", self._expression)
        return self


# pylint:disable=too-few-public-methods
class _ClassesWithHintAttribute(Protocol):
    """
    A class to be used in type hints. describes all classes that have a "hint" attribute
    """

    hint: str


TClassesWithHintAttribute = TypeVar("TClassesWithHintAttribute", bound=_ClassesWithHintAttribute)


class HintExpressionBuilder(ExpressionBuilder[TClassesWithHintAttribute]):
    """
    Allows to connect hints with logical operations.
    """

    @staticmethod
    def get_hint_text(hinty_object: Optional[_ClassesWithHintAttribute]) -> Optional[str]:
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

    def __init__(self, init_condition: Optional[_ClassesWithHintAttribute]):
        """
        Initialize by providing either a Hint Node or a hint string
        """
        self._expression = HintExpressionBuilder.get_hint_text(init_condition)

    def get_expression(self) -> Optional[str]:
        return self._expression

    def land(self, other: Optional[_ClassesWithHintAttribute]) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression += f" und {HintExpressionBuilder.get_hint_text(other)}"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self

    def lor(self, other: Optional[_ClassesWithHintAttribute]) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression += f" oder {HintExpressionBuilder.get_hint_text(other)}"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self

    def xor(self, other: Optional[_ClassesWithHintAttribute]) -> ExpressionBuilder:
        if other is not None:
            if self._expression:
                self._expression = f"Entweder ({self._expression}) oder ({HintExpressionBuilder.get_hint_text(other)})"
            else:
                self._expression = HintExpressionBuilder.get_hint_text(other)
        return self


# This class is only used by the FormatConstraintTransformer.
# That's why it only accepts EvaluatedFormatConstraints as input.
class FormatErrorMessageExpressionBuilder(ExpressionBuilder[EvaluatedFormatConstraint]):
    """
    Class to build the error messages for the format constraint evaluation.
    """

    def __init__(self, init_condition: EvaluatedFormatConstraint):
        self._expression = init_condition.error_message
        self.format_constraint_fulfilled = init_condition.format_constraint_fulfilled

    def get_expression(self) -> Optional[str]:
        return self._expression

    def land(self, other: EvaluatedFormatConstraint) -> ExpressionBuilder:
        if other.format_constraint_fulfilled is True:
            self._expression = self._expression
        else:
            if self._expression is None:
                self._expression = other.error_message
            else:
                self._expression = f"'{self._expression}' und '{other.error_message}'"
        return self

    def lor(self, other: EvaluatedFormatConstraint) -> ExpressionBuilder:
        if self.format_constraint_fulfilled is False and other.format_constraint_fulfilled is False:
            self._expression = f"'{self._expression}' oder '{other.error_message}'"
        else:
            self._expression = None
        return self

    def xor(self, other: EvaluatedFormatConstraint) -> ExpressionBuilder:
        if self.format_constraint_fulfilled is False and other.format_constraint_fulfilled is False:
            self._expression = f"Entweder '{self._expression}' oder '{other.error_message}'"
        elif self.format_constraint_fulfilled is True and other.format_constraint_fulfilled is True:
            self._expression = "Zwei exklusive Formatdefinitionen dürfen nicht gleichzeitig erfüllt sein"
            # TODO: Do we need to know which one? It's probably more work than benefit.
        else:
            self._expression = None
        return self
