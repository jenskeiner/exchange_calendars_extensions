from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Sequence
from datetime import date, timedelta
from functools import cached_property
from typing import Annotated, TypeVar

import pandas as pd
from exchange_calendars import ExchangeCalendar
from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints
from pydantic_core import core_schema

from .changes import (
    ChangeModeMulti,
    ChangeModeSingle,
    ChangeSet,
    ChangeSetDelta,
    DayChange,
)

T = TypeVar("T")


Interval = tuple[pd.Timestamp | None, T]


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
Weekmask2 = Annotated[
    str,
    StringConstraints(pattern=r"^[01]{7}$"),
]

WEEKMASK_PATTERN = r"^[01]{7}$"


class Weekmask(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.no_info_plain_validator_function(
            cls._validate,  # Single source of truth
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, v):
        """Validate and convert to a normalized Date."""
        if isinstance(v, cls):
            return v

        if not re.match(WEEKMASK_PATTERN, v):
            raise ValueError(f"Invalid weekmask: {v}")

        return cls(v)

    @classmethod
    def for_day(cls, day: int) -> Weekmask:
        return cls("0" * day + "1" + "0" * (7 - day))

    def contains(self, day: int) -> bool:
        return self[day] == "1"

    def set(self, day: int, value: bool) -> Weekmask:
        return Weekmask(self[:day] + ("1" if value else "0") + self[day + 1 :])

    def bitwise_and(self, other: Weekmask) -> Weekmask:
        return Weekmask(
            "".join("1" if x == "1" and y == "1" else "0" for x, y in zip(self, other))
        )


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

    def contains(self, ts: pd.Timestamp) -> bool:
        return (self.start_date is None or self.start_date <= ts) and (
            self.end_date is None or ts <= self.end_date
        )

    def empty(self) -> bool:
        return (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        )

    def mask(self) -> Weekmask:
        # Return a weekmask representing the days of the week occurring in the period from start_date to end_date.
        # For example, if start_date is a Monday and end_date is the following Wednesday, the mask should be "1110000".
        if self.start_date is None or self.end_date is None:
            return Weekmask("1111111")

        mask_bits = ["0"] * 7
        current = self.start_date
        while current <= self.end_date:
            if mask_bits[current.dayofweek] == "1":
                break  # All days already set.
            mask_bits[current.dayofweek] = "1"
            current += pd.Timedelta(days=1)

        return Weekmask("".join(mask_bits))

    @cached_property
    def length(self) -> int | None:
        if self.start_date is None or self.end_date is None:
            # Return None, meaning infinity.
            return None
        return (self.end_date - self.start_date).days + 1

    @classmethod
    def sort(
        cls, wp1: WeekmaskPeriod, wp2: WeekmaskPeriod
    ) -> tuple[WeekmaskPeriod, WeekmaskPeriod]:
        return (
            (wp1, wp2)
            if wp1.length is None
            or (wp2.length is not None and wp1.length >= wp2.length)
            else (wp2, wp1)
        )

    def is_compatible_with(self, other: WeekmaskPeriod) -> bool:
        a, b = self.sort(self, other)
        mask = b.mask()
        return a.weekmask.bitwise_and(mask) == b.weekmask.bitwise_and(mask)

    def merge(self, other: WeekmaskPeriod) -> WeekmaskPeriod:
        a, b = self.sort(self, other)
        return WeekmaskPeriod(
            weekmask=a.weekmask,
            start_date=a.start_date
            if (
                a.start_date is None
                or (b.start_date is not None and a.start_date <= b.start_date)
            )
            else b.start_date,
            end_date=a.end_date
            if (
                a.end_date is None
                or (b.end_date is not None and b.end_date <= a.end_date)
            )
            else b.end_date,
        )


def _not_none(x):
    if x is None:
        raise ValueError(f"{x!r} is None")
    return x


class SpecialWeekmaskPeriod(WeekmaskPeriod):
    """A special weekmask period. Must have an end date."""

    end_date: Annotated[pd.Timestamp | None, AfterValidator(_not_none)]


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

    default_weekmask = Weekmask(exchange_calendar.weekmask)

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


def find_interval(
    intervals: tuple[Interval[T], ...], timestamp: pd.Timestamp
) -> Interval[T]:
    """
    Find the interval containing the given timestamp using binary search.

    The intervals form a partition of time with no gaps. Each interval is
    a tuple of (start_date, value) where start_date is inclusive and the
    interval extends to (but does not include) the next interval's start_date.
    The first interval has None as start_date, representing (-infinity, ...).

    Parameters
    ----------
    intervals : tuple[Interval[T], ...]
        A tuple of (start_date, value) tuples sorted by start_date in ascending
        order, with the first start_date being None.
    timestamp : pd.Timestamp
        The timestamp to locate within the intervals.

    Returns
    -------
    Interval[T]
        The (start_date, value) tuple for the interval containing the timestamp.
    """
    if not intervals:
        raise ValueError("intervals must not be empty")

    # Extract start dates, replacing None with a sentinel far in the past
    # Using pd.Timestamp.min as the sentinel for binary search
    start_dates = [pd.Timestamp.min if d is None else d for d, _ in intervals]

    # Find insertion point: first index where start_date > timestamp
    # The interval we want is at idx - 1 (or len - 1 if idx == len)
    idx = bisect_right(start_dates, timestamp)

    if idx == 0:
        # Timestamp is before all intervals (only possible if first interval
        # doesn't start with None, which violates the invariant)
        raise ValueError(f"Timestamp {timestamp} is before all intervals")

    return intervals[idx - 1]


def _optimize_periods(
    periods: Sequence[WeekmaskPeriod],
) -> Sequence[WeekmaskPeriod]:
    if not periods:
        return periods

    result: list[WeekmaskPeriod] = []
    current = periods[0]

    for next_period in periods[1:]:
        if (
            # current.weekmask == next_period.weekmask
            current.is_compatible_with(next_period)
            and current.end_date is not None
            and next_period.start_date is not None
            and current.end_date + pd.Timedelta(days=1) == next_period.start_date
        ):
            current = current.merge(next_period)
        else:
            result.append(current)
            current = next_period

    result.append(current)
    return tuple(result)


def set_weekday(
    periods: Sequence[WeekmaskPeriod], ts: pd.Timestamp, weekday: bool
) -> tuple[WeekmaskPeriod, ...]:
    result = []
    for p in periods:
        if not p.contains(ts) or (weekday ^ (not p.weekmask.contains(ts.dayofweek))):
            # Interval already good.
            result.append(p)
        else:
            # Split into three intervals.
            p0 = WeekmaskPeriod(
                start_date=p.start_date,
                end_date=ts + pd.Timedelta(days=-1),
                weekmask=p.weekmask,
            )
            p1 = WeekmaskPeriod(
                start_date=ts,
                end_date=ts,
                weekmask=p.weekmask.set(ts.dayofweek, weekday),
            )
            p2 = WeekmaskPeriod(
                start_date=ts + pd.Timedelta(days=1),
                end_date=p.end_date,
                weekmask=p.weekmask,
            )
            result.extend([x for x in [p0, p1, p2] if not x.empty()])
    return tuple(_optimize_periods(result))


def copy_changeset(cs: ChangeSet) -> ChangeSet:
    return {k: DayChange.model_validate(v.model_dump()) for k, v in cs.items()}


def consolidate(changes: ChangeSetDelta) -> ChangeSet:
    return {k: v for k, v in changes.items() if isinstance(v, DayChange)}


def mode_multi_to_single(mode: ChangeModeMulti) -> ChangeModeSingle:
    return "replace" if mode == "replace_all" else mode
