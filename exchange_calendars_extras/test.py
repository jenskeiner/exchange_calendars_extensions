from abc import ABC

import exchange_calendars
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar

from exchange_calendars_extras.holiday import get_monthly_expiry_holiday, get_monthly_expiry_calendar, \
    get_quadruple_witching_calendar
from exchange_calendars_extras.observance import get_roll_backward_observance
from exchange_calendars_extras.offset import get_third_day_of_week_in_month_offset_class

xsto_calendar = exchange_calendars.get_calendar("XSTO").regular_holidays

observance = get_roll_backward_observance(xsto_calendar)

cal = get_quadruple_witching_calendar(4, observance)

x = get_third_day_of_week_in_month_offset_class(4, 6)
print(x().holiday(2020))

print(cal.holidays(start="2020-01-01", end="2020-12-31"))


# Protocol class.
class ExtendedExchangeCalendar(ExchangeCalendar, ABC):
    @property
    def witching_days(self) -> HolidayCalendar | None:
        ...


# A function that takes a class as an argument and returns a class.
def get_extended_class(cls: type) -> type:
    init = cls.__init__

    def __init__(self, *args, **kwargs):
        init(self, *args, **kwargs)
        self._witching_days = self.regular_holidays

    # A property that returns a HolidayCalendar or None.
    @property
    def witching_days(self) -> HolidayCalendar | None:
        return self._witching_days

    # Use type to create a new class.
    extended = type(cls.__name__ + "Extended", (cls, ExtendedExchangeCalendar), {
        "__init__": __init__,
        "witching_days": witching_days,
    })

    return extended


cls = get_extended_class(XLONExchangeCalendar)
calendar = cls()
print(calendar.witching_days)
