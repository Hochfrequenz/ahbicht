"""
Dataclasses that are relevant in the context of the content_evaluation.
"""

from dataclasses import dataclass, replace
from typing import Generic, Optional, TypeVar

from efoli import EdifactFormat, EdifactFormatVersion

_BodyT = TypeVar("_BodyT")
"""
the type of the data on which the evaluations are performed
"""


@dataclass
class EvaluatableData(Generic[_BodyT]):
    """
    Data that can be processed/evaluated by an evaluator. They must not change during a content_evaluation run.
    The evaluatable data act as a flexible container to pass information that might be necessary for the
    content_evaluation. As of now (because our content_evaluation capabilities are quite limited) the only information
    provided is the meta seed of the message itself. But in the future the data provided might grow.
    """

    body: _BodyT  #: the body of the message that is being validated in the respective format (e.g. an edifact_seed)
    edifact_format: EdifactFormat  #: the format of the evaluatable message (e.g. UTILMD)
    edifact_format_version: EdifactFormatVersion  #: the format version of the evaluable data (e.g. FV2210)
    # ideas for what else could go here:
    # - pruefidentifikator to tweak the content_evaluation depending on the situation?


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
