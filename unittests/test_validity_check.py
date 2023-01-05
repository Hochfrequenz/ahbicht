from contextvars import ContextVar
from typing import Optional

import inject
import pytest  # type:ignore[import]

from ahbicht.content_evaluation import is_valid_expression
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult, ContentEvaluationResultSchema
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData, EvaluatableDataProvider
from ahbicht.content_evaluation.evaluator_factory import create_content_evaluation_result_based_evaluators
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider
from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from unittests.defaults import default_test_format, default_test_version

_content_evaluation_result: ContextVar[Optional[ContentEvaluationResult]] = ContextVar(
    "_content_evaluation_result", default=None
)


def _get_evaluatable_data():
    """
    returns the _content_evaluation_result context var value wrapped in a EvaluatableData container.
    This is the kind of data that the ContentEvaluationResultBased RC/FC Evaluators, HintsProvider and Package Resolver
    require.
    :return:
    """
    cer = _content_evaluation_result.get()
    return EvaluatableData(
        body=ContentEvaluationResultSchema().dump(cer),
        edifact_format=default_test_format,
        edifact_format_version=default_test_version,
    )


class TestValidityCheck:
    """
    a test class for the expression validation feature
    """

    @pytest.fixture
    def inject_cer_evaluators(self):
        def configure(binder):
            binder.bind(
                TokenLogicProvider,
                SingletonTokenLogicProvider(
                    [*create_content_evaluation_result_based_evaluators(default_test_format, default_test_version)]
                ),
            )
            binder.bind_to_provider(EvaluatableDataProvider, _get_evaluatable_data)

        inject.configure_once(configure)
        yield
        inject.clear()

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
        ],
    )
    async def test_is_valid_expression(self, ahb_expression: str, expected_result: bool, inject_cer_evaluators):
        actual_str = await is_valid_expression(ahb_expression, lambda cer: _content_evaluation_result.set(cer))
        assert actual_str[0] == expected_result
        # check the tree as argument, too
        try:
            tree = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        except SyntaxError:
            return  # ok, the syntax error is actually raised on parsing already
        actual_tree = await is_valid_expression(tree, lambda cer: _content_evaluation_result.set(cer))
        assert actual_tree[0] == expected_result

    async def test_is_valid_expression_value_error(self):
        with pytest.raises(ValueError):
            await is_valid_expression(12345, None)
