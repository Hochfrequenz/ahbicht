"""
Test for the expansion of packages.
"""

from logging import LogRecord
from typing import List, Mapping, Optional

import inject
import pytest
from _pytest.fixtures import SubRequest
from efoli import EdifactFormat, EdifactFormatVersion
from lark import Token, Tree

from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.expression_resolver import (
    expand_packages,
    parse_expression_including_unresolved_subexpressions,
)
from ahbicht.expressions.package_expansion import JsonFilePackageResolver, PackageResolver
from ahbicht.models.mapping_results import PackageKeyConditionExpressionMapping, Repeatability
from ahbicht.utility_functions import parse_repeatability
from unittests.defaults import DefaultPackageResolver, return_empty_dummy_evaluatable_data


class TestPackageResolver:
    """
    Test for the expansions of packages
    """

    @pytest.fixture
    def inject_package_resolver(self, request: SubRequest):
        result_dict: Mapping[str, Optional[str]] = request.param
        resolver = DefaultPackageResolver(result_dict)
        inject.clear_and_configure(
            lambda binder: binder.bind(  # type:ignore[arg-type]
                TokenLogicProvider, SingletonTokenLogicProvider([resolver])
            ).bind_to_provider(EvaluatableDataProvider, return_empty_dummy_evaluatable_data)
        )
        yield
        inject.clear()

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

    @pytest.mark.datafiles("./unittests/provider_test_files/example_package_mapping_dict.json")
    @pytest.mark.datafiles("./unittests/provider_test_files/example_package_mapping_list.json")
    @pytest.mark.parametrize(
        "filename",
        [pytest.param("example_package_mapping_dict.json"), pytest.param("example_package_mapping_list.json")],
    )
    async def test_file_based_package_resolver(self, caplog, filename, datafiles):
        """Tests if package resolver provider is instantiated correctly."""
        path_to_hint_json = datafiles / filename
        package_resolver: PackageResolver = JsonFilePackageResolver(
            edifact_format=EdifactFormat.UTILMD,
            edifact_format_version=EdifactFormatVersion.FV2104,
            file_path=path_to_hint_json,
        )
        assert package_resolver.edifact_format == EdifactFormat.UTILMD
        assert package_resolver.edifact_format_version == EdifactFormatVersion.FV2104
        assert await package_resolver.get_condition_expression("123P") == PackageKeyConditionExpressionMapping(
            edifact_format=EdifactFormat.UTILMD, package_key="123P", package_expression="[1] U [2] O [3]"
        )
        assert await package_resolver.get_condition_expression("456P") == PackageKeyConditionExpressionMapping(
            edifact_format=EdifactFormat.UTILMD, package_key="456P", package_expression="[4] U [5] X [6]"
        )
        log_entries: List[LogRecord] = caplog.records
        assert log_entries[0].message == "Instantiated JsonFilePackageResolver"
        assert log_entries[1].message.startswith("Resolved expression")

    def test_how_to_access_repeatability_token(self):
        """
        This test demonstrates how to access the repeatability token from the parsed tree
        We extract those tokens also in the PackageExpansionTransformer, but we don't do anything with them there yet.
        """
        unexpanded_tree = parse_condition_expression_to_tree("[1P2..3]")
        assert unexpanded_tree is not None
        repeatability_tokens = [token for token in unexpanded_tree.children if token.type == "REPEATABILITY"]
        assert parse_repeatability(repeatability_tokens[0]) == Repeatability(min_occurrences=2, max_occurrences=3)

    @pytest.mark.parametrize(
        "inject_package_resolver",
        [{"4P": "([2] O [3])"}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                "Muss[3]U[4P0..1]",
                Tree(  # type:ignore[misc]
                    Token("RULE", "ahb_expression"),
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Tree(
                                    "and_composition",
                                    [
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "3")]),
                                        Tree(
                                            "and_composition",
                                            [
                                                Tree(
                                                    "or_composition",
                                                    [
                                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "2")]),
                                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "3")]),
                                                    ],
                                                ),
                                                Tree(Token("RULE", "condition"), [Token("REPEATABILITY", "0..1")]),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
            ),
        ],
    )
    async def test_expression_resolver_valid_include_repeatabilities(
        self, inject_package_resolver, expression: str, expected_tree: Tree[Token]
    ):
        actual_tree = await parse_expression_including_unresolved_subexpressions(
            expression, resolve_packages=True, include_package_repeatabilities=True
        )
        assert actual_tree == expected_tree
