from contextvars import ContextVar
from typing import Optional

import inject
import pytest  # type:ignore[import]

from ahbicht.content_evaluation import is_valid_expression
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.fc_evaluators import ContentEvaluationResultBasedFcEvaluator
from ahbicht.content_evaluation.rc_evaluators import ContentEvaluationResultBasedRcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.hints_provider import ContentEvaluationResultBasedHintsProvider
from ahbicht.expressions.package_expansion import ContentEvaluationResultBasedPackageResolver
from unittests.defaults import (
    default_test_format,
    default_test_version,
    store_content_evaluation_result_in_evaluatable_data,
)

_content_evaluation_result: ContextVar[Optional[ContentEvaluationResult]] = ContextVar(
    "_content_evaluation_result", default=None
)


def _get_evaluatable_data():
    """
    returns the _content_evaluation_result context var value wrapped in a EvaluatableData container.
    This is the kind of data that the ContentEvaluationResultBased RC/FC Evaluators, HintsProvider and Package Resolver
    require.
    :return:
    """
    cer = _content_evaluation_result.get()
    return EvaluatableData(
        edifact_seed=ContentEvaluationResultSchema().dump(cer),
        edifact_format=default_test_format,
        edifact_format_version=default_test_version,
    )


class TestValidityCheck:
    """
    a test class for the expression validation feature
    """

    @pytest.fixture
    def inject_cer_evaluators(self):
        fc_evaluator = ContentEvaluationResultBasedFcEvaluator()
        fc_evaluator.edifact_format = default_test_format
        fc_evaluator.edifact_format_version = default_test_version

        rc_evaluator = ContentEvaluationResultBasedRcEvaluator()
        rc_evaluator.edifact_format = default_test_format
        rc_evaluator.edifact_format_version = default_test_version

        package_resolver = ContentEvaluationResultBasedPackageResolver()
        package_resolver.edifact_format = default_test_format
        package_resolver.edifact_format_version = default_test_version

        hints_provider = ContentEvaluationResultBasedHintsProvider()
        hints_provider.edifact_format = default_test_format
        hints_provider.edifact_format_version = default_test_version

        def configure(binder):
            binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([fc_evaluator, rc_evaluator, package_resolver, hints_provider]),
            )
            binder.bind_to_provider(EvaluatableDataProvider, _get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

    @pytest.mark.parametrize(
        "ahb_expression,expected_result",
        [
            pytest.param("Foo", False),
            pytest.param("Muss [1] U [2]", True),
            pytest.param("Muss [61] O [584]", False),  # connecting a hint with LOR is not valid
            pytest.param("Muss [123] O [584]", False),
            pytest.param("Muss [501] X [999]", False),  # connecting a hint XOR fc is not valid
            pytest.param("Muss [501] O [999]", False),  # connecting a hint LOR fc is not valid
            pytest.param("Muss [983][1] X [984][2]", True),
        ],
    )
    async def test_is_valid_expression(self, ahb_expression: str, expected_result: bool, inject_cer_evaluators):
        actual = await is_valid_expression(ahb_expression, lambda cer: _content_evaluation_result.set(cer))
        assert actual[0] == expected_result
