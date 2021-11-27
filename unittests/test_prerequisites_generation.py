""" Tests for the parsing of the conditions tests (Mussfeldprüfung) """

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationPrerequisites
from ahbicht.expressions.condition_expression_parser import get_prerequisites


class TestPreqrequisitesGeneration:
    @pytest.mark.parametrize(
        "expression, expected_prerequisites",
        [
            pytest.param(
                "[1]",
                ContentEvaluationPrerequisites(
                    hint_keys=[], requirement_constraint_keys=["1"], format_constraint_keys=[], package_keys=[]
                ),
            ),
            pytest.param(
                "([1] U [2]) O ([1] X [3])",
                ContentEvaluationPrerequisites(
                    hint_keys=[],
                    requirement_constraint_keys=["1", "2", "3"],
                    format_constraint_keys=[],
                    package_keys=[],
                ),
            ),
            pytest.param(
                "[100]U([2]U([53]O[4]))[999][502]",
                ContentEvaluationPrerequisites(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2", "4", "53", "100"],
                    format_constraint_keys=["999"],
                    package_keys=[],
                ),
            ),
        ],
    )
    def test_prerequisite_from_condition_expression(
        self, expression: str, expected_prerequisites: ContentEvaluationPrerequisites
    ):
        """
        Tests that the prerequisites are generated correctly.
        """
        actual = get_prerequisites(expression)
        assert actual == expected_prerequisites
