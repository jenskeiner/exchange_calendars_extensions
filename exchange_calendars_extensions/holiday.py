from datetime import timedelta
from typing import Optional, Callable

import pandas as pd
from exchange_calendars.pandas_extensions.holiday import Holiday

from exchange_calendars_extensions.offset import LastDayOfMonthOffsetClasses, \
    ThirdDayOfWeekInMonthOffsetClasses


def get_monthly_expiry_holiday(
        name: str,
        day_of_week: int,
        month: int,
        observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None,
        start_date=None,
        end_date=None,
        tz=None) -> Holiday:
    """
    Return a holiday that occurs yearly on the third day of the week in the given month.
    :param name: The name of the holiday.
    :param day_of_week: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
    :param month: 1 = January, 2 = February, ..., 12 = December.
    :param observance: A function that takes a datetime and returns a datetime.
    :param start_date: The first date on which this holiday is valid.
    :param end_date: The last date on which this holiday is valid.
    :param tz: The timezone in which to interpret the holiday.
    :return: A Holiday object.
    """
    return Holiday(name, month=1, day=1,
                   offset=ThirdDayOfWeekInMonthOffsetClasses[day_of_week][month](),
                   observance=observance, start_date=start_date, end_date=end_date, tz=tz)


def get_last_day_of_month_holiday(
        name: str,
        month: int,
        observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None,
        start_date=None,
        end_date=None,
        tz=None) -> Holiday:
    """
    Return a holiday that occurs yearly on the last day of the given month.
    :param name: The name of the holiday.
    :param month: 1 = January, 2 = February, ..., 12 = December.
    :param observance: A function that takes a datetime and returns a datetime.
    :param start_date: The first date on which this holiday is valid.
    :param end_date: The last date on which this holiday is valid.
    :param tz: The timezone in which to interpret the holiday.
    :return: A Holiday object.
    """
    return Holiday(name, month=1, day=1,
                   offset=LastDayOfMonthOffsetClasses[month](),
                   observance=observance, start_date=start_date, end_date=end_date, tz=tz)


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
        tz=None
    ):
        """
        Constructor.
        :param name: Name of holiday.
        :param day_of_week: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
        :param start_date: The first date on which this holiday is valid.
        :param end_date: The last date on which this holiday is valid.
        """
        super().__init__(
            name,
            year=None,
            month=None,
            day=None,
            offset=None,
            observance=None,
            start_date=start_date,
            end_date=end_date,
            days_of_week=None,
            tz=tz
        )
        self.day_of_week = day_of_week

    def _dates(self, start_date, end_date):
        """
        Return a list of dates on which this holiday occurs between start_date and end_date.
        """
        # Determine effective start date.
        if self.start_date is not None:
            start_date = max(start_date, self.start_date.tz_localize(start_date.tz))

        # Determine effective end date.
        if self.end_date is not None:
            end_date = min(end_date, self.end_date.tz_localize(end_date.tz))

        if start_date > end_date:
            return pd.DatetimeIndex([])

        # Get the first date larger or equal to start_date where the day of the week is the same as day_of_week.
        first = start_date + pd.Timedelta(days=(self.day_of_week - start_date.dayofweek) % 7)

        if first > end_date:
            return pd.DatetimeIndex([])

        # Get the last date smaller or equal to end_date where the day of the week is the same as day_of_week.
        last = end_date - pd.Timedelta(days=(end_date.dayofweek - self.day_of_week) % 7)

        # Create a pandas DateTimeIndex with the dates of the holidays.
        dates = pd.date_range(start=first, end=last, freq=timedelta(days=7))

        # Return the dates.
        return dates

    def dates(self, start_date, end_date, return_name=False):
        # Get DateTimeIndex with the dates of the holidays.
        dates = self._dates(start_date, end_date)

        return pd.Series(self.name, index=dates, dtype=pd.DatetimeTZDtype) if return_name else dates
