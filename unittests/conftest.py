"""
why conftest.py?
https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""

import pytest
from _pytest.fixtures import SubRequest

from ahbicht.content_evaluation.ahb_context import AhbContext
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.evaluator_factory import create_content_evaluation_result_based_evaluators
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from unittests.defaults import default_test_format, default_test_version


def store_content_evaluation_result_in_evaluatable_data(
    content_evaluation_result: ContentEvaluationResult,
) -> EvaluatableData[dict]:
    """
    a helper method for the tests to store a serialized content evaluation result in an EvaluatableData instance
    :param content_evaluation_result:
    :return: a new EvaluatableData instance
    """
    cer_dict = content_evaluation_result.model_dump(mode="json")
    return EvaluatableData(
        body=cer_dict, edifact_format=default_test_format, edifact_format_version=default_test_version
    )


@pytest.fixture
def ahb_context_from_cer(request: SubRequest) -> AhbContext:
    """
    Builds an AhbContext from a ContentEvaluationResult parameter.
    Uses ContentEvaluationResultBased evaluators + the CER as evaluatable data body.
    """
    content_evaluation_result: ContentEvaluationResult = request.param
    assert isinstance(content_evaluation_result, ContentEvaluationResult)

    evaluatable_data = store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)
    rc_evaluator, fc_evaluator, hints_provider, package_resolver = create_content_evaluation_result_based_evaluators(
        default_test_format, default_test_version
    )
    # Wire up evaluatable_data into the CER-based evaluators so they can look up results
    fc_evaluator._evaluatable_data = evaluatable_data
    hints_provider._evaluatable_data = evaluatable_data
    package_resolver._evaluatable_data = evaluatable_data

    return AhbContext(
        rc_evaluator=rc_evaluator,
        fc_evaluator=fc_evaluator,
        hints_provider=hints_provider,
        package_resolver=package_resolver,
        evaluatable_data=evaluatable_data,
    )
