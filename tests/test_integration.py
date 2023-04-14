import datetime
from datetime import time
from types import NoneType
from typing import Optional, List, Tuple, Sequence, Union, Dict, Any

import pandas as pd
import pytest
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.pandas_extensions.holiday import Holiday
from pytz import timezone
from pandas.tseries.holiday import next_monday


def apply_extensions():
    """ Apply the extensions to the exchange_calendars module. """
    import exchange_calendars_extensions as ece
    ece.apply_extensions()


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
            return HolidayCalendar([Holiday(name=f"Holiday {i}", month=ts.month, day=ts.day) for i, ts in
                                    enumerate(holidays)] if holidays else [])

        @property
        def adhoc_holidays(self):
            return adhoc_holidays if adhoc_holidays else []

        @property
        def special_closes(self):
            return list(map(lambda x: (x[0], HolidayCalendar(
                [Holiday(name=f"Special Close {i}", month=ts.month, day=ts.day, observance=next_monday) for i, ts in
                 enumerate(x[1])])), special_closes)) if special_closes else []

        @property
        def special_closes_adhoc(self):
            return list(map(lambda x: (x[0], pd.DatetimeIndex([x[1]] if not isinstance(x[1], list) else x[1])),
                            adhoc_special_closes)) if adhoc_special_closes else []

        @property
        def special_opens(self):
            return list(map(lambda x: (x[0], HolidayCalendar(
                [Holiday(name=f"Special Open {i}", month=ts.month, day=ts.day, observance=next_monday) for i, ts in
                 enumerate(x[1])])), special_opens)) if special_opens else []

        @property
        def special_opens_adhoc(self):
            return list(map(lambda x: (x[0], pd.DatetimeIndex([x[1]] if not isinstance(x[1], list) else x[1])),
                            adhoc_special_opens)) if adhoc_special_opens else []

        # Weekmask.
        @property
        def weekmask(self):
            return weekmask

    ec.register_calendar_type("TEST", TestCalendar)

    import exchange_calendars_extensions as ece

    ece.register_extension("TEST", TestCalendar, day_of_week_expiry=day_of_week_expiry)

    ece.apply_extensions()


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


@pytest.mark.isolated
def test_apply_extensions():
    """ Test that calendars are modified when apply_extensions() is called """
    apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("XETR")

    # Check if returned Calendar is of expected types.
    assert isinstance(c, ec.ExchangeCalendar)
    assert isinstance(c, ece.ExtendedExchangeCalendar)
    assert isinstance(c, ece.holiday_calendar.ExchangeCalendarExtensions)


@pytest.mark.isolated
def test_extended_calendar_xetr():
    """ Test the additional properties of the extended XETR calendar. """
    apply_extensions()

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


@pytest.mark.isolated
def test_extended_calendar_test():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("TEST")

    assert isinstance(c, ece.ExtendedExchangeCalendar)
    
    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")
    
    # Verify regular holidays for 2022, 2023, and 2024.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
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


@pytest.mark.isolated
def test_add_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_holiday("TEST", pd.Timestamp("2023-07-03"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should show as regular holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-07-03"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2023-07-03"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_holiday("TEST", pd.Timestamp("2023-01-01"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should overwrite existing regular holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Added Holiday",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_holiday("TEST", pd.Timestamp("2023-02-01"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should be a regular holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Overwritten ad-hoc holiday should be removed from list.
    assert c.adhoc_holidays == []

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_holiday("TEST", pd.Timestamp("2023-01-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Removed day should no longer be in regular holidays.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Removed holiday should not affect ad-hoc holidays.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Removed day should not be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_holiday("TEST", pd.Timestamp("2023-02-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be untouched.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Removed holiday should no longer be in ad-hoc holidays.
    assert c.adhoc_holidays == []

    # Removed day should not be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_non_existent_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_holiday("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be untouched.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Ad-hoc holidays should be untouched.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Calendar holidays_all should be untouched.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_add_and_remove_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Add and then remove the same day. This should be a no-op.
    ece.add_holiday("TEST", pd.Timestamp("2023-07-03"), "Added Holiday")
    ece.remove_holiday("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be unchanged.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Ad-hoc holidays should be unchanged.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Calendar holidays_all should be unchanged.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_add_and_remove_existing_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Add and then remove the same existing holiday. The day should be removed.
    ece.add_holiday("TEST", pd.Timestamp("2023-01-01"), "Added Holiday")
    ece.remove_holiday("TEST", pd.Timestamp("2023-01-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Day should be removed from regular holidays.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Ad-hoc holidays should be unchanged.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Day should be removed from holidays_all.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_and_add_new_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Remove and then add the same new holiday. The removal of a non-existent holiday should be ignored, so the day
    # should be added eventually.
    ece.remove_holiday("TEST", pd.Timestamp("2023-07-03"))
    ece.add_holiday("TEST", pd.Timestamp("2023-07-03"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should show as regular holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-07-03"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2023-07-03"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_and_add_existing_regular_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Remove and then add the same existent holiday. This should be equivalent to just adding (and thereby overwriting)
    # the existing regular holiday.
    ece.remove_holiday("TEST", pd.Timestamp("2023-01-01"))
    ece.add_holiday("TEST", pd.Timestamp("2023-01-01"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holiday should be overwritten.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Added Holiday",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_remove_and_add_existing_adhoc_holiday():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Remove and then add the same existent holiday. This should be equivalent to just adding (and thereby overwriting)
    # the existing regular holiday.
    ece.remove_holiday("TEST", pd.Timestamp("2023-02-01"))
    ece.add_holiday("TEST", pd.Timestamp("2023-02-01"), "Added Holiday")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holiday should contain the added holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Ad-hoc holidays should be empty.
    assert c.adhoc_holidays == []

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_add_and_remove_new_holiday_multiple_times():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Add and then remove the same day. This should be a no-op.
    ece.add_holiday("TEST", pd.Timestamp("2023-07-03"), "Added Holiday")
    ece.remove_holiday("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Regular holidays should be unchanged.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Ad-hoc holidays should be unchanged.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Calendar holidays_all should be unchanged.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-02-01"): "ad-hoc holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Now, remove and then add the same day. The removal of a non-existent holiday should be ignored, so the day should
    # be added eventually.
    ece.remove_holiday("TEST", pd.Timestamp("2023-07-03"))
    ece.add_holiday("TEST", pd.Timestamp("2023-07-03"), "Added Holiday")

    # This should return a fresh instance, reflecting above changes.
    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Added holiday should show as regular holiday.
    assert c.regular_holidays.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-01-01"): "Holiday 0",
        pd.Timestamp("2023-01-01"): "Holiday 0",
        pd.Timestamp("2023-07-03"): "Added Holiday",
        pd.Timestamp("2024-01-01"): "Holiday 0"})).empty

    # Added holiday should not be in ad-hoc holidays, i.e. this should be unmodified.
    assert c.adhoc_holidays == [pd.Timestamp("2023-02-01")]

    # Added holiday should be in holidays_all calendar.
    assert c.holidays_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
         pd.Timestamp("2022-01-01"): "Holiday 0",
         pd.Timestamp("2023-01-01"): "Holiday 0",
         pd.Timestamp("2023-02-01"): "ad-hoc holiday",
         pd.Timestamp("2023-07-03"): "Added Holiday",
         pd.Timestamp("2024-01-01"): "Holiday 0"})).empty


@pytest.mark.isolated
def test_add_new_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_open("TEST", pd.Timestamp("2023-07-03"), time(12, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should be unchanged.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # There should be a new calendar for the added special open time.
    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-07-03"): "Added Special Open"})).empty

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2023-07-03"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_add_new_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_open("TEST", pd.Timestamp("2023-07-03"), time(11, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should be unchanged.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-07-03"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2023-07-03"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_regular_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_open("TEST", pd.Timestamp("2023-05-01"), time(12, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # There should be a new calendar for the added special open time.
    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-05-01"): "Added Special Open"})).empty

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Added Special Open",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_regular_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions(special_opens=[(time(11, 00), [pd.Timestamp("2023-05-01")]), (time(12, 00), [pd.Timestamp("2023-05-04")])])
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2024-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty

    ece.add_special_open("TEST", pd.Timestamp("2023-05-01"), time(12, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Added Special Open",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty

    # Added special open should not be in ad-hoc special opens, i.e. this should be unmodified.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Added Special Open",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2024-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_open_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_open("TEST", pd.Timestamp("2023-06-01"), time(12, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-06-01"): "Added Special Open"})).empty

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_open_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_open("TEST", pd.Timestamp("2023-06-01"), time(11, 0), "Added Special Open")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "Added Special Open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_remove_existing_regular_special_open():
    add_test_calendar_and_apply_extensions(special_opens=[(time(11, 00), [pd.Timestamp("2023-05-01")]), (time(12, 00), [pd.Timestamp("2023-05-04")])])
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_open("TEST", pd.Timestamp("2023-05-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 2

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    assert c.special_opens[1][0] == time(12, 0)
    assert c.special_opens[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2022-05-04"): "Special Open 0",
        pd.Timestamp("2023-05-04"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2024-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-06"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_remove_existing_ad_hoc_special_open():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_open("TEST", pd.Timestamp("2023-06-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == []

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_remove_non_existent_special_open():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_open("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special open times.
    assert len(c.special_opens) == 1

    # Special opens for regular special open time should exclude the overwritten day.
    assert c.special_opens[0][0] == time(11, 0)
    assert c.special_opens[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty

    # Ad-hoc special opens should now be empty.
    assert c.special_opens_adhoc == [(time(11, 00), pd.Timestamp("2023-06-01"))]

    # Added special open should be in consolidated calendar.
    assert c.special_opens_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-05-02"): "Special Open 0",
        pd.Timestamp("2023-05-01"): "Special Open 0",
        pd.Timestamp("2023-06-01"): "ad-hoc special open",
        pd.Timestamp("2024-05-01"): "Special Open 0"})).empty


@pytest.mark.isolated
def test_add_new_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_close("TEST", pd.Timestamp("2023-07-03"), time(15, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special closes for regular special close time should be unchanged.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # There should be a new calendar for the added special close time.
    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-07-03"): "Added Special Close"})).empty

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2023-07-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_add_new_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_close("TEST", pd.Timestamp("2023-07-03"), time(14, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should be unchanged.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-07-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 0), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2023-07-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_regular_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_close("TEST", pd.Timestamp("2023-03-01"), time(15, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # There should be a new calendar for the added special close time.
    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-03-01"): "Added Special Close"})).empty

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Added Special Close",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_regular_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions(special_closes=[(time(14, 00), [pd.Timestamp("2023-03-01")]), (time(15, 00), [pd.Timestamp("2023-03-04")])])
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2024-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty

    ece.add_special_close("TEST", pd.Timestamp("2023-03-01"), time(15, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Added Special Close",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty

    # Added special close should not be in ad-hoc special closes, i.e. this should be unmodified.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Added Special Close",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2024-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_close_with_new_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_close("TEST", pd.Timestamp("2023-04-03"), time(15, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2023-04-03"): "Added Special Close"})).empty

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_overwrite_existing_ad_hoc_special_close_with_existing_time():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.add_special_close("TEST", pd.Timestamp("2023-04-03"), time(14, 0), "Added Special Close")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "Added Special Close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_remove_existing_regular_special_close():
    add_test_calendar_and_apply_extensions(special_closes=[(time(14, 00), [pd.Timestamp("2023-03-01")]), (time(15, 00), [pd.Timestamp("2023-03-04")])])
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_close("TEST", pd.Timestamp("2023-03-01"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 2

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    assert c.special_closes[1][0] == time(15, 0)
    assert c.special_closes[1][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2022-03-04"): "Special Close 0",
        pd.Timestamp("2023-03-06"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2024-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-04"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_remove_existing_ad_hoc_special_close():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_close("TEST", pd.Timestamp("2023-04-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == []

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


@pytest.mark.isolated
def test_remove_non_existent_special_close():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    ece.remove_special_close("TEST", pd.Timestamp("2023-07-03"))

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")

    # Check number of distinct special close times.
    assert len(c.special_closes) == 1

    # Special Closes for regular special close time should exclude the overwritten day.
    assert c.special_closes[0][0] == time(14, 0)
    assert c.special_closes[0][1].holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty

    # Ad-hoc special closes should now be empty.
    assert c.special_closes_adhoc == [(time(14, 00), pd.Timestamp("2023-04-03"))]

    # Added special close should be in consolidated calendar.
    assert c.special_closes_all.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-01"): "Special Close 0",
        pd.Timestamp("2023-03-01"): "Special Close 0",
        pd.Timestamp("2023-04-03"): "ad-hoc special close",
        pd.Timestamp("2024-03-01"): "Special Close 0"})).empty


def test_add_quarterly_expiry():
    add_test_calendar_and_apply_extensions()
    import exchange_calendars as ec
    import exchange_calendars_extensions as ece

    # Add quarterly expiry.
    ece.add_quarterly_expiry("TEST", pd.Timestamp("2023-06-15"), "Added Quarterly Expiry")

    c = ec.get_calendar("TEST")

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")


    # Quarterly expiry dates should be empty.
    assert c.quarterly_expiries.holidays(start=start, end=end, return_name=True).compare(pd.Series({
        pd.Timestamp("2022-03-18"): "quarterly expiry",
        pd.Timestamp("2022-06-17"): "quarterly expiry",
        pd.Timestamp("2022-09-16"): "quarterly expiry",
        pd.Timestamp("2022-12-16"): "quarterly expiry",
        pd.Timestamp("2023-03-17"): "quarterly expiry",
        #pd.Timestamp("2023-06-15"): "Added Quarterly Expiry",
        pd.Timestamp("2023-06-16"): "quarterly expiry",
        pd.Timestamp("2023-09-15"): "quarterly expiry",
        pd.Timestamp("2023-12-15"): "quarterly expiry",
        pd.Timestamp("2024-03-15"): "quarterly expiry",
        pd.Timestamp("2024-06-21"): "quarterly expiry",
        pd.Timestamp("2024-09-20"): "quarterly expiry",
        pd.Timestamp("2024-12-20"): "quarterly expiry"})).empty
