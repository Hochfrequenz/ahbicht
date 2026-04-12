import pytest

from ahbicht.content_evaluation.expression_check import is_valid_expression
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from unittests.defaults import default_test_format, default_test_version


class TestValidityCheck:
    """
    a test class for the expression validation feature
    """

    @pytest.mark.parametrize(
        "ahb_expression,expected_result",
        [
            pytest.param("Foo", False),
            pytest.param("Muss [1] U [2]", True),
            pytest.param("Muss [61] O [584]", False),  # connecting a hint with LOR is not valid
            pytest.param("Muss [123] O [584]", False),
            pytest.param("Muss [501] X [999]", False),  # connecting a hint XOR fc is not valid
            pytest.param("Muss [501] O [999]", False),  # connecting a hint LOR fc is not valid
            pytest.param("Muss [983][1] X [984][2]", True),
            pytest.param(
                "([446] ∧ ([465] ∨ [466]) ∧ [467] ∧ ([468] ⊻ ([469] ∧ [470])) ⊻ [448]", False
            ),  # unbalanced brackets
            pytest.param("Muss [15] ∧ [2050]", True),  # contains a 'Geschütztes' Leerzeichen
            pytest.param("Muss [15]🙄∧ [2050]", False),
            pytest.param(
                "X ([950] [509] ∧ ([64] V [70])) V ([960] [522] ∧ [71] ∧ [53])", True
            ),  # nur echt mit 'V' statt LOR
            pytest.param("X [1P0..n]", True),
        ],
    )
    async def test_is_valid_expression(self, ahb_expression: str, expected_result: bool):
        """Tests validity using AhbContext (no inject setup needed)."""
        actual_str = await is_valid_expression(
            ahb_expression,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        assert actual_str[0] == expected_result
        # check the tree as argument, too
        try:
            tree = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        except SyntaxError:
            return  # ok, the syntax error is actually raised on parsing already
        actual_tree = await is_valid_expression(
            tree,
            edifact_format=default_test_format,
            edifact_format_version=default_test_version,
        )
        assert actual_tree[0] == expected_result

    async def test_is_valid_expression_value_error(self):
        with pytest.raises(ValueError):
            await is_valid_expression(
                12345,
                edifact_format=default_test_format,
                edifact_format_version=default_test_version,
            )
        with pytest.raises(ValueError):
            await is_valid_expression(
                None,
                edifact_format=default_test_format,
                edifact_format_version=default_test_version,
            )
