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


def get_holiday_calendar_from_timestamps(timestamps: Iterable[pd.Timestamp], name: Optional[str] = None) -> HolidayCalendar:
    """
    Return a calendar with the given holidays.
    """
    rules = [Holiday(name, year=ts.year, month=ts.month, day=ts.day) for ts in timestamps]
    return HolidayCalendar(rules=rules)


class DayOfWeekPeriodicHoliday(Holiday):
    """
        A holiday that occurs on a specific day of the week and repeats weekly.
    """

    def __init__(
        self,
        name,
        day_of_week: int,
        start_date=None,
        end_date=None,
    ):
        super().__init__(
            name,
            None,
            None,
            None,
            None,
            None,
            start_date,
            end_date,
            None,
        )
        self.day_of_week = day_of_week

    def dates(self, start_date, end_date, return_name=False):
        """
        Return a list of dates on which this holiday occurs between start_date and end_date.
        """
        # Get the first date larger or equal to start_date where the day of the week is the same as day_of_week.
        first = start_date + pd.Timedelta(days=(self.day_of_week - start_date.dayofweek) % 7)
        # Get the last date smaller or equal to end_date where the day of the week is the same as day_of_week.
        last = end_date - pd.Timedelta(days=(end_date.dayofweek - self.day_of_week) % 7)
        # Get the number of weeks between first and last.
        num_weeks = (last - first).days // 7
        # Create a pandas DateTimeIndex with the dates of the holidays.
        dates = pd.date_range(start=first, end=last, freq=timedelta(days=7))
        # Return the dates.
        return dates.to_series()


def get_holiday_calendar_from_day_of_week(day_of_week: int, name: Optional[str] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each day of the week.
    """
    rules = [DayOfWeekPeriodicHoliday(name, day_of_week)]
    return HolidayCalendar(rules=rules)


def merge_all_special_days(exchange_calendar: ExchangeCalendar) -> HolidayCalendar:
    """
    Return a calendar with all special days from the given exchange calendar.
    """
    holiday_calendars = []

    # Add regular holidays.
    holiday_calendars.append(exchange_calendar.regular_holidays)

    # Add ad-hoc holidays.
    holiday_calendars.append(get_holiday_calendar_from_timestamps(exchange_calendar.adhoc_holidays))

    # Add regular special open days.
    for item in exchange_calendar.special_opens:
        _, definition = item
        if isinstance(definition, HolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition))

    # Add ad-hoc special opens.
    for item in exchange_calendar.special_opens_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition))

    # Add regular special close days.
    for item in exchange_calendar.special_closes:
        _, definition = item
        if isinstance(definition, HolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition))

    # Add ad-hoc special closes.
    for item in exchange_calendar.special_closes_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition))

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return reduce(lambda x, y: x.merge(y), holiday_calendars)
