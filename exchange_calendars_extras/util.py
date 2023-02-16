from datetime import timedelta
from functools import reduce
from typing import Iterable, Optional
from datetime import date

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


def third_day_of_week_in_month(day_of_week: int, month: int, year: int) -> date:
    """
    Return the third given day of the week in the given month and year.

    :param day_of_week: the day of the week, must be an integer between 0 (Monday) and 6 (Sunday).
    :param year: the year, must be an integer
    :param month: the month of the year, must be an integer between (inclusive) 1 and 12
    :return: the datetime.date representing the third Friday in the given month.
    """
    # The third given day in a month cannot be earlier than the 15th.
    third = date(year, month, 15)

    # Get day of week.
    w = third.weekday()

    # Adjust if necessary.
    if w != day_of_week:
        # Replace just the day of the month, adding a number of days, so that the day of the week is correct.
        third = third.replace(day=(15 + (day_of_week - w) % 7))
    return third
