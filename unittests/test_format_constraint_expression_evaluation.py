"""Test for the evaluation of the format constraint expression."""

from logging import LogRecord
from typing import Any, Optional

import pytest

from ahbicht.content_evaluation import fc_evaluators
from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.expressions.format_constraint_expression_evaluation import (
    _build_evaluated_format_constraint_nodes,
    format_constraint_evaluation,
)
from ahbicht.models.condition_nodes import EvaluatedFormatConstraint
from ahbicht.models.evaluation_results import FormatConstraintEvaluationResult
from unittests.defaults import (
    default_test_format,
    default_test_version,
    empty_default_hints_provider,
    empty_default_package_resolver,
    empty_default_rc_evaluator,
    empty_default_test_data,
)


class DummyFcEvaluator(FcEvaluator):
    """
    A dummy Format Constraint Evaluator
    """

    edifact_format = default_test_format
    edifact_format_version = default_test_version

    async def evaluate_950(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        [950] Format: Marktlokations-ID
        """
        # this is just a minimal working example; we skip all the stuff like check digits and so on for simplicity
        is_malo: bool = entered_input and len(entered_input) == 11  # type: ignore[assignment]
        if is_malo:
            error_message = None
        else:
            error_message = f"'{entered_input}' is not 11 characters long and hence no MaLo."
        return EvaluatedFormatConstraint(format_constraint_fulfilled=is_malo, error_message=error_message)

    async def evaluate_951(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        [951] Format: Zaehlpunktbezeichnung
        """
        # this is just a minimal working example; we skip regex matching and integrity checks for simplicity
        is_zaehlpunkt: bool = entered_input and len(entered_input) == 33  # type: ignore[assignment]
        if is_zaehlpunkt:
            error_message = None
        else:
            error_message = f"'{entered_input}' is not a valid Zählpunktbezeichnung."
        return EvaluatedFormatConstraint(format_constraint_fulfilled=is_zaehlpunkt, error_message=error_message)


def _make_dummy_fc_context(fc_evaluator: Optional[FcEvaluator] = None) -> AhbContext:
    """Helper to build an AhbContext with the given FC evaluator."""
    return AhbContext(
        rc_evaluator=empty_default_rc_evaluator,
        fc_evaluator=fc_evaluator or empty_default_rc_evaluator,  # type: ignore[arg-type]
        hints_provider=empty_default_hints_provider,
        package_resolver=empty_default_package_resolver,
        evaluatable_data=empty_default_test_data,
    )


class TestFormatConstraintExpressionEvaluation:
    """Test for the evaluation of the format constraint expressions"""

    _input_values = {
        "901": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
        "902": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="902 muss erfüllt sein"),
        "903": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
        "904": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="904 muss erfüllt sein"),
        # For testing nested XOR with realistic error messages (like [950] and [951] in real usage)
        "950": EvaluatedFormatConstraint(
            format_constraint_fulfilled=False, error_message="Formatbedingung nicht erfüllt"
        ),
        "951": EvaluatedFormatConstraint(
            format_constraint_fulfilled=False, error_message="Formatbedingung nicht erfüllt"
        ),
    }

    @pytest.mark.parametrize(
        "format_constraint_expression, expected_format_constraints_fulfilled, expected_error_message",
        [
            pytest.param("[901]", True, None),
            pytest.param("[902]", False, "902 muss erfüllt sein"),
            pytest.param("[901]U[903]", True, None),
            pytest.param("[901]U[902]", False, "902 muss erfüllt sein"),
            pytest.param("[902]U[901]", False, "902 muss erfüllt sein"),
            pytest.param("[902]U[904]", False, "'902 muss erfüllt sein' und '904 muss erfüllt sein'"),
            pytest.param("[901]O[903]", True, None),
            pytest.param("[901]O[902]", True, None),
            pytest.param("[902]O[901]", True, None),
            pytest.param("[902]O[904]", False, "'902 muss erfüllt sein' oder '904 muss erfüllt sein'"),
            pytest.param(
                "[901]X[903]", False, "Zwei exklusive Formatdefinitionen dürfen nicht gleichzeitig erfüllt sein"
            ),
            pytest.param("[901]X[902]", True, None),
            pytest.param("[902]X[901]", True, None),
            pytest.param("[902]X[904]", False, "Entweder '902 muss erfüllt sein' oder '904 muss erfüllt sein'"),
            # Nested XOR: should use parentheses for compound expressions, not nested quotes
            pytest.param(
                "[902]X[904]X[902]",
                False,
                "Entweder (Entweder '902 muss erfüllt sein' oder '904 muss erfüllt sein') oder '902 muss erfüllt sein'",
            ),
            pytest.param(
                "[950]X[951]X[950]",
                False,
                "Entweder (Entweder 'Formatbedingung nicht erfüllt' oder 'Formatbedingung nicht erfüllt') "
                "oder 'Formatbedingung nicht erfüllt'",
            ),
            # Tests 'and before or'
            pytest.param("[902]U[904]O[901]", True, None),
            pytest.param("[901]O[902]U[904]", True, None),
            pytest.param("[902]U[901]O[903]", True, None),
            pytest.param("[902]O[901]U[903]", True, None),
            pytest.param("[902]O[901]U[904]", False, "'902 muss erfüllt sein' oder '904 muss erfüllt sein'"),
            pytest.param("[901]U[902]U[903]U[901]", False, "902 muss erfüllt sein"),
            pytest.param("[901]U[903]U[902]U[901]", False, "902 muss erfüllt sein"),
            # a very long one
            pytest.param("[901]U[902]O[901]U[901]U[902]O[902]O[901]", True, None),
            # with brackets
            pytest.param("([902]U[904])O[901]", True, None),
            pytest.param("[902]U([904]O[901])", False, "902 muss erfüllt sein"),
            pytest.param("[901]U[902]", False, "902 muss erfüllt sein"),
        ],
    )
    async def test_evaluate_valid_format_constraint_expression(
        self,
        mocker: Any,
        format_constraint_expression: str,
        expected_format_constraints_fulfilled: bool,
        expected_error_message: Optional[str],
    ) -> None:
        """
        Tests that valid format_constraint expressions are evaluated as expected.
        Odd condition_keys are True, even condition_keys are False
        """
        mocker.patch(
            "ahbicht.expressions.format_constraint_expression_evaluation._build_evaluated_format_constraint_nodes",
            return_value=self._input_values,
        )

        ctx = _make_dummy_fc_context()
        result = await format_constraint_evaluation(format_constraint_expression, ahb_context=ctx)

        assert isinstance(result, FormatConstraintEvaluationResult)
        assert result.format_constraints_fulfilled == expected_format_constraints_fulfilled
        assert result.error_message == expected_error_message

    @pytest.mark.parametrize(
        "format_constraints_expression, input_values, expected_error_message",
        [
            pytest.param(
                "[1]",
                {"1": "no_evaluated_format_constraint"},
                "Please make sure that the passed values are EvaluatedFormatConstraints.",
            ),
            pytest.param(
                "[1]U[2]",
                {"1": EvaluatedFormatConstraint(format_constraint_fulfilled=True)},
                "Please make sure that the input values contain all necessary condition_keys.",
            ),
        ],
    )
    async def test_evaluate_format_constraint_expressions_with_invalid_values(
        self,
        mocker: Any,
        format_constraints_expression: str,
        input_values: dict[str, Any],
        expected_error_message: str,
    ) -> None:
        """Tests that an error is raised when trying to pass invalid values."""
        mocker.patch(
            "ahbicht.expressions.format_constraint_expression_evaluation._build_evaluated_format_constraint_nodes",
            return_value=input_values,
        )

        ctx = _make_dummy_fc_context()
        with pytest.raises(ValueError) as excinfo:
            await format_constraint_evaluation(format_constraints_expression, ahb_context=ctx)

        assert expected_error_message in str(excinfo.value)

    @pytest.mark.parametrize(
        "condition_keys, entered_input, expected_evaluated_fc_nodes",
        [
            pytest.param(
                ["950", "951"],
                "12345678913",
                {
                    "950": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
                    "951": EvaluatedFormatConstraint(
                        format_constraint_fulfilled=False,
                        error_message="'12345678913' is not a valid Zählpunktbezeichnung.",
                    ),
                },
            ),
            pytest.param(
                ["950", "951"],
                "DE00056266802AO6G56M11SN51G21M24S",
                {
                    "950": EvaluatedFormatConstraint(
                        format_constraint_fulfilled=False,
                        error_message="'DE00056266802AO6G56M11SN51G21M24S' is not 11 characters long and hence no MaLo.",
                    ),
                    "951": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
                },
            ),
        ],
    )
    async def test_build_evaluated_format_constraint_nodes(
        self,
        caplog: pytest.LogCaptureFixture,
        condition_keys: list[str],
        entered_input: str,
        expected_evaluated_fc_nodes: dict[str, EvaluatedFormatConstraint],
    ) -> None:
        """Tests that evaluated format constraints nodes are build correctly."""
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set(entered_input)
        dummy_fc_evaluator = DummyFcEvaluator()
        ctx = _make_dummy_fc_context(fc_evaluator=dummy_fc_evaluator)
        evaluated_fc_nodes = await _build_evaluated_format_constraint_nodes(condition_keys, ahb_context=ctx)
        assert evaluated_fc_nodes == expected_evaluated_fc_nodes
        log_entries: list[LogRecord] = list(caplog.records)
        fc_log_entries = [e for e in log_entries if e.message.startswith("The format constraint")]
        assert len(fc_log_entries) == 2  # because in both parametrized test cases we evaluate 2 FCs
        for log_entry in fc_log_entries:
            assert "evaluated to " in log_entry.message

    @pytest.mark.parametrize(
        "format_constraint_expression, entered_input, is_successful, error_message",
        [
            pytest.param("[931]", "2022-01-01T00:00:00+00:00", True, "+00:00"),
            pytest.param("[931]", "202201010000+00", True, "EDIFACT datetime"),
            pytest.param("[931]", "2022-01-01T00:00:00Z", True, "Z is +00:00"),
            pytest.param("[931]", None, False, "None"),
            pytest.param("[931]", "2022-12-31T16:00:00-08:00", False, None),  # yes, it's truly a format constraint
            pytest.param("[931]", "2022-01-01T01:00:00+01:00", False, None),  # yes, it's that bad
            pytest.param("[932]", None, False, "empty or None"),
            pytest.param("[932]", "2022-01-01T00:00:00Z", False, "Stromtag"),
            pytest.param("[933]", "2022-01-01T00:00:00Z", False, "Stromtag"),
            pytest.param("[934]", "2022-01-01T06:00:00Z", False, "Gastag"),
            pytest.param("[935]", "2022-01-01T06:00:00Z", False, "Gastag"),
            pytest.param("[932]", "2022-06-01T00:00:00+02:00", True, None),
            pytest.param("[933]", "2022-01-01T00:00:00+01:00", True, None),
            pytest.param("[934]", "2022-06-01T06:00:00+02:00", True, None),
            pytest.param("[935]", "2022-01-01T06:00:00+01:00", True, None),
        ],
    )
    async def test_93x_format_constraints(
        self,
        format_constraint_expression: str,
        entered_input: str,
        is_successful: bool,
        error_message: Optional[str],
    ) -> None:
        """
        Tests that the default FC evaluator ships evaluation methods for 932, 933, 934 and 935 (those expanded from UBx)
        """
        fc_evaluators.text_to_be_evaluated_by_format_constraint.set(entered_input)
        dummy_fc_evaluator = DummyFcEvaluator()
        ctx = _make_dummy_fc_context(fc_evaluator=dummy_fc_evaluator)
        result = await format_constraint_evaluation(format_constraint_expression, ahb_context=ctx)
        assert result is not None
        assert result.format_constraints_fulfilled == is_successful
        if is_successful is False and error_message is not None:
            assert error_message in result.error_message  # type: ignore[operator]
