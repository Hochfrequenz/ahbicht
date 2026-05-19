"""
A module to allow easy distinction between different types of condition nodes (by mapping their integer key)
"""

import re

from ahbicht.models.condition_node_type import ConditionNodeType

REGEX_PACKAGE_REPEATABILITY = re.compile(r"^(?P<n>\d+)\.\.(?P<m>\d+|n)$")

PACKAGE_1P_RC_KEY: str = "9999"
"""
A special, hardcoded condition key that is used when resolving the package '1P'.

Background:
Package '1P' is an empty dummy-package that should always evaluate as FULFILLED (RC_FULFILLED).
Unlike other packages (e.g. '2P', '3P', ...) which are resolved dynamically via a PackageResolver that maps
package keys to condition expressions, '1P' is treated as a special case and directly converted to a
requirement constraint that is always fulfilled.

Why we chose this approach:

1. Requirement constraint condition keys are normally in the range 1-499 (as defined by EDI@Energy
   "Allgemeine Festlegungen").
2. We cannot use any key in the 1-499 range because those keys may already be taken by actual
   requirement constraints defined in the AHB documents. Using an existing key would cause conflicts.
3. By using 9999 (a number well outside all defined ranges), we ensure no collision with any existing
   condition keys while still being able to leverage the existing RC infrastructure.
4. This constant is used in multiple places: in derive_condition_node_type() to recognize 9999 as a
   REQUIREMENT_CONSTRAINT type, in PackageExpansionTransformer to resolve '1P' to this key, and in
   RcEvaluator implementations to always return FULFILLED for this key.
"""


def derive_condition_node_type(condition_key: str) -> ConditionNodeType:
    """
    Returns the corresponding type of condition node for a given condition key
    """
    if condition_key.endswith("P"):
        return ConditionNodeType.PACKAGE
    match = REGEX_PACKAGE_REPEATABILITY.match(condition_key)
    if match:
        return ConditionNodeType.PACKAGE_REPEATABILITY
    if 1 <= int(condition_key) <= 499:
        return ConditionNodeType.REQUIREMENT_CONSTRAINT
    if condition_key == PACKAGE_1P_RC_KEY:
        # condition_key == PACKAGE_1P_RC_KEY (9999) is a special case for package '1P'.
        # See the docstring of PACKAGE_1P_RC_KEY for details.
        return ConditionNodeType.REQUIREMENT_CONSTRAINT
    if 500 <= int(condition_key) <= 900:
        return ConditionNodeType.HINT
    if 901 <= int(condition_key) <= 999:
        return ConditionNodeType.FORMAT_CONSTRAINT
    if 2000 <= int(condition_key) <= 2499:
        return ConditionNodeType.REPEATABILITY_CONSTRAINT
    raise ValueError("Condition key is not in valid number range.")
