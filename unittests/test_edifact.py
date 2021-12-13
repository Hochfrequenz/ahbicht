from typing import Optional, Tuple

import pytest  # type:ignore[import]

from ahbicht.edifact import EdifactFormat, pruefidentifikator_to_format


class TestEdifact:
    """
    Tests the edifact module
    """

    @pytest.mark.parametrize(
        "expectation_tuple",
        [
            ("11042", EdifactFormat.UTILMD),
            ("13002", EdifactFormat.MSCONS),
            ("25001", EdifactFormat.UTILTS),
            ("10000", None),
        ],
    )
    def test_pruefi_to_format(self, expectation_tuple: Tuple[str, EdifactFormat]):
        """
        Tests that the prüfis can be mapped to an EDIFACT format
        """
        assert pruefidentifikator_to_format(expectation_tuple[0]) == expectation_tuple[1]

    @pytest.mark.parametrize(
        "illegal_pruefi",
        [None, "", "asdas", "01234"],
    )
    def test_illegal_pruefis(self, illegal_pruefi: Optional[str]):
        """
        Test that illegal pruefis are not accepted
        :return:
        """
        with pytest.raises(ValueError):
            pruefidentifikator_to_format(illegal_pruefi)  # type:ignore[arg-type] # ok, because this raises an error
