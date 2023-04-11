import datetime
from abc import ABC
from dataclasses import dataclass
from functools import reduce
from typing import Iterable, Optional, Callable, Union, Type, Protocol, List, Tuple, runtime_checkable

import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar as ExchangeHolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
from exchange_calendars.pandas_extensions.holiday import Holiday as ExchangeCalendarsHoliday
from pandas.tseries.holiday import Holiday as PandasHoliday

from exchange_calendars_extensions import ExchangeCalendarChangeSet
from exchange_calendars_extensions.holiday import get_monthly_expiry_holiday, DayOfWeekPeriodicHoliday, \
    get_last_day_of_month_holiday
from exchange_calendars_extensions.observance import get_roll_backward_observance


class HolidayCalendar(ExchangeHolidayCalendar):
    def __init__(self, rules):
        super().__init__(rules=rules)

    def holidays(self, start=None, end=None, return_name=False):
        """
        Return all holidays between start and end, inclusive.
        """
        holidays = super().holidays(start=start, end=end, return_name=return_name)
        if return_name:
            return holidays[~holidays.index.duplicated()]
        else:
            return holidays.drop_duplicates()


def get_holiday_calendar_from_timestamps(timestamps: Iterable[pd.Timestamp], name: Optional[str] = None) -> HolidayCalendar:
    """
    Return a calendar with the given holidays.
    """
    rules = [Holiday(name, year=ts.year, month=ts.month, day=ts.day) for ts in list(dict.fromkeys(timestamps))]  # As of Python 3.7, dict preserves insertion order.
    return HolidayCalendar(rules=rules)


def get_holiday_calendar_from_day_of_week(day_of_week: int, name: Optional[str] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each day of the week.
    """
    rules = [DayOfWeekPeriodicHoliday(name, day_of_week)]
    return ExchangeHolidayCalendar(rules=rules)


def merge_calendars(calendars: Iterable[HolidayCalendar]) -> HolidayCalendar:
    """
    Return a calendar with all holidays from the given calendars merged into a single HolidayCalendar.
    """
    x = reduce(lambda x, y: HolidayCalendar(rules=[r for r in x.rules] + [r for r in y.rules]), calendars, HolidayCalendar(rules=[]))
    return x


def get_holidays_calendar(exchange_calendar: ExchangeCalendar) -> HolidayCalendar:
    holiday_calendars = [get_holiday_calendar_from_timestamps(exchange_calendar.adhoc_holidays, name='ad-hoc holiday'),
                         exchange_calendar.regular_holidays]

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_special_opens_calendar(exchange_calendar: ExchangeCalendar) -> HolidayCalendar:
    """
    Return a calendar with all special days from the given exchange calendar merged into a single HolidayCalendar.
    """
    holiday_calendars = []

    # Add ad-hoc special opens.
    for item in exchange_calendar.special_opens_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition, name='ad-hoc special open'))

    # Add regular special open days.
    for item in exchange_calendar.special_opens:
        _, definition = item
        if isinstance(definition, ExchangeHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition, name='special open'))

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_special_closes_calendar(exchange_calendar: ExchangeCalendar) -> HolidayCalendar:
    """
    Return a calendar with all special days from the given exchange calendar merged into a single HolidayCalendar.
    """
    holiday_calendars = []

    # Add ad-hoc special closes.
    for item in exchange_calendar.special_closes_adhoc:
        _, definition = item
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition, name='ad-hoc special close'))

    # Add regular special close days.
    for item in exchange_calendar.special_closes:
        _, definition = item
        if isinstance(definition, ExchangeHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition, name='special close'))

    # Merge all calendars by reducing the list of calendars into one, calling the merge method on each pair.
    return merge_calendars(holiday_calendars)


def get_weekend_days_calendar(exchange_calendar: ExchangeCalendar) -> HolidayCalendar:
    rules = [DayOfWeekPeriodicHoliday('weekend day', day_of_week) for day_of_week, v in enumerate(exchange_calendar.weekmask) if v == '0']
    return ExchangeHolidayCalendar(rules=rules)


def get_monthly_expiry_calendar(day_of_week: int, observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each month's expiry, but exclude quarterly expiry days aka quadruple witching.
    """
    rules = [get_monthly_expiry_holiday('monthly expiry', day_of_week, month, observance) for month in [1, 2, 4, 5, 7, 8, 10, 11]]
    return ExchangeHolidayCalendar(rules=rules)


def get_quadruple_witching_calendar(day_of_week: int, observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each quarterly expiry aka quadruple witching.
    """
    rules = [get_monthly_expiry_holiday('quarterly expiry', day_of_week, month, observance) for month in [3, 6, 9, 12]]
    return ExchangeHolidayCalendar(rules=rules)


def get_last_day_of_month_calendar(name: Optional[str] = 'last trading day of month', observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each last day of the month.
    """
    rules = [get_last_day_of_month_holiday(name, i, observance=observance) for i in range(1, 13)]
    return ExchangeHolidayCalendar(rules=rules)


@runtime_checkable
class ExchangeCalendarExtensions(Protocol):

    @property
    def weekend_days(self) -> HolidayCalendar:
        ...  # pragma: no cover

    @property
    def holidays_all(self) -> HolidayCalendar:
        ...  # pragma: no cover

    @property
    def special_opens_all(self) -> HolidayCalendar:
        ...  # pragma: no cover

    @property
    def special_closes_all(self) -> HolidayCalendar:
        ...  # pragma: no cover
    @property
    def monthly_expiries(self) -> Union[HolidayCalendar, None]:
        ...  # pragma: no cover

    @property
    def quarterly_expiries(self) -> Union[HolidayCalendar, None]:
        ...  # pragma: no cover

    @property
    def last_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        ...  # pragma: no cover

    @property
    def last_regular_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        ...


@dataclass
class AdjustedProperties:
    regular_holidays_rules: List[Holiday]
    adhoc_holidays: List[pd.Timestamp]
    special_closes: List[Tuple[datetime.time, List[Holiday] | int]]
    adhoc_special_closes: List[Tuple[datetime.time, pd.DatetimeIndex]]
    special_opens: List[Tuple[datetime.time, List[Holiday] | int]]
    adhoc_special_opens: List[Tuple[datetime.time, pd.DatetimeIndex]]
    #holidays_all: HolidayCalendar
    #special_opens_all: HolidayCalendar
    #special_closes_all: HolidayCalendar
    #weekend_days: HolidayCalendar
    #monthly_expiry_days: Optional[HolidayCalendar]
    #quarterly_expiry_days: Optional[HolidayCalendar]
    #last_trading_session_of_months: Optional[HolidayCalendar]
    #last_regular_session_days_of_months: Optional[HolidayCalendar]


class ExtendedExchangeCalendar(ExchangeCalendar, ExchangeCalendarExtensions, ABC):
    ...


def extend_class(cls: Type[ExchangeCalendar], day_of_week_expiry: int = 4,
                 changeset_provider: Callable[[], ExchangeCalendarChangeSet] = None) -> type:
    """
    Extend the given ExchangeCalendar class with additional properties.

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

    Similarly to monthly_expiries, the property quarterly_expiries returns expiry days for months March, June, September,
    and December, also known as quarterly expiries or triple/quadruple witching.

    The property last_trading_days_of_months returns the last trading day of each month. Note that the last trading day
    may be a special open/close day.

    The property last_regular_trading_days_of_months returns the last regular trading day of each month. The only
    difference to last_trading_days_of_months is that this property always returns the last regular trading day and
    never a special open/close day. That is, if the last trading day of a month is a special open/close day, here the
    day is rolled back to the previous regular trading day instead.

    :param cls: the input class to extend.
    :param day_of_week_expiry: the day of the week when expiry days are observed. Defaults to 4, which is Friday.
    :param changeset_provider: The optional function that returns a changeset to apply to the calendar.
    :return: the extended class.
    """
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
        """
        return any([d == ts for d in holiday.dates(start_date=ts, end_date=ts)])

    def clone_holiday(holiday: Union[PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday],
                      start_date: Optional[pd.Timestamp] = None, end_date: Optional[pd.Timestamp] = None) -> Union[PandasHoliday, ExchangeCalendarsHoliday, DayOfWeekPeriodicHoliday]:
        """
        Create a clone of the given holiday.
        """
        start_date_effective = start_date if start_date is not None else holiday.start_date
        end_date_effective = end_date if end_date is not None else holiday.end_date
        if isinstance(holiday, PandasHoliday):
            return PandasHoliday(name=holiday.name, year=holiday.year, month=holiday.month, day=holiday.day, offset=holiday.offset, observance=holiday.observance, start_date=start_date_effective, end_date=end_date_effective, days_of_week=holiday.days_of_week)
        elif isinstance(holiday, ExchangeCalendarsHoliday):
            return ExchangeCalendarsHoliday(name=holiday.name, year=holiday.year, month=holiday.month, day=holiday.day, offset=holiday.offset, observance=holiday.observance, start_date=start_date_effective, end_date=end_date_effective, days_of_week=holiday.days_of_week, tz=holiday.tz)
        elif isinstance(holiday, DayOfWeekPeriodicHoliday):
            return DayOfWeekPeriodicHoliday(name=holiday.name, day_of_week=holiday.weekday, start_date=start_date_effective, end_date=end_date_effective, tz=holiday.tz)
        else:
            raise NotImplementedError(f"Unsupported holiday type: {type(holiday)}")

    def remove_holiday(rules: List[Holiday], ts: pd.Timestamp) -> None:
        """
        Modify the given list of rules, if necessary, to exclude the given timestamp.

        Any rules that coincide with ts are removed and replaced by two new rules that don't contain ts. The list is
        modified in place.

        :param rules: The list of rules to modify.
        :param ts: The timestamp to exclude.
        :return: None
        """
        # Determine any rules that coincide with ts.
        remove = [rule for rule in rules if is_holiday(rule, ts)]

        # Modify rules to exclude ts.
        for rule in remove:
            # Create copies of rule with end date set to ts - 1 day and ts + 1 day, respectively.
            rule_before_ts = clone_holiday(rule, end_date=ts - pd.Timedelta(days=1))
            rule_after_ts = clone_holiday(rule, start_date=ts + pd.Timedelta(days=1))
            # Determine index of rule in list.
            rule_index = rules.index(rule)
            # Remove original rule.
            rules.pop(rule_index)
            # Add the new rules.
            rules.insert(rule_index, rule_before_ts)
            rules.insert(rule_index + 1, rule_after_ts)

    def add_special_session(name: str, ts: pd.Timestamp, t: datetime.time, special_sessions: List[Holiday],
                            adhoc_special_sessions: List[Tuple[datetime.time, pd.DatetimeIndex]]) -> None:
        # Determine number of existing special opens or ad-hoc special opens that collide with ts.
        has_collisions = any([any([is_holiday(rule, ts) for rule in rules]) for _, rules in special_sessions]) or any(
            [ts in adhoc_ts for _, adhoc_ts in adhoc_special_sessions])

        if not has_collisions:
            # Add the special session.

            # Define the new Holiday.
            h = Holiday(name, year=ts.year, month=ts.month, day=ts.day)

            # Whether the new holiday has been added.
            added = False

            # Loop over all times and the respective rules.
            for t0, rules in special_sessions:
                # CHeck if time matches.
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
        else:
            # Skip adding the special session.
            pass

    def __init__(self, *args, **kwargs):
        # Get a copy of the original rules.
        regular_holidays_rules: List[Holiday] = regular_holidays_orig(self).rules.copy()

        # Get a copy of the original ad-hoc holidays.
        adhoc_holidays: List[pd.Timestamp] = adhoc_holidays_orig(self).copy()

        # Get a copy of the original special closes.
        special_closes: List[Tuple[datetime.time, List[Holiday] | int]] = [
            (t, d if isinstance(d, int) else d.rules.copy()) for t, d in special_closes_orig(self).copy()]

        # Get a copy of the original ad-hoc special opens.
        adhoc_special_closes: List[Tuple[datetime.time, pd.DatetimeIndex]] = adhoc_special_closes_orig(self).copy()

        # Get a copy of the original special opens.
        special_opens: List[Tuple[datetime.time, List[Holiday] | int]] = [
            (t, d if isinstance(d, int) else d.rules.copy()) for t, d in special_opens_orig(self).copy()]

        # Get a copy of the original ad-hoc special opens.
        adhoc_special_opens: List[Tuple[datetime.time, pd.DatetimeIndex]] = adhoc_special_opens_orig(self).copy()

        if changeset_provider is not None:
            changeset: ExchangeCalendarChangeSet = changeset_provider()

            if changeset is not None:
                # Remove holidays.

                # Loop over holidays to remove.
                for ts in changeset.holidays_remove:
                    remove_holiday(regular_holidays_rules, ts)

                    # Remove any ad-hoc holidays that coincide with ts.
                    adhoc_holidays = [adhoc_ts for adhoc_ts in adhoc_holidays if adhoc_ts != ts]

                # Add holidays.

                # Loop over holidays to add.
                for ts, name in changeset.holidays_add:
                    # Determine number of existing rules or ad-hoc holidays that collide with ts.
                    has_collisions = any([is_holiday(rule, ts) for rule in regular_holidays_rules]) or any([ts == adhoc_ts for adhoc_ts in adhoc_holidays])

                    if has_collisions:
                        # Remove the holiday first.
                        remove_holiday(regular_holidays_rules, ts)

                        # Remove any ad-hoc holidays that coincide with ts.
                        adhoc_holidays = [adhoc_ts for adhoc_ts in adhoc_holidays if adhoc_ts != ts]

                    # Add the holiday.
                    regular_holidays_rules.append(Holiday(name, year=ts.year, month=ts.month, day=ts.day))

                # Remove special closes.

                # Loop over special closes to remove.
                for ts in changeset.special_closes_remove:
                    # Loop over all times in special_closes.
                    for _, rules in special_closes:
                        if isinstance(rules, int):
                            # Check if the day of week corresponding to ts is the same as rules.
                            if ts.dayofweek == rules:
                                raise NotImplementedError("Removing a special close date that corresponds to a day of week rule is not supported.")
                        else:
                            # List of rules.
                            remove_holiday(rules, ts)

                    # Remove any ad-hoc holidays that coincide with ts.
                    adhoc_special_closes = [(_, adhoc_ts) if True else (_, adhoc_ts.drop(ts)) for _, adhoc_ts in adhoc_special_closes]

                # Add special closes.

                # Loop over special closes to add.
                for ts, t, name in changeset.special_closes_add:
                    add_special_session(name, ts, t, special_closes, adhoc_special_closes)

                # Remove special opens.

                # Loop over special opens to remove.
                for ts in changeset.special_opens_remove:
                    # Loop over all times in special_opens.
                    for _, rules in special_opens:
                        if isinstance(rules, int):
                            # Check if the day of week corresponding to ts is the same as rules.
                            if ts.dayofweek == rules:
                                raise NotImplementedError(
                                    "Removing a special open date that corresponds to a day of week rule is not supported.")
                        else:
                            # List of rules.
                            remove_holiday(rules, ts)

                    # Remove any ad-hoc holidays that coincide with ts.
                    adhoc_special_opens = [(_, adhoc_ts) if True else (_, adhoc_ts.drop(ts)) for _, adhoc_ts in
                                           adhoc_special_opens]

                # Add special opens.

                # Loop over special opens to add.
                for ts, t, name in changeset.special_opens_add:
                    add_special_session(name, ts, t, special_opens, adhoc_special_opens)

        self._adjusted_properties = AdjustedProperties(regular_holidays_rules=regular_holidays_rules,
                                                       adhoc_holidays=adhoc_holidays,
                                                       special_closes=special_closes,
                                                       adhoc_special_closes=adhoc_special_closes,
                                                       special_opens=special_opens,
                                                       adhoc_special_opens=adhoc_special_opens)

        init_orig(self, *args, **kwargs)

        self._holidays_all = get_holidays_calendar(self)
        self._special_opens_all = get_special_opens_calendar(self)
        self._special_closes_all = get_special_closes_calendar(self)
        special_business_days = merge_calendars([self._special_opens_all, self._special_closes_all])
        self._weekend_days = get_weekend_days_calendar(self)
        weekends_and_holidays = merge_calendars([self._weekend_days, self._holidays_all])
        weekends_holidays_and_special_business_days = merge_calendars([weekends_and_holidays, special_business_days])
        self._monthly_expiry_days = get_monthly_expiry_calendar(day_of_week_expiry, get_roll_backward_observance(weekends_holidays_and_special_business_days))
        self._quarterly_expiry_days = get_quadruple_witching_calendar(day_of_week_expiry, get_roll_backward_observance(weekends_holidays_and_special_business_days))
        self._last_trading_day_of_month = get_last_day_of_month_calendar('last trading day of month', get_roll_backward_observance(weekends_and_holidays))
        self._last_regular_trading_day_of_month = get_last_day_of_month_calendar('last regular trading day of month', get_roll_backward_observance(weekends_holidays_and_special_business_days))

    @property
    def regular_holidays(self) -> HolidayCalendar | None:
        return HolidayCalendar(rules=self._adjusted_properties.regular_holidays_rules)

    @property
    def adhoc_holidays(self) -> List[pd.Timestamp]:
        return self._adjusted_properties.adhoc_holidays.copy()

    @property
    def special_closes(self) -> List[Tuple[datetime.time, HolidayCalendar | int]]:
        return [(t, HolidayCalendar(rules=rules)) for t, rules in self._adjusted_properties.special_closes]

    @ property
    def special_closes_adhoc(self) -> List[Tuple[datetime.time, pd.DatetimeIndex]]:
        return self._adjusted_properties.adhoc_special_closes.copy()

    @property
    def special_opens(self) -> List[Tuple[datetime.time, HolidayCalendar | int]]:
        return [(t, HolidayCalendar(rules=rules)) for t, rules in self._adjusted_properties.special_opens]

    @ property
    def special_opens_adhoc(self) -> List[Tuple[datetime.time, pd.DatetimeIndex]]:
        return self._adjusted_properties.adhoc_special_opens.copy()

    @property
    def weekend_days(self) -> Union[HolidayCalendar, None]:
        return self._weekend_days

    @property
    def holidays_all(self) -> Union[HolidayCalendar, None]:
        return self._holidays_all

    @property
    def special_opens_all(self) -> Union[HolidayCalendar, None]:
        return self._special_opens_all

    @property
    def special_closes_all(self) -> Union[HolidayCalendar, None]:
        return self._special_closes_all

    @property
    def monthly_expiries(self) -> Union[HolidayCalendar, None]:
        return self._monthly_expiry_days

    @property
    def quarterly_expiries(self) -> Union[HolidayCalendar, None]:
        return self._quarterly_expiry_days

    @property
    def last_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        return self._last_trading_day_of_month

    @property
    def last_regular_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        return self._last_regular_trading_day_of_month

    # Use type to create a new class.
    extended = type(cls.__name__ + "Extended", (cls, ExtendedExchangeCalendar), {
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
        "last_regular_trading_days_of_months": last_regular_trading_days_of_months
    })

    return extended
