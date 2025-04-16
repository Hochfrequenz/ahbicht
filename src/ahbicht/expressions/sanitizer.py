"""contains a function to sanitize user input/expressions from the AHBs"""

from typing import Literal, Optional, overload

_replacements: dict[str, str] = {
    "\u00a0": " ",  # no-break space,
    "V": "∨",  # Vogel-V != logical OR
    "v": "∨",
}


@overload
def sanitize_expression(expression: Literal[None]) -> Literal[None]: ...
@overload
def sanitize_expression(expression: str) -> str: ...


def sanitize_expression(expression: Optional[str]) -> Optional[str]:
    """
    fixes some common issues with expressions from the AHBs
    """
    if expression is None:
        return None
    for key, value in _replacements.items():
        expression = expression.replace(key, value)
    return expression.strip()


__all__ = ["sanitize_expression"]
