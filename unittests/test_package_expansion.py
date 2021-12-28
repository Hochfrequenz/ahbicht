"""
Test for the expansion of packages.
"""
from typing import Mapping, Optional

import inject
import pytest
from _pytest.fixtures import SubRequest

from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.expression_resolver import expand_packages
from ahbicht.expressions.package_expansion import DictBasedPackageResolver, PackageResolver

pytestmark = pytest.mark.asyncio


class TestPackageExpansion:
    """
    Test for the expansions of packages
    """

    @pytest.fixture
    def inject_package_resolver(self, request: SubRequest):
        result_dict: Mapping[str, Optional[str]] = request.param
        resolver = DictBasedPackageResolver(result_dict)
        inject.clear_and_configure(
            lambda binder: binder.bind(PackageResolver, resolver)  # type:ignore[arg-type]
        )

    @pytest.mark.parametrize(
        "inject_package_resolver",
        [{"123P": "[1] U ([2] O [3])"}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "unexpanded_expression, expected_expanded_expression",
        [
            pytest.param("[123P]", "[1] U ([2] O [3])"),
            pytest.param("[17] U [123P]", "[12] U ([1] U ([2] O [3]))"),
        ],
    )
    async def test_correct_injection(
        self, inject_package_resolver, unexpanded_expression: str, expected_expanded_expression: str
    ):
        unexpanded_tree = parse_condition_expression_to_tree(unexpanded_expression)
        tree = await expand_packages(parsed_tree=unexpanded_tree)
        assert tree is not None
