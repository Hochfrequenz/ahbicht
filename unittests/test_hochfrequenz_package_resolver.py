"""
Tests the HochfrequenzPackageResolver
"""
import pytest  # type:ignore[import]
from aioresponses import CallbackResult, aioresponses
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.helper.hochfrequenz_package_resolver import HochfrequenzPackageResolver
from ahbicht.mapping_results import PackageKeyConditionExpressionMapping

pytestmark = pytest.mark.asyncio


class TestHochfrequenzPackageResolver:
    async def test_hochfrequenz_package_api_success(self):
        package_resolver = HochfrequenzPackageResolver(api_url="https://test.inv")
        package_resolver.edifact_format = EdifactFormat.UTILMD
        package_resolver.edifact_format_version = EdifactFormatVersion.FV2204
        with aioresponses() as mocked_server:
            mocked_server.get(
                "https://test.inv/FV2204/UTILMD/10P",
                payload={"package_expression": "[20] \u2227 [244]", "package_key": "10P", "edifact_format": "UTILMD"},
            )
            actual = await package_resolver.get_condition_expression("10P")
            assert actual == PackageKeyConditionExpressionMapping(
                edifact_format=EdifactFormat.UTILMD, package_key="10P", package_expression="[20] ∧ [244]"
            )

    async def test_hochfrequenz_package_api_failure(self):
        package_resolver = HochfrequenzPackageResolver(api_url="https://test.inv")
        package_resolver.edifact_format = EdifactFormat.UTILMD
        package_resolver.edifact_format_version = EdifactFormatVersion.FV2204

        def simulate_error(url, **kwargs):
            return CallbackResult(status=400, payload={"see": "you did something wrong"})

        with aioresponses() as mocked_server:
            mocked_server.get(url="https://test.inv/FV2204/UTILMD/000P", callback=simulate_error)
            actual = await package_resolver.get_condition_expression("000P")
            assert actual == PackageKeyConditionExpressionMapping(
                # see the documentation: if the package could not be resolved, you'll get a None package_expression
                # but the PackageKeyConditionExpressionMapping itself is _not_ None
                edifact_format=EdifactFormat.UTILMD,
                package_key="000P",
                package_expression=None,
            )
