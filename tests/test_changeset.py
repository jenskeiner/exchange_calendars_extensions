import datetime as dt
from copy import copy, deepcopy
from typing import Union, Type

import pandas as pd
import pytest
from pydantic import ValidationError

from exchange_calendars_extensions import DayType
from exchange_calendars_extensions.changeset import Changes, ChangeSet, DaySpec, DayWithTimeSpec


class TestChanges:
    def test_empty_changes(self):
        c = Changes[DaySpec]()
        assert c.add == dict()
        assert c.remove == set()
        assert len(c) == 0
        assert not c

    @pytest.mark.parametrize('typ, d', [
        (DaySpec, {"add": {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}}),
        (DaySpec,
         {"add": {pd.Timestamp("2020-01-01"): {"name": "Holiday"}, pd.Timestamp("2020-01-02"): {"name": "Holiday"}}}),
        (DaySpec, {"add": {dt.date.fromisoformat("2020-01-01"): {"name": "Holiday"},
                           dt.date.fromisoformat("2020-01-02"): {"name": "Holiday"}}}),
        (DaySpec, {"add": {"2020-01-01": {"name": "Holiday"}, pd.Timestamp("2020-01-02"): {"name": "Holiday"}}}),
        (DaySpec, {"remove": [pd.Timestamp("2020-01-03")]}),
        (DaySpec, {"remove": [pd.Timestamp("2020-01-03"), pd.Timestamp("2020-01-04")]}),
        (DaySpec, {"remove": [dt.date.fromisoformat("2020-01-03"), dt.date.fromisoformat("2020-01-04")]}),
        (DaySpec, {"remove": ["2020-01-03", "2020-01-04"]}),
        (DayWithTimeSpec, {"add": {"2020-01-01": {"name": "Holiday", "time": dt.time(10, 0)}}}),
        (DayWithTimeSpec, {"add": {"2020-01-01": {"name": "Holiday", "time": dt.time(10, 0)},
                                   "2020-01-02": {"name": "Holiday", "time": dt.time(10, 0)}}}),
        (DayWithTimeSpec, {"add": {"2020-01-01": {"name": "Holiday", "time": "10:00"},
                                   "2020-01-02": {"name": "Holiday", "time": "10:00"}}}),
        (DayWithTimeSpec, {"add": {"2020-01-01": {"name": "Holiday", "time": "10:00:00"},
                                   "2020-01-02": {"name": "Holiday", "time": "10:00:00"}}}),
    ])
    def test_from_valid_dict(self, typ: Union[Type[DaySpec], Type[DayWithTimeSpec]], d: dict):
        _ = Changes[typ](**d)

    @pytest.mark.parametrize('typ, d', [
        (DaySpec, {"foo": {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}}),  # Invalid top-level key.
        (DaySpec, {"add": {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}, "foo": ["2020-01-03"]}),
        # Extra top-level key.
        (DaySpec, {"add": {dt.time(10, 0): {"name": "Holiday"}}}),  # Invalid timestamp.
        (DaySpec, {"add": {"202020-01-01": {"name": "Holiday"}}}),  # Invalid timestamp.
        (DaySpec, {"add": {"2020-01-01": {"foo": "Holiday"}}}),  # Invalid key in day spec.
        (DaySpec, {"add": {"2020-01-01": {"name": "Holiday", "time": "10:00"}}}),  # Extra key in day spec.
        (DaySpec, {"add": {"2020-01-01": {"name": "Holiday", "foo": "bar"}}}),  # Extra key in day spec.
        (DayWithTimeSpec, {"add": {"2020-01-01": {"foo": "Holiday", "time": "10:00"}}}),  # Invalid key in day spec.
        (DayWithTimeSpec, {"add": {"2020-01-01": {"name": "Holiday", "time": "10:00", "foo": "bar"}}}),
        # Extra key in day spec.
        (DaySpec, {"remove": [pd.Timestamp("2020-01-03")], "foo": ["2020-01-04"]}),  # Extra top-level key.
        (DaySpec, {"remove": ["202020-01-03"]}),  # Invalid timestamp.
    ])
    def test_from_invalid_dict(self, typ: Union[Type[DaySpec], Type[DayWithTimeSpec]], d: dict):
        with pytest.raises(ValidationError):
            _ = Changes[typ](**d)

    def test_add_day(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        assert c.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Holiday"})}
        assert c.remove == set()
        assert len(c) == 1
        assert c

    def test_add_day_duplicate(self):
        c = Changes[DaySpec]()
        c.remove_day(date=pd.Timestamp("2020-01-01"))
        with pytest.raises(ValidationError):
            c.add_day(date=pd.Timestamp("2020-01-01"), value=DaySpec(**{"name": "Holiday"}))
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert len(c) == 1
        assert c

    def test_remove_clear_add_day(self):
        c = Changes[DaySpec]()
        c.remove_day(date="2020-01-01")
        c.clear_day(date="2020-01-01")
        c.add_day(date="2020-01-01", value=DaySpec(**{"name": "Holiday"}))
        assert c.add == {pd.Timestamp("2020-01-01"): {"name": "Holiday"}}
        assert c.remove == set()
        assert len(c) == 1
        assert c

    def test_add_day_twice(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        c.add_day(date="2020-01-01", value={"name": "Foo"})
        assert c.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Foo"})}
        assert c.remove == set()
        assert len(c) == 1
        assert c

    def test_remove_day(self):
        c = Changes[DaySpec]()
        c.remove_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert len(c) == 1
        assert c

    def test_remove_day_duplicate(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        with pytest.raises(ValidationError):
            c.remove_day(date="2020-01-01")
        assert c.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Holiday"})}
        assert c.remove == set()
        assert len(c) == 1
        assert c

    def test_add_clear_remove_day(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        c.clear_day(date="2020-01-01")
        c.remove_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert len(c) == 1
        assert c

    def test_remove_day_twice(self):
        c = Changes[DaySpec]()
        c.remove_day(date="2020-01-01")
        c.remove_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert len(c) == 1
        assert c

    def test_clear_day(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        assert c.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Holiday"})}
        assert c.remove == set()
        assert len(c) == 1
        assert c
        c.clear_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == set()
        assert len(c) == 0
        assert not c

        c.remove_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == {pd.Timestamp("2020-01-01")}
        assert len(c) == 1
        assert c
        c.clear_day(date="2020-01-01")
        assert c.add == dict()
        assert c.remove == set()
        assert len(c) == 0
        assert not c

    def test_clear(self):
        c = Changes[DaySpec]()
        c.add_day(date="2020-01-01", value={"name": "Holiday"})
        c.remove_day(date="2020-01-02")
        assert c.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Holiday"})}
        assert c.remove == {pd.Timestamp("2020-01-02")}
        assert len(c) == 2
        assert c
        c.clear()
        assert c.add == dict()
        assert c.remove == set()
        assert len(c) == 0
        assert not c

    def test_eq(self):
        c1 = Changes[DaySpec]()
        c1.add_day(date="2020-01-01", value={"name": "Holiday"})
        c1.remove_day(date="2020-01-02")
        c2 = Changes[DaySpec]()
        c2.add_day(date="2020-01-01", value={"name": "Holiday"})
        c2.remove_day(date="2020-01-02")
        assert c1 == c2

        c3 = Changes[DaySpec]()
        c3.add_day(date="2020-01-01", value={"name": "Holiday"})
        assert c1 != c3

        c3 = Changes[DaySpec]()
        c3.remove_day(date="2020-01-02")
        assert c1 != c3

    def test_copy(self):
        c1 = Changes[DaySpec]()
        c1.add_day(date="2020-01-01", value={"name": "Holiday"})
        c1.remove_day(date="2020-01-02")
        c2 = copy(c1)
        assert c1 == c2
        assert c1 is not c2
        assert c1.add is c2.add
        assert c1.remove is c2.remove

    def test_deepcopy(self):
        c1 = Changes[DaySpec]()
        c1.add_day(date="2020-01-01", value={"name": "Holiday"})
        c1.remove_day(date="2020-01-02")
        c2 = deepcopy(c1)
        assert c1 == c2
        assert c1 is not c2
        assert c1.add is not c2.add
        assert c1.remove is not c2.remove


class TestChangeSet:
    def test_empty_changeset(self):
        cs = ChangeSet()
        assert len(cs) == 0

    @pytest.mark.parametrize(["date", "value", "day_type"], [
        ("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01"), {"name": "Holiday"}, DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Holiday"}, "holiday"),
        ("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01"), {"name": "Special Open", "time": "10:00:00"}, DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01").date(), {"name": "Special Open", "time": dt.time(10, 0)}, "special_open"),
        ("2020-01-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01"), {"name": "Special Close", "time": "16:00:00"}, DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01").date(), {"name": "Special Close", "time": dt.time(16, 0)}, "special_close"),
        ("2020-01-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Monthly Expiry"}, "monthly_expiry"),
        ("2020-01-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Quarterly Expiry"}, "quarterly_expiry"),
    ])
    def test_add_valid_day(self, date, value, day_type):
        cs = ChangeSet()
        cs.add_day(date, value, day_type)
        assert len(cs) == 1

        # Normalise day type to string.
        day_type = day_type.value if isinstance(day_type, DayType) else day_type

        # The day types where the day was not added.
        other_day_types = (x.value for x in DayType if x != day_type)

        # Determine day spec type to use for day type.
        spec_t = DaySpec if day_type in ("holiday", "monthly_expiry", "quarterly_expiry") else DayWithTimeSpec

        # Check given day type.
        assert getattr(cs, day_type).add == {pd.Timestamp("2020-01-01"): spec_t(**value)}
        assert getattr(cs, day_type).remove == set()

        # Check other day types.
        for other_day_type in other_day_types:
            assert getattr(cs, other_day_type).add == dict()
            assert getattr(cs, other_day_type).remove == set()

    @pytest.mark.parametrize(["date", "day_type"], [
        ("2020-01-01", DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01"), DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01").date(), "holiday"),
        ("2020-01-01", DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01"), DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01").date(), "special_open"),
        ("2020-01-01", DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01"), DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01").date(), "special_close"),
        ("2020-01-01", DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), "monthly_expiry"),
        ("2020-01-01", DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), "quarterly_expiry"),
    ])
    def test_remove_day(self, date, day_type):
        cs = ChangeSet()
        cs.remove_day(date, day_type)
        assert len(cs) == 1

        # Normalise day type to string.
        day_type = day_type.value if isinstance(day_type, DayType) else day_type

        # The day types where the day was not added.
        other_day_types = (x.value for x in DayType if x != day_type)

        # Check given day type.
        assert getattr(cs, day_type).add == dict()
        assert getattr(cs, day_type).remove == {pd.Timestamp("2020-01-01")}

        # Check other day types.
        for other_day_type in other_day_types:
            assert getattr(cs, other_day_type).add == dict()
            assert getattr(cs, other_day_type).remove == set()

    def test_remove_day_all_day_types(self):
        cs = ChangeSet()
        cs.remove_day("2020-01-01")
        assert len(cs) == len(DayType)

        # Check all day types.
        for day_type in DayType:
            assert getattr(cs, day_type.value).add == dict()
            assert getattr(cs, day_type.value).remove == {pd.Timestamp("2020-01-01")}

    @pytest.mark.parametrize(["date", "value", "day_type"], [
        ("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01"), {"name": "Holiday"}, DayType.HOLIDAY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Holiday"}, "holiday"),
        ("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01"), {"name": "Special Open", "time": "10:00:00"}, DayType.SPECIAL_OPEN),
        (pd.Timestamp("2020-01-01").date(), {"name": "Special Open", "time": dt.time(10, 0)}, "special_open"),
        ("2020-01-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01"), {"name": "Special Close", "time": "16:00:00"}, DayType.SPECIAL_CLOSE),
        (pd.Timestamp("2020-01-01").date(), {"name": "Special Close", "time": dt.time(16, 0)}, "special_close"),
        ("2020-01-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Monthly Expiry"}, "monthly_expiry"),
        ("2020-01-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01"), {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
        (pd.Timestamp("2020-01-01").date(), {"name": "Quarterly Expiry"}, "quarterly_expiry"),
    ])
    def test_clear_day(self, date, value, day_type):
        cs = ChangeSet()
        cs.add_day(date, value, day_type)
        cs.clear_day(date)
        assert len(cs) == 0

        # Check all day types.
        for x in DayType:
            assert getattr(cs, x.value).add == dict()
            assert getattr(cs, x.value).remove == set()

    def test_clear_day_all_day_types(self):
        cs = ChangeSet()
        cs.add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
        cs.remove_day("2020-01-01", DayType.SPECIAL_OPEN)
        cs.remove_day("2020-01-01", DayType.SPECIAL_CLOSE)
        cs.remove_day("2020-01-01", DayType.MONTHLY_EXPIRY)
        cs.remove_day("2020-01-01", DayType.QUARTERLY_EXPIRY)
        cs.clear_day("2020-01-01")
        assert len(cs) == 0

        # Check all day types.
        for x in DayType:
            assert getattr(cs, x.value).add == dict()
            assert getattr(cs, x.value).remove == set()

    def test_clear(self):
        cs = ChangeSet()
        cs.add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
        cs.add_day("2020-01-02", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)
        cs.add_day("2020-01-03", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE)
        cs.add_day("2020-01-04", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)
        cs.add_day("2020-01-05", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)
        cs.remove_day("2020-01-06", DayType.HOLIDAY)
        cs.remove_day("2020-01-07", DayType.SPECIAL_OPEN)
        cs.remove_day("2020-01-08", DayType.SPECIAL_CLOSE)
        cs.remove_day("2020-01-09", DayType.MONTHLY_EXPIRY)
        cs.remove_day("2020-01-10", DayType.QUARTERLY_EXPIRY)

        assert len(cs) == 10
        assert cs.holiday.add == {pd.Timestamp("2020-01-01"): DaySpec(**{"name": "Holiday"})}
        assert cs.holiday.remove == {pd.Timestamp("2020-01-06")}
        assert cs.special_open.add == {
            pd.Timestamp("2020-01-02"): DayWithTimeSpec(**{"name": "Special Open", "time": "10:00"})}
        assert cs.special_open.remove == {pd.Timestamp("2020-01-07")}
        assert cs.special_close.add == {
            pd.Timestamp("2020-01-03"): DayWithTimeSpec(**{"name": "Special Close", "time": "16:00"})}
        assert cs.special_close.remove == {pd.Timestamp("2020-01-08")}
        assert cs.monthly_expiry.add == {pd.Timestamp("2020-01-04"): DaySpec(**{"name": "Monthly Expiry"})}
        assert cs.monthly_expiry.remove == {pd.Timestamp("2020-01-09")}
        assert cs.quarterly_expiry.add == {pd.Timestamp("2020-01-05"): DaySpec(**{"name": "Quarterly Expiry"})}
        assert cs.quarterly_expiry.remove == {pd.Timestamp("2020-01-10")}

        cs.clear()

        assert not cs

        # Check all day types.
        for x in DayType:
            assert getattr(cs, x.value).add == dict()
            assert getattr(cs, x.value).remove == set()

    @pytest.mark.parametrize(["date", "value", "day_type"], [
        ("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY),
        ("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN),
        ("2020-01-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE),
        ("2020-01-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
        ("2020-01-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
    ])
    def test_add_remove_day_for_same_day_type(self, date, value, day_type: DayType):
        cs = ChangeSet()
        cs.remove_day(date, day_type)
        with pytest.raises(ValidationError):
            cs.add_day(date, value, day_type)
        assert getattr(cs, day_type.value).add == dict()
        assert getattr(cs, day_type.value).remove == {pd.Timestamp(date)}
        assert len(cs) == 1
        assert cs

        # Determine day spec type to use for day type.
        spec_t = DaySpec if day_type in (
        DayType.HOLIDAY, DayType.MONTHLY_EXPIRY, DayType.QUARTERLY_EXPIRY) else DayWithTimeSpec

        cs = ChangeSet()
        cs.add_day(date, value, day_type)
        with pytest.raises(ValidationError):
            cs.remove_day(date, day_type)
        assert getattr(cs, day_type.value).add == {pd.Timestamp(date): spec_t(**value)}
        assert getattr(cs, day_type.value).remove == set()
        assert len(cs) == 1
        assert cs

    def test_add_same_day_twice(self):
        cs = ChangeSet()
        cs.add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
        with pytest.raises(ValidationError):
            cs.add_day("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)
        assert len(cs) == 1
        assert cs

    @pytest.mark.parametrize(["d", "cs"], [
        ({"holiday": {"add": {"2020-01-01": {"name": "Holiday"}}}},
         ChangeSet().add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)),
        ({"special_open": {"add": {"2020-01-01": {"name": "Special Open", "time": "10:00"}}}},
         ChangeSet().add_day("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)),
        ({"special_close": {"add": {"2020-01-01": {"name": "Special Close", "time": "16:00"}}}},
         ChangeSet().add_day("2020-01-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE)),
        ({"monthly_expiry": {"add": {"2020-01-01": {"name": "Monthly Expiry"}}}},
         ChangeSet().add_day("2020-01-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)),
        ({"quarterly_expiry": {"add": {"2020-01-01": {"name": "Quarterly Expiry"}}}},
         ChangeSet().add_day("2020-01-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)),
        ({"holiday": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.HOLIDAY)),
        ({"special_open": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_OPEN)),
        ({"special_close": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_CLOSE)),
        ({"monthly_expiry": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.MONTHLY_EXPIRY)),
        ({"quarterly_expiry": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.QUARTERLY_EXPIRY)),
        ({"special_open": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_OPEN)),
        ({"special_close": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_CLOSE)),
        ({"monthly_expiry": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.MONTHLY_EXPIRY)),
        ({"quarterly_expiry": {"remove": ["2020-01-01"]}},
         ChangeSet().remove_day("2020-01-01", DayType.QUARTERLY_EXPIRY)),
        ({
             "holiday": {"add": {"2020-01-01": {"name": "Holiday"}}, "remove": ["2020-01-02"]},
             "special_open": {"add": {"2020-02-01": {"name": "Special Open", "time": "10:00"}},
                              "remove": ["2020-02-02"]},
             "special_close": {"add": {"2020-03-01": {"name": "Special Close", "time": "16:00"}},
                               "remove": ["2020-03-02"]},
             "monthly_expiry": {"add": {"2020-04-01": {"name": "Monthly Expiry"}}, "remove": ["2020-04-02"]},
             "quarterly_expiry": {"add": {"2020-05-01": {"name": "Quarterly Expiry"}}, "remove": ["2020-05-02"]}
         },
         ChangeSet()
         .add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
         .remove_day("2020-01-02", day_type=DayType.HOLIDAY)
         .add_day("2020-02-01", {"name": "Special Open", "time": dt.time(10, 0)}, DayType.SPECIAL_OPEN)
         .remove_day("2020-02-02", day_type=DayType.SPECIAL_OPEN)
         .add_day("2020-03-01", {"name": "Special Close", "time": dt.time(16, 0)}, DayType.SPECIAL_CLOSE)
         .remove_day("2020-03-02", day_type=DayType.SPECIAL_CLOSE)
         .add_day("2020-04-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)
         .remove_day("2020-04-02", day_type=DayType.MONTHLY_EXPIRY)
         .add_day("2020-05-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)
         .remove_day(pd.Timestamp("2020-05-02"), day_type=DayType.QUARTERLY_EXPIRY)),
    ])
    def test_changeset_from_valid_non_empty_dict(self, d: dict, cs: ChangeSet):
        cs0 = ChangeSet(**d)
        assert cs0 == cs

    @pytest.mark.parametrize(["d"], [
        # Invalid day type.
        ({"foo": {"add": {"2020-01-01": {"name": "Holiday"}}}},),
        ({"foo": {"add": {"2020-01-01": {"name": "Holiday"}}}},),
        ({"foo": {"add": {"2020-01-01": {"name": "Holiday"}}}},),
        # Invalid date.
        ({"holiday": {"add": {"foo": {"name": "Holiday"}}}},),
        ({"monthly_expiry": {"add": {"foo": {"name": "Monthly Expiry"}}}},),
        ({"quarterly_expiry": {"add": {"foo": {"name": "Quarterly Expiry"}}}},),
        # Invalid value.
        ({"holiday": {"add": {"2020-01-01": {"foo": "Holiday"}}}},),
        ({"holiday": {"add": {"2020-01-01": {"name": "Holiday", "time": "10:00"}}}},),
        ({"holiday": {"add": {"2020-01-01": {"name": "Holiday", "foo": "bar"}}}},),
        ({"monthly_expiry": {"add": {"2020-01-01": {"foo": "Monthly Expiry"}}}},),
        ({"quarterly_expiry": {"add": {"2020-01-01": {"foo": "Quarterly Expiry"}}}},),
        # Invalid day type.
        ({"foo": {"add": {"2020-01-01": {"name": "Special Open", "time": "10:00"}}}},),
        ({"foo": {"add": {"2020-01-01": {"name": "Special Close", "time": "10:00"}}}},),
        # Invalid date.
        ({"special_open": {"add": {"foo": {"name": "Special Open", "time": "10:00"}}}},),
        ({"special_close": {"add": {"foo": {"name": "Special Close", "time": "10:00"}}}},),
        # Invalid value key.
        ({"special_open": {"add": {"2020-01-01": {"foo": "Special Open", "time": "10:00"}}}},),
        ({"special_open": {"add": {"2020-01-01": {"name": "Special Open", "foo": "10:00"}}}},),
        ({"special_close": {"add": {"2020-01-01": {"foo": "Special Close", "time": "10:00"}}}},),
        ({"special_close": {"add": {"2020-01-01": {"name": "Special Close", "foo": "10:00"}}}},),
    ])
    def test_changeset_from_invalid_dict(self, d: dict):
        with pytest.raises(ValidationError):
            ChangeSet(**d)

    @pytest.mark.parametrize(["d"], [
        # Same day added twice for different day types.
        ({
             "holiday": {"add": {"2020-01-01": {"name": "Holiday"}}},
             "special_open": {"add": {"2020-01-01": {"name": "Special Open", "time": "10:00"}}}
         },),
        ({
             "holiday": {"add": {"2020-01-01": {"name": "Holiday"}}},
             "special_close": {"add": {"2020-01-01": {"name": "Special Close", "time": "16:00"}}}
         },),
        ({
             "holiday": {"add": {"2020-01-01": {"name": "Holiday"}}},
             "monthly_expiry": {"add": {"2020-01-01": {"name": "Monthly Expiry"}}}
         },),
        ({
             "holiday": {"add": {"2020-01-01": {"name": "Holiday"}}},
             "quarterly_expiry": {"add": {"2020-01-01": {"name": "Quarterly Expiry"}}}
         },),
        # Same day added and removed for same day type.
        ({"holiday": {"add": {"2020-01-01": {"name": "Holiday"}}, "remove": ["2020-01-01"]}},),
        ({"special_open": {"add": {"2020-01-01": {"name": "Special Open", "time": "10:00"}},
                           "remove": ["2020-01-01"]}},),
        ({"special_close": {"add": {"2020-01-01": {"name": "Special Close", "time": "16:00"}},
                            "remove": ["2020-01-01"]}},),
        ({"monthly_expiry": {"add": {"2020-01-01": {"name": "Holiday"}}, "remove": ["2020-01-01"]}},),
        ({"quarterly_expiry": {"add": {"2020-01-01": {"name": "Holiday"}}, "remove": ["2020-01-01"]}},), ])
    def test_changeset_from_inconsistent_dict(self, d: dict):
        with pytest.raises(ValidationError):
            ChangeSet(**d)

    @pytest.mark.parametrize(["cs", "cs_normalized"], [
        (ChangeSet().add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY),
         ChangeSet().remove_day("2020-01-01").clear_day("2020-01-01", DayType.HOLIDAY).add_day("2020-01-01",
                                                                                               {"name": "Holiday"},
                                                                                               DayType.HOLIDAY)),
        (ChangeSet().add_day("2020-01-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN),
         ChangeSet().remove_day("2020-01-01").clear_day("2020-01-01", DayType.SPECIAL_OPEN).add_day("2020-01-01", {
             "name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)),
        (ChangeSet().add_day("2020-01-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE),
         ChangeSet().remove_day("2020-01-01").clear_day("2020-01-01", DayType.SPECIAL_CLOSE).add_day("2020-01-01", {
             "name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE)),
        (ChangeSet().add_day("2020-01-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY),
         ChangeSet().remove_day("2020-01-01").clear_day("2020-01-01", DayType.MONTHLY_EXPIRY).add_day("2020-01-01", {
             "name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)),
        (ChangeSet().add_day("2020-01-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY),
         ChangeSet().remove_day("2020-01-01").clear_day("2020-01-01", DayType.QUARTERLY_EXPIRY).add_day("2020-01-01", {
             "name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)),
        (ChangeSet().remove_day("2020-01-01", DayType.HOLIDAY),
         ChangeSet().remove_day("2020-01-01", DayType.HOLIDAY)),
        (ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_OPEN),
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_OPEN)),
        (ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_CLOSE),
         ChangeSet().remove_day("2020-01-01", DayType.SPECIAL_CLOSE)),
        (ChangeSet().remove_day("2020-01-01", DayType.MONTHLY_EXPIRY),
         ChangeSet().remove_day("2020-01-01", DayType.MONTHLY_EXPIRY)),
        (ChangeSet().remove_day("2020-01-01", DayType.QUARTERLY_EXPIRY),
         ChangeSet().remove_day("2020-01-01", DayType.QUARTERLY_EXPIRY)),
        (ChangeSet()
         .add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
         .remove_day("2020-01-02", DayType.HOLIDAY)
         .add_day("2020-02-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)
         .remove_day("2020-02-02", DayType.SPECIAL_OPEN)
         .add_day("2020-03-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE)
         .remove_day("2020-03-02", DayType.SPECIAL_CLOSE)
         .add_day("2020-04-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)
         .remove_day("2020-04-02", DayType.MONTHLY_EXPIRY)
         .add_day("2020-05-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)
         .remove_day("2020-05-02", DayType.QUARTERLY_EXPIRY),
         ChangeSet()
         .remove_day("2020-01-01")
         .clear_day("2020-01-01", DayType.HOLIDAY)
         .add_day("2020-01-01", {"name": "Holiday"}, DayType.HOLIDAY)
         .remove_day("2020-01-02", DayType.HOLIDAY)
         .remove_day("2020-02-01")
         .clear_day("2020-02-01", DayType.SPECIAL_OPEN)
         .add_day("2020-02-01", {"name": "Special Open", "time": "10:00"}, DayType.SPECIAL_OPEN)
         .remove_day("2020-02-02", DayType.SPECIAL_OPEN)
         .remove_day("2020-03-01")
         .clear_day("2020-03-01", DayType.SPECIAL_CLOSE)
         .add_day("2020-03-01", {"name": "Special Close", "time": "16:00"}, DayType.SPECIAL_CLOSE)
         .remove_day("2020-03-02", DayType.SPECIAL_CLOSE)
         .remove_day("2020-04-01")
         .clear_day("2020-04-01", DayType.MONTHLY_EXPIRY)
         .add_day("2020-04-01", {"name": "Monthly Expiry"}, DayType.MONTHLY_EXPIRY)
         .remove_day("2020-04-02", DayType.MONTHLY_EXPIRY)
         .remove_day("2020-05-01")
         .clear_day("2020-05-01", DayType.QUARTERLY_EXPIRY)
         .add_day("2020-05-01", {"name": "Quarterly Expiry"}, DayType.QUARTERLY_EXPIRY)
         .remove_day("2020-05-02", DayType.QUARTERLY_EXPIRY)),
    ])
    def test_normalize(self, cs: ChangeSet, cs_normalized: ChangeSet):
        # Return copy.
        cs_normalized0 = cs.normalize(inplace=False)
        # Should have returned a new copy.
        assert id(cs_normalized0) != id(cs)
        assert id(cs_normalized0) != id(cs_normalized)
        # Should be identical to passed in normalized changeset.
        assert cs_normalized0 == cs_normalized
        # Idempotency.
        assert cs_normalized0.normalize(inplace=False) == cs_normalized0

        # In-place.
        cs_normalized0 = cs.normalize(inplace=True)
        # Should have returned the same object.
        assert id(cs_normalized0) == id(cs)
        assert id(cs_normalized0) != id(cs_normalized)
        # Should be identical to passed in normalized changeset.
        assert cs_normalized0 == cs_normalized
