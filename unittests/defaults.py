"""
contains reusable classes and instances of AHBicht Evaluators and Resolvers.
They are supposed to be used in unittests where they need to be injected but don't have a real purpose.
Inject them to have a concise test setup.
"""
from itertools import cycle
from typing import Iterator

from maus.edifact import EdifactFormat, EdifactFormatVersion

#: the default edifact format used in the unit tests
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue
from ahbicht.expressions.hints_provider import DictBasedHintsProvider
from ahbicht.expressions.package_expansion import DictBasedPackageResolver

default_test_format: EdifactFormat = EdifactFormat.UTILMD
#: the default edifact format version used in the unit tests
default_test_version: EdifactFormatVersion = EdifactFormatVersion.FV2210
#: an empty EvaluatableData instance
empty_default_test_data: EvaluatableData[dict] = EvaluatableData(
    body={}, edifact_format=default_test_format, edifact_format_version=default_test_version
)


class EmptyDefaultRcEvaluator(RcEvaluator):
    """
    An RC Evaluator in the default edifact format and edifact format version
    """

    def _get_default_context(self):
        return None

    def __init__(self):
        super().__init__()
        self.edifact_format = default_test_format
        self.edifact_format_version = default_test_version


empty_default_rc_evaluator = EmptyDefaultRcEvaluator()


class IteratingFulfilledUnfulfilledRcEvaluator(RcEvaluator):
    def _get_default_context(self):
        return None

    def __init__(self):
        super().__init__()
        self.edifact_format = default_test_format
        self.edifact_format_version = default_test_version
        self.result_cycle_1: Iterator[ConditionFulfilledValue] = cycle(
            [ConditionFulfilledValue.FULFILLED, ConditionFulfilledValue.UNFULFILLED]
        )
        self.result_cycle_2: Iterator[ConditionFulfilledValue] = cycle(
            [
                ConditionFulfilledValue.FULFILLED,
                ConditionFulfilledValue.FULFILLED,
                ConditionFulfilledValue.UNFULFILLED,
                ConditionFulfilledValue.UNFULFILLED,
            ]
        )

    def evaluate_1(self, _, __) -> ConditionFulfilledValue:
        # goes like: fulfilled, unfulfilled, fulfilled, unfulfilled, fulfilled, unfulfilled...
        return next(self.result_cycle_1)

    def evaluate_2(self, _, __) -> ConditionFulfilledValue:
        # goes like: fulfilled, fulfilled, unfulfilled, unfulfilled, fulfilled, fulfilled, unfulfilled, unfulfilled, ...
        return next(self.result_cycle_2)


iterating_rc_evaluator = IteratingFulfilledUnfulfilledRcEvaluator()


class EmptyDefaultFcEvaluator(FcEvaluator):
    """
    An (empty) FC Evaluator in the default edifact format and edifact format version
    """

    def __init__(self):
        super().__init__()
        self.edifact_format = default_test_format
        self.edifact_format_version = default_test_version


empty_default_fc_evaluator = EmptyDefaultFcEvaluator()


class DefaultHintsProvider(DictBasedHintsProvider):
    """
    An (empty) Hints Provider in the default edifact format and edifact format version
    """

    def __init__(self, mappings):
        super().__init__(mappings)
        self.edifact_format = default_test_format
        self.edifact_format_version = default_test_version


empty_default_hints_provider = DefaultHintsProvider({})


class DefaultPackageResolver(DictBasedPackageResolver):
    """
    An (empty) Package Resolver in the default edifact format and edifact format version
    """

    def __init__(self, mappings):
        super().__init__(mappings)
        self.edifact_format = default_test_format
        self.edifact_format_version = default_test_version


empty_default_package_resolver = DefaultPackageResolver({})


def return_empty_dummy_evaluatable_data() -> EvaluatableData[dict]:
    """
    :return: empty evaluatable data in the default format and format version
    """
    return empty_default_test_data
