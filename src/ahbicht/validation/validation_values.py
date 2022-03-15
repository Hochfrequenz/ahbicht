"""This module contains the enums for the possible validation values."""

from enum import Enum


class RequirementValidationValue(str, Enum):
    """
    Possible values to describe the state of the validation
    in the requirement_validation attribute of the ValidationResult.
    The values without "AND_EMPTY" or "AND_FILLED" is for segment_level
    due to no value that could be filled or empty.
    It's easier to put all of them in one Enum for the ValidationResult class.
    """

    IS_REQUIRED = "IS_REQUIRED"  #: element is required
    IS_FORBIDDEN = "IS_FORBIDDEN"  #: element is forbidden
    IS_OPTIONAL = "IS_OPTIONAL"  #: element is optional
    IS_REQUIRED_AND_EMPTY = "IS_REQUIRED_AND_EMPTY"  #: field is required, but empty
    IS_REQUIRED_AND_FILLED = "IS_REQUIRED_AND_FILLED"  #: field is required and filled
    IS_FORBIDDEN_AND_EMPTY = "IS_FORBIDDEN_AND_EMPTY"  #: field is forbidden and empty
    IS_FORBIDDEN_AND_FILLED = "IS_FORBIDDEN_AND_FILLED"  #: field is forbidden, but filled
    IS_OPTIONAL_AND_EMPTY = "IS_OPTIONAL_AND_EMPTY"  #: field is optional and empty
    IS_OPTIONAL_AND_FILLED = "IS_OPTIONAL_AND_FILLED"  #: field is optional and filled

    def __str__(self):
        return self.value
