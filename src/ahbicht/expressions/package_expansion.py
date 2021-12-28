"""
Package Expansion is the process of finding the condition expression which was abbreviated by using a package.
F.e. if inside a tree "[123P]" is replaced by "[1] U ([2] O [3])".
"""
from abc import ABC, abstractmethod
from typing import Mapping, Optional


# pylint:disable=too-few-public-methods
class PackageResolver(ABC):
    """
    A package resolver provides condition expressions for given package keys.
    """

    @abstractmethod
    async def get_condition_expression(self, package_key: str) -> Optional[str]:
        """
        Returns a condition expression (e.g. "[1] U ([2] O [3]) for the given package_key (e.g. "123P")
        Returns None if the package is unresolvable.
        :param package_key:
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
        :param results:
        """
        self._all_packages: Mapping[str, Optional[str]] = results

    async def get_condition_expression(self, package_key: str) -> Optional[str]:
        if not package_key:
            raise ValueError(f"The package key must not be None/empty but was '{package_key}'")
        if package_key in self._all_packages:
            return self._all_packages[package_key]
        return None
