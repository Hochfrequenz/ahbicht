"""
Package Expansion is the process of finding the condition expression which was abbreviated by using a package.
F.e. if inside a tree "[123P]" is replaced by "[1] U ([2] O [3])".
"""
from abc import ABC, abstractmethod
from typing import Mapping, Optional, Type

import inject
from lark import Token, Tree
from lark.exceptions import VisitError

from ahbicht.expressions.base_transformer import BaseTransformer
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


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

    def get_condition_expression(self, package_key: str) -> Optional[str]:
        if not package_key:
            raise ValueError(f"The package key must not be None/empty but was '{package_key}'")
        if package_key in self._all_packages:
            return self._all_packages[package_key]
        return None


class PackageExpansionTransformer(BaseTransformer[Tree, Tree]):
    """
    The PackageExpansionTransformer expands packages inside a tree to condition expressions by using a PackageResolver.
    """

    def __init__(self):
        super().__init__(input_values=None)
        self._resolver: Type[PackageResolver] = inject.instance(PackageResolver)

    def package(self, token: Token):
        ce = self._resolver.get_condition_expression(token.value)
        return parse_condition_expression_to_tree(ce)

    def and_composition(self, left: Tree, right: Tree) -> Tree:
        return left

    def or_composition(self, left: Tree, right: Tree) -> Tree:
        return left

    def xor_composition(self, left: Tree, right: Tree) -> Tree:
        return left


async def expand_packages(parsed_tree: Tree) -> Tree:
    """
    Replaces all the "short" packages in parser_tree with the respective "long" condition expressions
    """
    try:
        result = PackageExpansionTransformer().transform(parsed_tree)
    except VisitError as visit_err:
        raise visit_err.orig_exc

    return result
