""" Tests the PackageResolver, that assumes a ContentEvaluationResult to be present in the evaluatable data"""

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.package_expansion import ContentEvaluationResultBasedPackageResolver
from ahbicht.mapping_results import PackageKeyConditionExpressionMapping
from unittests.defaults import (
    EmptyDefaultFcEvaluator,
    EmptyDefaultRcEvaluator,
    default_test_format,
    default_test_version,
    store_content_evaluation_result_in_evaluatable_data,
)


class TestCerBasedPackageResolver:
    """Test for the evaluation using the ContentEvaluationResult Based Hints Provider"""

    @pytest.fixture
    def inject_cer_evaluators(self, request: SubRequest):
        # indirect parametrization: https://stackoverflow.com/a/33879151/10009545
        content_evaluation_result: ContentEvaluationResult = request.param
        assert isinstance(content_evaluation_result, ContentEvaluationResult)
        package_resolver = ContentEvaluationResultBasedPackageResolver()
        package_resolver.edifact_format = default_test_format
        package_resolver.edifact_format_version = default_test_version

        def get_evaluatable_data():
            return store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)

        def configure(binder):
            binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider([EmptyDefaultRcEvaluator(), EmptyDefaultFcEvaluator(), package_resolver]),
            )
            binder.bind_to_provider(EvaluatableDataProvider, get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

    @pytest.mark.parametrize(
        "inject_cer_evaluators",
        [
            pytest.param(
                ContentEvaluationResult(
                    format_constraints={},
                    requirement_constraints={},
                    hints={},
                    packages={
                        "2P": "[2]",
                        "3P": "[3] U [4]",
                    },
                )
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "condition_key, expected_result",
        [
            pytest.param(
                "2P",
                PackageKeyConditionExpressionMapping(
                    package_key="2P", edifact_format=default_test_format, package_expression="[2]"
                ),
            ),
            pytest.param(
                "3P",
                PackageKeyConditionExpressionMapping(
                    package_key="3P", edifact_format=default_test_format, package_expression="[3] U [4]"
                ),
            ),
            pytest.param(
                "4P",
                PackageKeyConditionExpressionMapping(
                    package_expression=None, edifact_format=default_test_format, package_key="4P"
                ),
            ),
        ],
    )
    async def test_evaluation(
        self, condition_key: str, expected_result: PackageKeyConditionExpressionMapping, inject_cer_evaluators
    ):
        token_logic_provider: TokenLogicProvider = inject.instance(TokenLogicProvider)  # type:ignore[assignment]
        package_resolver = token_logic_provider.get_package_resolver(default_test_format, default_test_version)
        actual = await package_resolver.get_condition_expression(condition_key)
        assert actual == expected_result
