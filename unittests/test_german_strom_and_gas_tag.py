"""
Tests the evaluation of the start/end of a German Strom- or Gastag.
"""
from datetime import datetime, timezone

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.german_strom_and_gas_tag import is_gastag_limit, is_stromtag_limit


class TestGermanStromAndGasTag:
    @pytest.mark.parametrize(
        "dt, expected_is_start_or_end_of_german_stromtag",
        [
            pytest.param(datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2019, 12, 31, 23, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime(2019, 12, 31, 22, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2022, 3, 26, 23, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-03-27T00:00:00+01:00"), True),
            pytest.param(datetime.fromisoformat("2022-03-27T00:00:00+02:00"), False),
            pytest.param(datetime(2022, 3, 27, 22, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-03-28T00:00:00+02:00"), True),
            pytest.param(datetime(2022, 10, 29, 22, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-10-30T00:00:00+02:00"), True),
            pytest.param(datetime(2022, 10, 30, 23, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-10-31T00:00:00+01:00"), True),
            pytest.param(datetime.fromisoformat("2022-10-31T00:00:00+02:00"), False),
        ],
    )
    def test_stromtag(self, dt: datetime, expected_is_start_or_end_of_german_stromtag: bool):
        actual = is_stromtag_limit(dt)
        assert actual == expected_is_start_or_end_of_german_stromtag

    @pytest.mark.parametrize(
        "dt, expected_is_start_or_end_of_german_gastag",
        [
            pytest.param(datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2020, 1, 1, 5, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime(2020, 1, 1, 4, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2022, 3, 26, 5, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-03-26T06:00:00+01:00"), True),
            pytest.param(datetime.fromisoformat("2022-03-27T04:00:00+02:00"), False),
            pytest.param(datetime(2022, 3, 27, 4, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-03-27T06:00:00+02:00"), True),
            pytest.param(datetime(2022, 10, 29, 4, 0, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime.fromisoformat("2022-10-30T06:00:00+01:00"), True),
            pytest.param(datetime.fromisoformat("2022-10-30T06:00:00+02:00"), False),
        ],
    )
    def test_gastag(self, dt: datetime, expected_is_start_or_end_of_german_gastag: bool):
        actual = is_gastag_limit(dt)
        assert actual == expected_is_start_or_end_of_german_gastag
