""" Tests for the parsing of the conditions tests (Mussfeldprüfung) """

import json
from typing import List

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.categorized_key_extract import CategorizedKeyExtract, CategorizedKeyExtractSchema
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.expressions.condition_expression_parser import extract_categorized_keys
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint

pytestmark = pytest.mark.asyncio


class TestCategorizedKeyExtraction:
    @pytest.mark.parametrize(
        "expression, expected_key_extract",
        [
            pytest.param(
                "[1]",
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["1"],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
            ),
            pytest.param(
                "([1] U [2]) O ([1] X [3])",
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["1", "2", "3"],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
            ),
            pytest.param(
                "[100]U([2]U([53]O[4]))[999][502]",
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2", "4", "53", "100"],
                    format_constraint_keys=["999"],
                    package_keys=[],
                    time_condition_keys=[],
                ),
            ),
            pytest.param(
                "[100]U([2]U([53]O[4]))[999][502]U[123P]",
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2", "4", "53", "100"],
                    format_constraint_keys=["999"],
                    package_keys=["123P"],
                    time_condition_keys=[],
                ),
            ),
            pytest.param(
                "[UB3]U[100]U([2]U([53]O[4]))[999][502]U[123P]",
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2", "4", "53", "100"],
                    format_constraint_keys=["999"],
                    package_keys=["123P"],
                    time_condition_keys=["UB3"],
                ),
            ),
        ],
    )
    async def test_extraction_of_categorized_keys_from_condition_expression(
        self, expression: str, expected_key_extract: CategorizedKeyExtract
    ):
        """
        Tests that the CategorizedKeyExtract is generated correctly.
        """
        actual = await extract_categorized_keys(expression)
        assert actual == expected_key_extract

    @pytest.mark.parametrize(
        "key_extract, expected_cers",
        [
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=[],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                [],
                id="0 FC, 0 RC",
            ),
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["1"],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                [
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.FULFILLED},
                        packages={},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.UNFULFILLED},
                        packages={},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.UNKNOWN},
                        packages={},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={},
                        requirement_constraints={"1": ConditionFulfilledValue.NEUTRAL},
                        packages={},
                    ),
                ],
                id="0 FC, 1 RC",
            ),
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=[],
                    format_constraint_keys=["901"],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                [
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=True)},
                        requirement_constraints={},
                        packages={},
                    ),
                    ContentEvaluationResult(
                        hints={},
                        format_constraints={"901": EvaluatedFormatConstraint(format_constraint_fulfilled=False)},
                        requirement_constraints={},
                        packages={},
                    ),
                ],
                id="1 FC, 0 RC",
            ),
        ],
    )
    def test_possible_cer_generation_small_results(
        self, key_extract: CategorizedKeyExtract, expected_cers: List[ContentEvaluationResult]
    ):
        actual = key_extract.generate_possible_content_evaluation_results()
        # We only test the small edge cases as real code.
        # This quickly gets super large. 2 FCs * 2 RCs is already 64 results
        assert actual == expected_cers

    # pylint:disable=fixme
    # todo: register as custom mark https://docs.pytest.org/en/stable/mark.html
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
        categorized_keys = CategorizedKeyExtractSchema().load(file_content["categorizedKeyExtract"])
        expected_result = ContentEvaluationResultSchema(many=True).load(file_content["expected_result"])
        actual = categorized_keys.generate_possible_content_evaluation_results()
        # json_string = ContentEvaluationResultSchema(many=True).dumps(actual)
        assert actual == expected_result
