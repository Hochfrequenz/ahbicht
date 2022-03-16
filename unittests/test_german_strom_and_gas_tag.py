"""
Tests the evaluation of the start/end of a German Strom- or Gastag.
"""
from datetime import datetime, timedelta, timezone

import pytest  # type:ignore[import]

from ahbicht.content_evaluation.german_strom_and_gas_tag import (
    _parse_as_datetime,
    berlin,
    is_gastag_limit,
    is_stromtag_limit,
)


class TestGermanStromAndGasTag:
    @pytest.mark.parametrize(
        "dt_string, expected_datetime",
        [
            pytest.param(
                "2019-12-31T23:00:00+01:00", datetime(2019, 12, 31, 23, 0, 0, tzinfo=timezone(timedelta(seconds=3600)))
            ),
            pytest.param("2022-01-01T00:00:00+00:00", datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
            pytest.param("2022-01-01T00:00:00Z", datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
            pytest.param("2021-12-31T23:00:00-01:00", datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
        ],
    )
    def test_successful_parsing(self, dt_string: str, expected_datetime: datetime):
        actual, error = _parse_as_datetime(dt_string)
        assert error is None
        assert actual == expected_datetime

    @pytest.mark.parametrize(
        "dt_string, expected_error_msg",
        [
            pytest.param("2019-12-31T00:00:00", "Neither offset nor timezone was given"),
            pytest.param("2019-12-31T25:00:00+00:00", "hour must be in 0..23"),
            pytest.param("foo", "Invalid isoformat string"),
            pytest.param("", "empty or None"),
        ],
    )
    def test_errornous_parsing(self, dt_string: str, expected_error_msg: str):
        actual, error = _parse_as_datetime(dt_string)
        assert actual is None
        assert error is not None
        assert error.format_constraint_fulfilled is False
        assert expected_error_msg in error.error_message  # type:ignore[operator]

    @pytest.mark.parametrize(
        "dt, expected_is_start_or_end_of_german_stromtag",
        [
            pytest.param(datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2019, 12, 31, 23, 0, 0, tzinfo=timezone.utc), True),
            pytest.param(datetime(2019, 12, 31, 22, 0, 0, tzinfo=timezone.utc), False),
            pytest.param(datetime(2010, 1, 1, 0, 0, 0, tzinfo=berlin), True),
            pytest.param(datetime(2010, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(seconds=3600))), True),
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
            pytest.param(datetime.fromisoformat("2022-10-29T12:00:00-10:00"), True, id="Hawaii, German DST"),
            pytest.param(datetime.fromisoformat("2022-10-30T13:00:00-10:00"), True, id="Hawaii, German standard time"),
            pytest.param(datetime.fromisoformat("2022-10-30T07:00:00+09:00"), True, id="Tokyo, German DST"),
            pytest.param(datetime.fromisoformat("2022-10-31T08:00:00+09:00"), True, id="Tokyo, German standard time"),
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
            pytest.param(datetime.fromisoformat("2022-10-29T19:00:00-10:00"), True, id="Hawaii, German DST"),
            pytest.param(datetime.fromisoformat("2022-10-30T19:00:00-10:00"), True, id="Hawaii, German standard time"),
            pytest.param(datetime.fromisoformat("2022-10-29T09:45:00+05:45"), True, id="Nepal, German DST"),
            pytest.param(datetime.fromisoformat("2022-10-30T10:45:00+05:45"), True, id="Nepal, German standard time 1"),
            pytest.param(datetime.fromisoformat("2022-10-31T10:45:00+05:45"), True, id="Nepal, German standard time 2"),
        ],
    )
    def test_gastag(self, dt: datetime, expected_is_start_or_end_of_german_gastag: bool):
        actual = is_gastag_limit(dt)
        assert actual == expected_is_start_or_end_of_german_gastag
