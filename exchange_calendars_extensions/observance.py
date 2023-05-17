from typing import Callable

import pandas as pd
from exchange_calendars.exchange_calendar import HolidayCalendar


def get_roll_backward_observance(calendar: HolidayCalendar) -> Callable[[pd.Timestamp], pd.Timestamp]:
    """
    Return a function that rolls back a date to the last regular business day, according to a given holiday
    calendar.

    Regular business days are those days that are not defined as holidays by the given holiday calendar. This means,
    for example, that the calendar also needs to define weekend days as holidays to avoid rolling a date back to
    weekend day.

    Parameters
    ----------
    calendar : HolidayCalendar
        The holiday calendar to use for determining holidays.

    Returns
    -------
    Callable[[pd.Timestamp], pd.Timestamp]
        A function that takes a date and returns the last business day on or before that date, according to the given
        calendar.
    """

    def f(date: pd.Timestamp) -> pd.Timestamp:
        # Repeat until done.
        while True:
            # A date a few days in the past, relative to the current date.
            limit = date - pd.Timedelta(days=5)

            # Get all holidays between the limit date and the current date.
            holidays = calendar.holidays(limit, date)

            while date >= limit:
                # If the date is a holiday, roll it back one day.
                if date in holidays:
                    date = date - pd.Timedelta(days=1)
                else:
                    # Otherwise, we're done.
                    return date

            # If we get here, we've rolled back more than 5 days. Rinse and repeat.

    return f
