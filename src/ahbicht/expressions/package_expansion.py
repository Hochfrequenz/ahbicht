"""
Package Expansion is the process of finding the condition expression which was abbreviated by using a package.
e.g. if inside a tree "[123P]" is replaced by "[1] U ([2] O [3])".
"""
from abc import ABC, abstractmethod
from typing import Mapping, Optional

from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.mapping_results import PackageKeyConditionExpressionMapping


# pylint:disable=too-few-public-methods
class PackageResolver(ABC):
    """
    A package resolver provides condition expressions for given package keys.
    """

    # define some common attributes. They will be needed to find the correct resolver for each use case.
    edifact_format: EdifactFormat = NotImplementedError(  # type:ignore[assignment]
        "The inheriting package resolver needs to define a format to which it is applicable."
    )  #: the format for which the resolver may be used
    edifact_format_version: EdifactFormatVersion = NotImplementedError(  # type:ignore[assignment]
        "The inheriting package resolver needs to define a format version."
    )  #: the format version for which the resolver may be used

    @abstractmethod
    async def get_condition_expression(self, package_key: str) -> PackageKeyConditionExpressionMapping:
        """
        Returns a condition expression (e.g. "[1] U ([2] O [3])") for the given package_key (e.g. "123P")
        Returns None in the package_expression if the package is unresolvable (see 'has_been_resolved_successfully').
        :param package_key: The unique (integer) key of the package. The 'P' suffix is required.
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method.")


class DictBasedPackageResolver(PackageResolver):
    """
    A Package Resolver that is based on hardcoded values from a dictionary
    """

    def __init__(self, results: Mapping[str, Optional[str]]):
        """
        Initialize with a dictionary that contains all the condition expressions.
        :param results: maps the package key (e.g. '123') to the package expression (e.g. '[1] U [2]')
        """
        for key in results.keys():
            if not key.endswith("P"):
                raise ValueError("The keys should end with 'P' to avoid ambiguities. Use '123P' instead of '123'.")
        self._all_packages: Mapping[str, Optional[str]] = results

    async def get_condition_expression(self, package_key: str) -> PackageKeyConditionExpressionMapping:
        if not package_key:
            raise ValueError(f"The package key must not be None/empty but was '{package_key}'")
        if not package_key.endswith("P"):
            raise ValueError("The package key should be provided with a trailing 'P'.")
        if package_key in self._all_packages:
            return PackageKeyConditionExpressionMapping(
                package_key=package_key,
                package_expression=self._all_packages[package_key],
                edifact_format=EdifactFormat.UTILMD,
            )
        return PackageKeyConditionExpressionMapping(
            package_key=package_key,
            package_expression=None,
            edifact_format=EdifactFormat.UTILMD,
        )
