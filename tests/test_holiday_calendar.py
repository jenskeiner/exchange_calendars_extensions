from datetime import time

import pandas as pd
from exchange_calendars import get_calendar, ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from exchange_calendars.exchange_calendar_xlon import ChristmasEve, NewYearsEvePost2000
from pytz import timezone

from exchange_calendars_extensions.holiday_calendar import get_holiday_calendar_from_timestamps, \
    get_holiday_calendar_from_day_of_week, merge_calendars, get_holidays_calendar, get_special_closes_calendar


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


def test_merge_calendars():
    calendar1 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")])
    calendar2 = get_holiday_calendar_from_day_of_week(0)
    calendar = merge_calendars((calendar1, calendar2))
    holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
    assert pd.Timestamp("2019-01-01") in holidays
    assert pd.Timestamp("2019-01-02") in holidays
    assert pd.Timestamp("2019-01-07") in holidays
    assert pd.Timestamp("2019-01-14") in holidays
    assert pd.Timestamp("2019-01-21") in holidays
    assert pd.Timestamp("2019-01-28") in holidays
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
    assert not pd.Timestamp("2019-01-22") in holidays
    assert not pd.Timestamp("2019-01-23") in holidays
    assert not pd.Timestamp("2019-01-24") in holidays
    assert not pd.Timestamp("2019-01-25") in holidays


def test_merge_calendars_with_overlapping_holidays():
    calendar1 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-02")])
    calendar2 = get_holiday_calendar_from_timestamps([pd.Timestamp("2019-01-01"), pd.Timestamp("2019-01-03")])
    calendar = merge_calendars((calendar1, calendar2))
    holidays = calendar.holidays(start=pd.Timestamp("2019-01-01"), end=pd.Timestamp("2019-01-31"))
    assert len(holidays == 3)
    assert pd.Timestamp("2019-01-01") in holidays
    assert pd.Timestamp("2019-01-02") in holidays
    assert pd.Timestamp("2019-01-03") in holidays
    assert not pd.Timestamp("2019-01-04") in holidays


def test_get_holidays_calendar():
    calendar = get_calendar("XLON")
    holidays_calendar = get_holidays_calendar(calendar)
    holidays = holidays_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
    expected_holidays = pd.Series({
        pd.Timestamp("2020-01-01"): "New Year's Day",
        pd.Timestamp("2020-04-10"): "Good Friday",
        pd.Timestamp("2020-04-13"): "Easter Monday",
        pd.Timestamp("2020-05-08"): "ad-hoc holiday",
        pd.Timestamp("2020-05-25"): "Spring Bank Holiday",
        pd.Timestamp("2020-08-31"): "Summer Bank Holiday",
        pd.Timestamp("2020-12-25"): "Christmas",
        pd.Timestamp("2020-12-26"): "Boxing Day",
        pd.Timestamp("2020-12-28"): "Weekend Boxing Day",
    })
    assert holidays.compare(expected_holidays).empty


def test_get_special_closes_calendar():

    class TestCalendar(ExchangeCalendar):
        regular_early_close = time(12, 30)
        name = "TEST"
        tz = timezone("Europe/London")
        open_times = ((None, time(8)),)
        close_times = ((None, time(16, 30)),)

        @property
        def regular_holidays(self): return HolidayCalendar([])

        @property
        def adhoc_holidays(self): return []

        @property
        def special_closes(self):
            return [
                (
                    self.regular_early_close,
                    HolidayCalendar(
                        [
                            ChristmasEve,
                            NewYearsEvePost2000,
                        ]
                    ),
                ),
                (time(11, 30), 0)  # Monday
            ]

        @property
        def special_closes_adhoc(self):
            return [
                (
                    self.regular_early_close,
                    pd.DatetimeIndex([
                        pd.Timestamp("2020-01-08"),
                        pd.Timestamp("2020-08-12"),
                    ])
                )
            ]

        ...

    calendar = TestCalendar()
    special_closes_calendar = get_special_closes_calendar(calendar)
    special_closes = special_closes_calendar.holidays(start=pd.Timestamp("2020-01-01"), end=pd.Timestamp("2020-12-31"), return_name=True)
    expected_special_closes = pd.Series({
        pd.Timestamp("2020-01-06"): "special close day",
        pd.Timestamp("2020-01-08"): "ad-hoc special close day",
        pd.Timestamp("2020-01-13"): "special close day",
        pd.Timestamp("2020-01-20"): "special close day",
        pd.Timestamp("2020-01-27"): "special close day",
        pd.Timestamp("2020-02-03"): "special close day",
        pd.Timestamp("2020-02-10"): "special close day",
        pd.Timestamp("2020-02-17"): "special close day",
        pd.Timestamp("2020-02-24"): "special close day",
        pd.Timestamp("2020-03-02"): "special close day",
        pd.Timestamp("2020-03-09"): "special close day",
        pd.Timestamp("2020-03-16"): "special close day",
        pd.Timestamp("2020-03-23"): "special close day",
        pd.Timestamp("2020-03-30"): "special close day",
        pd.Timestamp("2020-04-06"): "special close day",
        pd.Timestamp("2020-04-13"): "special close day",
        pd.Timestamp("2020-04-20"): "special close day",
        pd.Timestamp("2020-04-27"): "special close day",
        pd.Timestamp("2020-05-04"): "special close day",
        pd.Timestamp("2020-05-11"): "special close day",
        pd.Timestamp("2020-05-18"): "special close day",
        pd.Timestamp("2020-05-25"): "special close day",
        pd.Timestamp("2020-06-01"): "special close day",
        pd.Timestamp("2020-06-08"): "special close day",
        pd.Timestamp("2020-06-15"): "special close day",
        pd.Timestamp("2020-06-22"): "special close day",
        pd.Timestamp("2020-06-29"): "special close day",
        pd.Timestamp("2020-07-06"): "special close day",
        pd.Timestamp("2020-07-13"): "special close day",
        pd.Timestamp("2020-07-20"): "special close day",
        pd.Timestamp("2020-07-27"): "special close day",
        pd.Timestamp("2020-08-03"): "special close day",
        pd.Timestamp("2020-08-10"): "special close day",
        pd.Timestamp("2020-08-12"): "ad-hoc special close day",
        pd.Timestamp("2020-08-17"): "special close day",
        pd.Timestamp("2020-08-24"): "special close day",
        pd.Timestamp("2020-08-31"): "special close day",
        pd.Timestamp("2020-09-07"): "special close day",
        pd.Timestamp("2020-09-14"): "special close day",
        pd.Timestamp("2020-09-21"): "special close day",
        pd.Timestamp("2020-09-28"): "special close day",
        pd.Timestamp("2020-10-05"): "special close day",
        pd.Timestamp("2020-10-12"): "special close day",
        pd.Timestamp("2020-10-19"): "special close day",
        pd.Timestamp("2020-10-26"): "special close day",
        pd.Timestamp("2020-11-02"): "special close day",
        pd.Timestamp("2020-11-09"): "special close day",
        pd.Timestamp("2020-11-16"): "special close day",
        pd.Timestamp("2020-11-23"): "special close day",
        pd.Timestamp("2020-11-30"): "special close day",
        pd.Timestamp("2020-12-07"): "special close day",
        pd.Timestamp("2020-12-14"): "special close day",
        pd.Timestamp("2020-12-21"): "special close day",
        pd.Timestamp("2020-12-24"): "Christmas Eve",
        pd.Timestamp("2020-12-28"): "special close day",
        pd.Timestamp("2020-12-31"): "New Year's Eve",
    })
    assert special_closes.compare(expected_special_closes).empty
