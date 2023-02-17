from exchange_calendars import get_calendar, ExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars_extensions import ExtendedExchangeCalendar, apply_extensions

apply_extensions()
calendar = get_calendar("XLON")
print(f"weekend: {calendar.weekend_days.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"holiday: {calendar.holidays_all.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"special open: {calendar.special_opens_all.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"special close: {calendar.special_closes_all.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"monthly expiry: {calendar.monthly_expiries.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"quarterly expiry: {calendar.quarterly_expiries.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"last trading day of month: {calendar.last_trading_days_of_months.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"last regular trading day of month: {calendar.last_regular_trading_days_of_months.holidays(start='2020-01-01', end='2020-12-31')}")
print(isinstance(calendar, ExchangeCalendar))
print(isinstance(calendar, ExtendedExchangeCalendar))
print(isinstance(calendar, XLONExchangeCalendar))
