"""This module contains the enums for the possible validation values."""

from enum import Enum


class RequirementValidationValue(str, Enum):
    """
    Possible values to describe the state of the validation
    in the requirement_validation attribute of the ValidationResult.
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


# class RequirementValidationValue(str, Enum):
#     """
#     Possible values to describe the state of the validation
#     in the requirement_validation attribute of the ValidationResult.
#     """

#     IS_REQUIRED = "IS_REQUIRED"  #: element is required
#     IS_FORBIDDEN = "IS_FORBIDDEN"  #: element is forbidden
#     IS_OPTIONAL = "IS_OPTIONAL"  #: element is optional

#     def __str__(self):
#         return self.value


class FormatValidationValue(str, Enum):
    """
    Possible values to describe the state of the validation
    in the format_validation attribute of the ValidationResult.
    """

    #: format constraints are fullfilled
    FORMAT_CONSTRAINTS_ARE_FULFILLED = "FORMAT_CONSTRAINTS_ARE_FULFILLED"
    #: format constraints are not fullfilled
    FORMAT_CONSTRAINTS_ARE_NOT_FULFILLED = "FORMAT_CONSTRAINTS_ARE_NOT_FULFILLED"

    def __str__(self):
        return self.value
