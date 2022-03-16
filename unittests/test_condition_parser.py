# type:ignore[misc]
""" Tests for the parsing of the conditions tests (Mussfeldprüfung) """

import pytest  # type:ignore[import]
from lark import Token, Tree

from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree


class TestConditionParser:
    """Test for the parsing of the conditions tests (Mussfeldprüfung)"""

    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                # single condition
                "[1]",
                Tree("condition", [Token("CONDITION_KEY", "1")]),
            ),
            pytest.param(
                # single condition with whitespace
                "[1  ]",
                Tree("condition", [Token("CONDITION_KEY", "1")]),
            ),
            pytest.param(
                # simple or_composition
                "[1]O[2]",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # simple or_composition with lower case "o"
                "[1]o[2]",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # simple and_composition with lower case "u"
                "[1]u[2]",
                Tree(
                    "and_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # simple or_composition with whitespace
                " [1] O[ 2]",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # simple or_composition with whitespace and tab
                " [1]\tO[ 2]",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # and/or combination, and before or
                "[1]U[2]    O[53]",
                Tree(
                    "or_composition",
                    [
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                    ],
                ),
            ),
            pytest.param(
                # and/or combination, and before or, different order
                "[53]O[1]U[2]",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # xor_composition
                "[1]X[2]",
                Tree(
                    "xor_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # xor_composition with lower case "x"
                "[1]x[2]",
                Tree(
                    "xor_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # xor_composition
                "[1]⊻[2]",
                Tree(
                    "xor_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # time condition
                "[UB1]u[2]",
                Tree(
                    "and_composition",
                    [
                        Tree("time_condition", [Token("TIME_CONDITION_KEY", "UB1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
        ],
    )
    def test_parse_valid_expression_to_tree(self, expression: str, expected_tree: Tree[Token]):
        """
        Tests that valid expressions containing operators "O"/"U"/"X", different whitespaces
        and no brackets are parsed as expected.
        """
        parsed_tree = parse_condition_expression_to_tree(expression)

        assert isinstance(parsed_tree, Tree)
        assert parsed_tree == expected_tree

    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                #  no brackets
                " [1][987]",
                Tree(
                    "then_also_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "987")]),
                    ],
                ),
            ),
            pytest.param(
                #  two format constraints with an operator
                "[901]U[987]",
                Tree(
                    "and_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "901")]),
                        Tree("condition", [Token("CONDITION_KEY", "987")]),
                    ],
                ),
            ),
            pytest.param(
                # format constraint is attached as suffix _without_ an operator
                "([1]U[2])[987]",
                Tree(
                    "then_also_composition",
                    [
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree("condition", [Token("CONDITION_KEY", "987")]),
                    ],
                ),
            ),
            pytest.param(
                # format constraint is attached as prefix _without_ an operator
                "[987]([1]U[2])",
                Tree(
                    "then_also_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "987")]),
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # MSCONS AHB, Kapitel 7
                "([902] U [906] [46])",
                Tree(
                    "and_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "902")]),
                        Tree(
                            "then_also_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "906")]),
                                Tree("condition", [Token("CONDITION_KEY", "46")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # two format constraints
                "([950]([2]U[4]))O([951]([1]U[3]))",
                Tree(
                    "or_composition",
                    [
                        Tree(
                            "then_also_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "950")]),
                                Tree(
                                    "and_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                                        Tree("condition", [Token("CONDITION_KEY", "4")]),
                                    ],
                                ),
                            ],
                        ),
                        Tree(
                            "then_also_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "951")]),
                                Tree(
                                    "and_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                                        Tree("condition", [Token("CONDITION_KEY", "3")]),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_parse_valid_expression_to_tree_with_format_constraints(self, expression: str, expected_tree: Tree):
        """
        Tests that valid expressions containing operators "O" and "U", different whitespaces
        and no brackets are parsed as expected. It is similiar to the test `test_parse_valid_expression_to_tree`
        but it adds format constraints.
        """
        parsed_tree = parse_condition_expression_to_tree(expression)

        assert isinstance(parsed_tree, Tree)
        assert parsed_tree == expected_tree

    @pytest.mark.parametrize(
        "expression, expected_tree",
        [
            pytest.param(
                # single condition
                "([1])",
                Tree("condition", [Token("CONDITION_KEY", "1")]),
            ),
            pytest.param(
                # simple or_composition
                "([1]O[2])",
                Tree(
                    "or_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "1")]),
                        Tree("condition", [Token("CONDITION_KEY", "2")]),
                    ],
                ),
            ),
            pytest.param(
                # and/or combination, and in brackets
                "([1]U[2])O[53]",
                Tree(
                    "or_composition",
                    [
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                    ],
                ),
            ),
            pytest.param(
                # and/or combination, or in brackets
                "([1]O[2])U[53]",
                Tree(
                    "and_composition",
                    [
                        Tree(
                            "or_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                    ],
                ),
            ),
            pytest.param(
                # and/or combination, or in brackets, different order
                "[53]U([1]O[2])",
                Tree(
                    "and_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                        Tree(
                            "or_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # complex expression with two brackets
                "([1]O[2])U([53]U[4]O[12])",
                Tree(
                    "and_composition",
                    [
                        Tree(
                            "or_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree(
                            "or_composition",
                            [
                                Tree(
                                    "and_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                                        Tree("condition", [Token("CONDITION_KEY", "4")]),
                                    ],
                                ),
                                Tree("condition", [Token("CONDITION_KEY", "12")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # complex expression with two brackets
                "([1]∨[2])∧([53]∧[4]∨[12])",
                Tree(
                    "and_composition",
                    [
                        Tree(
                            "or_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "1")]),
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                        Tree(
                            "or_composition",
                            [
                                Tree(
                                    "and_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                                        Tree("condition", [Token("CONDITION_KEY", "4")]),
                                    ],
                                ),
                                Tree("condition", [Token("CONDITION_KEY", "12")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # nested brackets
                "[100]U([2]U([53]O[4]))",
                Tree(
                    "and_composition",
                    [
                        Tree("condition", [Token("CONDITION_KEY", "100")]),
                        Tree(
                            "and_composition",
                            [
                                Tree("condition", [Token("CONDITION_KEY", "2")]),
                                Tree(
                                    "or_composition",
                                    [
                                        Tree("condition", [Token("CONDITION_KEY", "53")]),
                                        Tree("condition", [Token("CONDITION_KEY", "4")]),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # nested brackets
                "[10P]U([1]O[2])",
                Tree(
                    "and_composition",
                    [
                        Tree(Token("RULE", "package"), [Token("PACKAGE_KEY", "10P")]),
                        Tree(
                            "or_composition",
                            [
                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "1")]),
                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                # nested brackets
                "[10P1..5]U([1]O[2])",
                Tree(
                    "and_composition",
                    [
                        Tree(Token("RULE", "package"), [Token("PACKAGE_KEY", "10P"), Token("REPEATABILITY", "1..5")]),
                        Tree(
                            "or_composition",
                            [
                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "1")]),
                                Tree(Token("RULE", "condition"), [Token("CONDITION_KEY", "2")]),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_parse_valid_expression_with_brackets_to_tree(self, expression: str, expected_tree: Tree):
        """Tests that valid strings that contain brackets are parsed as expected."""
        parsed_tree = parse_condition_expression_to_tree(expression)

        assert isinstance(parsed_tree, Tree)
        assert parsed_tree == expected_tree

    @pytest.mark.parametrize(
        "expression",
        [
            pytest.param(None),
            pytest.param(""),
            pytest.param("   "),
            pytest.param("[1"),
            pytest.param("1]"),
            pytest.param("1"),
            pytest.param("[]"),
            pytest.param("[2]U[1"),
            pytest.param("[2]U1"),
            pytest.param("[2]U"),
            pytest.param("([1]U[2]"),  # missing closing bracket
            pytest.param("[1]U[2])"),  # missing opening bracket
            pytest.param("[P1]"),  # Package "P" at beginning
        ],
    )
    def test_parse_invalid_expression(self, expression: str):
        """Tests that an error is raised when trying to parse an invalid string."""

        with pytest.raises(SyntaxError) as excinfo:
            parse_condition_expression_to_tree(expression)

        assert """Please make sure that:
             * all conditions have the form [INT]
             * all packages have the form [INTPn..m]
             * no conditions are empty
             * all compositions are combined by operators 'U'/'O'/'X' or without an operator
             * all open brackets are closed again and vice versa
             """ in str(
            excinfo.value
        )

    @pytest.mark.parametrize(
        "old_expression, new_expression",
        [
            pytest.param("[1]U[2]", "[1]∧[2]"),
            pytest.param("[1]O[2]", "[1]∨[2]"),
            pytest.param("[1]X[2]", "[1]⊻[2]"),
            pytest.param(
                "([951][510]U[522])O([950][514]U([523]O[525]))", "([951][510]∧[522])∨([950][514]∧([523]∨[525]))"
            ),
        ],
    )
    def test_equivalence_of_new_and_old_notation_expressions(self, old_expression: str, new_expression: str):
        """
        Tests that U/O/X are treated just the same as the new logical operands.
        :return:
        """
        old_tree = parse_condition_expression_to_tree(old_expression)
        new_tree = parse_condition_expression_to_tree(new_expression)
        assert old_tree == new_tree
