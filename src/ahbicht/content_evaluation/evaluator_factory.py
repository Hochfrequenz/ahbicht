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
from typing import Callable, Optional, Tuple

import inject
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.fc_evaluators import DictBasedFcEvaluator, FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator, RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.hints_provider import DictBasedHintsProvider, HintsProvider
from ahbicht.expressions.package_expansion import DictBasedPackageResolver, PackageResolver


def create_hardcoded_evaluators(
    content_evaluation_result: ContentEvaluationResult,
    edifact_format: Optional[EdifactFormat] = None,
    edifact_format_version: Optional[EdifactFormatVersion] = None,
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
    if edifact_format is not None:
        rc_evaluator.edifact_format = edifact_format
        fc_evaluator.edifact_format = edifact_format
        hints_provider.edifact_format = edifact_format
        package_resolver.edifact_format = edifact_format
    if edifact_format_version is not None:
        rc_evaluator.edifact_format_version = edifact_format_version
        fc_evaluator.edifact_format_version = edifact_format_version
        hints_provider.edifact_format_version = edifact_format_version
        package_resolver.edifact_format_version = edifact_format_version
    return rc_evaluator, fc_evaluator, hints_provider, package_resolver


def create_and_inject_hardcoded_evaluators(
    content_evaluation_result: ContentEvaluationResult,
    evaluatable_data_provider: Optional[Callable[[], EvaluatableData]] = None,
    edifact_format: Optional[EdifactFormat] = None,
    edifact_format_version: Optional[EdifactFormatVersion] = None,
):
    """
    Creates evaluators from hardcoded content_evaluation result and injects them

    :param content_evaluation_result:
    :return:
    """
    evaluators = create_hardcoded_evaluators(
        content_evaluation_result, edifact_format=edifact_format, edifact_format_version=edifact_format_version
    )

    def configure(binder):
        binder.bind(TokenLogicProvider, SingletonTokenLogicProvider([*evaluators]))
        if evaluatable_data_provider is not None:
            binder.bind_to_provider(EvaluatableDataProvider, evaluatable_data_provider)

    inject.configure_once(configure)
