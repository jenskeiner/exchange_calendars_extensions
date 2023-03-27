import datetime
from abc import ABC
from dataclasses import dataclass
from functools import reduce
from typing import Iterable, Optional, Callable, Union, Type, Protocol, List, Tuple

from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar as ExchangeHolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
import pandas as pd

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
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition, name='ad-hoc special open day'))

    # Add regular special open days.
    for item in exchange_calendar.special_opens:
        _, definition = item
        if isinstance(definition, ExchangeHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition, name='special open day'))

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
        holiday_calendars.append(get_holiday_calendar_from_timestamps(definition, name='ad-hoc special close day'))

    # Add regular special close days.
    for item in exchange_calendar.special_closes:
        _, definition = item
        if isinstance(definition, ExchangeHolidayCalendar):
            holiday_calendars.append(definition)
        elif isinstance(definition, int):
            holiday_calendars.append(get_holiday_calendar_from_day_of_week(definition, name='special close day'))

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
    #regular_special_opens_rules: List[Holiday]
    #regular_special_closes_rules: List[Holiday]
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

    def is_in_holiday(holiday: Holiday, ts: pd.Timestamp) -> bool:
        """
        Determine if the given timestamp is a holiday.
        """
        return any([d == ts for d in holiday.dates(start_date=ts, end_date=ts)])

    def __init__(self, *args, **kwargs):
        if changeset_provider is not None:
            changeset: ExchangeCalendarChangeSet = changeset_provider()

            # Get a copy of the original rules.
            regular_holidays_rules: List[Holiday] = regular_holidays_orig(self).rules.copy()

            # Get a copy of the original ad-hoc holidays.
            adhoc_holidays: List[pd.Timestamp] = adhoc_holidays_orig(self).copy()

            # Remove holidays.

            # Loop over holidays to remove.
            for ts in changeset.holidays_remove:
                # Determine any rules that coincide with ts.
                rules_to_remove = [rule for rule in regular_holidays_rules if is_in_holiday(rule, ts)]

                # Modify rules to exclude ts.
                for rule in rules_to_remove:
                    # Create a copies of rule with end date set to ts - 1 day and ts + 1 day, respectively.
                    rule_before_ts = Holiday(rule.name, year=rule.year, month=rule.month, day=rule.day, end_date=ts - pd.Timedelta(days=1))
                    rule_after_ts = Holiday(rule.name, year=rule.year, month=rule.month, day=rule.day, start_date=ts + pd.Timedelta(days=1))
                    # Remove the original rule.
                    regular_holidays_rules.remove(rule)
                    # Add the new rules.
                    regular_holidays_rules.append(rule_before_ts)
                    regular_holidays_rules.append(rule_after_ts)

                # Remove any ad-hoc holidays that coincide with ts.
                adhoc_holidays = [adhoc_ts for adhoc_ts in adhoc_holidays if adhoc_ts != ts]

            # Add holidays.

            # Loop over holidays to add.
            for ts, name in changeset.holidays_add:
                # Determine number of existing rules or ad-hoc holidays that collide with ts.
                has_collisions = any([is_in_holiday(rule, ts) for rule in regular_holidays_rules]) or any([ts == adhoc_ts for adhoc_ts in adhoc_holidays])

                if not has_collisions:
                    # Add the holiday.
                    regular_holidays_rules.append(Holiday(name, year=ts.year, month=ts.month, day=ts.day))
                else:
                    # Skip adding the holiday.
                    pass

            # Get a copy of the original special closes.
            special_closes: List[Tuple[datetime.time, List[Holiday] | int]] = [(t, d if isinstance(d, int) else d.rules.copy() ) for t, d in special_closes_orig(self).copy()]

            # Get a copy of the original ad-hoc special opens.
            adhoc_special_closes: List[Tuple[datetime.time, pd.DatetimeIndex]] = adhoc_special_closes_orig(self).copy()

            # Remove special closes.
            
            # Loop over special closes to remove.
            #for ts in changeset.special_closes_remove:
                # Determine any special closes that coincide with ts.
            #    special_closes_to_remove = [(t, d) for t, d in special_closes if any([is_in_holiday(holiday, ts) for _, holiday in d])]

                # Remove the special closes.
            #    for special_close in special_closes_to_remove:
            #        special_closes.remove(special_close)

                # Remove any ad-hoc special closes that coincide with ts.
            #    adhoc_special_closes = [(t, adhoc_ts) for t, adhoc_ts in adhoc_special_closes if ts not in adhoc_ts]

            # Add special closes.
            
            # Loop over special closes to add.
            for ts, t, name in changeset.special_closes_add:
                # Determine number of existing special opens or ad-hoc special opens that collide with ts.
                has_collisions = any([any([is_in_holiday(holiday, ts) for _, holiday in rules]) for _, rules in special_closes]) or any([ts in adhoc_ts for _, adhoc_ts in adhoc_special_closes])

                if not has_collisions:
                    # Add the special close.
                    
                    # Define the new Holiday.
                    h = Holiday(name, year=ts.year, month=ts.month, day=ts.day)
                    
                    added = False
                    for t0, rules in special_closes:
                        if t == t0:
                            rules.append(h)
                            added = True
                            break
                    
                    if not added:
                        special_closes.append((t, [h]))
                else:
                    # Skip adding the special close.
                    pass


        else:
            # Just use the original rules and ad-hoc holidays.
            regular_holidays_rules = regular_holidays_orig(self).rules
            adhoc_holidays = adhoc_holidays_orig(self)

        self._adjusted_properties = AdjustedProperties(regular_holidays_rules=regular_holidays_rules,
                                                       adhoc_holidays=adhoc_holidays)

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
    def regular_holidays(self):
        return HolidayCalendar(rules=self._adjusted_properties.regular_holidays_rules)

    @property
    def adhoc_holidays(self):
        return self._adjusted_properties.adhoc_holidays.copy()

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
