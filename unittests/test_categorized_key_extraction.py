"""Tests for the parsing of the conditions tests (Mussfeldprüfung)"""

import json
from pathlib import Path
from typing import List

import pytest

from ahbicht.expressions.condition_expression_parser import extract_categorized_keys
from ahbicht.models.categorized_key_extract import CategorizedKeyExtract, CategorizedKeyExtractSchema
from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema


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
                "Muss [1]",
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
            pytest.param(
                "[100]U([2050]U([53]O[4]))[999][502]U[2002]",
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["4", "53", "100", "2002", "2050"],
                    format_constraint_keys=["999"],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                id="repeatability constraint",
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
    def test_possible_cer_generation_large_results(self, test_file_path: str, datafiles):
        with open(datafiles / Path(test_file_path), "r", encoding="utf-8") as infile:
            file_content = json.load(infile)
        categorized_keys = CategorizedKeyExtractSchema().load(file_content["categorizedKeyExtract"])
        expected_result = ContentEvaluationResultSchema(many=True).load(file_content["expected_result"])
        actual = categorized_keys.generate_possible_content_evaluation_results()
        # json_string = ContentEvaluationResultSchema(many=True).dumps(actual)
        assert actual == expected_result

    @pytest.mark.parametrize(
        "cer_a,cer_b,expected",
        [
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=[],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=[],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=[],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                id="empty+empty=empty",
            ),
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=["501"],
                    requirement_constraint_keys=["1"],
                    format_constraint_keys=["901"],
                    package_keys=["1P"],
                    time_condition_keys=["UB1"],
                ),
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2"],
                    format_constraint_keys=["902"],
                    package_keys=["2P"],
                    time_condition_keys=["UB2"],
                ),
                CategorizedKeyExtract(
                    hint_keys=["501", "502"],
                    requirement_constraint_keys=["1", "2"],
                    format_constraint_keys=["901", "902"],
                    package_keys=["1P", "2P"],
                    time_condition_keys=["UB1", "UB2"],
                ),
                id="simply add",
            ),
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=["502"],
                    requirement_constraint_keys=["2"],
                    format_constraint_keys=["902"],
                    package_keys=["2P"],
                    time_condition_keys=["UB2"],
                ),
                CategorizedKeyExtract(
                    hint_keys=["501", "502"],
                    requirement_constraint_keys=["1", "2"],
                    format_constraint_keys=["901", "902"],
                    package_keys=["1P", "3P", "2P"],
                    time_condition_keys=["UB3", "UB1"],
                ),
                CategorizedKeyExtract(
                    hint_keys=["501", "502"],
                    requirement_constraint_keys=["1", "2"],
                    format_constraint_keys=["901", "902"],
                    package_keys=[
                        "1P",
                        "2P",
                        "3P",
                    ],
                    time_condition_keys=["UB1", "UB2", "UB3"],
                ),
                id="remove duplicates, sort, sanitize",
            ),
        ],
    )
    def test_adding_categorized_key_extracts(
        self, cer_a: CategorizedKeyExtract, cer_b: CategorizedKeyExtract, expected: CategorizedKeyExtract
    ):
        actual = cer_a + cer_b
        assert actual == expected

    @pytest.mark.parametrize(
        "actual, expected_key_extract",
        [
            pytest.param(
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["10", "1..3", "3", "1..2"],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                CategorizedKeyExtract(
                    hint_keys=[],
                    requirement_constraint_keys=["1..2", "1..3", "3", "10"],
                    format_constraint_keys=[],
                    package_keys=[],
                    time_condition_keys=[],
                ),
                id="repeatability constraint key",
            ),
        ],
    )
    async def test_categorized_keys_sort_keys_including_repeatabilities(
        self, actual: CategorizedKeyExtract, expected_key_extract: CategorizedKeyExtract
    ):
        """
        Tests that the CategorizedKeyExtract is generated correctly.
        """
        actual._sort_keys()
        assert actual == expected_key_extract
