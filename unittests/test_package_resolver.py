"""
Test for the expansion of packages.
"""
from typing import Mapping, Optional

import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.expression_resolver import expand_packages
from ahbicht.expressions.package_expansion import DictBasedPackageResolver, PackageResolver

pytestmark = pytest.mark.asyncio


class TestPackageResolver:
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
            pytest.param("[123P7..8]", "[1] U ([2] O [3])"),
            pytest.param("[123P10..11]", "[1] U ([2] O [3])"),
            pytest.param("[123P0..5]", "[1] U ([2] O [3])"),
            pytest.param("[17] U [123P]", "[17] U ([1] U ([2] O [3]))"),
        ],
    )
    async def test_correct_injection(
        self, inject_package_resolver, unexpanded_expression: str, expected_expanded_expression: str
    ):
        unexpanded_tree = parse_condition_expression_to_tree(unexpanded_expression)
        actual_tree = await expand_packages(parsed_tree=unexpanded_tree)
        assert actual_tree is not None
        expected_expanded_tree = parse_condition_expression_to_tree(expected_expanded_expression)
        assert actual_tree == expected_expanded_tree

    @pytest.mark.parametrize(
        "inject_package_resolver",
        [{"123P": "[1] U ([2] O [3])"}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "unexpanded_expression, error_message",
        [
            pytest.param("[123P8..7]", "0≤n≤m is not fulfilled for n=8, m=7"),
        ],
    )
    async def test_invalid_package_repeatability(
        self, inject_package_resolver, unexpanded_expression: str, error_message: str
    ):
        unexpanded_tree = parse_condition_expression_to_tree(unexpanded_expression)
        with pytest.raises(ValueError) as invalid_repeatability_error:
            _ = await expand_packages(parsed_tree=unexpanded_tree)
        assert error_message in str(invalid_repeatability_error)
