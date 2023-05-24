import datetime as dt

import pandas as pd
import pytest
import json

from schema import SchemaError

from exchange_calendars_extensions import ChangeSet, HolidaysAndSpecialSessions
from exchange_calendars_extensions.changeset import Changes, DaySpec, _DaySchema, _to_time


class TestChanges:
    def test_empty_changes(self):
        c = Changes[DaySpec](schema=_DaySchema)
        assert c.add == dict()
        assert c.remove == set()
        assert c.is_empty()
        assert c.is_consistent()

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_correct_schema(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=strict)

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_incorrect_schema(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        with pytest.raises(SchemaError):
            # Wrong field name.
            c.add_day(date=pd.Timestamp("2020-01-01"), value={"foo": "Holiday"}, strict=strict)
        with pytest.raises(SchemaError):
            # Too many fields.
            c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday", "time": dt.time(10, 0)}, strict=strict)

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_add_day_no_duplicate(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=strict)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == set()
        assert not c.is_empty()
        assert c.is_consistent()

    def test_add_day_duplicate_strict(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=True)
        with pytest.raises(ValueError):
            c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert not c.is_empty()
        assert c.is_consistent()

    def test_add_day_duplicate_lax(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=True)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=False)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == set()
        assert not c.is_empty()
        assert c.is_consistent()

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def add_day_twice(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=strict)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Foo"}, strict=strict)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Foo"}}
        assert c.remove == set()
        assert not c.is_empty()
        assert c.is_consistent()

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_remove_day_no_duplicate(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=True)
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert not c.is_empty()
        assert c.is_consistent()

    def test_remove_day_duplicate_strict(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        with pytest.raises(ValueError):
            c.remove_day(date=pd.Timestamp("2020-01-01"), strict=True)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == set()
        assert not c.is_empty()
        assert c.is_consistent()

    def test_remove_day_duplicate_lax(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=False)
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert not c.is_empty()
        assert c.is_consistent()

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_remove_day_twice(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=strict)
        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=strict)
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert not c.is_empty()
        assert c.is_consistent()

    @pytest.mark.parametrize(["strict"], [(True,), (False,)])
    def test_clear_day(self, strict: bool):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=strict)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == set()
        assert not c.is_empty()
        assert c.is_consistent()
        c.clear_day(date=pd.Timestamp("2020-01-01"))
        assert c.add == dict()
        assert c.remove == set()
        assert c.is_empty()
        assert c.is_consistent()

        c.remove_day(date=pd.Timestamp("2020-01-01"), strict=strict)
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert not c.is_empty()
        assert c.is_consistent()
        c.clear_day(date=pd.Timestamp("2020-01-01"))
        assert c.add == dict()
        assert c.remove == set()
        assert c.is_empty()
        assert c.is_consistent()

    def test_clear(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        c.remove_day(date=pd.Timestamp("2020-01-02"), strict=True)
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == {pd.Timestamp("2020-01-02")}
        assert not c.is_empty()
        assert c.is_consistent()
        c.clear()
        assert c.add == dict()
        assert c.remove == set()
        assert c.is_empty()
        assert c.is_consistent()

    def test_str(self):
        c = Changes[DaySpec](schema=_DaySchema)
        c.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        c.remove_day(date=pd.Timestamp("2020-01-02"), strict=True)
        assert str(c) == "Changes(add={Timestamp('2020-01-01 00:00:00'): {'name': 'Holiday'}}, remove={Timestamp('2020-01-02 00:00:00')})"

    def test_eq(self):
        c1 = Changes[DaySpec](schema=_DaySchema)
        c1.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        c1.remove_day(date=pd.Timestamp("2020-01-02"), strict=True)
        c2 = Changes[DaySpec](schema=_DaySchema)
        c2.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        c2.remove_day(date=pd.Timestamp("2020-01-02"), strict=True)
        assert c1 == c2

        c3 = Changes[DaySpec](schema=_DaySchema)
        c3.add_day(date=pd.Timestamp("2020-01-01"), value={"name": "Holiday"}, strict=True)
        assert c1 != c3

        c3 = Changes[DaySpec](schema=_DaySchema)
        c3.remove_day(date=pd.Timestamp("2020-01-02"), strict=True)
        assert c1 != c3


class TestToTime:
    def test_to_time_valid(self):
        assert _to_time("10:00") == dt.time(10, 0)
        assert _to_time("10:00:00") == dt.time(10, 0)
        assert _to_time(dt.time(10, 0)) == dt.time(10, 0)

    def test_to_time_invalid(self):
        with pytest.raises(ValueError):
            _to_time("10:00:00.000")
        with pytest.raises(ValueError):
            _to_time("10:00:00.000000")
        with pytest.raises(ValueError):
            _to_time("10.00")


class TestHolidaysAndSpecialSessions:
    def test_from_str_valid(self):
        assert HolidaysAndSpecialSessions.from_str("holiday") == HolidaysAndSpecialSessions.HOLIDAY
        assert HolidaysAndSpecialSessions.from_str("HoLiDaY") == HolidaysAndSpecialSessions.HOLIDAY
        assert HolidaysAndSpecialSessions.from_str("special_open") == HolidaysAndSpecialSessions.SPECIAL_OPEN
        assert HolidaysAndSpecialSessions.from_str("SpEcIaL_OpEn") == HolidaysAndSpecialSessions.SPECIAL_OPEN
        assert HolidaysAndSpecialSessions.from_str("special_close") == HolidaysAndSpecialSessions.SPECIAL_CLOSE
        assert HolidaysAndSpecialSessions.from_str("monthly_expiry") == HolidaysAndSpecialSessions.MONTHLY_EXPIRY
        assert HolidaysAndSpecialSessions.from_str("quarterly_expiry") == HolidaysAndSpecialSessions.QUARTERLY_EXPIRY

    def test_from_str_invalid(self):
        with pytest.raises(KeyError):
            HolidaysAndSpecialSessions.from_str("invalid")


def test_empty_changeset_from_dict():
    d = {}
    cs = ChangeSet.from_dict(d)
    assert cs.is_empty()
    assert cs.is_consistent()


@pytest.mark.parametrize(["d_str", "cs"], [
    ("""{"holiday": {"add": [{"date": "2020-01-01", "value": {"name": "Holiday"}}]}}""",
     ChangeSet().add_day(pd.Timestamp("2020-01-01"), {"name": "Holiday"}, HolidaysAndSpecialSessions.HOLIDAY)),
    ("""{"special_open": {"add": [{"date": "2020-01-01", "value": {"name": "Special Open", "time": "10:00"}}]}}""",
     ChangeSet().add_day(pd.Timestamp("2020-01-01"), {"name": "Special Open", "time": dt.time(10, 0)},
                         HolidaysAndSpecialSessions.SPECIAL_OPEN)),
    ("""{"special_close": {"add": [{"date": "2020-01-01", "value": {"name": "Special Close", "time": "16:00"}}]}}""",
     ChangeSet().add_day(pd.Timestamp("2020-01-01"), {"name": "Special Close", "time": dt.time(16, 0)},
                         HolidaysAndSpecialSessions.SPECIAL_CLOSE)),
    ("""{"monthly_expiry": {"add": [{"date": "2020-01-01", "value": {"name": "Monthly Expiry"}}]}}""",
     ChangeSet().add_day(pd.Timestamp("2020-01-01"), {"name": "Monthly Expiry"},
                         HolidaysAndSpecialSessions.MONTHLY_EXPIRY)),
    ("""{"quarterly_expiry": {"add": [{"date": "2020-01-01", "value": {"name": "Quarterly Expiry"}}]}}""",
     ChangeSet().add_day(pd.Timestamp("2020-01-01"), {"name": "Quarterly Expiry"},
                         HolidaysAndSpecialSessions.QUARTERLY_EXPIRY)),
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
