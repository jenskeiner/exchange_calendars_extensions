from abc import ABC

from exchange_calendars.exchange_calendar import ExchangeCalendar, HolidayCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar


def witching_days_decorator(cls):
    class Decorated(cls):
        @property
        def witching_days(self) -> HolidayCalendar | None:
            """Holiday calendar representing calendar's witching days."""
            return None

    return Decorated


@witching_days_decorator
class XLONExtendedExchangeCalendar(XLONExchangeCalendar):
    ...


class ExtendedExchangeCalendar:
    ...
