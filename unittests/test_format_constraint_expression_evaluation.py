""" Test for the evaluation of the format constraint expression. """
from typing import Optional

import inject
import pytest  # type:ignore[import]
import pytest_asyncio  # type:ignore[import]
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.evaluation_results import FormatConstraintEvaluationResult
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraint
from ahbicht.expressions.format_constraint_expression_evaluation import (
    _build_evaluated_format_constraint_nodes,
    format_constraint_evaluation,
)

pytestmark = pytest.mark.asyncio


class DummyFcEvaluator(FcEvaluator):
    """
    A dummy Format Constraint Evaluator
    """

    edifact_format = EdifactFormat.UTILMD
    edifact_format_version = EdifactFormatVersion.FV2104

    # no-self-use: The following methods are not static because it refers to the terminals of the lark grammar.

    async def evaluate_950(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        [950] Format: Marktlokations-ID
        """
        # this is just a minimal working example; we skip all the stuff like check digits and so on for simplicity
        is_malo: bool = entered_input and len(entered_input) == 11  # type:ignore[assignment]
        if is_malo:
            error_message = None
        else:
            error_message = f"'{entered_input}' is not 11 characters long and hence no MaLo."
        return EvaluatedFormatConstraint(format_constraint_fulfilled=is_malo, error_message=error_message)

    async def evaluate_951(self, entered_input: str) -> EvaluatedFormatConstraint:
        """
        [951] Format: Zählpunktbezeichnung
        """
        # this is just a minimal working example; we skip regex matching and integrity checks for simplicity
        is_zaehlpunkt: bool = entered_input and len(entered_input) == 33  # type:ignore[assignment]
        if is_zaehlpunkt:
            error_message = None
        else:
            error_message = f"'{entered_input}' is not a valid Zählpunktbezeichnung."
        return EvaluatedFormatConstraint(format_constraint_fulfilled=is_zaehlpunkt, error_message=error_message)


class TestFormatConstraintExpressionEvaluation:
    """Test for the evaluation of the format constraint expressions"""

    _input_values = {
        "901": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
        "902": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="902 muss erfüllt sein"),
        "903": EvaluatedFormatConstraint(format_constraint_fulfilled=True),
        "904": EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message="904 muss erfüllt sein"),
    }

    @pytest_asyncio.fixture()
    def setup_and_teardown_injector(self):
        inject.clear_and_configure(lambda binder: binder.bind(FcEvaluator, DummyFcEvaluator()))
        yield
        inject.clear()

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
        ],
    )
    async def test_evaluate_valid_format_constraint_expression(
        self, mocker, format_constraint_expression, expected_format_constraints_fulfilled, expected_error_message
    ):
        """
        Tests that valid format_constraint expressions are evaluated as expected.
        Odd condition_keys are True, even condition_keys are False
        """
        mocker.patch(
            "ahbicht.expressions.format_constraint_expression_evaluation._build_evaluated_format_constraint_nodes",
            return_value=self._input_values,
        )

        result = await format_constraint_evaluation(format_constraint_expression, entered_input=None)

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
        mocker,
        format_constraints_expression: str,
        input_values: dict,
        expected_error_message: str,
    ):
        """Tests that an error is raised when trying to pass invalid values."""
        mocker.patch(
            "ahbicht.expressions.format_constraint_expression_evaluation._build_evaluated_format_constraint_nodes",
            return_value=input_values,
        )

        with pytest.raises(ValueError) as excinfo:
            await format_constraint_evaluation(
                format_constraints_expression, entered_input=None  # type:ignore[arg-type]
            )

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
        self, condition_keys, entered_input, expected_evaluated_fc_nodes, setup_and_teardown_injector
    ):
        """Tests that evaluated format constraints nodes are build correctly."""
        evaluated_fc_nodes = await _build_evaluated_format_constraint_nodes(condition_keys, entered_input)
        assert evaluated_fc_nodes == expected_evaluated_fc_nodes

    @pytest.mark.parametrize(
        "format_constraint_expression, entered_input, is_successful, error_message",
        [
            pytest.param("[931]", "2022-01-01T00:00:00+00:00", True, "+00:00"),
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
        format_constraint_expression,
        entered_input: str,
        is_successful: bool,
        error_message: Optional[str],
        setup_and_teardown_injector,
    ):
        """
        Tests that the default FC evaluator ships evaluation methods for 932, 933, 934 and 935 (those expanded from UBx)
        """
        result = await format_constraint_evaluation(format_constraint_expression, entered_input=entered_input)
        assert result is not None
        assert result.format_constraints_fulfilled == is_successful
        if is_successful is False and error_message is not None:
            assert error_message in result.error_message  # type:ignore[operator]
