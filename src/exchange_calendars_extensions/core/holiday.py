from datetime import timedelta, tzinfo
from typing import Optional, Callable, Union

import pandas as pd
from exchange_calendars.pandas_extensions.holiday import Holiday
from pandas import Series, DatetimeIndex

from exchange_calendars_extensions.core.offset import (
    LastDayOfMonthOffsetClasses,
    ThirdDayOfWeekInMonthOffsetClasses,
)


def get_monthly_expiry_holiday(
    name: str,
    day_of_week: int,
    month: int,
    observance: Union[Callable[[pd.Timestamp], pd.Timestamp], None] = None,
    start_date: Union[pd.Timestamp, None] = None,
    end_date: Union[pd.Timestamp, None] = None,
    tz: Union[tzinfo, None] = None,
) -> Holiday:
    """
    Return a holiday that occurs yearly on the third given day of the week in the given month of the year.

    For example, when day_of_week=2 and month=1, this returns a holiday that occurs yearly on the third Wednesday in
    January.

    Parameters
    ----------
    name : str
        The name of the holiday.
    day_of_week : int
        0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
    month : int
        1 = January, 2 = February, ..., 12 = December.
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        A function that takes a datetime and returns a datetime, by default None.
    start_date : Optional[pd.Timestamp], optional
        The first date on which this holiday is valid, by default None.
    end_date : Optional[pd.Timestamp], optional
        The last date on which this holiday is valid, by default None.
    tz : Optional[tzinfo], optional
        The timezone in which to interpret the holiday, by default None.

    Returns
    -------
    Holiday
        A new Holiday object as specified.
    """
    return Holiday(
        name,
        month=1,
        day=1,
        offset=ThirdDayOfWeekInMonthOffsetClasses[day_of_week][month](),
        observance=observance,
        start_date=start_date,
        end_date=end_date,
        tz=tz,
    )


def get_last_day_of_month_holiday(
    name: str,
    month: int,
    observance: Union[Callable[[pd.Timestamp], pd.Timestamp], None] = None,
    start_date: Union[pd.Timestamp, None] = None,
    end_date: Union[pd.Timestamp, None] = None,
    tz: Union[tzinfo, None] = None,
) -> Holiday:
    """
    Return a holiday that occurs yearly on the last day of the given month of the year.

    For example, when month=1, this returns a holiday that occurs yearly on the last day of January.

    Parameters
    ----------
    name : str
        The name of the holiday.
    month : int
        1 = January, 2 = February, ..., 12 = December.
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        A function that takes a datetime and returns a datetime, by default None.
    start_date : Optional[pd.Timestamp], optional
        The first date on which this holiday is valid, by default None.
    end_date : Optional[pd.Timestamp], optional
        The last date on which this holiday is valid, by default None.
    tz : Optional[tzinfo], optional
        The timezone in which to interpret the holiday, by default None.

    Returns
    -------
    Holiday
        A new Holiday object as specified.
    """
    return Holiday(
        name,
        month=1,
        day=1,
        offset=LastDayOfMonthOffsetClasses[month](),
        observance=observance,
        start_date=start_date,
        end_date=end_date,
        tz=tz,
    )


class DayOfWeekPeriodicHoliday(Holiday):
    """
    A holiday that occurs on a specific day of the week and repeats weekly.
    """

    def __init__(
        self,
        name: str,
        day_of_week: int,
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
        tz: Optional[tzinfo] = None,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        name : str
            The name of the holiday.
        day_of_week : int
            0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
        start_date : Optional[pd.Timestamp], optional
            The first date on which this holiday is valid, by default None.
        end_date : Optional[pd.Timestamp], optional
            The last date on which this holiday is valid, by default None.
        tz : Optional[tzinfo], optional
            The timezone in which to interpret the holiday, by default None.

        Returns
        -------
        None
        """
        # Super constructor.
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
            tz=tz,
        )

        # Store day of week.
        self.day_of_week = day_of_week

    def _dates(self, start_date, end_date) -> pd.DatetimeIndex:
        """
        Return a list of dates on which this holiday occurs between start_date and end_date.

        Parameters
        ----------
        start_date : starting date, datetime-like, optional
        end_date : ending date, datetime-like, optional

        Returns
        -------
        pd.DatetimeIndex
            A list of dates on which this holiday occurs between start_date and end_date.
        """
        # Determine effective start date.
        if self.start_date is not None:
            start_date = max(start_date, self.start_date.tz_localize(start_date.tz))

        # Determine effective end date.
        if self.end_date is not None:
            end_date = min(end_date, self.end_date.tz_localize(end_date.tz))

        if start_date > end_date:
            # Empty result.
            return pd.DatetimeIndex([])

        # Get the first date larger or equal to start_date where the day of the week is the same as day_of_week.
        first = start_date + pd.Timedelta(
            days=(self.day_of_week - start_date.dayofweek) % 7
        )

        if first > end_date:
            # Empty result.
            return pd.DatetimeIndex([])

        # Get the last date smaller or equal to end_date where the day of the week is the same as day_of_week.
        last = end_date - pd.Timedelta(days=(end_date.dayofweek - self.day_of_week) % 7)

        # Create a pandas DateTimeIndex with the dates of the holidays.
        dates = pd.date_range(start=first, end=last, freq=timedelta(days=7))

        # Return the dates.
        return dates

    def dates(
        self, start_date, end_date, return_name=False
    ) -> Union[DatetimeIndex, Series]:
        # Get DateTimeIndex with the dates of the holidays.
        dates = self._dates(start_date, end_date)

        # Return the dates, either as a series (return_name=True) or as a DateTimeIndex (return_name=False).
        return pd.Series(self.name, index=dates) if return_name else dates
