import pytest  # type:ignore[import]
from lark import Token, Tree

from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions


class TestExpressionResolver:
    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                "Muss[3]U[4] Soll[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Tree(
                                    "and_composition",
                                    [
                                        Tree("condition_key", [Token("INT", "3")]),
                                        Tree("condition_key", [Token("INT", "4")]),
                                    ],
                                ),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [Token("MODAL_MARK", "Soll"), Tree("condition_key", [Token("INT", "5")])],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "X[504]O[6]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "X"),
                                Tree(
                                    "or_composition",
                                    [
                                        Tree("condition_key", [Token("INT", "504")]),
                                        Tree("condition_key", [Token("INT", "6")]),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "[905]([504]U[6])",
                Tree(
                    "then_also_composition",
                    [
                        Tree("condition_key", [Token("INT", "905")]),
                        Tree(
                            "and_composition",
                            [
                                Tree("condition_key", [Token("INT", "504")]),
                                Tree("condition_key", [Token("INT", "6")]),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_expression_resolver_valid(self, expression: str, expected_tree: Tree):
        actual_tree = parse_expression_including_unresolved_subexpressions(expression)
        assert actual_tree == expected_tree

    @pytest.mark.parametrize(
        "expression",
        [
            pytest.param(
                "foo",
            ),
        ],
    )
    def test_expression_resolver_failing(self, expression: str):
        with pytest.raises(SyntaxError) as excinfo:
            parse_expression_including_unresolved_subexpressions(expression)

        assert """Please make sure that the ahb_expression starts with a requirement indicator \
(i.e Muss/M, Soll/S, Kann/K, X, O, U) and the condition expressions consist of only \
the following characters: [ ] ( ) U ∧ O ∨ X ⊻ and digits.""" in str(
            excinfo.value
        )

        assert """Please make sure that:
             * all conditions have the form [INT]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """ in str(
            excinfo.value
        )
