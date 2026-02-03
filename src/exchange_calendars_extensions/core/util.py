from datetime import date
from datetime import timedelta
from typing import Annotated

import pandas as pd
from exchange_calendars import ExchangeCalendar
from pydantic import BaseModel, ConfigDict, StringConstraints


def get_month_name(month: int) -> str:
    """
    Convert month to capitalized name of month.

    Parameters
    ----------
    month : int
        Month number (1-12).

    Returns
    -------
    str
        Name of month.
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    month_name = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ][month - 1]

    return month_name


def get_day_of_week_name(day_of_week: int) -> str:
    """
    Convert day of week number to name.

    Parameters
    ----------
    day_of_week : int
        Day of week number (0-6), where 0 is Monday and 6 is Sunday.

    Returns
    -------
    str
        Name of day of week.
    """
    if day_of_week < 0 or day_of_week > 6:
        raise ValueError("Day of week must be between 0 and 6.")

    day_of_week_name = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ][day_of_week]

    return day_of_week_name


def third_day_of_week_in_month(day_of_week: int, month: int, year: int) -> date:
    """
    Return the third given day of the week in the given month and year.

    Parameters
    ----------
    day_of_week : int
        the day of the week, must be an integer between 0 (Monday) and 6 (Sunday).
    year : int
        the year, must be an integer
    month : int
        the month of the year, must be an integer between (inclusive) 1 and 12

    Returns
    -------
    datetime.date
        the datetime.date representing the third Friday in the given month.
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


def last_day_in_month(month: int, year: int) -> date:
    """
    Return the last day in the given month and year.

    Parameters
    ----------
    month : int
        the month of the year, must be an integer between (inclusive) 1 and 12
    year : int
        the year, must be an integer

    Returns
    -------
    datetime.date
        the datetime.date representing the last day in the given month.
    """
    return (date(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )


# Specifies which days of the week are trading days, Mon - Sun, e.g. "1111100".
Weekmask = Annotated[
    str,
    StringConstraints(pattern=r"^[01]{7}$"),
]


class WeekmaskPeriod(BaseModel):
    """A period during which a specific weekmask applies to an exchange calendar.

    Attributes
    ----------
    weekmask : Weekmask
        The weekmask string (e.g., "1111100" where 1=open, 0=closed for Mon-Sun).
    start_date : pd.Timestamp | None
        The first date this weekmask applies. None means from the beginning of time.
    end_date : pd.Timestamp | None
        The last date this weekmask applies. None means to infinity.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    weekmask: Weekmask
    start_date: pd.Timestamp | None = None
    end_date: pd.Timestamp | None = None


class SpecialWeekmaskPeriod(WeekmaskPeriod):
    """A special weekmask period. Must have an end date."""

    end_date: pd.Timestamp


def get_weekmask_periods(
    exchange_calendar: ExchangeCalendar,
) -> tuple[WeekmaskPeriod, ...]:
    """
    Return all weekmask periods for the exchange calendar as a tuple of WeekmaskPeriod objects.

    This provides a uniform interface for accessing weekmasks regardless of whether the calendar
    has a single weekmask or multiple special_weekmasks. Gaps between special_weekmasks are
    filled with the default weekmask.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to get weekmask periods from.

    Returns
    -------
    tuple[WeekmaskPeriod, ...]
        A tuple of WeekmaskPeriod objects.
    """
    special_weekmasks = getattr(
        exchange_calendar, "special_weekmasks", None
    )  # Assumed to be sorted and non-overlapping.

    default_weekmask = exchange_calendar.weekmask

    if not special_weekmasks:
        return (WeekmaskPeriod(weekmask=default_weekmask),)

    periods: list[WeekmaskPeriod] = []

    # Track the day after the last period ended
    next_available_start: pd.Timestamp | None = None

    for start_date, end_date, weekmask in special_weekmasks:
        # Fill gap between last period and this special weekmask with default weekmask
        if start_date is not None:
            if next_available_start is None:
                # First special weekmask doesn't start from beginning - add default period from beginning
                periods.append(
                    WeekmaskPeriod(
                        weekmask=default_weekmask,
                        start_date=None,
                        end_date=start_date - pd.Timedelta(days=1),
                    )
                )
            elif start_date > next_available_start:
                # There's a gap - add default weekmask period
                periods.append(
                    WeekmaskPeriod(
                        weekmask=default_weekmask,
                        start_date=next_available_start,
                        end_date=start_date - pd.Timedelta(days=1),
                    )
                )

        # Add the special weekmask period
        periods.append(
            SpecialWeekmaskPeriod(
                weekmask=weekmask, start_date=start_date, end_date=end_date
            )
        )

        # Next available start is the day after this special weekmask ends
        next_available_start = end_date + pd.Timedelta(days=1)

    # Add final default weekmask period (from day after last special weekmask to infinity)
    periods.append(
        WeekmaskPeriod(weekmask=default_weekmask, start_date=next_available_start)
    )

    return tuple(periods)


def get_applicable_weekmask_period(
    exchange_calendar: ExchangeCalendar, date: pd.Timestamp
) -> WeekmaskPeriod:
    """
    Return the applicable weekmask period for the exchange calendar at the given date.

    This is a convenience wrapper around get_weekmask_periods that finds the specific
    WeekmaskPeriod that applies to the given date.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to get the weekmask from.
    date : pd.Timestamp
        The date for which to get the applicable weekmask period.

    Returns
    -------
    WeekmaskPeriod
        The WeekmaskPeriod that applies to the given date.
    """
    periods = get_weekmask_periods(exchange_calendar)

    for period in periods:
        if (period.start_date is None or date >= period.start_date) and (
            period.end_date is None or date <= period.end_date
        ):
            return period

    # This should never happen if periods cover all dates
    raise ValueError(f"No weekmask period found for date {date}")
