import datetime as dt
from abc import ABC
from collections.abc import Callable, Iterable, Sequence
from copy import copy
from dataclasses import dataclass, field
from functools import cached_property, reduce
from typing import (
    Any,
    Literal,
    Protocol,
    Union,
    runtime_checkable,
)

import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import (
    HolidayCalendar as ExchangeCalendarsHolidayCalendar,
)
from exchange_calendars.pandas_extensions.holiday import Holiday
from exchange_calendars.pandas_extensions.holiday import (
    Holiday as ExchangeCalendarsHoliday,
)
from exchange_calendars.pandas_extensions.offsets import (
    MultipleWeekmaskCustomBusinessDay,
)
from pandas import Timestamp
from pandas.tseries.holiday import Holiday as PandasHoliday
from pandas.tseries.offsets import CustomBusinessDay
from pydantic import ConfigDict, Field, TypeAdapter, validate_call
from pydantic.experimental.missing_sentinel import MISSING

from .changes import (
    BusinessDaySpec,
    ChangeSet,
    DayChange,
    NonBusinessDaySpec,
)
from .holiday import (
    DayOfWeekPeriodicHoliday,
    get_last_day_of_month_holiday,
    get_monthly_expiry_holiday,
)
from .util import (
    WeekmaskPeriod,
    find_interval,
    get_weekmask_periods,
    set_weekday,
)

from .datetime import (
    DateLike,
    DateLikeInput,
)

# Timdelta that represents a day minus the smallest increment of time.
ONE_DAY_MINUS_EPS = pd.Timedelta(1, "D") - pd.Timedelta(1, "ns")


class HolidayCalendar(ExchangeCalendarsHolidayCalendar):
    """
    A subclass of exchange_calendars.exchange_calendar.HolidayCalendar that supports overlapping rules, i.e. rules that
    apply to the same date.

    Duplicates are dropped from the result. Which duplicate is dropped is generally undefined, but if the rules
    parameters has an ordering, rules with lower indices will have higher priority.

    Parameters
    ----------
    rules : Iterable[PandasHoliday]
        The rules that define this calendar.
    """

    def __init__(self, rules) -> None:
        super().__init__(rules=rules)

    def holidays(self, start=None, end=None, return_name=False):
        # Get the holidays from the parent class.
        holidays = super().holidays(start=start, end=end, return_name=return_name)

        # Drop duplicates, keeping the first occurrence.
        if return_name:
            assert isinstance(holidays, pd.Series)
            return holidays[~holidays.index.duplicated()]
        else:
            return holidays.drop_duplicates()


def get_conflicts(
    holidays_dates: list[pd.Timestamp | None],
    other_holidays: pd.DatetimeIndex,
    weekend_days_or_periods: tuple[WeekmaskPeriod, ...],
) -> list[int]:
    """
    Get the indices of holidays that coincide with holidays from the other calendar or the given weekend days.

    Parameters
    ----------
    holidays_dates : List[Union[pd.Timestamp, None]]
        The dates of the holidays. A date may be None and is then ignored.
    other_holidays : pd.DatetimeIndex
        The dates of the holidays from the other calendar.
    weekend_days_or_periods : tuple[WeekmaskPeriod, ...]
        Tuple of WeekmaskPeriod objects that define different weekend periods.

    Returns
    -------
    List[int]
        The indices of holidays that coincide with holidays from the other calendar or the given weekend days.
    """

    def is_weekend_day(date: pd.Timestamp) -> bool:
        """Check if a date is a weekend day based on the applicable weekmask period."""
        # Find the applicable period for this date
        for period in weekend_days_or_periods:
            if (period.start_date is None or date >= period.start_date) and (
                period.end_date is None or date <= period.end_date
            ):
                return period.weekmask[date.weekday()] == "0"
        # Fallback: if no period matches, treat as not a weekend
        return False

    # Determine the indices of holidays that coincide with holidays from the other calendar.
    return [
        i
        for i in range(len(holidays_dates))
        if holidays_dates[i] is not None
        and (
            holidays_dates[i] in other_holidays
            or is_weekend_day(holidays_dates[i])
            or holidays_dates[i] in holidays_dates[i + 1 :]
        )
    ]


# A function that takes a date and returns a date or None.
RollFn = Callable[[pd.Timestamp], Union[pd.Timestamp, None]]


def roll_one_day_same_month(d: pd.Timestamp) -> pd.Timestamp | None:
    """
    Roll the given date back one day and return the result if the month is still the same. Return None otherwise.

    This function can be used to prevent certain days from being rolled back into the previous month. For example, the
    last trading day of July 2015 on ASEX is not defined since the exchange was closed the entire month. Hence, this day
    should not be rolled into June.

    Parameters
    ----------
    d : pd.Timestamp
        The date to roll back.

    Returns
    -------
    pd.Timestamp | None
        The rolled back date, if the month is still the same, or None otherwise.
    """
    # Month.
    month = d.month

    # Roll back one day.
    d = d - pd.Timedelta(days=1)

    # If the month changed, return None.
    if d.month != month:
        return None

    # Return the rolled back date.
    return d


# A function that takes a date range and returns a possibly modified (expanded) range.
PreGrowFn = Callable[
    [pd.Timestamp | None, pd.Timestamp | None],
    tuple[pd.Timestamp | None, pd.Timestamp | None],
]


def pre_grow_end_of_month(
    start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Returns the given date range expanded to the last day of the month of the end date.

    Only the end date is modified, if needed. The start date always remains the same. For example, if the input range
    is [2026-01-15, 2026-02-23], then the returned range will be [2026-01-15, 2026-02-28].

    Rationale: The expansion up to the month end is required when determining special days like expiry days or the last
    trading day in a month which are rolled backwards relative to other holidays/special days and weekend days, so that
    these special days are taken into account if the requested date range from a holiday calendar only includes a
    period of time whee these days may be rolled to, but which excludes the original unrolled day.

    For example, the last trading day in a month, say January 2026, is determined by an offset that initialy returns the
    last calendar day of the month (2026-01-31) and then rolls the day forward until reaching the first business day
    (2026-01-30). If the corresponding calendar is queried for the single-day range [2026-01-30, 2026,01,30], the result
    should include the last trading day that has been rolled to 2026-01-30 from 2026-01-31. That is why the underlying
    unadjusted days must be queried with the expanded range [2026-01-30, 2026-01-31], or the result would be empty.

    For quarterly and monthly expiry days, it would be enough to expand the range up to the unadjusted days which are
    always strictly before the month end, but expanding to the month end or further does not change the result.


    Parameters
    ----------
    start : pd.Timestamp
        The start date.
    end : pd.Timestamp
        The end date.

    Returns
    -------
    tuple[pd.Timestamp, pd.Timestamp]
        The expanded date range.
    """
    if end is not None:
        try:
            end = end + pd.offsets.MonthEnd()
        except pd.errors.OutOfBoundsDatetime as _:
            pass

    return start, end


def filter_by_range(
    data: pd.Series | pd.DatetimeIndex,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.Series | pd.DatetimeIndex:
    """
    Filter a Series or DatetimeIndex to only include dates within the given range.

    Parameters
    ----------
    data : pd.Series | pd.DatetimeIndex
        The Series or DatetimeIndex to filter.
    start : pd.Timestamp | None
        The start of the range (inclusive). If None, no lower bound is applied.
    end : pd.Timestamp | None
        The end of the range (inclusive). If None, no upper bound is applied.

    Returns
    -------
    pd.Series | pd.DatetimeIndex
        The filtered data, with the same type as the input.
    """
    if start is None and end is None:
        return data
    dates = data.index if isinstance(data, pd.Series) else data
    mask = dates >= start if start is not None else True
    if end is not None:
        mask = mask & (dates <= end)
    return data[mask]


class AdjustedHolidayCalendar(ExchangeCalendarsHolidayCalendar):
    def __init__(
        self,
        rules,
        other: ExchangeCalendarsHolidayCalendar,
        weekmask_periods: tuple[WeekmaskPeriod, ...],
        roll_fn: RollFn = lambda d: d + pd.Timedelta(days=-1),
        pre_grow_fn: PreGrowFn = pre_grow_end_of_month,
    ) -> None:
        super().__init__(rules=rules)
        self._other = other
        self._weekmask_periods = weekmask_periods
        self._roll_fn = roll_fn
        self._pre_grow_fn = pre_grow_fn

    def holidays(self, start=None, end=None, return_name=False):
        start = Timestamp(start) if start is not None else None
        end = Timestamp(end) if end is not None else None

        return filter_by_range(
            self._holidays(*self._pre_grow_fn(start, end), return_name), start, end
        )

    def _holidays(self, start=None, end=None, return_name=False):
        # Get unadjusted holidays.
        holidays = super().holidays(start=start, end=end, return_name=return_name)

        # Get the holidays from the other calendar.
        other_holidays = self._other.holidays(start=start, end=end, return_name=False)

        holidays_dates = list(holidays.index if return_name else holidays)

        conflicts = get_conflicts(
            holidays_dates, other_holidays, self._weekmask_periods
        )

        if len(conflicts) == 0:
            return holidays

        while True:
            # For each index of a conflicting holiday, adjust the date by using the roll function.
            for i in conflicts:
                holidays_dates[i] = self._roll_fn(holidays_dates[i])

            conflicts = get_conflicts(
                holidays_dates, other_holidays, self._weekmask_periods
            )

            if len(conflicts) == 0:
                break

        if return_name:
            # Return a series, filter out dates that are None.
            return pd.Series(
                {d: n for d, n in zip(holidays_dates, holidays.values) if d is not None}
            )
        else:
            # Return index, filter out dates that are None.
            return pd.DatetimeIndex([d for d in holidays_dates if d is not None])


_ta = TypeAdapter(DateLike, config=ConfigDict(arbitrary_types_allowed=True))


def get_holiday_calendar_from_timestamps(
    timestamps: list[pd.Timestamp],
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with holidays given by a collection of timestamps.

    If name is specified, each holiday will use that given name.

    Parameters
    ----------
    timestamps : Iterable[pd.Timestamp]
        The timestamps of the holidays.
    name : Optional[str], optional
        The name to use for each holiday, by default None.

    Returns
    -------
    ExchangeCalendarsHolidayCalendar
        A new HolidayCalendar object as specified.
    """
    # Generate list of rules, one for each timestamp.
    rules = [
        Holiday(
            name=None,
            year=ts.year,
            month=ts.month,
            day=ts.day,
            start_date=ts,
            end_date=ts,
        )
        for ts in set(dict.fromkeys(timestamps))
    ]  # As of Python 3.7, dict preserves insertion order.

    # Return a new HolidayCalendar with the given rules.
    return ExchangeCalendarsHolidayCalendar(rules=rules)


def get_holiday_calendar_from_day_of_week(*, day_of_week: int) -> HolidayCalendar:
    """
    Return a holiday calendar with a periodic holiday occurring on each instance of the given day of the week.

    Parameters
    ----------
    day_of_week : int
        The day of the week to use, where 0 is Monday and 6 is Sunday.
    name : Optional[str], optional
        The name to use for the holiday, by default None.
    """
    # Generate list of rules. Actually contains only one rule for the given day of the week.
    rules = [DayOfWeekPeriodicHoliday(None, day_of_week)]

    # Return a new HolidayCalendar with the given rules.
    return ExchangeCalendarsHolidayCalendar(rules=rules)


def merge_calendars(
    calendars: Iterable[ExchangeCalendarsHolidayCalendar],
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with all holidays from the given calendars merged into a single HolidayCalendar.

    The rules of the returned calendar will be the concatenation of the rules of the given calendars. Note that rules
    that occur earlier take precedence in case of conflicts, i.e. rules that apply to the same date.
    """
    x = reduce(
        lambda x, y: HolidayCalendar(rules=[r for r in x.rules] + [r for r in y.rules]),
        calendars,
        ExchangeCalendarsHolidayCalendar(rules=[]),
    )
    return x


def get_holidays_calendar(
    exchange_calendar: ExchangeCalendar,
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with all holidays, regular and ad-hoc, from the given exchange calendar merged into a
    single calendar.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to use.

    Returns
    -------
    ExchangeCalendarsHolidayCalendar
        A new HolidayCalendar with all holidays from the given EchangeCalendar.
    """
    holiday_calendars = [
        get_holiday_calendar_from_timestamps(exchange_calendar.adhoc_holidays),
        exchange_calendar.regular_holidays,
    ]

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_special_opens_calendar(
    exchange_calendar: ExchangeCalendar,
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with all special opens, regular and ad-hoc, from the given exchange calendar merged into a
    single calendar.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to use.

    Returns
    -------
    ExchangeCalendarsHolidayCalendar
        A new HolidayCalendar with all special opens from the given EchangeCalendar.
    """
    holiday_calendars = []

    # Add ad-hoc special opens.
    for item in exchange_calendar.special_opens_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition))

    # Add regular special open days.
    for item in exchange_calendar.special_opens:
        _, definition = item
        if isinstance(definition, ExchangeCalendarsHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(
                get_holiday_calendar_from_day_of_week(day_of_week=definition)
            )

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_special_closes_calendar(
    exchange_calendar: ExchangeCalendar,
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with all special closes, regular and ad-hoc, from the given exchange calendar merged into
    a single calendar.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to use.

    Returns
    -------
    ExchangeCalendarsHolidayCalendar
        A new HolidayCalendar with all special closes from the given EchangeCalendar.
    """
    holiday_calendars = []

    # Add ad-hoc special closes.
    for item in exchange_calendar.special_closes_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition))

    # Add regular special close days.
    for item in exchange_calendar.special_closes:
        _, definition = item
        if isinstance(definition, ExchangeCalendarsHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(
                get_holiday_calendar_from_day_of_week(day_of_week=definition)
            )

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_days_calendar(
    periods: Sequence[WeekmaskPeriod],
    mask: Literal["0", "1"],
) -> ExchangeCalendarsHolidayCalendar:
    """
    Return a holiday calendar with all weekend days from the given exchange calendar as holidays.

    Parameters
    ----------
    exchange_calendar : ExchangeCalendar
        The exchange calendar to use.

    Returns
    -------
    ExchangeCalendarsHolidayCalendar
        A new HolidayCalendar with all weekend days from the given EchangeCalendar.

    Notes
    -----
    For calendars with special_weekmasks (where the weekmask has changed over time), this function
    creates rules for each period with its respective weekmask.

    The default weekmask applies to all periods not covered by special weekmasks.
    """
    rules: list[Holiday] = []

    for p in periods:
        for day_of_week, v in enumerate(p.weekmask):
            if v == mask:
                rules.append(
                    DayOfWeekPeriodicHoliday(
                        name=None,
                        day_of_week=day_of_week,
                        start_date=p.start_date,
                        end_date=p.end_date,
                    )
                )

    return ExchangeCalendarsHolidayCalendar(rules=rules)


def get_monthly_expiry_rules(
    day_of_week: int,
    observance: Callable[[pd.Timestamp], pd.Timestamp] | None = None,
) -> list[Holiday]:
    """
    Return a list of rules for a calendar with a holiday for each month's expiry, but excluding quarterly expiry days.

    Parameters
    ----------
    day_of_week : int
        The day of the week to use, where 0 is Monday and 6 is Sunday.
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        The observance function to use, by default None.

    Returns
    -------
    List[Holiday]
        A list of rules for a calendar with a holiday for each month's expiry, but excluding quarterly expiry days.
    """
    return [
        get_monthly_expiry_holiday(
            name=None, day_of_week=day_of_week, month=month, observance=observance
        )
        for month in [1, 2, 4, 5, 7, 8, 10, 11]
    ]


def get_quadruple_witching_rules(
    day_of_week: int,
    observance: Callable[[pd.Timestamp], pd.Timestamp] | None = None,
) -> list[Holiday]:
    """
    Return a list of rules for a calendar with a holiday for each quarterly expiry aka quadruple witching.

    Parameters
    ----------
    day_of_week : int
        The day of the week to use, where 0 is Monday and 6 is Sunday.
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        The observance function to use, by default None.

    Returns
    -------
    List[Holiday]
        A list of rules for a calendar with a holiday for each quarterly expiry aka quadruple witching.
    """
    return [
        get_monthly_expiry_holiday(
            name=None, day_of_week=day_of_week, month=month, observance=observance
        )
        for month in [3, 6, 9, 12]
    ]


def get_last_day_of_month_rules(
    observance: Callable[[pd.Timestamp], pd.Timestamp] | None = None,
) -> list[Holiday]:
    """
    Return a list of rules for a calendar with a holiday for each last trading day of the month.

    Parameters
    ----------
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        The observance function to use, by default None.

    Returns
    -------
    List[Holiday]
        A list of rules for a calendar with a holiday for each last trading day of the month.
    """
    return [
        get_last_day_of_month_holiday(name=None, month=i, observance=observance)
        for i in range(1, 13)
    ]


@runtime_checkable
class ExchangeCalendarExtensions(Protocol):
    """
    A protocol for extensions to the exchange_calendars.ExchangeCalendar class.
    """

    @property
    def weekend_days(self) -> ExchangeCalendarsHolidayCalendar:
        """
        Return holiday calendar containing all weekend days as holidays.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with all weekend days as holidays.
        """
        ...  # pragma: no cover

    @property
    def week_days(self) -> ExchangeCalendarsHolidayCalendar:
        """
        Return holiday calendar containing all week days as holidays.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with all week days as holidays.
        """
        ...  # pragma: no cover

    @property
    def holidays_all(self) -> ExchangeCalendarsHolidayCalendar:
        """
        Return a holiday calendar containing all holidays, regular and ad-hoc.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with all holidays.
        """
        ...  # pragma: no cover

    @property
    def special_opens_all(self) -> ExchangeCalendarsHolidayCalendar:
        """
        Return a holiday calendar with all special opens, regular and ad-hoc.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with all special opens.
        """
        ...  # pragma: no cover

    @property
    def special_closes_all(self) -> ExchangeCalendarsHolidayCalendar:
        """
        Return a holiday calendar with all special closes, regular and ad-hoc.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with all special closes.
        """
        ...  # pragma: no cover

    @property
    def monthly_expiries(self) -> ExchangeCalendarsHolidayCalendar | None:
        """
        Return a holiday calendar with a holiday for each monthly expiry, but excluding quarterly expiry days.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each monthly expiry.
        """
        ...  # pragma: no cover

    @property
    def quarterly_expiries(self) -> ExchangeCalendarsHolidayCalendar | None:
        """
        Return a holiday calendar with a holiday for each quarterly expiry aka quadruple witching.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each quarterly expiry.
        """
        ...  # pragma: no cover

    @property
    def last_trading_days_of_months(
        self,
    ) -> ExchangeCalendarsHolidayCalendar:
        """
        Return a holiday calendar with a holiday for each last trading day of the month.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each last trading day of the month.
        """
        ...  # pragma: no cover

    @property
    def last_regular_trading_days_of_months(
        self,
    ) -> ExchangeCalendarsHolidayCalendar:
        """
        Return a holiday calendar with a holiday for each last regular trading day of the month.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each last regular trading day of the month.
        """
        ...

    def tags(
        self,
        *,
        tags: set[str] = Field(default_factory=frozenset),
        start: DateLikeInput | None = None,
        end: DateLikeInput | None = None,
        return_tags: bool = False,
    ) -> pd.DatetimeIndex | pd.Series:
        """
        Return a DatetimeIndex or Series of timestamps that have the specified tags.

        Parameters
        ----------
        tags : Collection[str]
            The tags to search for.
        start : pd.Timestamp
            The start date of the search.
        end : pd.Timestamp
            The end date of the search.
        return_tags : bool, optional
            Whether to return the tags as a Series, by default False.

        Returns
        -------
        pd.DatetimeIndex | pd.Series
            A DatetimeIndex or Series of timestamps that have the specified tags.
        """
        ...


@dataclass
class AdjustedProperties:
    """
    A dataclass for storing adjusted properties of an exchange calendar.
    """

    open_times: tuple[tuple[pd.Timestamp, Any], ...]
    close_times: tuple[tuple[pd.Timestamp, Any], ...]
    weekmasks: tuple[WeekmaskPeriod, ...]

    # The regular holidays of the exchange calendar.
    regular_holidays: list[Holiday]

    # The ad-hoc holidays of the exchange calendar.
    adhoc_holidays: list[pd.Timestamp]

    # The special closes of the exchange calendar.
    special_closes: list[tuple[dt.time, list[Holiday]]]

    # The ad-hoc special closes of the exchange calendar.
    adhoc_special_closes: list[tuple[dt.time, pd.DatetimeIndex]]

    # The special opens of the exchange calendar.
    special_opens: list[tuple[dt.time, list[Holiday]]]

    # The ad-hoc special opens of the exchange calendar.
    adhoc_special_opens: list[tuple[dt.time, pd.DatetimeIndex]]

    # The quarterly expiry days of the exchange calendar.
    quarterly_expiries: list[Holiday] = field(default_factory=list)

    # The monthly expiry days of the exchange calendar.
    monthly_expiries: list[Holiday] = field(default_factory=list)

    # The last trading days of the month of the exchange calendar.
    last_trading_days_of_months: list[Holiday] = field(default_factory=list)

    # The last regular trading days of the month of the exchange calendar.
    last_regular_trading_days_of_months: list[Holiday] = field(default_factory=list)


class ExtendedExchangeCalendar(ExchangeCalendarExtensions, ExchangeCalendar, ABC):
    """
    Abstract base class for exchange calendars with extended functionality.
    """

    ...


def extend_class(
    cls: type[ExchangeCalendar],
    day_of_week_expiry: int | None = None,
    changeset_provider: Callable[[], ChangeSet | None] | None = None,
) -> type:
    """
    Extend the given ExchangeCalendar class with additional properties.

    Parameters
    ----------
    cls : Type[ExchangeCalendar]
        The input class to extend.
    day_of_week_expiry : Union[int, None]
        The day of the week when expiry days are observed, where 0 is Monday and 6 is Sunday. Defaults to 4 (Friday).
    changeset_provider : Union[Callable[[], ChangeSet], None]
        The optional function that returns a changeset to apply to the calendar.

    Returns
    -------
    type
        The extended class.

    Notes
    -----
    This method returns an extended version of the given ExchangeCalendar sub-class with additional properties.
    Specifically, this method adds the following properties:
    - holidays_all: a HolidayCalendar with all holidays, regular and ad-hoc.
    - special_opens_all: a HolidayCalendar with all special open days, regular and ad-hoc.
    - special_closes_all: a HolidayCalendar with all special close days, regular and ad-hoc.
    - weekend_days: a HolidayCalendar with all weekend days.
    - week_days: a HolidayCalendar with all week days.
    - monthly_expiries: a HolidayCalendar with all monthly expiry days.
    - quarterly_expiries: a HolidayCalendar with all quarterly expiry days.
    - last_trading_days_of_months: a HolidayCalendar with the respective last trading day of each month.
    - last_regular_trading_days_of_months: a HolidayCalendar with the respective last regular trading day of each month.

    The properties holidays_all, special_opens_all, and special_closes_all make it more convenient to determine relevant
    days in a given date range since regular and ad-hoc special days are merged into a single calendar.

    The property weekend_days may be useful to determine weekend days in a given date range since parsing the weekmask
    property of the underlying ExchangeCalendar class is avoided. Similarly, week_days returns all days that are not
    weekend days.

    The property monthly_expiries returns expiry days for months January, February, April, May, July, August, October,
    and November. For most exchanges, these days are the third Friday or Thursday in the respective month. If that day
    is a holiday or special open/close day, an observance rule determines where the expiry day is shifted to. Typically,
    this will be the previous regular business day. For exchanges that do not observe monthly expiry days, this property
    may throw NotImplementedError.

    Similarly to monthly_expiries, the property quarterly_expiries returns expiry days for months March, June,
    September, and December, also known as quarterly expiries or triple/quadruple witching.

    The property last_trading_days_of_months returns the last trading day of each month. Note that the last trading day
    may be a special open/close day.

    The property last_regular_trading_days_of_months returns the last regular trading day of each month. The only
    difference to last_trading_days_of_months is that this property always returns the last regular trading day and
    never a special open/close day. That is, if the last trading day of a month is a special open/close day, here the
    day is rolled back to the previous regular trading day instead.
    """
    # Store some original methods and properties for later use below.
    init_orig = cls.__init__
    regular_holidays_orig = cls.regular_holidays.fget
    adhoc_holidays_orig = cls.adhoc_holidays.fget
    special_closes_orig = cls.special_closes.fget
    adhoc_special_closes_orig = cls.special_closes_adhoc.fget
    special_opens_orig = cls.special_opens.fget
    adhoc_special_opens_orig = cls.special_opens_adhoc.fget

    def get_name(date: pd.Timestamp, instance: ExchangeCalendar) -> str | None:
        """Return the name of the given day, if present in any calendar, or None otherwise.

        Search through original regular/ad-hoc holidays, special opens, special closes."""
        # Search regular holidays.
        regular = regular_holidays_orig(instance)
        if regular is not None:
            for rule in regular.rules:
                if is_holiday(rule, date):
                    return rule.name

        # Search special closes.
        specials_closes = special_closes_orig(instance)

        name = None

        if specials_closes is not None:
            for _, d in specials_closes:
                if isinstance(d, int):
                    # Won't change the name.
                    pass
                else:
                    for rule in d.rules:
                        if is_holiday(rule, date) and rule.name:
                            name = rule.name
                            break

        if name:
            return name

        # Search special opens.
        specials_opens = special_opens_orig(instance)
        if specials_opens is not None:
            for _, d in specials_opens:
                if isinstance(d, int):
                    if date.dayofweek == d:
                        # Won't change the name.
                        pass
                else:
                    for rule in d.rules:
                        if is_holiday(rule, date):
                            name = rule.name
                            break

        return name

    def is_holiday(holiday: Holiday, ts: pd.Timestamp) -> bool:
        """
        Determine if the given timestamp is a holiday.

        Parameters
        ----------
        holiday : Holiday
            The holiday to check.
        ts : pd.Timestamp
            The timestamp to check.

        Returns
        -------
        bool
            True if the timestamp is a holiday, False otherwise.
        """
        return any([d == ts for d in holiday.dates(start_date=ts, end_date=ts)])

    def clone_holiday(
        holiday: (PandasHoliday | ExchangeCalendarsHoliday | DayOfWeekPeriodicHoliday),
        start_date: pd.Timestamp | None = None,
        end_date: pd.Timestamp | None = None,
    ) -> PandasHoliday | ExchangeCalendarsHoliday | DayOfWeekPeriodicHoliday:
        """
        Return a copy of the given holiday.

        Parameters
        ----------
        holiday : Union[PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday]
            The holiday to copy.
        start_date : Optional[pd.Timestamp], optional
            The optional start date of the copy. If not given, the start date of the original holiday is used.
        end_date : Optional[pd.Timestamp], optional
            The optional end date of the copy. If not given, the end date of the original holiday is used.

        Returns
        -------
        Union[PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday]
            The copy of the given holiday.
        """
        # Determine the effective start and end dates.
        start_date_effective = (
            start_date if start_date is not None else holiday.start_date
        )
        end_date_effective = end_date if end_date is not None else holiday.end_date

        if isinstance(holiday, DayOfWeekPeriodicHoliday):
            return DayOfWeekPeriodicHoliday(
                name=holiday.name,
                day_of_week=holiday.day_of_week,
                start_date=start_date_effective,
                end_date=end_date_effective,
                tz=holiday.tz,
            )
        elif isinstance(holiday, ExchangeCalendarsHoliday):
            return ExchangeCalendarsHoliday(
                name=holiday.name,
                year=holiday.year,
                month=holiday.month,
                day=holiday.day,
                offset=holiday.offset,
                observance=holiday.observance,
                start_date=start_date_effective,
                end_date=end_date_effective,
                days_of_week=holiday.days_of_week,
                tz=holiday.tz,
            )
        elif isinstance(holiday, PandasHoliday):
            return PandasHoliday(
                name=holiday.name,
                year=holiday.year,
                month=holiday.month,
                day=holiday.day,
                offset=holiday.offset,
                observance=holiday.observance,
                start_date=start_date_effective,
                end_date=end_date_effective,
                days_of_week=holiday.days_of_week,
            )
        else:
            raise NotImplementedError(f"Unsupported holiday type: {type(holiday)}")

    def remove_day_from_rules(ts: pd.Timestamp, rules: list[Holiday]) -> list[Holiday]:
        """
        Parameters
        ----------
        ts : pd.Timestamp
            The timestamp to exclude.
        rules : List[Holiday]
            The list of rules to modify.

        Returns
        -------
        List[Holiday]
            The modified list of rules, with any rules that coincide with ts removed and replaced by two new rules that
            don't contain ts.
        """
        # Determine any rules that coincide with ts.
        remove = [rule for rule in rules if is_holiday(rule, ts)]

        # Modify rules to exclude ts.
        for rule in remove:
            # Create copies of rule with end date set to ts - 1 day and ts + 1 day, respectively.
            rule_before_ts = clone_holiday(rule, end_date=ts + pd.Timedelta(days=-1))
            rule_after_ts = clone_holiday(rule, start_date=ts + pd.Timedelta(days=1))
            # Determine index of rule in list.
            rule_index = rules.index(rule)
            # Remove original rule.
            rules.pop(rule_index)
            # Add the new rules.
            rules.insert(rule_index, rule_before_ts)
            rules.insert(rule_index + 1, rule_after_ts)

        return rules

    def add_special_session(
        name: str,
        ts: pd.Timestamp,
        t: dt.time,
        special_sessions: list[tuple[dt.time, list[Holiday]]],
    ) -> list[tuple[dt.time, list[Holiday]]]:
        """
        Add a special session to the given list of special sessions.

        Parameters
        ----------
        name : str
            The name of the special session to add.
        ts : pd.Timestamp
            The session's date
        t : dt.time
            The special open/close time.
        special_sessions : List[Holiday]
            List of special sessions to add the new session to.

        Returns
        -------
        List[Holiday]
            The given list of special sessions with the new session added.
        """
        # Define the new Holiday.
        h = Holiday(name, year=ts.year, month=ts.month, day=ts.day)

        # Whether the new holiday has been added.
        added = False

        # Loop over all times and the respective rules.
        for t0, rules in special_sessions:
            # Check if time matches.
            if t == t0:
                # Add to existing list.
                rules.append(h)
                # Flip the flag.
                added = True
                # Break the loop.
                break

        # If the holiday was not added, add a new entry.
        if not added:
            special_sessions.append((t, [h]))

        return special_sessions

    def remove_holiday(
        ts: pd.Timestamp,
        regular_holidays_rules: list[Holiday],
        adhoc_holidays: list[pd.Timestamp] = [],
    ) -> tuple[list[Holiday], list[pd.Timestamp]]:
        """
        Remove any holidays that coincide with ts.

        Parameters
        ----------
        ts : pd.Timestamp
            The timestamp to remove.
        regular_holidays_rules : List[Holiday]
            The list of regular holidays.
        adhoc_holidays : List[pd.Timestamp]
            The list of ad-hoc holidays.

        Returns
        -------
        Tuple[List[Holiday], List[pd.Timestamp]]
            The modified lists of regular and ad-hoc holidays.
        """
        regular_holidays_rules = remove_day_from_rules(ts, regular_holidays_rules)
        # Remove any ad-hoc holidays that coincide with ts, maybe.
        adhoc_holidays = [adhoc_ts for adhoc_ts in adhoc_holidays if adhoc_ts != ts]
        return regular_holidays_rules, adhoc_holidays

    def remove_special_session(
        ts: pd.Timestamp,
        regular_special_sessions: list[tuple[dt.time, list[Holiday]]],
        adhoc_special_sessions: list[tuple[dt.time, pd.DatetimeIndex]],
    ) -> tuple[
        list[tuple[dt.time, list[Holiday]]],
        list[tuple[dt.time, pd.DatetimeIndex]],
    ]:
        """
        Remove any special sessions that coincide with ts.

        Parameters
        ----------
        ts : pd.Timestamp
            The timestamp to remove.
        regular_special_sessions : List[Tuple[dt.time, List[Holiday]]]
            The list of regular special sessions.
        adhoc_special_sessions : List[Tuple[dt.time, pd.DatetimeIndex]]
            The list of ad-hoc special sessions.

        Returns
        -------
        Tuple[List[Tuple[dt.time, List[Holiday]]], List[Tuple[dt.time, pd.DatetimeIndex]]]
            The modified lists of regular and ad-hoc special sessions.
        """
        # Loop over all times in regular_special_sessions.
        for _, rules in regular_special_sessions:
            if isinstance(rules, int):
                # This case should never happen as these types of special sessions are converted into regular holiday
                # calendars when setting up the extended class.

                # Check if the day of week corresponding to ts is the same as rules.
                if ts.dayofweek == rules:
                    raise NotImplementedError(
                        "Removing a special session date that corresponds to a day of week rule is not supported."
                    )
            else:
                # List of rules.
                _ = remove_day_from_rules(ts, rules)

        # Remove any ad-hoc special sessions that coincide with ts.
        adhoc_special_sessions = [
            (t, adhoc_ts.drop(ts, errors="ignore"))
            for t, adhoc_ts in adhoc_special_sessions
        ]

        # Remove empty DateTime indices.
        adhoc_special_sessions = [
            (t, adhoc_ts)
            for t, adhoc_ts in adhoc_special_sessions
            if not adhoc_ts.empty
        ]

        return regular_special_sessions, adhoc_special_sessions

    @validate_call
    def tags(
        self,
        *,
        tags: set[str] = Field(default_factory=frozenset),
        start: DateLikeInput | None = None,
        end: DateLikeInput | None = None,
        return_tags: bool = False,
    ) -> pd.DatetimeIndex | pd.Series:
        """
        Return days that have all given tags.

        Parameters
        ----------
        tags : Collection[str]
            The tags to search for. Days must have ALL of these tags to be included.
        start : pd.Timestamp | None, optional
            The start of the date range (inclusive). If None, no lower bound is applied.
        end : pd.Timestamp | None, optional
            The end of the date range (inclusive). If None, no upper bound is applied.
        return_tags : bool, optional
            If True, return a Series mapping dates to their tag sets.
            If False, return a DatetimeIndex of matching dates.

        Returns
        -------
        pd.DatetimeIndex | pd.Series
            If return_tags is False, returns a DatetimeIndex of dates that have all given tags.
            If return_tags is True, returns a Series mapping dates to their tag sets.
        """
        # Convert tags to a set for efficient comparison
        required_tags = frozenset(tags)

        # Filter dates that have all required tags and are within the date range
        matching_dates: dict[pd.Timestamp, set[str]] = {}
        for date, date_tags in self._custom_tags.items():
            # Check date range
            if start is not None and date < start:
                continue
            if end is not None and date > end:
                continue
            # Check if date has all required tags
            if required_tags.issubset(date_tags):
                matching_dates[date] = date_tags

        if return_tags:
            # Return a Series mapping dates to their tag sets
            return (
                pd.Series(matching_dates) if matching_dates else pd.Series(dtype=object)
            )
        else:
            # Return a DatetimeIndex of matching dates
            return (
                pd.DatetimeIndex(list(matching_dates.keys()))
                if matching_dates
                else pd.DatetimeIndex([])
            )

    def __init__(self, *args, **kwargs):
        # Initialize custom tags storage.
        self._custom_tags: dict[pd.Timestamp, set[str]] = {}

        # Save adjusted properties. Initialize with copies of the original properties.

        regular_holidays = regular_holidays_orig(self)
        regular_holidays = (
            list(copy(regular_holidays.rules)) if regular_holidays is not None else []
        )
        adhoc_holidays = adhoc_holidays_orig(self)
        adhoc_holidays = (
            [_ta.validate_python(x) for x in copy(adhoc_holidays)]
            if adhoc_holidays is not None
            else []
        )
        special_closes = special_closes_orig(self)
        special_closes = (
            [
                (
                    t,
                    [
                        DayOfWeekPeriodicHoliday("special close", d)
                    ]  # Convert weekly special close to rule.
                    if isinstance(d, int)
                    else list(copy(d.rules)),
                )  # Convert day-of-week to rule, else just copy.
                for t, d in copy(special_closes)
            ]
            if special_closes is not None
            else []
        )
        adhoc_special_closes = adhoc_special_closes_orig(self)
        adhoc_special_closes = (
            list(copy(adhoc_special_closes)) if adhoc_special_closes is not None else []
        )
        special_opens = special_opens_orig(self)
        special_opens = (
            [
                (
                    t,
                    [
                        DayOfWeekPeriodicHoliday("special open", d)
                    ]  # Convert weekly special open to rule.
                    if isinstance(d, int)
                    else list(copy(d.rules)),
                )  # Convert day-of-week to rule, else just copy.
                for t, d in copy(special_opens)
            ]
            if special_opens is not None
            else []
        )
        adhoc_special_opens = adhoc_special_opens_orig(self)
        adhoc_special_opens = (
            list(copy(adhoc_special_opens)) if adhoc_special_opens is not None else []
        )

        open_times = tuple(
            (d if d is not None else pd.Timestamp.min, t) for d, t in self.open_times
        )

        close_times = tuple(
            (d if d is not None else pd.Timestamp.min, t) for d, t in self.close_times
        )

        a = AdjustedProperties(
            open_times=open_times,
            close_times=close_times,
            weekmasks=get_weekmask_periods(self),
            regular_holidays=regular_holidays,
            adhoc_holidays=adhoc_holidays,
            special_closes=special_closes,
            adhoc_special_closes=adhoc_special_closes,
            special_opens=special_opens,
            adhoc_special_opens=adhoc_special_opens,
        )

        changeset: ChangeSet | None = (
            changeset_provider() if changeset_provider is not None else None
        )

        self._adjusted_properties = a

        if changeset is not None:
            for date, change in changeset.items():
                assert isinstance(change, DayChange)

                if change.tags is MISSING:
                    # Do not change tags.
                    pass
                else:
                    self._custom_tags[date] = set(change.tags)

                if change.spec:
                    if isinstance(change.spec, NonBusinessDaySpec):
                        regular_holiday_name_change = (
                            change.spec.holiday is MISSING
                            and change.name is not MISSING
                            and not HolidayCalendar(rules=a.regular_holidays)
                            .holidays(start=date, end=date)
                            .empty
                        )
                        if (
                            change.spec.holiday is not MISSING
                            or regular_holiday_name_change
                        ):
                            # Ensure day is not in holidays, special opens, or special closes.
                            a.regular_holidays, a.adhoc_holidays = remove_holiday(
                                date, a.regular_holidays, a.adhoc_holidays
                            )
                        a.special_opens, a.adhoc_special_opens = remove_special_session(
                            date, a.special_opens, a.adhoc_special_opens
                        )
                        a.special_closes, a.adhoc_special_closes = (
                            remove_special_session(
                                date, a.special_closes, a.adhoc_special_closes
                            )
                        )

                        # NOTE: Don't remove the day from monthly/quarterly expiries and other implied calendars.

                        if change.spec.holiday is True or regular_holiday_name_change:
                            # Add day to regular holidays.
                            name: str | None = (
                                change.name
                                if change.name is not MISSING
                                else get_name(date, self)
                            )
                            a.regular_holidays.append(
                                Holiday(
                                    name,
                                    year=date.year,
                                    month=date.month,
                                    day=date.day,
                                )
                            )

                        if change.spec.weekend_day is not MISSING:
                            a.weekmasks = set_weekday(
                                a.weekmasks, date, not change.spec.weekend_day
                            )

                    elif isinstance(change.spec, BusinessDaySpec):
                        name_prev: str | None = get_name(date, self)
                        regular_open = find_interval(a.open_times, date)[1]
                        regular_close = find_interval(a.close_times, date)[1]

                        def find_open() -> tuple[
                            dt.time, Literal["regular", "ad_hoc"] | None, str | None
                        ]:
                            for t, holidays in a.special_opens:
                                s = HolidayCalendar(rules=holidays).holidays(
                                    start=date, end=date, return_name=True
                                )
                                if not s.empty:
                                    return t, "regular", s.iloc[0]
                            for t, index in a.adhoc_special_opens:
                                if date in index:
                                    return t, "ad_hoc", None
                            return regular_open, None, None

                        def find_close() -> tuple[
                            dt.time, Literal["regular", "ad_hoc"] | None, str | None
                        ]:
                            for t, holidays in a.special_closes:
                                s = HolidayCalendar(rules=holidays).holidays(
                                    start=date, end=date, return_name=True
                                )
                                if not s.empty:
                                    return t, "regular", s.iloc[0]
                            for t, index in a.adhoc_special_closes:
                                if date in index:
                                    return t, "ad_hoc", None
                            return regular_close, None, None

                        prev_open, prev_open_type, prev_open_name = find_open()
                        prev_close, prev_close_type, prev_close_name = find_close()

                        # Determine the session times.
                        if change.spec.open is MISSING:
                            open_time = prev_open
                        else:
                            open_time = (
                                regular_open
                                if change.spec.open == "regular"
                                else change.spec.open
                            )
                        if change.spec.close is MISSING:
                            close_time = prev_close
                        else:
                            close_time = (
                                regular_close
                                if change.spec.close == "regular"
                                else change.spec.close
                            )

                        # Ensure day is not in holidays, special opens, or special closes.
                        a.regular_holidays, a.adhoc_holidays = remove_holiday(
                            date, a.regular_holidays, a.adhoc_holidays
                        )

                        if open_time != regular_open:
                            # Special open.
                            if (
                                prev_open_type in ("regular", "ad_hoc")
                                and prev_open == open_time
                                and (
                                    change.name is MISSING
                                    or change.name == prev_open_name
                                )
                            ):
                                # Keep original special open.
                                pass
                            else:
                                if prev_open_type is not None:
                                    # Remove previous special open.
                                    a.special_opens, a.adhoc_special_opens = (
                                        remove_special_session(
                                            date,
                                            a.special_opens,
                                            a.adhoc_special_opens,
                                        )
                                    )
                                # Insert new special open.
                                a.special_opens = add_special_session(
                                    change.name
                                    if change.name is not MISSING
                                    else name_prev,
                                    date,
                                    dt.time.fromisoformat(open_time.isoformat()),
                                    a.special_opens,
                                )
                        elif prev_open_type is not None:
                            # Remove previous special open.
                            a.special_opens, a.adhoc_special_opens = (
                                remove_special_session(
                                    date,
                                    a.special_opens,
                                    a.adhoc_special_opens,
                                )
                            )

                        if close_time != regular_close:
                            # Special close.
                            if (
                                prev_close_type in ("regular", "ad_hoc")
                                and prev_close == close_time
                                and (
                                    change.name is MISSING
                                    or change.name == prev_close_name
                                )
                            ):
                                # Keep original special close.
                                pass
                            else:
                                if prev_close_type is not None:
                                    # Remove previous special close.
                                    a.special_closes, a.adhoc_special_closes = (
                                        remove_special_session(
                                            date,
                                            a.special_closes,
                                            a.adhoc_special_closes,
                                        )
                                    )
                                # Insert new special close.
                                a.special_closes = add_special_session(
                                    change.name
                                    if change.name is not MISSING
                                    else name_prev,
                                    date,
                                    dt.time.fromisoformat(close_time.isoformat()),
                                    a.special_closes,
                                )
                        elif prev_close_type is not None:
                            # Remove previous special close.
                            a.special_closes, a.adhoc_special_closes = (
                                remove_special_session(
                                    date,
                                    a.special_closes,
                                    a.adhoc_special_closes,
                                )
                            )

                        # Day must be a week day.
                        a.weekmasks = set_weekday(a.weekmasks, date, True)
                    elif change.spec is MISSING:
                        pass  # Nothing to do.
                    else:
                        raise ValueError(f"Unsupported spec type: {type(change.spec)}")

        # Call upstream init method.
        init_orig(self, *args, **kwargs)

        # Set up monthly and quarterly expiries. This can only be done after holidays, special opens, and special closes
        # have been set up.
        a.monthly_expiries = (
            get_monthly_expiry_rules(day_of_week_expiry)
            if day_of_week_expiry is not None
            else []
        )
        a.quarterly_expiries = (
            get_quadruple_witching_rules(day_of_week_expiry)
            if day_of_week_expiry is not None
            else []
        )

        # Set up last trading days of the month.
        a.last_trading_days_of_months = get_last_day_of_month_rules()

        # Set up last regular trading days of the month. This can only be done after holidays, special opens,
        # special closes, monthly expiries, and quarterly expiries have been set up.
        a.last_regular_trading_days_of_months = get_last_day_of_month_rules()

        # Save a calendar with all holidays and another one with all holidays and special business days for later use.
        # These calendars are needed to generate calendars for monthly expiries, quarterly expiries, last trading days
        # of the month, and last regular trading days of the month. Each of these calendars defines contains days that
        # need to be rolled back to a previous business day if they fall on a holiday and/or special business day.
        self._holidays_shared = get_holidays_calendar(self)
        self._holidays_and_special_business_days_shared = merge_calendars(
            [
                get_holidays_calendar(self),
                get_special_opens_calendar(self),
                get_special_closes_calendar(self),
            ]
        )

        # Remove instances of weekly special open/close days that also coincide with a holiday.
        all_holidays = None

        def get_all_holidays() -> pd.DatetimeIndex:
            return self._holidays_shared.holidays(
                start=self.schedule.index[0], end=self.schedule.index[-1]
            )

        for t, rules in self._adjusted_properties.special_opens:
            for rule in rules:
                if isinstance(rule, DayOfWeekPeriodicHoliday):
                    if all_holidays is None:
                        all_holidays = get_all_holidays()
                    for ts in all_holidays.intersection(
                        rule.dates(
                            start_date=self.schedule.index[0],
                            end_date=self.schedule.index[-1],
                        )
                    ):
                        a.special_opens, a.adhoc_special_opens = remove_special_session(
                            ts, a.special_opens, a.adhoc_special_opens
                        )

        for t, rules in self._adjusted_properties.special_closes:
            for rule in rules:
                if isinstance(rule, DayOfWeekPeriodicHoliday):
                    if all_holidays is None:
                        all_holidays = get_all_holidays()
                    for ts in all_holidays.intersection(
                        rule.dates(
                            start_date=self.schedule.index[0],
                            end_date=self.schedule.index[-1],
                        )
                    ):
                        a.special_closes, a.adhoc_special_closes = (
                            remove_special_session(
                                ts, a.special_closes, a.adhoc_special_closes
                            )
                        )

    @property
    def regular_holidays(self) -> HolidayCalendar | None:
        return HolidayCalendar(rules=self._adjusted_properties.regular_holidays)

    @property
    def adhoc_holidays(self) -> list[pd.Timestamp]:
        return copy(self._adjusted_properties.adhoc_holidays)

    @property
    def special_closes(self) -> list[tuple[dt.time, HolidayCalendar | int]]:
        return [
            (t, rules if isinstance(rules, int) else HolidayCalendar(rules=rules))
            for t, rules in self._adjusted_properties.special_closes
        ]

    @property
    def special_closes_adhoc(self) -> list[tuple[dt.time, pd.DatetimeIndex]]:
        return copy(self._adjusted_properties.adhoc_special_closes)

    @property
    def special_opens(self) -> list[tuple[dt.time, HolidayCalendar | int]]:
        return [
            (t, rules if isinstance(rules, int) else HolidayCalendar(rules=rules))
            for t, rules in self._adjusted_properties.special_opens
        ]

    @property
    def special_opens_adhoc(self) -> list[tuple[dt.time, pd.DatetimeIndex]]:
        return copy(self._adjusted_properties.adhoc_special_opens)

    @property
    def weekend_days(self) -> HolidayCalendar | None:
        return get_days_calendar(self._adjusted_properties.weekmasks, mask="0")

    @property
    def week_days(self) -> HolidayCalendar | None:
        return get_days_calendar(self._adjusted_properties.weekmasks, mask="1")

    @property
    def holidays_all(self) -> HolidayCalendar | None:
        return get_holidays_calendar(self)

    @property
    def special_opens_all(self) -> HolidayCalendar | None:
        return get_special_opens_calendar(self)

    @property
    def special_closes_all(self) -> HolidayCalendar | None:
        return get_special_closes_calendar(self)

    @property
    def monthly_expiries(self) -> ExchangeCalendarsHolidayCalendar | None:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.monthly_expiries,
            other=self._holidays_and_special_business_days_shared,
            weekmask_periods=get_weekmask_periods(self),
            roll_fn=roll_one_day_same_month,
        )

    @property
    def quarterly_expiries(self) -> ExchangeCalendarsHolidayCalendar | None:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.quarterly_expiries,
            other=self._holidays_and_special_business_days_shared,
            weekmask_periods=get_weekmask_periods(self),
            roll_fn=roll_one_day_same_month,
        )

    @property
    def last_trading_days_of_months(
        self,
    ) -> ExchangeCalendarsHolidayCalendar | None:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.last_trading_days_of_months,
            other=self._holidays_shared,
            weekmask_periods=get_weekmask_periods(self),
            roll_fn=roll_one_day_same_month,
        )

    @property
    def last_regular_trading_days_of_months(
        self,
    ) -> ExchangeCalendarsHolidayCalendar | None:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.last_regular_trading_days_of_months,
            other=self._holidays_and_special_business_days_shared,
            weekmask_periods=get_weekmask_periods(self),
            roll_fn=roll_one_day_same_month,
        )

    @cached_property
    def day(self):
        if len(self._adjusted_properties.weekmasks) == 1:
            return CustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self._adjusted_properties.weekmasks[0].weekmask,
            )
        elif len(self._adjusted_properties.weekmasks) > 1:
            return MultipleWeekmaskCustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
                weekmasks=[
                    (wmp.start_date, wmp.end_date, wmp.weekmask)
                    for wmp in self._adjusted_properties.weekmasks
                ],
            )
        else:
            raise ValueError("No weekmasks found.")

    # Use type to create a new class.
    extended = type(
        cls.__name__ + "Extended",
        (cls, ExtendedExchangeCalendar),
        {
            "__init__": __init__,
            "regular_holidays": regular_holidays,
            "adhoc_holidays": adhoc_holidays,
            "special_closes": special_closes,
            "special_closes_adhoc": special_closes_adhoc,
            "special_opens": special_opens,
            "special_opens_adhoc": special_opens_adhoc,
            "weekend_days": weekend_days,
            "week_days": week_days,
            "holidays_all": holidays_all,
            "special_opens_all": special_opens_all,
            "special_closes_all": special_closes_all,
            "monthly_expiries": monthly_expiries,
            "quarterly_expiries": quarterly_expiries,
            "last_trading_days_of_months": last_trading_days_of_months,
            "last_regular_trading_days_of_months": last_regular_trading_days_of_months,
            "day": day,
            "tags": tags,
        },
    )

    return extended
