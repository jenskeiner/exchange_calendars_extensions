import datetime
from abc import ABC
from collections import OrderedDict
from collections.abc import Iterable
from copy import copy
from dataclasses import field, dataclass
from functools import reduce
from typing import (
    Optional,
    Callable,
    Union,
    Protocol,
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
from pandas.tseries.holiday import Holiday as PandasHoliday
from pydantic import validate_call, TypeAdapter, ConfigDict

from exchange_calendars_extensions.api.changes import (
    ChangeSet,
    DayType,
    DayMeta,
    TimestampLike,
    DateLike,
)
from exchange_calendars_extensions.core.holiday import (
    get_monthly_expiry_holiday,
    DayOfWeekPeriodicHoliday,
    get_last_day_of_month_holiday,
)

# Timdelta that represents a day minus the smallest increment of time.
ONE_DAY_MINUS_EPS = pd.Timedelta(1, "d") - pd.Timedelta(1, "ns")


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
            return holidays[~holidays.index.duplicated()]
        else:
            return holidays.drop_duplicates()


def get_conflicts(
    holidays_dates: list[Union[pd.Timestamp, None]],
    other_holidays: pd.DatetimeIndex,
    weekend_days: Iterable[int],
) -> list[int]:
    """
    Get the indices of holidays that coincide with holidays from the other calendar or the given weekend days.

    Parameters
    ----------
    holidays_dates : List[Union[pd.Timestamp, None]]
        The dates of the holidays. A date may be None and is then ignored.
    other_holidays : pd.DatetimeIndex
        The dates of the holidays from the other calendar.
    weekend_days : Iterable[int]
        The days of the week that are considered weekend days.

    Returns
    -------
    List[int]
        The indices of holidays that coincide with holidays from the other calendar or the given weekend days.
    """

    # Determine the indices of holidays that coincide with holidays from the other calendar.
    return [
        i
        for i in range(len(holidays_dates))
        if holidays_dates[i] is not None
        and (
            holidays_dates[i] in other_holidays
            or holidays_dates[i].weekday() in weekend_days
            or holidays_dates[i] in holidays_dates[i + 1 :]
        )
    ]


# A function that takes a date and returns a date or None.
RollFn = Callable[[pd.Timestamp], Union[pd.Timestamp, None]]


def roll_one_day_same_month(d: pd.Timestamp) -> Union[pd.Timestamp, None]:
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


class AdjustedHolidayCalendar(ExchangeCalendarsHolidayCalendar):
    def __init__(
        self,
        rules,
        other: ExchangeCalendarsHolidayCalendar,
        weekmask: str,
        roll_fn: RollFn = lambda d: d - pd.Timedelta(days=1),
    ) -> None:
        super().__init__(rules=rules)
        self._other = other
        self._weekend_days = {d for d in range(7) if weekmask[d] == "0"}
        self._roll_fn = roll_fn

    def holidays(self, start=None, end=None, return_name=False):
        # Get the holidays from the parent class.
        holidays = super().holidays(start=start, end=end, return_name=return_name)

        # Get the holidays from the other calendar.
        other_holidays = self._other.holidays(start=start, end=end, return_name=False)

        holidays_dates = list(holidays.index if return_name else holidays)

        conflicts = get_conflicts(holidays_dates, other_holidays, self._weekend_days)

        if len(conflicts) == 0:
            return holidays

        while True:
            # For each index of a conflicting holiday, adjust the date by using the roll function.
            for i in conflicts:
                holidays_dates[i] = self._roll_fn(holidays_dates[i])

            conflicts = get_conflicts(
                holidays_dates, other_holidays, self._weekend_days
            )

            if len(conflicts) == 0:
                break

        if return_name:
            # Return a series, filter out dates that are None.
            return pd.Series(
                {
                    d: n
                    for d, n in zip(holidays_dates, holidays.values)
                    if d is not None
                    and (start is None or d >= start)
                    and (end is None or d <= end)
                }
            )
        else:
            # Return index, filter out dates that are None.
            return pd.DatetimeIndex(
                [
                    d
                    for d in holidays_dates
                    if d is not None
                    and (start is None or d >= start)
                    and (end is None or d <= end)
                ]
            )


_ta = TypeAdapter(DateLike, config=ConfigDict(arbitrary_types_allowed=True))


def get_holiday_calendar_from_timestamps(
    timestamps: list[pd.Timestamp], name: Optional[str] = None
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
            name, year=ts.year, month=ts.month, day=ts.day, start_date=ts, end_date=ts
        )
        for ts in set(dict.fromkeys(timestamps))
    ]  # As of Python 3.7, dict preserves insertion order.

    # Return a new HolidayCalendar with the given rules.
    return ExchangeCalendarsHolidayCalendar(rules=rules)


def get_holiday_calendar_from_day_of_week(
    day_of_week: int, name: Optional[str] = None
) -> HolidayCalendar:
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
    rules = [DayOfWeekPeriodicHoliday(name, day_of_week)]

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
        get_holiday_calendar_from_timestamps(
            exchange_calendar.adhoc_holidays, name="ad-hoc holiday"
        ),
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
        holiday_calendars.append(
            get_holiday_calendar_from_timestamps(definition, name="ad-hoc special open")
        )

    # Add regular special open days.
    for item in exchange_calendar.special_opens:
        _, definition = item
        if isinstance(definition, ExchangeCalendarsHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(
                get_holiday_calendar_from_day_of_week(definition, name="special open")
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
        holiday_calendars.append(
            get_holiday_calendar_from_timestamps(
                definition, name="ad-hoc special close"
            )
        )

    # Add regular special close days.
    for item in exchange_calendar.special_closes:
        _, definition = item
        if isinstance(definition, ExchangeCalendarsHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(
                get_holiday_calendar_from_day_of_week(definition, name="special close")
            )

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_weekend_days_calendar(
    exchange_calendar: ExchangeCalendar,
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
    """
    rules = [
        DayOfWeekPeriodicHoliday("weekend day", day_of_week)
        for day_of_week, v in enumerate(exchange_calendar.weekmask)
        if v == "0"
    ]
    return ExchangeCalendarsHolidayCalendar(rules=rules)


def get_monthly_expiry_rules(
    day_of_week: int,
    observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None,
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
        get_monthly_expiry_holiday("monthly expiry", day_of_week, month, observance)
        for month in [1, 2, 4, 5, 7, 8, 10, 11]
    ]


def get_quadruple_witching_rules(
    day_of_week: int,
    observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None,
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
        get_monthly_expiry_holiday("quarterly expiry", day_of_week, month, observance)
        for month in [3, 6, 9, 12]
    ]


def get_last_day_of_month_rules(
    name: Optional[str] = "last trading day of month",
    observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None,
) -> list[Holiday]:
    """
    Return a list of rules for a calendar with a holiday for each last trading day of the month.

    Parameters
    ----------
    name : Optional[str], optional
        The name to use for the holidays, by default 'last trading day of month'.
    observance : Optional[Callable[[pd.Timestamp], pd.Timestamp]], optional
        The observance function to use, by default None.

    Returns
    -------
    List[Holiday]
        A list of rules for a calendar with a holiday for each last trading day of the month.
    """
    return [
        get_last_day_of_month_holiday(name, i, observance=observance)
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
    def monthly_expiries(self) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        """
        Return a holiday calendar with a holiday for each monthly expiry, but excluding quarterly expiry days.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each monthly expiry.
        """
        ...  # pragma: no cover

    @property
    def quarterly_expiries(self) -> Union[ExchangeCalendarsHolidayCalendar, None]:
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
    ) -> Union[ExchangeCalendarsHolidayCalendar, None]:
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
    ) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        """
        Return a holiday calendar with a holiday for each last regular trading day of the month.

        Returns
        -------
        ExchangeCalendarsHolidayCalendar
            A new HolidayCalendar with a holiday for each last regular trading day of the month.
        """
        ...

    def meta(
        self,
        start: Union[TimestampLike, None] = None,
        end: Union[TimestampLike, None] = None,
    ) -> dict[pd.Timestamp, DayMeta]: ...


@dataclass
class AdjustedProperties:
    """
    A dataclass for storing adjusted properties of an exchange calendar.
    """

    # The regular holidays of the exchange calendar.
    regular_holidays: list[Holiday]

    # The ad-hoc holidays of the exchange calendar.
    adhoc_holidays: list[pd.Timestamp]

    # The special closes of the exchange calendar.
    special_closes: list[tuple[datetime.time, Union[list[Holiday], int]]]

    # The ad-hoc special closes of the exchange calendar.
    adhoc_special_closes: list[tuple[datetime.time, pd.DatetimeIndex]]

    # The special opens of the exchange calendar.
    special_opens: list[tuple[datetime.time, Union[list[Holiday], int]]]

    # The ad-hoc special opens of the exchange calendar.
    adhoc_special_opens: list[tuple[datetime.time, pd.DatetimeIndex]]

    # The quarterly expiry days of the exchange calendar.
    quarterly_expiries: list[Holiday] = field(default_factory=list)

    # The monthly expiry days of the exchange calendar.
    monthly_expiries: list[Holiday] = field(default_factory=list)

    # The last trading days of the month of the exchange calendar.
    last_trading_days_of_months: list[Holiday] = field(default_factory=list)

    # The last regular trading days of the month of the exchange calendar.
    last_regular_trading_days_of_months: list[Holiday] = field(default_factory=list)


class ExtendedExchangeCalendar(ExchangeCalendar, ExchangeCalendarExtensions, ABC):
    """
    Abstract base class for exchange calendars with extended functionality.
    """

    ...


def extend_class(
    cls: type[ExchangeCalendar],
    day_of_week_expiry: Union[int, None] = None,
    changeset_provider: Union[Callable[[], ChangeSet], None] = None,
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
    - monthly_expiries: a HolidayCalendar with all monthly expiry days.
    - quarterly_expiries: a HolidayCalendar with all quarterly expiry days.
    - last_trading_days_of_months: a HolidayCalendar with the respective last trading day of each month.
    - last_regular_trading_days_of_months: a HolidayCalendar with the respective last regular trading day of each month.

    The properties holidays_all, special_opens_all, and special_closes_all make it more convenient to determine relevant
    days in a given date range since regular and ad-hoc special days are merged into a single calendar.

    The property weekend_days may be useful to determine weekend days in a given date range since parsing the weekmask
    property of the underlying ExchangeCalendar class is avoided.

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
        holiday: Union[
            PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday
        ],
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
    ) -> Union[PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday]:
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
        t: datetime.time,
        special_sessions: list[tuple[datetime.time, list[Holiday]]],
    ) -> list[tuple[datetime.time, list[Holiday]]]:
        """
        Add a special session to the given list of special sessions.

        Parameters
        ----------
        name : str
            The name of the special session to add.
        ts : pd.Timestamp
            The session's date
        t : datetime.time
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
        regular_special_sessions: list[tuple[datetime.time, list[Holiday]]],
        adhoc_special_sessions: list[tuple[datetime.time, pd.DatetimeIndex]],
    ) -> tuple[
        list[tuple[datetime.time, list[Holiday]]],
        list[tuple[datetime.time, pd.DatetimeIndex]],
    ]:
        """
        Remove any special sessions that coincide with ts.

        Parameters
        ----------
        ts : pd.Timestamp
            The timestamp to remove.
        regular_special_sessions : List[Tuple[datetime.time, List[Holiday]]]
            The list of regular special sessions.
        adhoc_special_sessions : List[Tuple[datetime.time, pd.DatetimeIndex]]
            The list of ad-hoc special sessions.

        Returns
        -------
        Tuple[List[Tuple[datetime.time, List[Holiday]]], List[Tuple[datetime.time, pd.DatetimeIndex]]]
            The modified lists of regular and ad-hoc special sessions.
        """
        # Loop over all times in regular_special_sessions.
        for _, rules in regular_special_sessions:
            if isinstance(rules, int):
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

    def __init__(self, *args, **kwargs):
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
                    [DayOfWeekPeriodicHoliday("special close", d)]
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
                    [DayOfWeekPeriodicHoliday("special open", d)]
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
        a = AdjustedProperties(
            regular_holidays=regular_holidays,
            adhoc_holidays=adhoc_holidays,
            special_closes=special_closes,
            adhoc_special_closes=adhoc_special_closes,
            special_opens=special_opens,
            adhoc_special_opens=adhoc_special_opens,
        )

        # Get changeset from provider, maybe.
        changeset: Union[ChangeSet, None] = (
            changeset_provider() if changeset_provider is not None else None
        )

        # Set changeset to None if it is empty.
        if changeset is not None and len(changeset) <= 0:
            changeset = None

        if changeset is not None:
            # Remove all changed days from holidays, special opens, and special closes.
            for ts in changeset.all_days(include_meta=False):
                a.regular_holidays, a.adhoc_holidays = remove_holiday(
                    ts, a.regular_holidays, a.adhoc_holidays
                )
                a.special_opens, a.adhoc_special_opens = remove_special_session(
                    ts, a.special_opens, a.adhoc_special_opens
                )
                a.special_closes, a.adhoc_special_closes = remove_special_session(
                    ts, a.special_closes, a.adhoc_special_closes
                )

            # Add holiday, special opens, and special closes.
            for date, props in changeset.add.items():
                if props.type == DayType.HOLIDAY:
                    # Add the holiday.
                    a.regular_holidays.append(
                        Holiday(
                            props.name, year=date.year, month=date.month, day=date.day
                        )
                    )
                elif props.type == DayType.SPECIAL_OPEN:
                    # Add the special open.
                    a.special_opens = add_special_session(
                        props.name, date, props.time, a.special_opens
                    )
                elif props.type == DayType.SPECIAL_CLOSE:
                    # Add the special close.
                    a.special_closes = add_special_session(
                        props.name, date, props.time, a.special_closes
                    )

        self._adjusted_properties = a

        # Save meta.
        self._meta = changeset.meta if changeset is not None else {}

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

        if changeset is not None:
            # Remove all changed days from monthly and quarterly expiries.
            for ts in changeset.all_days(include_meta=False):
                a.monthly_expiries, _ = remove_holiday(ts, a.monthly_expiries)
                a.quarterly_expiries, _ = remove_holiday(ts, a.quarterly_expiries)

            # Add monthly and quarterly expiries.
            for date, props in changeset.add.items():
                if props.type == DayType.MONTHLY_EXPIRY:
                    # Add the monthly expiry.
                    a.monthly_expiries.append(
                        Holiday(
                            props.name, year=date.year, month=date.month, day=date.day
                        )
                    )
                elif props.type == DayType.QUARTERLY_EXPIRY:
                    # Add the quarterly expiry.
                    a.quarterly_expiries.append(
                        Holiday(
                            props.name, year=date.year, month=date.month, day=date.day
                        )
                    )

        # Set up last trading days of the month.
        a.last_trading_days_of_months = get_last_day_of_month_rules(
            "last trading day of month"
        )

        # Set up last regular trading days of the month. This can only be done after holidays, special opens,
        # special closes, monthly expiries, and quarterly expiries have been set up.
        a.last_regular_trading_days_of_months = get_last_day_of_month_rules(
            "last regular trading day of month"
        )

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
    def regular_holidays(self) -> Union[HolidayCalendar, None]:
        return HolidayCalendar(rules=self._adjusted_properties.regular_holidays)

    @property
    def adhoc_holidays(self) -> list[pd.Timestamp]:
        return copy(self._adjusted_properties.adhoc_holidays)

    @property
    def special_closes(self) -> list[tuple[datetime.time, Union[HolidayCalendar, int]]]:
        return [
            (t, rules if isinstance(rules, int) else HolidayCalendar(rules=rules))
            for t, rules in self._adjusted_properties.special_closes
        ]

    @property
    def special_closes_adhoc(self) -> list[tuple[datetime.time, pd.DatetimeIndex]]:
        return copy(self._adjusted_properties.adhoc_special_closes)

    @property
    def special_opens(self) -> list[tuple[datetime.time, Union[HolidayCalendar, int]]]:
        return [
            (t, rules if isinstance(rules, int) else HolidayCalendar(rules=rules))
            for t, rules in self._adjusted_properties.special_opens
        ]

    @property
    def special_opens_adhoc(self) -> list[tuple[datetime.time, pd.DatetimeIndex]]:
        return copy(self._adjusted_properties.adhoc_special_opens)

    @property
    def weekend_days(self) -> Union[HolidayCalendar, None]:
        return get_weekend_days_calendar(self)

    @property
    def holidays_all(self) -> Union[HolidayCalendar, None]:
        return get_holidays_calendar(self)

    @property
    def special_opens_all(self) -> Union[HolidayCalendar, None]:
        return get_special_opens_calendar(self)

    @property
    def special_closes_all(self) -> Union[HolidayCalendar, None]:
        return get_special_closes_calendar(self)

    @property
    def monthly_expiries(self) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.monthly_expiries,
            other=self._holidays_and_special_business_days_shared,
            weekmask=self.weekmask,
            roll_fn=roll_one_day_same_month,
        )

    @property
    def quarterly_expiries(self) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.quarterly_expiries,
            other=self._holidays_and_special_business_days_shared,
            weekmask=self.weekmask,
            roll_fn=roll_one_day_same_month,
        )

    @property
    def last_trading_days_of_months(
        self,
    ) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.last_trading_days_of_months,
            other=self._holidays_shared,
            weekmask=self.weekmask,
            roll_fn=roll_one_day_same_month,
        )

    @property
    def last_regular_trading_days_of_months(
        self,
    ) -> Union[ExchangeCalendarsHolidayCalendar, None]:
        return AdjustedHolidayCalendar(
            rules=self._adjusted_properties.last_regular_trading_days_of_months,
            other=self._holidays_and_special_business_days_shared,
            weekmask=self.weekmask,
            roll_fn=roll_one_day_same_month,
        )

    @validate_call(config={"arbitrary_types_allowed": True})
    def meta(
        self,
        start: Union[TimestampLike, None] = None,
        end: Union[TimestampLike, None] = None,
    ) -> dict[pd.Timestamp, DayMeta]:
        # Check that when start and end are both given, they are both timezone-aware or both timezone-naive.
        if start and end:
            if bool(start.tz) != bool(end.tz):
                raise ValueError(
                    "start and end must both be timezone-aware or both timezone-naive."
                )

            if start > end:
                raise ValueError("start must be less than or equal to end.")

        # Get timezone from start or end, if given.
        tz = (start and start.tz) or (end and end.tz) or None

        # Return a dictionary with all metadata for days in the given range. A day is considered to comprise the full
        # period between midnight (inclusive) and the next midnight (exclusive). If that period overlaps with the given
        # range, the day is included in the result.
        #
        # Note: The code assumes that ONE_DAY_MINUS_EPS gets applied to timezone-naive timestamps where it corresponds
        # to (almost) a calendar day. The same may not be true for timezone-aware timestamps when the period includes
        # e.g. a DST transition.
        if tz:
            return OrderedDict(
                [
                    (k, v)
                    for k, v in self._meta.items()
                    if (
                        start is None
                        or (k + ONE_DAY_MINUS_EPS).tz_localize(tz=self.tz) >= start
                    )
                    and (end is None or (k.tz_localize(tz=self.tz)) <= end)
                ]
            )
        else:
            return OrderedDict(
                [
                    (k, v)
                    for k, v in self._meta.items()
                    if (start is None or (k + ONE_DAY_MINUS_EPS) >= start)
                    and (end is None or k <= end)
                ]
            )

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
            "holidays_all": holidays_all,
            "special_opens_all": special_opens_all,
            "special_closes_all": special_closes_all,
            "monthly_expiries": monthly_expiries,
            "quarterly_expiries": quarterly_expiries,
            "last_trading_days_of_months": last_trading_days_of_months,
            "last_regular_trading_days_of_months": last_regular_trading_days_of_months,
            "meta": meta,
        },
    )

    return extended
