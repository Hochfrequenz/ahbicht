"""
Contains the CategorizedKeyExtract and a schema for (de)serialization.
"""

from itertools import combinations, product

from pydantic import BaseModel, Field, RootModel, constr

from ahbicht.models.condition_nodes import ConditionFulfilledValue, EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult


# pylint: disable=too-few-public-methods,  unused-argument
class CategorizedKeyExtract(BaseModel):
    """
    A Categorized Key Extract contains those condition keys that are contained inside an expression.
    For expressions (that do not contain any unresolved package) it's possible to pre-generate all possible outcomes of
    a content evaluation. CategorizedKeyExtract is also the answer to the question:
    'Which information do I need to provide in a ContentEvaluationResult in order to evaluate a given expression?'
    """

    #: list of keys for which you'll need to provide hint texts in a ContentEvaluationResult
    hint_keys: list[str] = Field(default_factory=list)
    #: list of keys for which you'll need to provide EvaluatedFormatConstraints
    format_constraint_keys: list[str] = Field(default_factory=list)

    #: list of keys for which you'll need to provide ConditionFulfilledValues
    requirement_constraint_keys: list[str] = Field(default_factory=list)

    # for the valid-type ignore: https://stackoverflow.com/questions/67009123/how-can-mypy-accept-pydantics-constr-types

    #: list of packages that need to be resolved (additionally)
    package_keys: list[constr(pattern=r"^\d+P$")] = Field(default_factory=list)  # type:ignore[valid-type]

    #: a list of time conditions, if present
    time_condition_keys: list[constr(pattern=r"^UB(?:1|2|3)$")] = Field(default_factory=list)  # type:ignore[valid-type]

    def _remove_duplicates(self) -> None:
        """
        remove duplicates from all lists
        """
        self.hint_keys = [*set(self.hint_keys)]
        self.format_constraint_keys = [*set(self.format_constraint_keys)]
        self.requirement_constraint_keys = [*set(self.requirement_constraint_keys)]
        self.package_keys = [*set(self.package_keys)]
        self.time_condition_keys = [*set(self.time_condition_keys)]

    def _sort_keys(self) -> None:
        """
        sort the keys in all lists in ascending order
        """
        self.hint_keys.sort(key=int)
        self.format_constraint_keys.sort(key=int)
        self.requirement_constraint_keys.sort(key=self._sort_repeat_key)
        self.package_keys.sort()
        self.time_condition_keys.sort()

    def _sort_repeat_key(self, item: str) -> tuple:
        """
        Custom sort key for requirement_constraint_keys to handle 'n..m' format.
        """
        if ".." in item:
            n, m = map(int, item.split(".."))
            return (n, m)
        return (int(item),)

    def __add__(self, other: "CategorizedKeyExtract") -> "CategorizedKeyExtract":
        """
        Joins both this and the other categorized key extract.
        The result returned contains all those keys (once) that are present in either one or both of the summands.
        Duplicates will be removed.
        :param other: another categorized key extract
        :return: a new categorized key extract with the keys from both summands (which will be left untouched)
        """
        result = CategorizedKeyExtract(
            hint_keys=self.hint_keys + other.hint_keys,
            requirement_constraint_keys=self.requirement_constraint_keys + other.requirement_constraint_keys,
            format_constraint_keys=self.format_constraint_keys + other.format_constraint_keys,
            package_keys=self.package_keys + other.package_keys,
            time_condition_keys=self.time_condition_keys + other.time_condition_keys,
        )
        result.sanitize()  # removes duplicates, sorts the keys
        return result

    def sanitize(self) -> None:
        """
        Sanitize the result (remove duplicates, sort keys)
        """
        self._remove_duplicates()
        self._sort_keys()

    def generate_possible_content_evaluation_results(self) -> list[ContentEvaluationResult]:
        """
        A categorized key extract allows generating nearly all possible content evaluation results,
        except for hints, error messages, resolving packages.
        """
        results: list[ContentEvaluationResult] = []
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
            # In order to prevent 'results' to be empty if either the RC or FC list is empty, we added the 'dummy's.
            result = ContentEvaluationResult(
                hints={hint_key: f"Hinweis {hint_key}" for hint_key in self.hint_keys},
                # kvp is short for key value pair
                format_constraints={
                    fc_kvp[0]: EvaluatedFormatConstraint(format_constraint_fulfilled=fc_kvp[1])
                    for fc_kvp in fc_rc_tuple[0]
                    if fc_kvp[0] != "fc_dummy"
                },
                requirement_constraints={rc_kvp[0]: rc_kvp[1] for rc_kvp in fc_rc_tuple[1] if rc_kvp[0] != "rc_dummy"},
                packages={},  # is always empty because looping over all packages does not make sense in this context
            )
            if any(x for x in result.requirement_constraints.values() if x == ConditionFulfilledValue.NEUTRAL):
                continue
            results.append(result)
        return results


CategorizedKeyExtracts = RootModel[list[CategorizedKeyExtract]]

__all__ = ["CategorizedKeyExtract", "CategorizedKeyExtracts"]
