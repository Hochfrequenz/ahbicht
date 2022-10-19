"""
instantiates a "global" logger for all parsing related stuff
"""
import logging
from typing import Optional

parsing_logger = logging.getLogger("ahbicht.expressions")
parsing_logger.setLevel(logging.DEBUG)


class InvalidExpressionError(BaseException):
    """
    Is raised when an expression is well-formed but invalid.
    A syntactical error leads to a SyntaxError during parsing with lark whereas this exception occurs during evaluation.
    """

    def __init__(self, error_message: str, invalid_expression: Optional[str] = None):
        """
        initialize the exception
        :param invalid_expression: the expression which is invalid (if known)
        :param error_message: an explanation why it is invalid
        """
        # often we don't know the invalid expression itself because we only work with the tree that after the parsing
        self.invalid_expression = invalid_expression
        self.error_message = error_message

    def __str__(self):
        if self.invalid_expression is None:
            return f"{self.__class__}: Invalid expression because: {self.error_message}"
        return f"{self.__class__}: The expression '{self.invalid_expression}' in invalid because: {self.error_message}"
