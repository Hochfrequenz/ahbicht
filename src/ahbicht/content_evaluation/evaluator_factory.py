"""
A module to generate ready to use evaluators.

AHBicht, in the first place, is designed to do the content evaluation itself with actual code that checks if conditions
are fulfilled, format constraints are met and gets hints from somewhere. However, AHBicht can also be used to do a
"fake" content evaluation where the single truth values of conditions are already known.
Then the approach with implementing single methods whose outcomes are already known/hardcoded at compile time
seems like a big overhead. The code representation of "all outcomes are already known" is an instance of the
ContentEvaluationResult. Now the methods below are useful. Simply provide a content evaluation result (the data) and
the evaluators are created based on the already known outcomes. You do not have to actually touch any evaluator code.
"""
from typing import Tuple

import inject

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.fc_evaluators import DictBasedFcEvaluator, FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator, RcEvaluator
from ahbicht.expressions.hints_provider import DictBasedHintsProvider, HintsProvider
from ahbicht.expressions.package_expansion import DictBasedPackageResolver, PackageResolver


def create_hardcoded_evaluators(
    content_evaluation_result: ContentEvaluationResult,
) -> Tuple[RcEvaluator, FcEvaluator, HintsProvider, PackageResolver]:
    """
    Creates evaluators based on the given content_evaluation_result

    :param content_evaluation_result:
    :return:
    """
    rc_evaluator = DictBasedRcEvaluator(content_evaluation_result.requirement_constraints)
    fc_evaluator = DictBasedFcEvaluator(content_evaluation_result.format_constraints)
    hints_provider = DictBasedHintsProvider(content_evaluation_result.hints)
    package_resolver = DictBasedPackageResolver(content_evaluation_result.packages or {})
    return rc_evaluator, fc_evaluator, hints_provider, package_resolver


def create_and_inject_hardcoded_evaluators(content_evaluation_result: ContentEvaluationResult):
    """
    Creates evaluators from hardcoded content_evaluation result and injects them

    :param content_evaluation_result:
    :return:
    """
    evaluators = create_hardcoded_evaluators(content_evaluation_result)
    inject.clear_and_configure(
        lambda binder: binder.bind(RcEvaluator, evaluators[0])  # type:ignore[arg-type]
        .bind(FcEvaluator, evaluators[1])
        .bind(HintsProvider, evaluators[2])
        .bind(PackageResolver, evaluators[3])
    )
