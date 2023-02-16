from datetime import timedelta
from functools import reduce
from typing import Iterable, Optional

from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
import pandas as pd


def get_month_name(month: int):
    """
        Convert month to capitalized name of month.

        :param month: Month number (1-12).
        :return: Name of month.
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    month_name = \
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
     "December"][month - 1]

    return month_name


def get_day_of_week_name(day_of_week: int):
    """
    Convert day of week number to name.

    :param day_of_week: Day of week number (0-6), where 0 is Monday and 6 is Sunday.
    :return: Name of day of week.
    """
    if day_of_week < 0 or day_of_week > 6:
        raise ValueError("Day of week must be between 0 and 6.")

    day_of_week_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week]

    return day_of_week_name
