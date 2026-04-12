"""
AhbContext bundles all collaborators needed for AHB expression evaluation.

Instead of relying on a global dependency injection container, consumers create an AhbContext
and pass it explicitly to parsing and evaluation functions. This makes the data flow visible
and eliminates global mutable state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from efoli import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.hints_provider import HintsProvider
from ahbicht.expressions.package_expansion import PackageResolver

if TYPE_CHECKING:
    from ahbicht.content_evaluation.token_logic_provider import TokenLogicProvider
    from ahbicht.models.content_evaluation_result import ContentEvaluationResult


@dataclass
class AhbContext:
    """
    Holds all the collaborators needed for AHB expression evaluation and package resolution.

    There are two typical ways to create an AhbContext:

    1. From a ContentEvaluationResult (pre-computed results, e.g. in a REST API):
       ``AhbContext.from_content_evaluation_result(cer, edifact_format, edifact_format_version)``

    2. With custom evaluator instances (on-demand evaluation, e.g. in a message validator):
       ``AhbContext(rc_evaluator=..., fc_evaluator=..., ...)``
    """

    rc_evaluator: RcEvaluator
    fc_evaluator: FcEvaluator
    hints_provider: HintsProvider
    package_resolver: PackageResolver
    evaluatable_data: EvaluatableData[Any]

    @staticmethod
    def from_content_evaluation_result(
        content_evaluation_result: ContentEvaluationResult,
        edifact_format: EdifactFormat,
        edifact_format_version: EdifactFormatVersion,
        evaluatable_data: Optional[EvaluatableData[Any]] = None,
    ) -> AhbContext:
        """
        Creates an AhbContext from a ContentEvaluationResult.

        This is the simplest way to use ahbicht when all evaluation results are already known.
        Internally, this creates dict-based evaluators that just look up results from the CER.

        :param content_evaluation_result: the pre-computed evaluation results
        :param edifact_format: the EDIFACT format (e.g. UTILMD)
        :param edifact_format_version: the EDIFACT format version (e.g. FV2210)
        :param evaluatable_data: optional EvaluatableData; if None, one is created from the CER
        """
        from ahbicht.content_evaluation.evaluator_factory import (  # pylint:disable=import-outside-toplevel
            create_hardcoded_evaluators,
        )

        rc_evaluator, fc_evaluator, hints_provider, package_resolver = create_hardcoded_evaluators(
            content_evaluation_result,
            edifact_format=edifact_format,
            edifact_format_version=edifact_format_version,
        )

        if evaluatable_data is None:
            evaluatable_data = EvaluatableData(
                body=content_evaluation_result.model_dump(mode="json"),
                edifact_format=edifact_format,
                edifact_format_version=edifact_format_version,
            )

        return AhbContext(
            rc_evaluator=rc_evaluator,
            fc_evaluator=fc_evaluator,
            hints_provider=hints_provider,
            package_resolver=package_resolver,
            evaluatable_data=evaluatable_data,
        )

    @staticmethod
    def from_token_logic_provider(
        token_logic_provider: TokenLogicProvider,
        evaluatable_data: EvaluatableData[Any],
    ) -> AhbContext:
        """
        Creates an AhbContext from a TokenLogicProvider and EvaluatableData.

        This is a bridge for existing code that already has a configured TokenLogicProvider.

        :param token_logic_provider: a configured TokenLogicProvider instance
        :param evaluatable_data: the data to evaluate against
        """
        return AhbContext(
            rc_evaluator=token_logic_provider.get_rc_evaluator(
                evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
            ),
            fc_evaluator=token_logic_provider.get_fc_evaluator(
                evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
            ),
            hints_provider=token_logic_provider.get_hints_provider(
                evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
            ),
            package_resolver=token_logic_provider.get_package_resolver(
                evaluatable_data.edifact_format, evaluatable_data.edifact_format_version
            ),
            evaluatable_data=evaluatable_data,
        )
