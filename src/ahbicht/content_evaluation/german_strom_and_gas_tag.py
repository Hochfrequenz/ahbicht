"""
A module to evaluate datetimes and whether they are "on the edge" of a German "Stromtag" or "Gastag" respectively.
"""
from datetime import datetime, time

# The problem with the stdlib zoneinfo is, that the availability of timezones via ZoneInfo(zone_key) depends on the OS
# and system on which you're running it. In some cases "Europe/Berlin" might be available, but generally it's not,
# and it's PITA to manually define timezones. So we're using pytz as a datasource for timezone information.
from pytz import timezone

berlin = timezone("Europe/Berlin")


def _get_german_local_time(date_time: datetime) -> time:
    """
    returns the current german local time for the given datetime object
    """
    german_local_datetime = date_time.astimezone(berlin)
    return german_local_datetime.time()


# the functions below are excessively unit tested; Please add a test case if you suspect their behaviour to be wrong


def is_stromtag_limit(date_time: datetime) -> bool:  # the name is not as speaking as I'd like it to be
    """
    Returns true if and only if the given datetime dt is the inclusive start/exclusive end of a german "Stromtag".
    The "Stromtag" is the balancing relevant day in the German electricity market. It starts and ends at midnight in
    German local time which can be either 23PM or 22PM in UTC (depending on the daylight saving time in Germany).
    """
    german_local_time = _get_german_local_time(date_time)
    return german_local_time.hour == 0 and german_local_time.minute == 0 and german_local_time.second == 0


def is_gastag_limit(date_time: datetime) -> bool:  # the name is not as speaking as I'd like it to be
    """
    Returns true if and only if the given datetime dt is the inclusive start/exclusive end of a german "Gastag".
    The "Gastag" is the balancing relevant day in the German gas market. It starts and ends at 6am in German local time
    which can be either 4AM or 5AM in UTC (depending on the daylight saving time in Germany).
    """
    german_local_time = _get_german_local_time(date_time)
    return german_local_time.hour == 6 and german_local_time.minute == 0 and german_local_time.second == 0
