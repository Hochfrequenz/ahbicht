# type:ignore[misc]
""" Tests for the parsing of the ahb_expressions as they appear in the AHBs. """

import pytest  # type:ignore[import]
from lark import Token, Tree

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions


class TestAhbExpressionParser:
    """Tests for the parsing of the ahb_expressions as they appear in the AHBs."""

    @pytest.mark.parametrize(
        "ahb_expression, expected_tree",
        [
            pytest.param(
                "Muss",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "requirement_indicator",
                            [
                                Token("MODAL_MARK", "Muss"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "X",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "requirement_indicator",
                            [
                                Token("PREFIX_OPERATOR", "X"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Muss[1]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Token("CONDITION_EXPRESSION", "[1]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Soll[1]U[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Soll"),
                                Token("CONDITION_EXPRESSION", "[1]U[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "soll[1]u[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "soll"),
                                Token("CONDITION_EXPRESSION", "[1]u[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Muss[UB1]U[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Token("CONDITION_EXPRESSION", "[UB1]U[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Kann([1]O[5])U[904]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Kann"),
                                Token("CONDITION_EXPRESSION", "([1]O[5])U[904]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Kann([1]∨[5])∧[904]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Kann"),
                                Token("CONDITION_EXPRESSION", "([1]∨[5])∧[904]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "X[1]O[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "X"),
                                Token("CONDITION_EXPRESSION", "[1]O[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "O[1]O[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "O"),
                                Token("CONDITION_EXPRESSION", "[1]O[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "O([1]U[5]) U\t[905]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "O"),
                                Token("CONDITION_EXPRESSION", "([1]U[5]) U\t[905]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Kann([1]U[5])U[905]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Kann"),
                                Token("CONDITION_EXPRESSION", "([1]U[5])U[905]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Kann([1]∧[5])∧[905]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Kann"),
                                Token("CONDITION_EXPRESSION", "([1]∧[5])∧[905]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "kann([1]∧[5])∧[905]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "kann"),
                                Token("CONDITION_EXPRESSION", "([1]∧[5])∧[905]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "Muss[3]U[4]Soll[5]    Kann[502]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Muss"),
                                Token("CONDITION_EXPRESSION", "[3]U[4]"),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Soll"),
                                Token("CONDITION_EXPRESSION", "[5]    "),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "Kann"),
                                Token("CONDITION_EXPRESSION", "[502]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "M[3]U[4]S[5]    K[502]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "M"),
                                Token("CONDITION_EXPRESSION", "[3]U[4]"),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "S"),
                                Token("CONDITION_EXPRESSION", "[5]    "),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "K"),
                                Token("CONDITION_EXPRESSION", "[502]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "m[3]u[4]s[5]    k[502]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "m"),
                                Token("CONDITION_EXPRESSION", "[3]u[4]"),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "s"),
                                Token("CONDITION_EXPRESSION", "[5]    "),
                            ],
                        ),
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("MODAL_MARK", "k"),
                                Token("CONDITION_EXPRESSION", "[502]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "U[1]O[5]",
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "U"),
                                Token("CONDITION_EXPRESSION", "[1]O[5]"),
                            ],
                        ),
                    ],
                ),
            ),
            pytest.param(
                "u[1]O[5]",  # lower case "u"
                Tree(
                    "ahb_expression",
                    [
                        Tree(
                            "single_requirement_indicator_expression",
                            [
                                Token("PREFIX_OPERATOR", "u"),
                                Token("CONDITION_EXPRESSION", "[1]O[5]"),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_parse_valid_ahb_expression_to_to_single_requirement_indicator_expressions(
        self, ahb_expression: str, expected_tree: Tree[Token]
    ):
        """
        Tests that valid ahb expressions are parsed as expected.
        """
        parsed_tree = parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)

        assert isinstance(parsed_tree, Tree)
        assert parsed_tree == expected_tree

    @pytest.mark.parametrize(
        "ahb_expression",
        [
            pytest.param(None),
            pytest.param(""),
            pytest.param("   "),
            pytest.param("[1]"),  # without requirement indicator
            pytest.param("Mus[2]"),  # this is a tricky one because since we introduced lower case operators and modal
            # marks the characters alone are all ok (lower case 'u' is a valid expression operator and lower case 's'
            # could be interpreted as lower case model mark). As of 2021-10-27, when parsing an AHB expression we only
            # use a simple regex to roughly check if the characters at the positions where we expect condition
            # expressions to be found are allow-listed. But we do not check the grammar yet. The grammar is checked
            # upon parsing the condition expression, but that's the second step. To keep the test failing, I introduced
            # a negative look ahead where formerly only a "character set" allow list check.
            pytest.param("Muss[2]C[3]"),
        ],
    )
    def test_parse_invalid_ahb_expression(self, ahb_expression: str):
        """Tests that an error is raised when trying to parse an invalid string."""

        with pytest.raises(SyntaxError) as excinfo:
            parse_ahb_expression_to_single_requirement_indicator_expressions(ahb_expression)

        assert """Please make sure that the ahb_expression starts with a requirement indicator \
(i.e Muss/M, Soll/S, Kann/K, X, O, U) and the condition expressions consist of only \
the following characters: [ ] ( ) U ∧ O ∨ X ⊻ and digits.""" in str(
            excinfo.value
        )
