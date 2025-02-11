"""
Test for the expansion of packages.
"""

import pytest
from lark import Token, Tree

from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions


class TestTimeConditionReplacement:
    """
    Test for the replacement of time conditions
    """

    @pytest.mark.parametrize(
        "expression, replace_time_conditions, resolve_time_conditions, expected_tree",
        [
            pytest.param(
                "[UB1] U [42]",
                False,
                False,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(Token("RULE", "time_condition"), [Token("TIME_CONDITION_KEY", "UB1")]),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB1] U [42]",
                True,
                True,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "932")]),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB2] U [42]",
                False,
                False,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(Token("RULE", "time_condition"), [Token("TIME_CONDITION_KEY", "UB2")]),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB2] U [42]",
                False,
                False,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(Token("RULE", "time_condition"), [Token("TIME_CONDITION_KEY", "UB2")]),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB2] U [42]",
                False,
                True,
                Tree(
                    "and_composition",
                    [
                        Tree(
                            "xor_composition",
                            [
                                Tree(
                                    "and_composition",
                                    [
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "931")]),
                                        Tree(
                                            "then_also_composition",
                                            [
                                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "934")]),
                                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "490")]),
                                            ],
                                        ),
                                    ],
                                ),
                                Tree(
                                    "and_composition",
                                    [
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "931")]),
                                        Tree(
                                            "then_also_composition",
                                            [
                                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "935")]),
                                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "491")]),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB3] U [42]",
                False,
                False,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(Token("RULE", "time_condition"), [Token("TIME_CONDITION_KEY", "UB3")]),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
            pytest.param(
                "[UB3] U [42]",
                True,
                True,
                Tree(  # type:ignore[misc]
                    "and_composition",
                    [
                        Tree(  # type:ignore[misc]
                            "xor_composition",
                            [
                                Tree(  # type:ignore[misc]
                                    "then_also_composition",
                                    [
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "932")]),
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "492")]),
                                    ],
                                ),
                                Tree(  # type:ignore[misc]
                                    "then_also_composition",
                                    [
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "934")]),
                                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "493")]),
                                    ],
                                ),
                            ],
                        ),
                        Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "42")]),
                    ],
                ),
            ),
        ],
    )
    async def test_time_condition_expansion(
        self, expression: str, replace_time_conditions: bool, resolve_time_conditions: bool, expected_tree: Tree[Token]
    ):
        parsed_tree = await parse_expression_including_unresolved_subexpressions(
            expression, replace_time_conditions=replace_time_conditions, resolve_time_conditions=resolve_time_conditions
        )
        assert parsed_tree == expected_tree
