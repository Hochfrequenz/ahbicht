"""
Package Expansion is the process of finding the condition expression which was abbreviated by using a package.
e.g. if inside a tree "[123P]" is replaced by "[1] U ([2] O [3])".
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.mapping_results import PackageKeyConditionExpressionMapping, PackageKeyConditionExpressionMappingSchema


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


class JsonFilePackageResolver(DictBasedPackageResolver):
    """
    The JsonFilePackageResolver loads package keys/expressions from a JSON file.
    """

    def __init__(self, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion, file_path: Path):
        super().__init__(self._open_and_load_package_mappings(file_path))
        self.edifact_format = edifact_format
        self.edifact_format_version = edifact_format_version

    @staticmethod
    def _open_and_load_package_mappings(file_path: Path) -> Dict[str, Optional[str]]:
        """
        Opens the hint json file and loads it into an attribute of the class.
        The method can read both a dictionary of package key/package expression mappings and a
        list of PackageKeyConditionExpressionMappings
        """
        with open(file_path, encoding="utf-8") as json_infile:
            json_body = json.load(json_infile)
        if isinstance(json_body, dict):
            # {"1P": "[2] U [3]", "2P": "[4] O [5]"...
            return json_body
        # [{PackageKeyConditionExpressionMapping},...]
        mapping_list: List[PackageKeyConditionExpressionMapping] = PackageKeyConditionExpressionMappingSchema().load(
            json_body, many=True
        )
        return {mapping.package_key: mapping.package_expression for mapping in mapping_list}
