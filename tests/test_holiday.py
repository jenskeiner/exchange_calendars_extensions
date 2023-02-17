from pandas import DatetimeIndex, Series

from exchange_calendars_extensions.holiday import get_monthly_expiry_holiday, DayOfWeekPeriodicHoliday

import pandas as pd


def test_get_monthly_expiry_holiday():
    holiday = get_monthly_expiry_holiday(name="Holiday", day_of_week=0, month=1, start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2021-12-31"))

    # Verify name.
    assert holiday.name == "Holiday"

    # No holidays in 2018 because it's before the start date.
    assert holiday.dates(start_date=pd.Timestamp("2018-01-01"), end_date=pd.Timestamp("2018-12-31"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # No holidays since the end date is before the first holiday.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2019-01-20"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # A single holiday in 2019.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2019-12-31"), return_name=False).equals(DatetimeIndex([pd.Timestamp("2019-01-21")], dtype='datetime64[ns]', freq=None))

    # A single holiday in 2020.
    assert holiday.dates(start_date=pd.Timestamp("2020-01-01"), end_date=pd.Timestamp("2020-12-31"), return_name=False).equals(DatetimeIndex([pd.Timestamp("2020-01-20")], dtype='datetime64[ns]', freq=None))

    # A single holiday in 2021.
    assert holiday.dates(start_date=pd.Timestamp("2021-01-01"), end_date=pd.Timestamp("2021-12-31"), return_name=False).equals(DatetimeIndex([pd.Timestamp("2021-01-18")], dtype='datetime64[ns]', freq=None))

    # No holidays since the start date is after the last holiday.
    assert holiday.dates(start_date=pd.Timestamp("2021-01-19"), end_date=pd.Timestamp("2021-12-31"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # No holidays in 2022 because it's after the end date.
    assert holiday.dates(start_date=pd.Timestamp("2022-01-01"), end_date=pd.Timestamp("2022-12-31"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # Verify that the holiday name is returned.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2019-12-31"), return_name=True).equals(Series(['Holiday'], index=[pd.Timestamp('2019-01-21')]))


def test_day_of_week_periodic_holiday():
    holiday = DayOfWeekPeriodicHoliday(name="Holiday", day_of_week=0, start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2021-12-31"))

    # Verify name.
    assert holiday.name == "Holiday"

    # No holidays in 2018 because it's before the start date.
    assert holiday.dates(start_date=pd.Timestamp("2018-01-01"), end_date=pd.Timestamp("2018-12-31"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # No holidays since the end date is before the first holiday.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2019-01-06"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # No holidays since the provided range doesn't include the day of week.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-03"), end_date=pd.Timestamp("2019-01-05"), return_name=False).equals(DatetimeIndex([], dtype='datetime64[ns]', freq=None))

    # Verify expected days of week in 2019.
    assert holiday.dates(start_date=pd.Timestamp("2019-01-01"), end_date=pd.Timestamp("2019-12-31"), return_name=False).equals(DatetimeIndex([
        pd.Timestamp("2019-01-07"), pd.Timestamp("2019-01-14"), pd.Timestamp("2019-01-21"), pd.Timestamp("2019-01-28"),
        pd.Timestamp("2019-02-04"), pd.Timestamp("2019-02-11"), pd.Timestamp("2019-02-18"), pd.Timestamp("2019-02-25"),
        pd.Timestamp("2019-03-04"), pd.Timestamp("2019-03-11"), pd.Timestamp("2019-03-18"), pd.Timestamp("2019-03-25"),
        pd.Timestamp("2019-04-01"), pd.Timestamp("2019-04-08"), pd.Timestamp("2019-04-15"), pd.Timestamp("2019-04-22"),
        pd.Timestamp("2019-04-29"), pd.Timestamp("2019-05-06"), pd.Timestamp("2019-05-13"), pd.Timestamp("2019-05-20"),
        pd.Timestamp("2019-05-27"), pd.Timestamp("2019-06-03"), pd.Timestamp("2019-06-10"), pd.Timestamp("2019-06-17"),
        pd.Timestamp("2019-06-24"), pd.Timestamp("2019-07-01"), pd.Timestamp("2019-07-08"), pd.Timestamp("2019-07-15"),
        pd.Timestamp("2019-07-22"), pd.Timestamp("2019-07-29"), pd.Timestamp("2019-08-05"), pd.Timestamp("2019-08-12"),
        pd.Timestamp("2019-08-19"), pd.Timestamp("2019-08-26"), pd.Timestamp("2019-09-02"), pd.Timestamp("2019-09-09"),
        pd.Timestamp("2019-09-16"), pd.Timestamp("2019-09-23"), pd.Timestamp("2019-09-30"), pd.Timestamp("2019-10-07"),
        pd.Timestamp("2019-10-14"), pd.Timestamp("2019-10-21"), pd.Timestamp("2019-10-28"), pd.Timestamp("2019-11-04"),
        pd.Timestamp("2019-11-11"), pd.Timestamp("2019-11-18"), pd.Timestamp("2019-11-25"), pd.Timestamp("2019-12-02"),
        pd.Timestamp("2019-12-09"), pd.Timestamp("2019-12-16"), pd.Timestamp("2019-12-23"), pd.Timestamp("2019-12-30"),
    ], dtype='datetime64[ns]', freq=None))
