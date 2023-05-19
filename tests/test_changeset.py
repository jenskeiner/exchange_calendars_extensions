import datetime as dt

import pandas as pd
import pytest
import json

from exchange_calendars_extensions import ChangeSet, HolidaysAndSpecialSessions


def test_empty_changeset_from_dict():
    d = {}
    cs = ChangeSet.from_dict(d)
    assert cs.is_empty()
    assert cs.is_consistent()


@pytest.mark.parametrize(["d_str", "cs"], [
    ("""{"holiday": {"add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}]}}""",
     ChangeSet().add_day(HolidaysAndSpecialSessions.HOLIDAY, pd.Timestamp("2020-01-01"), {"name": "Holiday"})),
    ("""{"special_open": {"add": [{"date": "2020-01-01", "value": {"name": "Special Open", "time": "10:00"}}]}}""",
     ChangeSet().add_day(HolidaysAndSpecialSessions.SPECIAL_OPEN, pd.Timestamp("2020-01-01"), {"name": "Special Open", "time": dt.time(10, 0)})),
    ("""{"special_close": {"add": [{"date": "2020-01-01", "value": {"name": "Special Close", "time": "16:00"}}]}}""",
     ChangeSet().add_day(HolidaysAndSpecialSessions.SPECIAL_CLOSE, pd.Timestamp("2020-01-01"), {"name": "Special Close", "time": dt.time(16, 0)})),
    ("""{"monthly_expiry": {"add": [{"date": "2020-01-01", "value": {"name": "Monthly Expiry"}}]}}""",
     ChangeSet().add_day(HolidaysAndSpecialSessions.MONTHLY_EXPIRY, pd.Timestamp("2020-01-01"), {"name": "Monthly Expiry"})),
    ("""{"quarterly_expiry": {"add": [{"date": "2020-01-01", "value": {"name": "Quarterly Expiry"}}]}}""",
     ChangeSet().add_day(HolidaysAndSpecialSessions.QUARTERLY_EXPIRY, pd.Timestamp("2020-01-01"), {"name": "Quarterly Expiry"})),
])
def test_changeset_from_valid_non_empty_dict(d_str: str, cs: ChangeSet):
    d = json.loads(d_str)
    cs0 = ChangeSet.from_dict(d)
    assert not cs0.is_empty()
    assert cs0.is_consistent()
    assert cs0 == cs


@pytest.mark.parametrize(["d_str"], [
    # Invalid day type.
    ("""{"foo": {"add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}]}}""",),
    ("""{"foo": {"add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}]}}""",),
    ("""{"foo": {"add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}]}}""",),
    # Missing date key.
    ("""{"holiday": {"add": [{"value": {"name": "Holiday"}}]}}""",),
    ("""{"monthly_expiry": {"add": [{"value": {"name": "Monthly Expiry"}}]}}""",),
    ("""{"quarterly_expiry": {"add": [{"value": {"name": "Quarterly Expiry"}}]}}""",),
    # Invalid date key.
    ("""{"holiday": {"add": [{"date": "foo", "value": {"name": "Holiday"}}]}}""",),
    ("""{"monthly_expiry": {"add": [{"date": "foo", "value": {"name": "Monthly Expiry"}}]}}""",),
    ("""{"quarterly_expiry": {"add": [{"date": "foo", "value": {"name": "Quarterly Expiry"}}]}}""",),
    # Missing value key.
    ("""{"holiday": {"add": [{"date": "2020-01-01"}]}}""",),
    ("""{"monthly_expiry": {"add": [{"date": "2020-01-01"}]}}""",),
    ("""{"quarterly_expiry": {"add": [{"date": "2020-01-01"}]}}""",),
    # Invalid value key.
    ("""{"holiday": {"add": [{"date": "2020-01-01", "value": {"foo": "Holiday"}}]}}""",),
    ("""{"monthly_expiry": {"add": [{"date": "2020-01-01", "value": {"foo": "Monthly Expiry"}}]}}""",),
    ("""{"quarterly_expiry": {"add": [{"date": "2020-01-01", "value": {"foo": "Quarterly Expiry"}}]}}""",),
    # Invalid day type.
    ("""{"foo": {"add": [{"date": "2020-01-01", "value": {"name": "Special Open", "time": "10:00"}}]}}""",),
    ("""{"foo": {"add": [{"date": "2020-01-01", "value": {"name": "Special Close", "time": "10:00"}}]}}""",),
    # Missing date key.
    ("""{"special_open": {"add": [{"value": {"name": "Special Open", "time": "10:00"}}]}}""",),
    ("""{"special_close": {"add": [{"value": {"name": "Special Close", "time": "10:00"}}]}}""",),
    # Invalid date key.
    ("""{"special_open": {"add": [{"date": "foo", "value": {"name": "Special Open", "time": "10:00"}}]}}""",),
    ("""{"special_close": {"add": [{"date": "foo", "value": {"name": "Special Close", "time": "10:00"}}]}}""",),
    # Missing value key.
    ("""{"special_open": {"add": [{"date": "2020-01-01"}]}}""",),
    ("""{"special_close": {"add": [{"date": "2020-01-01"}]}}""",),
    # Invalid value key.
    ("""{"special_open": {"add": [{"date": "2020-01-01", "value": {"foo": "Special Open", "time": "10:00"}}]}}""",),
    ("""{"special_open": {"add": [{"date": "2020-01-01", "value": {"name": "Special Open", "foo": "10:00"}}]}}""",),
    ("""{"special_close": {"add": [{"date": "2020-01-01", "value": {"foo": "Special Close", "time": "10:00"}}]}}""",),
    ("""{"special_close": {"add": [{"date": "2020-01-01", "value": {"name": "Special Close", "foo": "10:00"}}]}}""",),
])
def test_changeset_from_invalid_dict(d_str: str):
    d = json.loads(d_str)
    with pytest.raises(ValueError):
        ChangeSet.from_dict(d)
