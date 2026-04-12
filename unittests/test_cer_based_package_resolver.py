"""Tests the PackageResolver, that assumes a ContentEvaluationResult to be present in the evaluatable data"""

import pytest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from ahbicht.models.mapping_results import PackageKeyConditionExpressionMapping
from unittests.defaults import default_test_format, default_test_version


class TestCerBasedPackageResolver:
    """Test for the evaluation using the ContentEvaluationResult Based Package Resolver"""

    @pytest.mark.parametrize(
        "ahb_context_from_cer",
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
        self,
        condition_key: str,
        expected_result: PackageKeyConditionExpressionMapping,
        ahb_context_from_cer: AhbContext,
    ) -> None:
        package_resolver = ahb_context_from_cer.package_resolver
        actual = await package_resolver.get_condition_expression(condition_key)
        assert actual == expected_result
