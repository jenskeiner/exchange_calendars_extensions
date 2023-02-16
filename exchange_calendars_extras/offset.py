from datetime import datetime, date

import pandas as pd
from pandas._libs.tslibs import localize_pydatetime
from pandas._libs.tslibs.offsets import Easter, apply_wraps

from exchange_calendars_extras.util import get_month_name, get_day_of_week_name, third_day_of_week_in_month


class AbstractHolidayOffset(Easter):

    @staticmethod
    def _is_normalized(dt):
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0:
            # Regardless of whether dt is datetime vs Timestamp
            return False
        if isinstance(dt, pd.Timestamp):
            return dt.nanosecond == 0
        return True

    """
    Auxiliary class for DateOffset instances for the different holidays.
    """

    @property
    def holiday(self):
        """
        Return the Gregorian date for the holiday in a given Gregorian calendar
        year.
        """
        pass

    @apply_wraps
    def _apply(self, other):
        current = self.holiday(other.year)
        current = datetime(current.year, current.month, current.day)
        current = localize_pydatetime(current, other.tzinfo)

        n = self.n
        if n >= 0 and other < current:
            n -= 1
        elif n < 0 and other > current:
            n += 1
        # TODO: Why does this handle the 0 case the opposite of others?

        new = self.holiday(other.year + n)
        new = datetime(
            new.year,
            new.month,
            new.day,
            other.hour,
            other.minute,
            other.second,
            other.microsecond,
        )
        return new

    # backwards compat
    apply = _apply

    def is_on_offset(self, dt):
        if self.normalize and not AbstractHolidayOffset._is_normalized(dt):
            return False
        return date(dt.year, dt.month, dt.day) == self.holiday(dt.year).to_pydate()


def get_monthly_expiry_offset_class(day_of_week: int, month: int) -> AbstractHolidayOffset:
    """
    Return the date of the monthly expiry for the given year.
    """
    def expiry(year):
        return third_day_of_week_in_month(day_of_week, month, year)

    @property
    def holiday(self):
        return expiry

    day_of_week_name = get_day_of_week_name(day_of_week)

    # convert month to capitalized name of month.
    month_name = get_month_name(month)

    # Create a new class.
    offset = type(f"MonthlyExpiry{month_name}{day_of_week_name}Offset", (AbstractHolidayOffset,), {
        "holiday": holiday,
    })

    return offset


OffsetClasses = {day_of_week: {month: get_monthly_expiry_offset_class(day_of_week, month) for month in range(1, 13)} for day_of_week in range(7)}
