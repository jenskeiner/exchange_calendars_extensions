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


def get_third_day_of_week_in_month_offset_class(day_of_week: int, month: int) -> AbstractHolidayOffset:
    """
    Return a new class that represents an offset that when applied to the first day of a year, results in the third given 
    day of the week in the given month.
    
    For example, to get the offset for the third Friday in June, call this function with day_of_week=4 and month=6. On many
    exchanges, this will be the quadruple witching day for the second quarter of the year.
    """

    @property
    def holiday(self):
        """
            Return a function that returns the date of the day for a given year.
        """
        return lambda year: third_day_of_week_in_month(day_of_week, month, year)

    # Get name of day of week.
    day_of_week_name = get_day_of_week_name(day_of_week)

    # Get name of month.
    month_name = get_month_name(month)

    # Create the new class.
    offset = type(f"MonthlyExpiry{month_name}{day_of_week_name}Offset", (AbstractHolidayOffset,), {
        "holiday": holiday,
    })

    # Return the new class.
    return offset


# A dictionary of dictionaries that maps day of week to month to corresponding offset class for select days of the week.
# For example, to get the offset class for the third Friday in June, use the following: OffsetClasses[4][6].
# This dictionary should contain classes for all required days of the week and months. Further days of the week may need 
# to be added if a more exotic case arises.
OffsetClasses = {day_of_week: {month: get_third_day_of_week_in_month_offset_class(day_of_week, month) for month in range(1, 13)} for day_of_week in [3, 4]}
