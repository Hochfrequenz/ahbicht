"""
Dataclasses that are relevant in the context of the content_evaluation.
"""
import threading
from dataclasses import dataclass, replace
from typing import Optional, Union

from maus.edifact import EdifactFormat, EdifactFormatVersion


@dataclass
class EvaluatableData:
    """
    Data that can be processed/evaluated by an evaluator. They must not change during a content_evaluation run.
    The evaluatable data act as a flexible container to pass information that might be necessary for the
    content_evaluation. As of now (because our content_evaluation capabilities are quite limited) the only information
    provided is the meta seed of the message itself. But in the future the data provided might grow.
    """

    edifact_seed: Union[dict, list]  #: the meta seed of the message that is being validated
    edifact_format: EdifactFormat  #: the format of the evaluatable message (e.g. UTILMD)
    edifact_format_version: EdifactFormatVersion  #: the format version of the evaluable data (e.g. FV2210)
    # ideas for what else could go here:
    # - pruefidentifikator to tweak the content_evaluation depending on the situation?


# pylint:disable=too-few-public-methods
class EvaluatableDataProvider:
    """
    This is just a dummy class that is used for dependency injection.
    Use it to call binder.bind_to_provider(EvaluatableDataProvider, func_that_returns_evaluatable_data_goes_here)
    during dependency injection.
    See https://github.com/ivankorobkov/python-inject#why-no-scopes
    """


# Create a thread-local storage for the message/evaluatable data under test
# see https://github.com/ivankorobkov/python-inject#why-no-scopes
_LOCAL = threading.local()


def get_thread_local_evaluatable_data() -> EvaluatableData:
    """
    returns the evaluatable data that have been set using set_thread_local_evaluatable_data before
    raises an exception if the set call is missing
    :return:
    """
    result: Optional[EvaluatableData] = getattr(_LOCAL, "evaluatable_data", None)
    if result is None:
        raise AttributeError(
            # pylint:disable=line-too-long
            f"No thread local evaluatable data have been found. Did you call '{set_thread_local_evaluatable_data.__name__}' before?"
        )
    return result


def set_thread_local_evaluatable_data(evaluatable_data: EvaluatableData):
    """
    set thread local evaluatable data (meaning they might be different in each call/request)
    :param evaluatable_data: the evaluatable data to be set
    """
    _LOCAL.evaluatable_data = evaluatable_data


@dataclass
class EvaluationContext:
    """
    A content_evaluation context describes the setting in which a condition shall be evaluated. The content_evaluation
    context might have different values for the same condition in one content_evaluation run. E.g. if the purpose of the
    condition is to make sure that every Zähler with zähler type "EHZ" has some properties the context of the
    content_evaluation is one zähler entry although there might be multiple zählers present in the message.
    """

    scope: Optional[
        str
    ]  # jsonpath that refers to the scope of the content_eval. If None, then "$" = entire message is used as scope.


def copy_evaluation_context(context: EvaluationContext) -> EvaluationContext:
    """
    Returns a deep copy of the provided context.
    This allows you to create a copy of a context instead of modifying the original context (as EvaluationContexts are
    "pass by reference")
    :param context:
    :return: a deep copy of the context
    """
    return replace(context)
