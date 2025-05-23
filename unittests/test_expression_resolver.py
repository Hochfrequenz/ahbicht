import pytest
from lark import Token, Tree

from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions


class TestExpressionResolver:
    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                "Muss[3]U[4] Soll[5]",
                Tree(  # type:ignore[misc]
                    "ahb_expression",
                    [
                        Tree(  # type:ignore[misc]
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Tree(  # type:ignore[misc]
                                    "and_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "3")]),
                                        Tree("condition", [Token("CONDITION_KEY", "4")]),
                                    ],
                                ),
                            ],
                        ),
                        Tree(  # type:ignore[misc]
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Soll"),
                                Tree("condition", [Token("CONDITION_KEY", "5")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "X[504]O[6]",
                Tree(  # type:ignore[misc]
                    "ahb_expression",
                    [
                        Tree(  # type:ignore[misc]
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "X"),
                                Tree(  # type:ignore[misc]
                                    "or_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "504")]),
                                        Tree("condition", [Token("CONDITION_KEY", "6")]),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "[905]([504]U[6])",
                Tree(  # type:ignore[misc]
                    "then_also_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "905")]),
                        Tree(  # type:ignore[misc]
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "504")]),
                                Tree("condition", [Token("CONDITION_KEY", "6")]),
                            ],
                        ),
                    ],
                ),
            ),
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
                                            Token("RULE", "package"),
                                            [Token("PACKAGE_KEY", "4P"), Token("REPEATABILITY", "0..1")],
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
    async def test_expression_resolver_valid(self, expression: str, expected_tree: Tree[Token]):
        actual_tree = await parse_expression_including_unresolved_subexpressions(
            expression, resolve_packages=False, include_package_repeatabilities=False
        )
        assert actual_tree == expected_tree

    @pytest.mark.parametrize(
        "expression",
        [
            pytest.param(
                "foo",
            ),
        ],
    )
    async def test_expression_resolver_failing(self, expression: str):
        with pytest.raises(SyntaxError) as excinfo:
            await parse_expression_including_unresolved_subexpressions(expression)

        assert """Please make sure that the ahb_expression starts with a requirement indicator \
(i.e Muss/M, Soll/S, Kann/K, X, O, U) and the condition expressions consist of only \
the following characters: [ ] ( ) U ∧ O ∨ X ⊻ and digits.""" in str(
            excinfo.value
        )

        assert """Please make sure that:
             * all conditions have the form [INT]
             * all packages have the form [INTPn..m]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """ in str(
            excinfo.value
        )
        # todo: implement wiederholbarkeiten
