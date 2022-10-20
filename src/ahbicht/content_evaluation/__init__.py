"""
functions related to content evaluation
"""
import asyncio
from typing import Any, Awaitable, Callable, List, Optional, Tuple

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import ContentEvaluationResultBasedRcEvaluator, RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
from ahbicht.expressions import InvalidExpressionError
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions


async def is_valid_expression(
    ahb_expression: str, content_evaluation_result_setter: Callable[[ContentEvaluationResult], Any]
) -> Tuple[bool, Optional[str]]:
    """
    Returns true iff the given expression is both well-formed and valid.
    An expression is valid if and only if all possible content evaluations lead to a meaningful results.
    ⚠ This only works if the provided content_evaluation_result_setter writes the EvaluatableData in such a way, that
    the injected Evaluators (FC/RC/Hints/Package) can work with it.
    This is easiest for the ContentEvaluationResultBased FC/RC/Hints/Package token logic providers.
    :param content_evaluation_result_setter: a threadsafe method that writes the given Content Evaluation Result into
    the evaluatable data
    :param ahb_expression: "Muss [1] U [2]" (returns True)  "Muss ([61]u [584]) o[583]" (returns False)
    :return: (True,None) iff the expression is valid; (False, error message) otherwise
    """
    try:
        tree = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        categorized_key_extract = extract_categorized_keys_from_tree(tree, sanitize=True)
    except SyntaxError as syntax_error:
        return False, str(syntax_error)
    evaluation_tasks: List[Awaitable] = []
    for content_evaluation_result in categorized_key_extract.generate_possible_content_evaluation_results():
        # create (but do not await) the evaluation tasks for all possible content evaluation results
        # the idea is, that if _any_ evaluation task raises an uncatched exception this can be interpreted as:
        # "the expression is invalid"
        async def evaluate_with_cer(cer: ContentEvaluationResult):
            content_evaluation_result_setter(cer)
            try:
                await evaluate_ahb_expression_tree(tree)
            except NotImplementedError as not_implemented_error:
                # we can ignore some specific errors
                if "due to missing information" in str(not_implemented_error):
                    pass  # this happens for UNKNOWN; it's okay because the expression might still be valid
                else:
                    raise not_implemented_error  # this is, in general, an indicator for an invalid expression
            except InvalidExpressionError as single_invalid_expression_error:
                single_invalid_expression_error.invalid_expression = ahb_expression
                raise

        evaluation_tasks.append(evaluate_with_cer(content_evaluation_result))
    try:
        # await the previously collected (yet unawaited) tasks
        await asyncio.gather(*evaluation_tasks)
    except InvalidExpressionError as invalid_expression_error:
        # if any evaluation throws a InvalidExpressionError the expression is invalid
        return False, invalid_expression_error.error_message
    return True, None
