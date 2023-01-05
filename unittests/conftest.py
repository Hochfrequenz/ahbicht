"""
why conftest.py?
https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session
"""
import inject
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]

from ahbicht.content_evaluation import ContentEvaluationResult, EvaluatableData, TokenLogicProvider
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResultSchema
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableDataProvider
from ahbicht.content_evaluation.evaluator_factory import create_content_evaluation_result_based_evaluators
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider
from unittests.defaults import default_test_format, default_test_version


def store_content_evaluation_result_in_evaluatable_data(
    content_evaluation_result: ContentEvaluationResult,
) -> EvaluatableData[dict]:
    """
    a helper method for the tests to store a serialized content evaluation result in an EvaluatableData instance
    :param content_evaluation_result:
    :return: a new EvaluatableData instance
    """
    schema = ContentEvaluationResultSchema()
    cer_dict = schema.dump(content_evaluation_result)
    return EvaluatableData(
        body=cer_dict, edifact_format=default_test_format, edifact_format_version=default_test_version
    )


@pytest.fixture
def inject_cer_evaluators(request: SubRequest):
    content_evaluation_result: ContentEvaluationResult = request.param
    assert isinstance(content_evaluation_result, ContentEvaluationResult)

    def get_evaluatable_data():
        return store_content_evaluation_result_in_evaluatable_data(content_evaluation_result)

    def configure(binder):
        binder.bind(
            TokenLogicProvider,
            SingletonTokenLogicProvider(
                [*create_content_evaluation_result_based_evaluators(default_test_format, default_test_version)]
            ),
        )
        binder.bind_to_provider(EvaluatableDataProvider, get_evaluatable_data)

    inject.configure_once(configure)
    yield
    inject.clear()
