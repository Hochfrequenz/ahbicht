""" Tests for the parsing of the conditions tests (Mussfeldprüfung) """

import json
from typing import List

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import (
    CategorizedKeyExtract,
    ContentEvaluationPrerequisites,
    ContentEvaluationPrerequisitesSchema,
    ContentEvaluationResult,
    ContentEvaluationResultSchema,
)
from ahbicht.expressions.condition_expression_parser import collect_prerequisites, extract_categorized_keys
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.content_evaluation_result import CategorizedKeyExtract
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys


class TestCategorizedKeyExtraction:
    @pytest.mark.parametrize(
        "expression, expected_prerequisites",
        [
            pytest.param(
                "[1]",
                CategorizedKeyExtract(
                    hint_keys=[], requirement_constraint_keys=["1"], format_constraint_keys=[], package_keys=[]
                ),
            ),
            pytest.param(
                "([1] U [2]) O ([1] X [3])",
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["1", "2", "3"],
                    format_constraint_keys=[],
                    package_keys=[],
                ),
            ),
            pytest.param(
                "[100]U([2]U([53]O[4]))[999][502]",
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2", "4", "53", "100"],
                    format_constraint_keys=["999"],
                    package_keys=[],
                ),
            ),
        ],
    )
    def test_extraction_of_categorized_keys_from_condition_expression(
        self, expression: str, expected_prerequisites: CategorizedKeyExtract
    ):
        """
        Tests that the prerequisites are generated correctly.
        """
        actual = extract_categorized_keys(expression)
        assert actual == expected_prerequisites


    @pytest.mark.parametrize(
        "prerequisites, expected_cers",
        [
            pytest.param(
                ContentEvaluationPrerequisites(
                    hint_keys=[], requirement_constraint_keys=[], format_constraint_keys=[], package_keys=[]
                ),
                [],
                id="0 FC, 0 RC",
            ),
            pytest.param(
                ContentEvaluationPrerequisites(
                    hint_keys=[], requirement_constraint_keys=["1"], format_constraint_keys=[], package_keys=[]
                ),
                [
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.FULFILLED},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.UNFULFILLED},
                    ),
                    ContentEvaluationResult(
                        hints={}, format_constraints={}, requirement_constraints={"1": ConditionFulfilledValue.UNKNOWN}
                    ),
                    ContentEvaluationResult(
                        hints={}, format_constraints={}, requirement_constraints={"1": ConditionFulfilledValue.NEUTRAL}
                    ),
                ],
                id="0 FC, 1 RC",
            ),
            pytest.param(
                ContentEvaluationPrerequisites(
                    hint_keys=[], requirement_constraint_keys=[], format_constraint_keys=["901"], package_keys=[]
                ),
                [
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=True)},
                        requirement_constraints={},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=False)},
                        requirement_constraints={},
                    ),
                ],
                id="1 FC, 0 RC",
            ),
        ],
    )
    def test_possible_cer_generation_small_results(
        self, prerequisites: ContentEvaluationPrerequisites, expected_cers: List[ContentEvaluationResult]
    ):
        actual = prerequisites.generate_possible_content_evaluation_results()
        # We only test the small edge cases as real code.
        # This quickly gets super large. 2 FCs * 2 RCs is already 64 results
        assert actual == expected_cers

    ALL_LARGE_TEST_CASES = pytest.mark.datafiles(
        "./unittests/content_evaluation_result_generation/example0.json",
        "./unittests/content_evaluation_result_generation/example1.json",
    )

    @pytest.mark.parametrize(
        "test_file_path",
        [
            pytest.param("example0.json", id="0 FC, 3 RC"),
            pytest.param("example1.json", id="2 FC, 3 RC"),
        ],
    )
    @ALL_LARGE_TEST_CASES
    def test_possible_cer_generation_large_results(self, test_file_path, datafiles):
        file_content = json.load(datafiles / test_file_path)
        prerequisites = ContentEvaluationPrerequisitesSchema().load(file_content["prerequisite"])
        expected_result = ContentEvaluationResultSchema(many=True).load(file_content["expected_result"])
        actual = prerequisites.generate_possible_content_evaluation_results()
        json_string = ContentEvaluationResultSchema(many=True).dumps(actual)
        assert actual == expected_result

