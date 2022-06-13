from maus.edifact import EdifactFormat, EdifactFormatVersion

#: the default edifact format used in the unit tests
from ahbicht.content_evaluation.evaluationdatatypes import EvaluatableData

default_test_format: EdifactFormat = EdifactFormat.UTILMD
#: the default edifact format version used in the unit tests
default_test_version: EdifactFormatVersion = EdifactFormatVersion.FV2210
#: an empty EvaluatableData instance
empty_default_test_data: EvaluatableData = EvaluatableData(
    edifact_seed={}, edifact_format=default_test_format, edifact_format_version=default_test_version
)


def return_empty_dummy_evaluatable_data():
    return empty_default_test_data
