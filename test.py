import pandas as pd
from exchange_calendars import get_calendar, ExchangeCalendar
from exchange_calendars.exchange_calendar_xetr import XETRExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars.exchange_calendar_xmil import XMILExchangeCalendar

from exchange_calendars_extensions import ExtendedExchangeCalendar, apply_extensions, add_holiday, remove_holiday
from exchange_calendars_extensions import __version__ as version
apply_extensions()
add_holiday("XETR", pd.Timestamp("2020-04-09"), "Gründonnerstag")
add_holiday("XETR", pd.Timestamp("2020-04-09"), "Test")
remove_holiday("XETR", pd.Timestamp("2020-04-10"))
calendar = get_calendar("XETR")
print(f"weekend: {calendar.weekend_days.holidays(start='2020-01-01', end='2020-12-31')}")
print(f"regular holidays: {calendar.regular_holidays.holidays(start='2020-01-01', end='2020-12-31', return_name=True)}")
print(f"all holidays: {calendar.holidays_all.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"special open: {calendar.special_opens_all.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"special close: {calendar.special_closes_all.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"monthly expiry: {calendar.monthly_expiries.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"quarterly expiry: {calendar.quarterly_expiries.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"last trading day of month: {calendar.last_trading_days_of_months.holidays(start='2020-01-01', end='2020-12-31')}")
# print(f"last regular trading day of month: {calendar.last_regular_trading_days_of_months.holidays(start='2020-01-01', end='2020-12-31')}")
# print(isinstance(calendar, ExchangeCalendar))
# print(isinstance(calendar, ExtendedExchangeCalendar))
# print(isinstance(calendar, XETRExchangeCalendar))
# #print(calendar.holidays_all.holidays(start='2020-01-01', end='2020-12-31', return_name=True))
# #print(calendar.quarterly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
# #print(calendar.monthly_expiries.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
# print(calendar.last_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
# print(calendar.last_regular_trading_days_of_months.holidays(start='2023-01-01', end='2023-12-31', return_name=True))
# print(version)
