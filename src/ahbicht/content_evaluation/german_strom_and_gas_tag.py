"""
A module to evaluate datetimes and whether they are "on the edge" of a German "Stromtag" or "Gastag" respectively
"""

import re
from datetime import datetime, time, timedelta
from datetime import timezone as tz
from enum import StrEnum
from typing import Callable, Literal, Optional, Tuple, Union

# The problem with the stdlib zoneinfo is, that the availability of timezones via ZoneInfo(zone_key) depends on the OS
# and system on which you're running it. In some cases "Europe/Berlin" might be available, but generally it's not,
# and it's PITA to manually define timezones. So we're using pytz as a datasource for timezone information.
from pytz import timezone, utc

from ahbicht.models.condition_nodes import EvaluatedFormatConstraint

berlin = timezone("Europe/Berlin")


class EdiFactDateTimeFormat(StrEnum):
    """
    EDIFACT time strings.
    """

    CCYY = "CCYY"
    CCYYMM = "CCYYMM"
    CCYYMMDD = "CCYYMMDD"
    CCYYMMDDHHMM = "CCYYMMDDHHMM"
    CCYYMMDDHHMMSS = "CCYYMMDDHHMMSS"
    CCYYMMDDHHMMZZZ = "CCYYMMDDHHMMZZZ"
    CCYYMMDDHHMMSSZZZ = "CCYYMMDDHHMMSSZZZ"
    MM = "MM"
    ZZRB = "ZZRB"
    MMWWMMWW = "MMWWMMWW"
    MMDD = "MMDD"


def _is_edifact_time_str(time_str):
    if len(time_str) == 2:
        return time_str.isdigit()
    return time_str[:-3].isdigit()


def _is_edifact_time_str_convertible_to_datetime(time_str: str) -> tuple[bool, Optional[EdiFactDateTimeFormat]]:
    """
    Checks wheter EDIFACT time string can be converted to datetime.
    """
    edifact_time_format: Optional[EdiFactDateTimeFormat] = None
    if len(time_str) == 2:  # 802 Monat erlaubt: 1, 3, 6, 12
        edifact_time_format = EdiFactDateTimeFormat.MM
    elif len(time_str) == 4 and EDIFACT_TIME_QUANTITY_REGEX.match(time_str):  # Z01 ZZRB
        edifact_time_format = EdiFactDateTimeFormat.ZZRB
    elif len(time_str) == 4 and int(time_str[:2]) < 12:  # 106 MMDD -> UTILMDS
        edifact_time_format = EdiFactDateTimeFormat.MMDD
    elif len(time_str) == 4:  # 602 CCYY
        edifact_time_format = EdiFactDateTimeFormat.CCYY
    elif len(time_str) == 6:  # 610 CCYYMM
        edifact_time_format = EdiFactDateTimeFormat.CCYYMM
    elif len(time_str) == 8 and int(time_str[:2]) < 12:  # 104 MMWWMMWW
        edifact_time_format = EdiFactDateTimeFormat.MMWWMMWW
    return edifact_time_format is None, edifact_time_format


def _get_german_local_time(date_time: datetime) -> time:
    """
    returns the current german local time for the given datetime object
    """
    german_local_datetime = date_time.astimezone(berlin)
    return german_local_datetime.time()


EDIFACT_DATETIME_REGEX = re.compile(
    r"^(?P<year>\d{4})?(?P<month>\d{2})?(?P<day>\d{2})?(?P<hour>\d{2})?"
    r"(?P<minute>\d{2})?(?P<second>\d{2})?(?P<timezone>[+-]\d{2})?$"
)
EDIFACT_TIME_QUANTITY_REGEX = re.compile(r"^(?P<quantity>\d{2})(?P<unit>[TWM])(?P<reference>[MQHJTR])$")


# the functions below are excessively unit tested; Please add a test case if you suspect their behaviour to be wrong
def parse_as_datetime(entered_input: str) -> Tuple[Optional[datetime], Optional[EvaluatedFormatConstraint]]:
    """
    Try to parse the given entered_input as datetime
    :param entered_input: a string
    :return: A tuple with the first item being a datetime if parsing was successful or the second item being
    an (erroneous) EvaluatedFormatConstraint if the parsing was not successful.
    """
    if not entered_input:
        return None, EvaluatedFormatConstraint(
            format_constraint_fulfilled=False,
            error_message="An empty or None string cannot be parsed as datetime",
        )
    try:
        if entered_input.endswith("Z"):
            entered_input = entered_input.replace("Z", "+00:00")

        # look if the input could be a strict EDIFACT datetime (i.e. something like 202201010000+00)
        if _is_edifact_time_str(entered_input):
            is_convertible, edi_time_format = _is_edifact_time_str_convertible_to_datetime(entered_input)
            if not is_convertible:
                return None, EvaluatedFormatConstraint(
                    format_constraint_fulfilled=False,
                    error_message=f"EDIFACT time string cannot be parsed as datetime {entered_input}"
                    f" as it is of format {edi_time_format}.",
                )
            edifact_datetime_match = EDIFACT_DATETIME_REGEX.match(entered_input)
            if edifact_datetime_match is not None:
                groups = {
                    key: int(value)
                    for key, value in edifact_datetime_match.groupdict().items()
                    if value is not None and key != "timezone"
                }
                offset = edifact_datetime_match.groupdict().get("timezone", None)
                result = datetime(**groups, tzinfo=None if offset is None else tz(timedelta(hours=int(offset))))
            else:
                return None, EvaluatedFormatConstraint(
                    format_constraint_fulfilled=False, error_message="Could not parse EDIFACT datetime"
                )  # should not happen
        else:
            result = datetime.fromisoformat(entered_input)
        if result.tzinfo is None:
            # If tzinfo is none the datetime is "naive" = not aware of its timezone.
            # We don't want naive datetimes because they are the root of all evil.
            return None, EvaluatedFormatConstraint(
                format_constraint_fulfilled=False,
                error_message=f"Neither offset nor timezone was given: '{entered_input}'",
            )
        return result, None
    except ValueError as value_error:
        return None, EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message=str(value_error))


def has_no_utc_offset(entered_input: str) -> EvaluatedFormatConstraint:
    """
    returns true if and only if entered_input is parsable as date time with explicit offset which has no UTC offset.
    This means the UTC offset is exactly "+00:00".
    """
    # the name of the method contains a negation because this it's commonly like this in the BDEW format constraints.
    date_time, error_result = parse_as_datetime(entered_input)
    if error_result is not None:
        return error_result
    original_time = date_time.time()  # type:ignore[union-attr]
    utc_time = date_time.astimezone(tz=utc).time()  # type:ignore[union-attr]
    if utc_time == original_time and utc_time.hour == 0 and utc_time.minute == 0 and utc_time.second == 0:
        return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)
    error_message = f"The provided date time '{entered_input}' has a UTC offset of {utc_time}."
    return EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message=error_message)


def is_stromtag_limit(date_time: datetime) -> bool:  # the name is not as speaking as I'd like it to be
    """
    Returns true if and only if the given date_time is the inclusive start/exclusive end of a german "Stromtag".
    The "Stromtag" is the balancing relevant day in the German electricity market. It starts and ends at midnight in
    German local time which can be either 23PM or 22PM in UTC (depending on the daylight saving time in Germany).
    """
    german_local_time = _get_german_local_time(date_time)
    return german_local_time.hour == 0 and german_local_time.minute == 0 and german_local_time.second == 0


def is_gastag_limit(date_time: datetime) -> bool:  # the name is not as speaking as I'd like it to be
    """
    Returns true if and only if the given date_time is the inclusive start/exclusive end of a german "Gastag".
    The "Gastag" is the balancing relevant day in the German gas market. It starts and ends at 6am in German local time
    which can be either 4AM or 5AM in UTC (depending on the daylight saving time in Germany).
    """
    german_local_time = _get_german_local_time(date_time)
    return german_local_time.hour == 6 and german_local_time.minute == 0 and german_local_time.second == 0


def is_xtag_limit(entered_input: str, division: Union[Literal["Strom"], Literal["Gas"]]) -> EvaluatedFormatConstraint:
    """
    Tries to parse the entered_input as datetime and checks if it is the start/end of a Strom- or Gastag
    """
    date_time, error_result = parse_as_datetime(entered_input)
    if error_result is not None:
        return error_result
    xtag_evaluator: Callable[[datetime], bool]
    if division == "Strom":
        xtag_evaluator = is_stromtag_limit
    elif division == "Gas":
        xtag_evaluator = is_gastag_limit
    else:
        raise NotImplementedError(f"The division must either be 'Strom' or 'Gas': '{division}'")
    if xtag_evaluator(date_time):  # type:ignore[arg-type]
        return EvaluatedFormatConstraint(format_constraint_fulfilled=True, error_message=None)
    error_message = (
        f"The given datetime '{date_time.isoformat()}' is not the limit of a {division}tag"  # type:ignore[union-attr]
    )
    return EvaluatedFormatConstraint(format_constraint_fulfilled=False, error_message=error_message)
