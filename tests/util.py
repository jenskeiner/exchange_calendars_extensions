import pytest
import pandas as pd

from exchange_calendars_extras.util import get_month_name, get_holiday_calendar_from_timestamps, \
    get_holiday_calendar_from_day_of_week


def test_get_month_name():
    assert get_month_name(1) == "January"
    assert get_month_name(2) == "February"
    assert get_month_name(3) == "March"
    assert get_month_name(4) == "April"
    assert get_month_name(5) == "May"
    assert get_month_name(6) == "June"
    assert get_month_name(7) == "July"
    assert get_month_name(8) == "August"
    assert get_month_name(9) == "September"
    assert get_month_name(10) == "October"
    assert get_month_name(11) == "November"
    assert get_month_name(12) == "December"
    with pytest.raises(ValueError):
        get_month_name(13)
    with pytest.raises(ValueError):
        get_month_name(0)
    with pytest.raises(ValueError):
        get_month_name(-1)


def get_day_of_week_name():
    assert get_day_of_week_name(0) == "Monday"
    assert get_day_of_week_name(1) == "Tuesday"
    assert get_day_of_week_name(2) == "Wednesday"
    assert get_day_of_week_name(3) == "Thursday"
    assert get_day_of_week_name(4) == "Friday"
    assert get_day_of_week_name(5) == "Saturday"
    assert get_day_of_week_name(6) == "Sunday"
    with pytest.raises(ValueError):
        get_day_of_week_name(7)
    with pytest.raises(ValueError):
        get_day_of_week_name(-1)


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
