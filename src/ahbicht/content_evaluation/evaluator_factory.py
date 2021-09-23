"""
A module to generate ready to use evaluators.
"""
from typing import Tuple

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.hints_provider import HintsProvider


def create_evaluators(
    content_evaluation_result: ContentEvaluationResult,
) -> Tuple[RcEvaluator, FcEvaluator, HintsProvider]:
    """
    create evaluators based on the given content_evaluation_result
    :param content_evaluation_result:
    :return:
    """
