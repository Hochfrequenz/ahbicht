"""
A module to generate ready to use evaluators.
"""
from typing import Tuple

import inject

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.fc_evaluators import DictBasedFcEvaluator, FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator, RcEvaluator
from ahbicht.expressions.hints_provider import DictBasesHintsProvider, HintsProvider


def create_evaluators(
    content_evaluation_result: ContentEvaluationResult,
) -> Tuple[RcEvaluator, FcEvaluator, HintsProvider]:
    """
    Creates evaluators based on the given content_evaluation_result
    :param content_evaluation_result:
    :return:
    """
    rc_evaluator = DictBasedRcEvaluator(content_evaluation_result.requirement_constraints)
    fc_evaluator = DictBasedFcEvaluator(content_evaluation_result.format_constraints)
    hints_provider = DictBasesHintsProvider(content_evaluation_result.hints)
    return rc_evaluator, fc_evaluator, hints_provider


def create_and_inject_hardcoded_evaluators(content_evaluation_result: ContentEvaluationResult):
    """
    Creates evaluators from hardcoded content_evaluation result and injects them
    :param content_evaluation_result:
    :return:
    """
    evaluators = create_evaluators(content_evaluation_result)
    inject.clear_and_configure(
        lambda binder: binder.bind(RcEvaluator, evaluators[0])
        .bind(FcEvaluator, evaluators[1])
        .bind(HintsProvider, evaluators[2])
    )
