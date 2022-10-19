"""
functions related to content evaluation
"""
import asyncio
from typing import Any, Awaitable, Callable, List

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import ContentEvaluationResultBasedRcEvaluator, RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
from ahbicht.expressions.ahb_expression_evaluation import evaluate_ahb_expression_tree
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys_from_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions


async def is_valid_expression(
    ahb_expression: str, content_eval_result_setter: Callable[[ContentEvaluationResult], Any]
) -> bool:
    """
    returns true iff the given expression is both well-formed and valid.
    Valid means that any evaluation leads to meaningful results.
    ⚠ This only works if you injected the ContentEvaluationResultBased... FC/RC/Hints/Package logic providers.
    :param content_eval_result_setter: a method that sets content evaluation result
    :param ahb_expression: "Muss [1] U [2]" (returns True)  "Muss ([61]u [584]) o[583]" (returns False)
    :return: True iff the expression is valid
    """
    try:
        tree = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        categorized_key_extract = extract_categorized_keys_from_tree(tree, sanitize=True)
    except SyntaxError:
        return False
    evaluation_tasks: List[Awaitable] = []
    for content_evaluation_result in categorized_key_extract.generate_possible_content_evaluation_results():

        async def evaluate_with_cer(cer: ContentEvaluationResult):
            content_eval_result_setter(cer)
            try:
                await evaluate_ahb_expression_tree(tree)
            except NotImplementedError as not_implemented_error:
                if "due to missing information" in str(not_implemented_error):
                    pass #  this happens for unknown mostly; it's ok
                else:
                    raise not_implemented_error  # this is, in general, an indicator for an invalid expression

        evaluation_tasks.append(evaluate_with_cer(content_evaluation_result))
    try:
        await asyncio.gather(*evaluation_tasks)
    except NotImplementedError:
        return False #  if any evaluation throws a (previously uncatched) NotImplementedError the expression is invalid
    return True
