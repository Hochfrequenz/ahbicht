"""
Tests the expression builder module.
"""

import pytest

from ahbicht.expressions.expression_builder import (
    FormatConstraintExpressionBuilder,
    FormatErrorMessageExpressionBuilder,
    HintExpressionBuilder,
)
from ahbicht.models.condition_nodes import EvaluatedFormatConstraint, Hint, UnevaluatedFormatConstraint


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


class TestFormatErrorMessageExpressionBuilder:
    """
    Tests the format error message expression builder for combining error messages.
    """

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                "'msg1' und 'msg2'",
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                "msg1",
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                "msg2",
            ),
        ],
    )
    def test_logical_and(self, init, other, expected):
        builder = FormatErrorMessageExpressionBuilder(init)
        actual = builder.land(other).get_expression()
        assert actual == expected

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                "'msg1' oder 'msg2'",
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                None,
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                None,
            ),
        ],
    )
    def test_logical_or(self, init, other, expected):
        builder = FormatErrorMessageExpressionBuilder(init)
        actual = builder.lor(other).get_expression()
        assert actual == expected

    @pytest.mark.parametrize(
        "init, other, expected",
        [
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                "Entweder 'msg1' oder 'msg2'",
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                "Zwei exklusive Formatdefinitionen dürfen nicht gleichzeitig erfüllt sein",
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1"),
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                None,
            ),
            pytest.param(
                EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None),
                EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2"),
                None,
            ),
        ],
    )
    def test_logical_xor(self, init, other, expected):
        builder = FormatErrorMessageExpressionBuilder(init)
        actual = builder.xor(other).get_expression()
        assert actual == expected

    def test_nested_xor_uses_parentheses_instead_of_quotes(self):
        """
        Test that nested XOR expressions use parentheses instead of quotes to avoid
        mismatched quote problems like "Entweder 'Entweder 'msg1' oder 'msg2'' oder 'msg3'".
        """
        fc1 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1")
        fc2 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2")
        fc3 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg3")

        builder = FormatErrorMessageExpressionBuilder(fc1)
        builder.xor(fc2)
        # After first xor: "Entweder 'msg1' oder 'msg2'"
        # After second xor, the compound expression should use parentheses:
        builder.format_constraint_fulfilled = False  # Keep it as False for continuing the chain
        result = builder.xor(fc3).get_expression()

        # The result should use parentheses around the compound expression, not quotes
        assert result == "Entweder (Entweder 'msg1' oder 'msg2') oder 'msg3'"

    def test_nested_lor_uses_parentheses(self):
        """
        Test that nested OR expressions use parentheses for compound expressions.
        """
        fc1 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1")
        fc2 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2")
        fc3 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg3")

        builder = FormatErrorMessageExpressionBuilder(fc1)
        builder.lor(fc2)
        # After first lor: "'msg1' oder 'msg2'"
        builder.format_constraint_fulfilled = False  # Keep it as False for continuing the chain
        result = builder.lor(fc3).get_expression()

        # The compound expression should use parentheses
        assert result == "('msg1' oder 'msg2') oder 'msg3'"

    def test_nested_land_uses_parentheses(self):
        """
        Test that nested AND expressions use parentheses for compound expressions.
        """
        fc1 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg1")
        fc2 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg2")
        fc3 = EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="msg3")

        builder = FormatErrorMessageExpressionBuilder(fc1)
        builder.land(fc2)
        # After first land: "'msg1' und 'msg2'"
        result = builder.land(fc3).get_expression()

        # The compound expression should use parentheses
        assert result == "('msg1' und 'msg2') und 'msg3'"
