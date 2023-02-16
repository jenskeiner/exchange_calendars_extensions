import pandas as pd

from exchange_calendars_extras.holiday_calendar import get_holiday_calendar_from_timestamps, get_holiday_calendar_from_day_of_week


def test_get_holiday_calendar_from_timestamps():
    timestamps = [pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")]
    calendar = get_holiday_calendar_from_timestamps(timestamps)
    holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
    assert pd.Timestamp("2019-01-01") in holidays
    assert pd.Timestamp("2019-01-02") in holidays
    assert not pd.Timestamp("2019-01-03") in holidays
    assert not pd.Timestamp("2019-01-04") in holidays


def test_get_holiday_calendar_from_day_of_week():
    calendar = get_holiday_calendar_from_day_of_week(0)
    holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
    assert pd.Timestamp("2019-01-07") in holidays
    assert pd.Timestamp("2019-01-14") in holidays
    assert pd.Timestamp("2019-01-21") in holidays
    assert pd.Timestamp("2019-01-28") in holidays
    assert not pd.Timestamp("2019-01-01") in holidays
    assert not pd.Timestamp("2019-01-02") in holidays
    assert not pd.Timestamp("2019-01-03") in holidays
    assert not pd.Timestamp("2019-01-04") in holidays
    assert not pd.Timestamp("2019-01-05") in holidays
    assert not pd.Timestamp("2019-01-06") in holidays
    assert not pd.Timestamp("2019-01-08") in holidays
    assert not pd.Timestamp("2019-01-09") in holidays
    assert not pd.Timestamp("2019-01-10") in holidays
    assert not pd.Timestamp("2019-01-11") in holidays
    assert not pd.Timestamp("2019-01-12") in holidays
    assert not pd.Timestamp("2019-01-13") in holidays
    assert not pd.Timestamp("2019-01-15") in holidays
    assert not pd.Timestamp("2019-01-16") in holidays
    assert not pd.Timestamp("2019-01-17") in holidays
    assert not pd.Timestamp("2019-01-18") in holidays
    assert not pd.Timestamp("2019-01-19") in holidays
    assert not pd.Timestamp("2019-01-20") in holidays
