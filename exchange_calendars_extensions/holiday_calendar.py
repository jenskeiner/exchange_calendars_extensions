from abc import ABC
from functools import reduce
from typing import Iterable, Optional, Callable, Union

from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar as ExchangeHolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
import pandas as pd

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
    rules = [get_monthly_expiry_holiday('quadruple witching', day_of_week, month, observance) for month in [3, 6, 9, 12]]
    return ExchangeHolidayCalendar(rules=rules)


def get_last_day_of_month_calendar(name: Optional[str] = 'last trading day of month', observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each last day of the month.
    """
    rules = [get_last_day_of_month_holiday(name, i, observance=observance) for i in range(1, 13)]
    return ExchangeHolidayCalendar(rules=rules)


class ExtendedExchangeCalendar(ExchangeCalendar, ABC):

    @property
    def weekend_days(self) -> HolidayCalendar:
        ...

    @property
    def holidays_all(self) -> HolidayCalendar:
        ...

    @property
    def special_opens_all(self) -> HolidayCalendar:
        ...

    @property
    def special_closes_all(self) -> HolidayCalendar:
        ...
    @property
    def monthly_expiries(self) -> Union[HolidayCalendar, None]:
        ...

    @property
    def quarterly_expiries(self) -> Union[HolidayCalendar, None]:
        ...

    @property
    def last_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        ...

    @property
    def last_regular_trading_days_of_months(self) -> Union[HolidayCalendar, None]:
        ...


# A function that takes a class as an argument and returns a class.
def extend_class(cls: type, day_of_week_expiry: int = 4) -> type:
    init = cls.__init__

    def __init__(self, *args, **kwargs):
        init(self, *args, **kwargs)
        self._holidays_all = get_holidays_calendar(self)
        self._special_opens_all = get_special_opens_calendar(self)
        self._special_closes_all = get_special_closes_calendar(self)
        special_days = merge_calendars([self._special_opens_all, self._special_closes_all])
        self._weekend_days = get_weekend_days_calendar(self)
        weekends_and_holidays = merge_calendars([self._weekend_days, self._holidays_all])
        weekends_holidays_and_special_days = merge_calendars([weekends_and_holidays, special_days])
        self._monthly_expiry_days = get_monthly_expiry_calendar(day_of_week_expiry, get_roll_backward_observance(weekends_holidays_and_special_days))
        self._quarterly_expiry_days = get_quadruple_witching_calendar(day_of_week_expiry, get_roll_backward_observance(weekends_holidays_and_special_days))
        self._last_trading_day_of_month = get_last_day_of_month_calendar('last trading day of month', get_roll_backward_observance(weekends_and_holidays))
        self._last_regular_trading_day_of_month = get_last_day_of_month_calendar('last regular trading day of month', get_roll_backward_observance(weekends_holidays_and_special_days))

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
