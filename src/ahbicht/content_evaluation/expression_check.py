"""
contains a high-level function that checks if a given expression is valid or not.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Union

from lark import Token, Tree
from lark.exceptions import UnexpectedCharacters, VisitError

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.expressions import InvalidExpressionError
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.models.content_evaluation_result import ContentEvaluationResult

if TYPE_CHECKING:
    from efoli import EdifactFormat, EdifactFormatVersion


async def is_valid_expression(  # pylint: disable=too-many-locals
    expression_or_tree: Union[str, Tree[Token]],
    content_evaluation_result_setter: Optional[Callable[[ContentEvaluationResult], Any]] = None,
    ahb_context: Optional[AhbContext] = None,
    edifact_format: Optional[EdifactFormat] = None,
    edifact_format_version: Optional[EdifactFormatVersion] = None,
) -> tuple[bool, Optional[str]]:
    """
    Returns true iff the given expression is both well-formed and valid.
    An expression is valid if and only if all possible content evaluations lead to a meaningful results.

    There are two ways to use this function:

    1. (New, recommended) Pass ``edifact_format`` and ``edifact_format_version``. A fresh ``AhbContext`` is built
       for each possible CER automatically. No inject setup needed.

    2. (Legacy, deprecated) Pass a ``content_evaluation_result_setter`` callback that writes the CER into the
       evaluatable data for the injected evaluators. Requires a configured inject container.

    :param expression_or_tree: "Muss [1] U [2]" (returns True)  "Muss ([61]u [584]) o[583]" (returns False)
    :param content_evaluation_result_setter: (deprecated) a threadsafe method that writes the given Content Evaluation
        Result into the evaluatable data
    :param ahb_context: optional AhbContext; if provided, its edifact_format/version are used to build per-CER contexts
    :param edifact_format: the EDIFACT format for building per-CER AhbContexts (used if ahb_context is None)
    :param edifact_format_version: the EDIFACT format version for building per-CER AhbContexts
    :return: (True,None) iff the expression is valid; (False, error message) otherwise
    """
    # Determine format/version for AhbContext construction
    _edifact_format = edifact_format
    _edifact_format_version = edifact_format_version
    if ahb_context is not None:
        _edifact_format = ahb_context.evaluatable_data.edifact_format
        _edifact_format_version = ahb_context.evaluatable_data.edifact_format_version

    tree: Tree[Token]
    parse_context_kwargs: dict = {}
    if ahb_context is not None:
        parse_context_kwargs["ahb_context"] = ahb_context
    if isinstance(expression_or_tree, str):
        try:
            tree = await parse_expression_including_unresolved_subexpressions(
                expression_or_tree, **parse_context_kwargs
            )
        except SyntaxError as syntax_error:
            return False, str(syntax_error)
        except VisitError as visit_error:
            return False, str(visit_error)
        except UnexpectedCharacters as unexpected_characters_error:
            return False, str(unexpected_characters_error)
    elif isinstance(expression_or_tree, Tree):
        tree = expression_or_tree
    else:
        raise ValueError(f"{expression_or_tree} is neither a string nor a Tree")
    categorized_key_extract = extract_categorized_keys_from_tree(tree, sanitize=True)
    evaluation_tasks: list[Awaitable] = []
    for content_evaluation_result in categorized_key_extract.generate_possible_content_evaluation_results():

        async def evaluate_with_cer(cer: ContentEvaluationResult):
            eval_kwargs: dict = {}
            if _edifact_format is not None and _edifact_format_version is not None:
                # New path: build a fresh AhbContext per CER
                cer_context = AhbContext.from_content_evaluation_result(cer, _edifact_format, _edifact_format_version)
                eval_kwargs["ahb_context"] = cer_context
            elif content_evaluation_result_setter is not None:
                # Legacy path: use the setter callback + inject
                content_evaluation_result_setter(cer)
            else:
                raise ValueError(
                    "is_valid_expression requires either (edifact_format + edifact_format_version) "
                    "or a content_evaluation_result_setter callback."
                )
            try:
                await evaluate_ahb_expression_tree(tree, **eval_kwargs)
            except NotImplementedError as not_implemented_error:
                # we can ignore some specific errors
                if "due to missing information" in str(not_implemented_error):
                    pass  # this happens for UNKNOWN; it's okay because the expression might still be valid
                else:
                    raise not_implemented_error  # this is, in general, an indicator for an invalid expression
            except InvalidExpressionError as single_invalid_expression_error:
                if isinstance(expression_or_tree, str):
                    single_invalid_expression_error.invalid_expression = expression_or_tree
                raise

        evaluation_tasks.append(evaluate_with_cer(content_evaluation_result))
    try:
        # await the previously collected (yet unawaited) tasks
        await asyncio.gather(*evaluation_tasks)
    except InvalidExpressionError as invalid_expression_error:
        # if any evaluation throws a InvalidExpressionError the expression is invalid
        return False, invalid_expression_error.error_message
    return True, None


__all__ = ["is_valid_expression"]
