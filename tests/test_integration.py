import datetime
from datetime import time
from types import NoneType
from typing import Optional, List, Tuple, Sequence, Union

import pandas as pd
import pytest
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
from pytz import timezone
from pandas.tseries.holiday import next_monday


def apply_extensions(f):
    """ Apply the extensions to the exchange_calendars module. """
    def inner(*args, **kwargs):
        import exchange_calendars_extensions as ece
        ece.apply_extensions()
        return f(*args, **kwargs)

    return inner


def add_test_calendar_and_apply_extensions(holidays: Optional[List[pd.Timestamp]] = [pd.Timestamp("2023-01-01")],
                                           adhoc_holidays: Optional[List[pd.Timestamp]] = [pd.Timestamp("2023-02-01")],
                                           regular_special_close: Optional[time] = time(14, 00),
                                           special_closes: Optional[List[pd.Timestamp]] = [(time(14, 00), [pd.Timestamp("2023-03-01")])],
                                           adhoc_special_closes: Optional[List[Tuple[datetime.time, pd.Timestamp]]] = [(time(14, 00), pd.Timestamp("2023-04-03"))],
                                           regular_special_open: Optional[time] = time(11, 00),
                                           special_opens: Optional[List[pd.Timestamp]] = [(time(11, 00), [pd.Timestamp("2023-05-01")])],
                                           adhoc_special_opens: Optional[List[Tuple[datetime.time, pd.Timestamp]]] = [(time(11, 00), pd.Timestamp("2023-06-01"))],
                                           weekmask: Optional[str] = "1111100",
                                           day_of_week_expiry: Union[NoneType, int] = 4):
    """ Factory to add a test calendar to the exchange_calendars module, define an extended version of it and apply the
    extensions. """
    def decorator(f):
        def inner(*args, **kwargs):
            import exchange_calendars as ec

            # Define a test calendar class, subclassing the ExchangeCalendar class. Within the class body, define the
            # holidays, special closes and special opens, as well as the weekmask, based on the parameters passed to the
            # factory.
            class TestCalendar(ec.ExchangeCalendar):
                # Regular open/close times.
                open_times = ((None, time(9)),)
                close_times = ((None, time(17, 30)),)

                # Special open/close times.
                regular_early_close = regular_special_close
                regular_late_open = regular_special_open

                # Name.
                name = "TEST"

                # Timezone.
                tz = timezone("CET")

                # Holidays.
                @property
                def regular_holidays(self):
                    return HolidayCalendar([Holiday(name=f"Holiday {i}", month=ts.month, day=ts.day) for i, ts in enumerate(holidays)] if holidays else [])

                @property
                def adhoc_holidays(self):
                    return adhoc_holidays if adhoc_holidays else []

                @property
                def special_closes(self):
                    return list(map(lambda x: (x[0], HolidayCalendar([Holiday(name=f"Special Close {i}", month=ts.month, day=ts.day, observance=next_monday) for i, ts in enumerate(x[1])])), special_closes)) if special_closes else []

                @property
                def special_closes_adhoc(self):
                    return list(map(lambda x: (x[0], pd.DatetimeIndex([x[1]] if not isinstance(x[1], list) else x[1])), adhoc_special_closes)) if adhoc_special_closes else []

                @property
                def special_opens(self):
                    return list(map(lambda x: (x[0], HolidayCalendar([Holiday(name=f"Special Open {i}", month=ts.month, day=ts.day, observance=next_monday) for i, ts in enumerate(x[1])])), special_opens)) if special_opens else []

                @property
                def special_opens_adhoc(self):
                    return list(map(lambda x: (x[0], pd.DatetimeIndex([x[1]] if not isinstance(x[1], list) else x[1])), adhoc_special_opens)) if adhoc_special_opens else []

                # Weekmask.
                @property
                def weekmask(self):
                    return weekmask

            ec.register_calendar_type("TEST", TestCalendar)

            import exchange_calendars_extensions as ece

            ece.register_extension("TEST", TestCalendar, day_of_week_expiry=day_of_week_expiry)
            
            ece.apply_extensions()

            return f(*args, **kwargs)

        return inner

    return decorator


@pytest.mark.isolated
def test_unmodified_calendars():
    """ Test that calendars are unmodified when the module is just imported, without calling apply_extensions() """
    import exchange_calendars_extensions as ece

    import exchange_calendars as ec
    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected type.
    assert isinstance(c, ec.ExchangeCalendar)

    # Check if returned Calendar is not of extended type.
    assert not isinstance(c, ece.ExtendedExchangeCalendar)
    assert not isinstance(c, ece.holiday_calendar.ExchangeCalendarExtensions)


@apply_extensions
@pytest.mark.isolated
def test_apply_extensions():
    """ Test that calendars are modified when apply_extensions() is called """
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected types.
    assert isinstance(c, ec.ExchangeCalendar)
    assert isinstance(c, ece.ExtendedExchangeCalendar)
    assert isinstance(c, ece.holiday_calendar.ExchangeCalendarExtensions)


@apply_extensions
@pytest.mark.isolated
def test_extended_calendar_xetr():
    """ Test the additional properties of the extended XETR calendar. """
    import exchange_calendars as ec

    c = ec.get_calendar("XETR")

    # Check if additional properties are present.
    assert hasattr(c, "holidays_all")
    assert isinstance(c.holidays_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "special_opens_all")
    assert isinstance(c.special_opens_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "special_closes_all")
    assert isinstance(c.special_closes_all, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "weekend_days")
    assert isinstance(c.weekend_days, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "monthly_expiries")
    assert isinstance(c.monthly_expiries, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "quarterly_expiries")
    assert isinstance(c.quarterly_expiries, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "last_trading_days_of_months")
    assert isinstance(c.last_trading_days_of_months, ec.exchange_calendar.HolidayCalendar)

    assert hasattr(c, "last_regular_trading_days_of_months")
    assert isinstance(c.last_regular_trading_days_of_months, ec.exchange_calendar.HolidayCalendar)


@add_test_calendar_and_apply_extensions()
@pytest.mark.isolated
def test_extended_calendar_test():
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("TEST")

    assert isinstance(c, ece.ExtendedExchangeCalendar)
    
    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")
    
    # Verify regular holidays for 2022, 2023, and 2024.
    c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0", 
        pd.Timestamp("2023-01-01"): "Holiday 0", 
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty
    
    # Verify adhoc holidays.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]
    
    # Verify special closes for 2022, 2023, and 2024.
    assert len(c.special_closes) == 1
    assert len(c.special_closes[0]) == 2
    assert c.special_closes[0][0] == datetime.time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-03-01'): 'Special Close 0',
        pd.Timestamp('2023-03-01'): 'Special Close 0',
        pd.Timestamp('2024-03-01'): 'Special Close 0'})).empty
    
    # Verify adhoc special closes.
    assert c.special_closes_adhoc == [(datetime.time(14, 0), pd.DatetimeIndex([pd.Timestamp("2023-04-03")]))]
    
    # Verify special opens for 2022, 2023, and 2024.
    assert len(c.special_opens) == 1
    assert len(c.special_opens[0]) == 2
    assert c.special_opens[0][0] == datetime.time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-05-02'): 'Special Open 0',
        pd.Timestamp('2023-05-01'): 'Special Open 0',
        pd.Timestamp('2024-05-01'): 'Special Open 0'})).empty
    
    # Verify adhoc special opens.
    assert c.special_opens_adhoc == [(datetime.time(11, 0), pd.DatetimeIndex([pd.Timestamp("2023-06-01")]))]
    
    # Verify additional holiday calendars.
    
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0", 
        pd.Timestamp("2023-01-01"): "Holiday 0", 
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty
    
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-03-01'): 'Special Close 0',
        pd.Timestamp('2023-03-01'): 'Special Close 0',
        pd.Timestamp('2023-04-03'): "ad-hoc special close",
        pd.Timestamp('2024-03-01'): 'Special Close 0'})).empty
    
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-05-02'): 'Special Open 0',
        pd.Timestamp('2023-05-01'): 'Special Open 0',
        pd.Timestamp('2023-06-01'): "ad-hoc special open",
        pd.Timestamp('2024-05-01'): 'Special Open 0'})).empty
    
    assert c.weekend_days.holidays(start=pd.Timestamp('2023-01-01'), end=pd.Timestamp('2023-01-31'), return_name=True).compare(pd.Series({
        pd.Timestamp('2023-01-01'): 'weekend day',
        pd.Timestamp('2023-01-07'): 'weekend day',
        pd.Timestamp('2023-01-08'): 'weekend day',
        pd.Timestamp('2023-01-14'): 'weekend day',
        pd.Timestamp('2023-01-15'): 'weekend day',
        pd.Timestamp('2023-01-21'): 'weekend day',
        pd.Timestamp('2023-01-22'): 'weekend day',
        pd.Timestamp('2023-01-28'): 'weekend day',
        pd.Timestamp('2023-01-29'): 'weekend day'})).empty
    
    assert c.quarterly_expiries.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-03-18'): 'quarterly expiry',
        pd.Timestamp('2022-06-17'): 'quarterly expiry',
        pd.Timestamp('2022-09-16'): 'quarterly expiry',
        pd.Timestamp('2022-12-16'): 'quarterly expiry',
        pd.Timestamp('2023-03-17'): 'quarterly expiry',
        pd.Timestamp('2023-06-16'): 'quarterly expiry',
        pd.Timestamp('2023-09-15'): 'quarterly expiry',
        pd.Timestamp('2023-12-15'): 'quarterly expiry',
        pd.Timestamp('2024-03-15'): 'quarterly expiry',
        pd.Timestamp('2024-06-21'): 'quarterly expiry',
        pd.Timestamp('2024-09-20'): 'quarterly expiry',
        pd.Timestamp('2024-12-20'): 'quarterly expiry'})).empty

    assert c.monthly_expiries.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-01-21'): 'monthly expiry',
        pd.Timestamp('2022-02-18'): 'monthly expiry',
        pd.Timestamp('2022-04-15'): 'monthly expiry',
        pd.Timestamp('2022-05-20'): 'monthly expiry',
        pd.Timestamp('2022-07-15'): 'monthly expiry',
        pd.Timestamp('2022-08-19'): 'monthly expiry',
        pd.Timestamp('2022-10-21'): 'monthly expiry',
        pd.Timestamp('2022-11-18'): 'monthly expiry',
        pd.Timestamp('2023-01-20'): 'monthly expiry',
        pd.Timestamp('2023-02-17'): 'monthly expiry',
        pd.Timestamp('2023-04-21'): 'monthly expiry',
        pd.Timestamp('2023-05-19'): 'monthly expiry',
        pd.Timestamp('2023-07-21'): 'monthly expiry',
        pd.Timestamp('2023-08-18'): 'monthly expiry',
        pd.Timestamp('2023-10-20'): 'monthly expiry',
        pd.Timestamp('2023-11-17'): 'monthly expiry',
        pd.Timestamp('2024-01-19'): 'monthly expiry',
        pd.Timestamp('2024-02-16'): 'monthly expiry',
        pd.Timestamp('2024-04-19'): 'monthly expiry',
        pd.Timestamp('2024-05-17'): 'monthly expiry',
        pd.Timestamp('2024-07-19'): 'monthly expiry',
        pd.Timestamp('2024-08-16'): 'monthly expiry',
        pd.Timestamp('2024-10-18'): 'monthly expiry',
        pd.Timestamp('2024-11-15'): 'monthly expiry'})).empty
    
    assert c.last_trading_days_of_months.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-01-31'): 'last trading day of month',
        pd.Timestamp('2022-02-28'): 'last trading day of month',
        pd.Timestamp('2022-03-31'): 'last trading day of month',
        pd.Timestamp('2022-04-29'): 'last trading day of month',
        pd.Timestamp('2022-05-31'): 'last trading day of month',
        pd.Timestamp('2022-06-30'): 'last trading day of month',
        pd.Timestamp('2022-07-29'): 'last trading day of month',
        pd.Timestamp('2022-08-31'): 'last trading day of month',
        pd.Timestamp('2022-09-30'): 'last trading day of month',
        pd.Timestamp('2022-10-31'): 'last trading day of month',
        pd.Timestamp('2022-11-30'): 'last trading day of month',
        pd.Timestamp('2022-12-30'): 'last trading day of month',
        pd.Timestamp('2023-01-31'): 'last trading day of month',
        pd.Timestamp('2023-02-28'): 'last trading day of month',
        pd.Timestamp('2023-03-31'): 'last trading day of month',
        pd.Timestamp('2023-04-28'): 'last trading day of month',
        pd.Timestamp('2023-05-31'): 'last trading day of month',
        pd.Timestamp('2023-06-30'): 'last trading day of month',
        pd.Timestamp('2023-07-31'): 'last trading day of month',
        pd.Timestamp('2023-08-31'): 'last trading day of month',
        pd.Timestamp('2023-09-29'): 'last trading day of month',
        pd.Timestamp('2023-10-31'): 'last trading day of month',
        pd.Timestamp('2023-11-30'): 'last trading day of month',
        pd.Timestamp('2023-12-29'): 'last trading day of month',
        pd.Timestamp('2024-01-31'): 'last trading day of month',
        pd.Timestamp('2024-02-29'): 'last trading day of month',
        pd.Timestamp('2024-03-29'): 'last trading day of month',
        pd.Timestamp('2024-04-30'): 'last trading day of month',
        pd.Timestamp('2024-05-31'): 'last trading day of month',
        pd.Timestamp('2024-06-28'): 'last trading day of month',
        pd.Timestamp('2024-07-31'): 'last trading day of month',
        pd.Timestamp('2024-08-30'): 'last trading day of month',
        pd.Timestamp('2024-09-30'): 'last trading day of month',
        pd.Timestamp('2024-10-31'): 'last trading day of month',
        pd.Timestamp('2024-11-29'): 'last trading day of month',
        pd.Timestamp('2024-12-31'): 'last trading day of month'})).empty
    
    
    assert c.last_regular_trading_days_of_months.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp('2022-01-31'): 'last regular trading day of month',
        pd.Timestamp('2022-02-28'): 'last regular trading day of month',
        pd.Timestamp('2022-03-31'): 'last regular trading day of month',
        pd.Timestamp('2022-04-29'): 'last regular trading day of month',
        pd.Timestamp('2022-05-31'): 'last regular trading day of month',
        pd.Timestamp('2022-06-30'): 'last regular trading day of month',
        pd.Timestamp('2022-07-29'): 'last regular trading day of month',
        pd.Timestamp('2022-08-31'): 'last regular trading day of month',
        pd.Timestamp('2022-09-30'): 'last regular trading day of month',
        pd.Timestamp('2022-10-31'): 'last regular trading day of month',
        pd.Timestamp('2022-11-30'): 'last regular trading day of month',
        pd.Timestamp('2022-12-30'): 'last regular trading day of month',
        pd.Timestamp('2023-01-31'): 'last regular trading day of month',
        pd.Timestamp('2023-02-28'): 'last regular trading day of month',
        pd.Timestamp('2023-03-31'): 'last regular trading day of month',
        pd.Timestamp('2023-04-28'): 'last regular trading day of month',
        pd.Timestamp('2023-05-31'): 'last regular trading day of month',
        pd.Timestamp('2023-06-30'): 'last regular trading day of month',
        pd.Timestamp('2023-07-31'): 'last regular trading day of month',
        pd.Timestamp('2023-08-31'): 'last regular trading day of month',
        pd.Timestamp('2023-09-29'): 'last regular trading day of month',
        pd.Timestamp('2023-10-31'): 'last regular trading day of month',
        pd.Timestamp('2023-11-30'): 'last regular trading day of month',
        pd.Timestamp('2023-12-29'): 'last regular trading day of month',
        pd.Timestamp('2024-01-31'): 'last regular trading day of month',
        pd.Timestamp('2024-02-29'): 'last regular trading day of month',
        pd.Timestamp('2024-03-29'): 'last regular trading day of month',
        pd.Timestamp('2024-04-30'): 'last regular trading day of month',
        pd.Timestamp('2024-05-31'): 'last regular trading day of month',
        pd.Timestamp('2024-06-28'): 'last regular trading day of month',
        pd.Timestamp('2024-07-31'): 'last regular trading day of month',
        pd.Timestamp('2024-08-30'): 'last regular trading day of month',
        pd.Timestamp('2024-09-30'): 'last regular trading day of month',
        pd.Timestamp('2024-10-31'): 'last regular trading day of month',
        pd.Timestamp('2024-11-29'): 'last regular trading day of month',
        pd.Timestamp('2024-12-31'): 'last regular trading day of month'})).empty
        