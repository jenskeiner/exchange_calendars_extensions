from typing import Optional, Callable

import pandas as pd
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday

from exchange_calendars_extras.offset import get_monthly_expiry_offset_class
from exchange_calendars_extras.util import get_day_of_week_name, get_month_name


def get_monthly_expiry_holiday(day_of_week: int, month: int, observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> Holiday:
    day_of_week_name = get_day_of_week_name(day_of_week)

    # convert month to capitalized name of month.
    month_name = get_month_name(month)

    return Holiday(f"MonthlyExpiry{month_name}{day_of_week_name}Offset", month=1, day=1,
                   offset=get_monthly_expiry_offset_class(day_of_week, month)(), observance=observance)


def get_monthly_expiry_calendar(day_of_week: int, observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each month's expiry, but exclude quarterly expiries aka quadruple witching.
    """
    rules = [get_monthly_expiry_holiday(day_of_week, month, observance) for month in [1, 2, 4, 5, 7, 8, 10, 11]]
    return HolidayCalendar(rules=rules)


def get_quadruple_witching_calendar(day_of_week: int, observance: Optional[Callable[[pd.Timestamp], pd.Timestamp]] = None) -> HolidayCalendar:
    """
    Return a calendar with a holiday for each month's expiry, but exclude quarterly expiries aka quadruple witching.
    """
    rules = [get_monthly_expiry_holiday(day_of_week, month, observance) for month in [3, 6, 9, 12]]
    return HolidayCalendar(rules=rules)
