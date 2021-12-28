"""
Contains the CategorizedKeyExtract and a schema for (de)serialization.
"""

from itertools import combinations, product
from typing import List

import attr
from marshmallow import Schema, fields, post_load

from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResult
from ahbicht.expressions.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint


# pylint: disable=too-few-public-methods, no-self-use, unused-argument
@attr.s(auto_attribs=True)
class CategorizedKeyExtract:
    """
    A Categorized Key Extract contains those condition keys that are contained inside an expression.
    For expressions (that do not contain any unresolved package) it's possible to pre-generate all possible outcomes of
    a content evaluation. CategorizedKeyExtract is also the answer to the question:
    'Which information do I need to provide in a ContentEvaluationResult in order to evaluate a given expression?'
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
        A categorized key extract allows to generate nearly all possible content evaluation results,
        except for hints, error messages, resolving packages.
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
                # y[0] is the key (and y[1] is the value (true/false))
                # We only want those combinations where the number of distinct keys == the number of keys present.
                # To better understand this, try evaluating the following expression in your debugger:
                #   list(combinations(product(["A", "B", "C"], [True, False]), len(["A", "B", "C"])))
                # In this (unfiltered) result, you'll find entries with the keys: ('A', 'A', 'B') or ('A', 'B', 'B').
                # These artefacts will be removed with the following if. Only the ('A', 'B', 'C') entries will pass.
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
                # kvp is short for key value pair
                format_constraints={
                    fc_kvp[0]: EvaluatedFormatConstraint(format_constraint_fulfilled=fc_kvp[1])
                    for fc_kvp in fc_rc_tuple[0]
                    if fc_kvp[0] != "fc_dummy"
                },
                requirement_constraints={rc_kvp[0]: rc_kvp[1] for rc_kvp in fc_rc_tuple[1] if rc_kvp[0] != "rc_dummy"},
            )
            results.append(result)
        return results


class CategorizedKeyExtractSchema(Schema):
    """
    A schema to (de)serialize CategorizedKeyExtractSchema
    """

    hint_keys = fields.List(fields.String())
    format_constraint_keys = fields.List(fields.String())
    requirement_constraint_keys = fields.List(fields.String())
    package_keys = fields.List(fields.String())

    @post_load
    def deserialize(self, data, **kwargs) -> CategorizedKeyExtract:
        """
        Converts the barely typed data dictionary into an actual CategorizedKeyExtractSchema
        """
        return CategorizedKeyExtract(**data)
