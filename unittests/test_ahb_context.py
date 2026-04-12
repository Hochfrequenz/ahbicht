"""
Tests for the AhbContext dataclass and its factory methods.
"""

import pytest
from efoli import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import DictBasedRcEvaluator, RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider
from ahbicht.expressions.hints_provider import HintsProvider
from ahbicht.expressions.package_expansion import PackageResolver
from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_fc_evaluator,
    empty_default_hints_provider,
    empty_default_package_resolver,
    empty_default_rc_evaluator,
    empty_default_test_data,
)


class TestAhbContextDirectConstruction:
    """Tests for creating AhbContext with explicit evaluator instances."""

    def test_creates_context_with_all_fields(self) -> None:
        ctx = AhbContext(
            rc_evaluator=empty_default_rc_evaluator,
            fc_evaluator=empty_default_fc_evaluator,
            hints_provider=empty_default_hints_provider,
            package_resolver=empty_default_package_resolver,
            evaluatable_data=empty_default_test_data,
        )
        assert isinstance(ctx.rc_evaluator, RcEvaluator)
        assert isinstance(ctx.fc_evaluator, FcEvaluator)
        assert isinstance(ctx.hints_provider, HintsProvider)
        assert isinstance(ctx.package_resolver, PackageResolver)
        assert ctx.evaluatable_data is empty_default_test_data


class TestAhbContextFromContentEvaluationResult:
    """Tests for the from_content_evaluation_result factory method."""

    def test_creates_context_from_cer(self) -> None:
        cer = ContentEvaluationResult(
            requirement_constraints={"2": ConditionFulfilledValue.FULFILLED},
            format_constraints={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=True)},
            hints={"555": "some hint"},
        )
        ctx = AhbContext.from_content_evaluation_result(
            cer,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        assert isinstance(ctx.rc_evaluator, RcEvaluator)
        assert isinstance(ctx.fc_evaluator, FcEvaluator)
        assert isinstance(ctx.hints_provider, HintsProvider)
        assert isinstance(ctx.package_resolver, PackageResolver)
        assert ctx.evaluatable_data.edifact_format == default_test_format
        assert ctx.evaluatable_data.edifact_format_version == default_test_version

    def test_uses_provided_evaluatable_data_if_given(self) -> None:
        cer = ContentEvaluationResult(
            requirement_constraints={},
            format_constraints={},
            hints={},
        )
        custom_data = EvaluatableData(
            body={"custom": True},
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2210,
        )
        ctx = AhbContext.from_content_evaluation_result(
            cer,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
            evaluatable_data=custom_data,
        )
        assert ctx.evaluatable_data is custom_data

    @pytest.mark.asyncio
    async def test_rc_evaluator_returns_correct_values(self) -> None:
        cer = ContentEvaluationResult(
            requirement_constraints={
                "2": ConditionFulfilledValue.FULFILLED,
                "3": ConditionFulfilledValue.UNFULFILLED,
            },
            format_constraints={},
            hints={},
        )
        ctx = AhbContext.from_content_evaluation_result(
            cer,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        result = await ctx.rc_evaluator.evaluate_single_condition("2", ctx.evaluatable_data)
        assert result == ConditionFulfilledValue.FULFILLED

        result = await ctx.rc_evaluator.evaluate_single_condition("3", ctx.evaluatable_data)
        assert result == ConditionFulfilledValue.UNFULFILLED


class TestAhbContextFromTokenLogicProvider:
    """Tests for the from_token_logic_provider bridge factory."""

    def test_creates_context_from_tlp(self) -> None:
        tlp = SingletonTokenLogicProvider(
            [
                empty_default_rc_evaluator,
                empty_default_fc_evaluator,
                empty_default_hints_provider,
                empty_default_package_resolver,
            ]
        )
        ctx = AhbContext.from_token_logic_provider(tlp, empty_default_test_data)
        assert ctx.rc_evaluator is empty_default_rc_evaluator
        assert ctx.fc_evaluator is empty_default_fc_evaluator
        assert ctx.hints_provider is empty_default_hints_provider
        assert ctx.package_resolver is empty_default_package_resolver
        assert ctx.evaluatable_data is empty_default_test_data
