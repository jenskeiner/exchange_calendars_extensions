import datetime as dt
from collections import OrderedDict

import pandas as pd
import pytest
from pydantic import TypeAdapter, ValidationError
from pydantic.experimental.missing_sentinel import MISSING

from exchange_calendars_extensions.changes import (
    BusinessDaySpec,
    ChangeSetDelta,
    DayChange,
    DaySpec,
    NonBusinessDaySpec,
)
from exchange_calendars_extensions.datetime import DateLike


@pytest.fixture()
def business_day_spec() -> BusinessDaySpec:
    return BusinessDaySpec()


@pytest.fixture()
def non_business_day_weekend() -> NonBusinessDaySpec:
    return NonBusinessDaySpec(weekend_day=True)


@pytest.fixture()
def non_business_day_holiday() -> NonBusinessDaySpec:
    return NonBusinessDaySpec(holiday=True)


@pytest.fixture()
def day_change_minimal() -> DayChange:
    return DayChange()


class TestNonBusinessDaySpec:
    """Tests for NonBusinessDaySpec model and its validator."""

    @pytest.mark.parametrize(
        ("weekend_day", "holiday"),
        (
            pytest.param(True, MISSING, id="weekend_only"),
            pytest.param(MISSING, True, id="holiday_only"),
            pytest.param(True, True, id="both_true"),
            pytest.param(True, False, id="weekend_true_holiday_false"),
            pytest.param(False, True, id="holiday_true_weekend_false"),
        ),
    )
    def test_valid_combinations(self, weekend_day, holiday) -> None:
        kwargs = {}
        if weekend_day is not MISSING:
            kwargs["weekend_day"] = weekend_day
        if holiday is not MISSING:
            kwargs["holiday"] = holiday
        spec = NonBusinessDaySpec(**kwargs)
        assert spec.weekend_day is weekend_day
        assert spec.holiday is holiday

    @pytest.mark.parametrize(
        ("weekend_day", "holiday"),
        (
            pytest.param(MISSING, MISSING, id="both_missing"),
            pytest.param(False, MISSING, id="weekend_false_holiday_missing"),
            pytest.param(MISSING, False, id="holiday_false_weekend_missing"),
            pytest.param(False, False, id="both_false"),
        ),
    )
    def test_rejects_invalid_combinations(self, weekend_day, holiday) -> None:
        kwargs = {}
        if weekend_day is not MISSING:
            kwargs["weekend_day"] = weekend_day
        if holiday is not MISSING:
            kwargs["holiday"] = holiday
        with pytest.raises(ValidationError, match="weekend day or a holiday"):
            NonBusinessDaySpec(**kwargs)


class TestBusinessDaySpec:
    """Tests for the BusinessDaySpec model."""

    @pytest.mark.parametrize(
        ("open_val", "close_val", "expected_open", "expected_close"),
        (
            pytest.param(MISSING, MISSING, MISSING, MISSING, id="both_missing"),
            pytest.param("regular", "regular", "regular", "regular", id="both_regular"),
            pytest.param(
                dt.time(9, 30),
                dt.time(16, 0),
                dt.time(9, 30),
                dt.time(16, 0),
                id="time_objects",
            ),
            pytest.param(
                "09:30", "16:00", dt.time(9, 30), dt.time(16, 0), id="time_strings"
            ),
            pytest.param(
                "regular",
                dt.time(15, 0),
                "regular",
                dt.time(15, 0),
                id="mixed_regular_and_time",
            ),
            pytest.param(
                dt.time(10, 0), MISSING, dt.time(10, 0), MISSING, id="only_open"
            ),
            pytest.param(MISSING, "regular", MISSING, "regular", id="only_close"),
        ),
    )
    def test_open_close_values(
        self, open_val, close_val, expected_open, expected_close
    ) -> None:
        kwargs = {}
        if open_val is not MISSING:
            kwargs["open"] = open_val
        if close_val is not MISSING:
            kwargs["close"] = close_val
        spec = BusinessDaySpec(**kwargs)
        assert spec.open is expected_open or spec.open == expected_open
        assert spec.close is expected_close or spec.close == expected_close


# ---------------------------------------------------------------------------
# DaySpec (discriminated union)
# ---------------------------------------------------------------------------


class TestDaySpec:
    """Tests for the DaySpec discriminated union."""

    _ta = TypeAdapter(DaySpec)

    def test_resolves_to_business_day_spec(self) -> None:
        spec = self._ta.validate_python({"business_day": True})
        assert isinstance(spec, BusinessDaySpec)

    def test_resolves_to_non_business_day_spec(self) -> None:
        spec = self._ta.validate_python({"business_day": False, "weekend_day": True})
        assert isinstance(spec, NonBusinessDaySpec)

    def test_business_day_with_open_close(self) -> None:
        spec = self._ta.validate_python(
            {"business_day": True, "open": dt.time(9, 30), "close": dt.time(16, 0)}
        )
        assert isinstance(spec, BusinessDaySpec)
        assert spec.open == dt.time(9, 30)
        assert spec.close == dt.time(16, 0)

    def test_missing_discriminator_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._ta.validate_python({})


# ---------------------------------------------------------------------------
# DayChange
# ---------------------------------------------------------------------------


class TestDayChange:
    """Tests for the DayChange model."""

    def test_all_defaults(self) -> None:
        dc = DayChange()
        assert dc.spec is MISSING
        assert dc.name is MISSING
        assert dc.tags is MISSING

    def test_with_business_day_spec(self, business_day_spec: BusinessDaySpec) -> None:
        dc = DayChange(spec=business_day_spec)
        assert isinstance(dc.spec, BusinessDaySpec)

    def test_with_non_business_day_spec(
        self, non_business_day_weekend: NonBusinessDaySpec
    ) -> None:
        dc = DayChange(spec=non_business_day_weekend)
        assert isinstance(dc.spec, NonBusinessDaySpec)

    def test_name_string(self) -> None:
        dc = DayChange(name="Holiday")
        assert dc.name == "Holiday"

    def test_name_none(self) -> None:
        dc = DayChange(name=None)
        assert dc.name is None

    def test_name_missing(self) -> None:
        dc = DayChange()
        assert dc.name is MISSING

    def test_tags_set(self) -> None:
        dc = DayChange(tags={"tag-a", "tag-b"})
        assert dc.tags == {"tag-a", "tag-b"}

    def test_tags_empty_set(self) -> None:
        dc = DayChange(tags=set())
        assert dc.tags == set()

    def test_tags_missing(self) -> None:
        dc = DayChange()
        assert dc.tags is MISSING

    def test_full_construction(self) -> None:
        dc = DayChange(
            spec=BusinessDaySpec(open=dt.time(9, 30), close=dt.time(16, 0)),
            name="Special Day",
            tags={"custom-tag"},
        )
        assert dc.name == "Special Day"
        assert dc.tags == {"custom-tag"}
        assert isinstance(dc.spec, BusinessDaySpec)
        assert dc.spec.open == dt.time(9, 30)
        assert dc.spec.close == dt.time(16, 0)

    def test_from_dict_business_day(self) -> None:
        dc = DayChange.model_validate(
            {
                "spec": {"business_day": True, "open": "regular"},
                "name": "Test",
                "tags": ["x"],
            }
        )
        assert isinstance(dc.spec, BusinessDaySpec)
        assert dc.name == "Test"
        assert dc.tags == {"x"}

    def test_from_dict_non_business_day(self) -> None:
        dc = DayChange.model_validate(
            {
                "spec": {"business_day": False, "holiday": True},
                "name": "New Year",
            }
        )
        assert isinstance(dc.spec, NonBusinessDaySpec)
        assert dc.name == "New Year"
        assert dc.tags is MISSING


class TestChangeSet:
    """Tests for the ChangeSet annotated type alias."""

    _ta = TypeAdapter(ChangeSetDelta)

    def test_empty_changeset(self) -> None:
        cs = self._ta.validate_python({})
        assert len(cs) == 0
        assert isinstance(cs, OrderedDict)

    def test_single_entry(self) -> None:
        cs = self._ta.validate_python({"2024-01-15": DayChange()})
        assert len(cs) == 1
        assert pd.Timestamp("2024-01-15") in cs

    def test_sorts_entries_by_date(self) -> None:
        cs = self._ta.validate_python(
            {
                "2024-12-25": DayChange(name="Christmas"),
                "2024-01-01": DayChange(name="New Year"),
                "2024-07-04": DayChange(name="Independence Day"),
            }
        )
        keys = list(cs.keys())
        assert keys == [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-07-04"),
            pd.Timestamp("2024-12-25"),
        ]

    def test_with_mixed_day_specs(self) -> None:
        cs = self._ta.validate_python(
            {
                "2024-01-15": DayChange(spec=BusinessDaySpec()),
                "2024-12-25": DayChange(
                    spec=NonBusinessDaySpec(holiday=True),
                ),
            }
        )
        assert isinstance(cs[DateLike("2024-01-15")].spec, BusinessDaySpec)
        assert isinstance(cs[DateLike("2024-12-25")].spec, NonBusinessDaySpec)

    def test_date_key_from_string(self) -> None:
        cs = self._ta.validate_python({"2024-01-15": DayChange()})
        assert pd.Timestamp("2024-01-15") in cs

    def test_date_key_from_datetime_date(self) -> None:
        cs = self._ta.validate_python({dt.date(2024, 1, 15): DayChange()})
        assert pd.Timestamp("2024-01-15") in cs

    def test_date_key_from_timestamp(self) -> None:
        cs = self._ta.validate_python({pd.Timestamp("2024-01-15"): DayChange()})
        assert pd.Timestamp("2024-01-15") in cs

    def test_from_dict_validation(self) -> None:
        cs = self._ta.validate_python(
            {
                "2024-02-14": {"name": "Valentine's Day"},
                "2024-01-01": {"name": "New Year"},
            }
        )
        keys = list(cs.keys())
        assert keys[0] == pd.Timestamp("2024-01-01")
        assert keys[1] == pd.Timestamp("2024-02-14")
