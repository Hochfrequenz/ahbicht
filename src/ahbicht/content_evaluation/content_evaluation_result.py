"""
This module contains a class to store _all_ kinds of content evaluation results.
"""
from itertools import combinations, product
from typing import Dict, List, Optional
from uuid import UUID

import attr
from marshmallow import Schema, fields, post_load

from ahbicht.expressions.condition_nodes import (
    ConditionFulfilledValue,
    EvaluatedFormatConstraint,
    EvaluatedFormatConstraintSchema,
)

# pylint: disable=too-few-public-methods, no-self-use, unused-argument


@attr.s(auto_attribs=True)
class ContentEvaluationResult:
    """
    A class that holds the results of a full content evaluation (meaning all hints, requirement constraints and
    format constraints have been evaluated)
    """

    hints: Dict[str, Optional[str]]  #: maps the key of a hint (e.g. "501" to a hint text)
    format_constraints: Dict[
        str, EvaluatedFormatConstraint
    ]  #: maps the key of a format constraint to the respective evaluation result
    requirement_constraints: Dict[
        str, ConditionFulfilledValue
    ]  #: maps the key of a requirement_constraint to the respective evaluation result
    id: Optional[UUID] = None  #: optional guid


class ContentEvaluationResultSchema(Schema):
    """
    A schema to (de)serialize ContentEvaluationResults
    """

    hints = fields.Dict(keys=fields.String(allow_none=False), values=fields.String(allow_none=True), required=True)
    format_constraints = fields.Dict(
        keys=fields.String(allow_none=False),
        values=fields.Nested(EvaluatedFormatConstraintSchema, allow_none=False, required=True),
        required=True,
    )
    requirement_constraints = fields.Dict(
        keys=fields.String(allow_none=False), values=fields.String(allow_none=True), required=True
    )
    id = fields.UUID(required=False, dump_default=False, missing=None)

    @post_load
    def deserialize(self, data, **kwargs) -> ContentEvaluationResult:
        """
        Converts the barely typed data dictionary into an actual ContentEvaluationResult

        :param data:
        :param kwargs:
        :return:
        """
        result = ContentEvaluationResult(**data)
        for rc_key, rc_value in result.requirement_constraints.items():
            if not isinstance(rc_value, ConditionFulfilledValue):
                for enum_value in ConditionFulfilledValue:
                    if str(rc_value).upper() == enum_value.value:
                        result.requirement_constraints[rc_key] = ConditionFulfilledValue(enum_value.value)
                        break
        return result


@attr.s(auto_attribs=True)
class ContentEvaluationPrerequisites:
    """
    For expressions (that do not contain any unresolved package) it's possible to pre-generate all possible outcomes of
    a content evaluation. ContentEvaluationPrerequisites are the answer to the question:
    'Which information do I need to provide in a ContentEvaluationResult in order to evaluation a given expression?'
    """

    hint_keys: List[str]  #: list of keys for which you'll need to provide hint texts in a ContentEvaluationResult
    format_constraint_keys: List[str]  #: list of keys for which you'll need to provide EvaluatedFormatConstraints
    requirement_constraint_keys: List[str]  #: list of keys for which you'll need to provide ConditionFulfilledValues
    package_keys: List[str]  #: list of packages that need to be resolved (additionally)

    def _remove_duplicates(self) -> None:
        """
        remove duplicates from all lists
        """
        self.hint_keys = [*set(self.hint_keys)]
        self.format_constraint_keys = [*set(self.format_constraint_keys)]
        self.requirement_constraint_keys = [*set(self.requirement_constraint_keys)]
        self.package_keys = [*set(self.package_keys)]

    def _sort_keys(self) -> None:
        """
        sort the keys in all lists in ascending order
        """
        self.hint_keys.sort(key=int)
        self.format_constraint_keys.sort(key=int)
        self.requirement_constraint_keys.sort(key=int)
        self.package_keys.sort()

    def sanitize(self) -> None:
        """
        Sanitize the result (remove duplicates, sort keys)
        """
        self._remove_duplicates()
        self._sort_keys()

    def generate_possible_content_evaluation_results(self) -> List[ContentEvaluationResult]:
        """
        A prerequisite allows to generate nearly all possible content evaluation results, except for hints, error
        messages, resolving packages.
        """
        results: List[ContentEvaluationResult] = []
        if len(self.format_constraint_keys) == 0 and len(self.requirement_constraint_keys) == 0:
            return results
        # for easier debugging below, replace the generators "(" with a materialized lists "["
        if len(self.format_constraint_keys) > 0:
            possible_fcs = (
                z
                for z in combinations(
                    product(self.format_constraint_keys, [True, False]), len(self.format_constraint_keys)
                )
                if len({y[0] for y in z}) == len(self.format_constraint_keys)
            )
        else:
            possible_fcs = [(("fc_dummy", True),)]  # type:ignore[assignment]

        if len(self.requirement_constraint_keys) > 0:
            possible_rcs = (
                z
                for z in combinations(
                    product(self.requirement_constraint_keys, ConditionFulfilledValue),
                    len(self.requirement_constraint_keys),
                )
                if len({y[0] for y in z}) == len(self.requirement_constraint_keys)
            )
        else:
            possible_rcs = [(("rc_dummy", ConditionFulfilledValue.NEUTRAL),)]  # type:ignore[assignment]
        for fc_rc_tuple in product(possible_fcs, possible_rcs):
            # This product would have length 0 if one of the "factors" had length 0.
            # In order to prevent 'results' to be empty if either the RC or FC list is empty, we added the the 'dummy's.
            result = ContentEvaluationResult(
                hints={hint_key: f"Hinweis {hint_key}" for hint_key in self.hint_keys},
                format_constraints={
                    fc_kvp[0]: EvaluatedFormatConstraint(format_constraint_fulfilled=fc_kvp[1])
                    for fc_kvp in fc_rc_tuple[0]
                    if fc_kvp[0] != "fc_dummy"
                },
                requirement_constraints={rc_kvp[0]: rc_kvp[1] for rc_kvp in fc_rc_tuple[1] if rc_kvp[0] != "rc_dummy"},
            )
            results.append(result)
        return results


class ContentEvaluationPrerequisitesSchema(Schema):
    """
    A schema to (de)serialize ContentEvaluationPrerequisites
    """

    hint_keys = fields.List(fields.String())
    format_constraint_keys = fields.List(fields.String())
    requirement_constraint_keys = fields.List(fields.String())
    package_keys = fields.List(fields.String())

    @post_load
    def deserialize(self, data, **kwargs) -> ContentEvaluationPrerequisites:
        """
        Converts the barely typed data dictionary into an actual ContentEvaluationPrerequisites
        """
        return ContentEvaluationPrerequisites(**data)
