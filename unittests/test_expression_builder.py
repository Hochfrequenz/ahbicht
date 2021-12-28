"""
Tests the expression builder module.
"""
import pytest  # type:ignore[import]

from ahbicht.expressions.condition_nodes import Hint, UnevaluatedFormatConstraint
from ahbicht.expressions.expression_builder import FormatConstraintExpressionBuilder, HintExpressionBuilder


class TestFormatConstraintExpressionBuilder:
    """
    Tests the format constraint expression builder.
    """

    def test_simple_construction(self):
        fc_1 = UnevaluatedFormatConstraint(condition_key="1")
        fc_2 = UnevaluatedFormatConstraint(condition_key="2")
        fc_3 = UnevaluatedFormatConstraint(condition_key="3")
        fc_4 = UnevaluatedFormatConstraint(condition_key="4")
        fceb = FormatConstraintExpressionBuilder(fc_1).lor(fc_2).land(fc_3).xor(fc_4)
        assert fceb.get_expression() == "(([1] O [2]) U [3]) X [4]"

        fceb_from_str = FormatConstraintExpressionBuilder("[7] U [8] U [9]").lor(fc_2).land("[3]").xor(fc_4)
        assert fceb_from_str.get_expression() == "((([7] U [8] U [9]) O [2]) U [3]) X [4]"


class TestHintExpressionBuilder:
    """
    Tests the hint expression builder.
    """

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(Hint(condition_key="0", hint="foo"), None, "foo"),
            pytest.param(None, Hint(condition_key="0", hint="bar"), "bar"),
            pytest.param(Hint(condition_key="0", hint="foo"), Hint(condition_key="1", hint="bar"), "foo und bar"),
            pytest.param("foo", Hint(condition_key="1", hint="bar"), "foo und bar"),
            pytest.param("foo", "bar", "foo und bar"),
            pytest.param(None, None, None),
        ],
    )
    def test_logical_and(self, init, other, expected: Hint):
        builder: HintExpressionBuilder = HintExpressionBuilder(init)
        actual = builder.land(other).get_expression()
        assert actual == expected

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(Hint(condition_key="0", hint="foo"), None, "foo"),
            pytest.param(None, Hint(condition_key="0", hint="bar"), "bar"),
            pytest.param(Hint(condition_key="0", hint="foo"), Hint(condition_key="1", hint="bar"), "foo oder bar"),
            pytest.param("foo", Hint(condition_key="1", hint="bar"), "foo oder bar"),
            pytest.param("foo", "bar", "foo oder bar"),
            pytest.param(None, None, None),
        ],
    )
    def test_logical_or(self, init, other, expected: Hint):
        builder: HintExpressionBuilder = HintExpressionBuilder(init)
        actual = builder.lor(other).get_expression()
        assert actual == expected

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(Hint(condition_key="0", hint="foo"), None, "foo"),
            pytest.param(None, Hint(condition_key="0", hint="bar"), "bar"),
            pytest.param(
                Hint(condition_key="0", hint="foo"), Hint(condition_key="1", hint="bar"), "Entweder (foo) oder (bar)"
            ),
            pytest.param("foo", Hint(condition_key="1", hint="bar"), "Entweder (foo) oder (bar)"),
            pytest.param(
                "foo und x und y", Hint(condition_key="1", hint="bar"), "Entweder (foo und x und y) oder (bar)"
            ),
            pytest.param("foo", "bar", "Entweder (foo) oder (bar)"),
            pytest.param(None, None, None),
        ],
    )
    def test_logical_xor(self, init, other, expected: Hint):
        builder: HintExpressionBuilder = HintExpressionBuilder(init)
        actual = builder.xor(other).get_expression()
        assert actual == expected

    def test_a_longer_concatenation(self):
        builder = HintExpressionBuilder("foo").land("bar").lor("asd").xor("xyz")
        assert builder.get_expression() == "Entweder (foo und bar oder asd) oder (xyz)"
