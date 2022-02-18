"""
Contains a Package Resolver that uses the Hochfrequenz API to resolve package keys to condition expressions
"""
import aiohttp

from ahbicht.expressions.package_expansion import PackageResolver
from ahbicht.mapping_results import PackageKeyConditionExpressionMapping, PackageKeyConditionExpressionMappingSchema


# pylint: disable=too-few-public-methods
class HochfrequenzPackageResolver(PackageResolver):
    """
    A package resolver that uses a REST API (by Hochfrequenz) to resolve packages.
    Note that this resolver requires an internet connection to work and the hochfrequenz API to be up and running.
    Consider using this resolver to retrieve package information once and then dump them into something fast and stable
    like f.e. a JSON file, a database or feed its results into a hardcoded package resolver once on startup.
    Relying on external web services is prone to be a bottleneck for your application.
    """

    _hochfrequenz_base_uri = "https://ahbicht.azurewebsites.net/api/ResolvePackageConditionExpression/"

    def __init__(self, api_url=_hochfrequenz_base_uri):
        """
        initializes the package resolver; you may overwrite the base url (f.e. for a test-system)
        """
        self.api_url = api_url

    async def get_condition_expression(self, package_key: str) -> PackageKeyConditionExpressionMapping:
        request_url = f"{self.api_url}/{self.edifact_format_version}/{self.edifact_format}/{package_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as response:
                print("Status:", response.status)
                if response.status != 200:
                    return PackageKeyConditionExpressionMapping(
                        package_key=package_key, package_expression=None, edifact_format=self.edifact_format
                    )
                response_body = await response.json()
                result = PackageKeyConditionExpressionMappingSchema().load(response_body)
                return result
