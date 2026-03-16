import pandas as pd
import pytest

from exchange_calendars_extensions.core.offset import (
    get_last_day_of_month_offset_class,
    get_third_day_of_week_in_month_offset_class,
)


class TestOffsets:
    @pytest.mark.parametrize(
        "day_of_week, month, expected",
        (
            (3, 1, "2020-01-16"),
            (4, 1, "2020-01-17"),
            (3, 2, "2020-02-20"),
            (4, 2, "2020-02-21"),
            (3, 3, "2020-03-19"),
            (4, 3, "2020-03-20"),
            (3, 4, "2020-04-16"),
            (4, 4, "2020-04-17"),
            (3, 5, "2020-05-21"),
            (4, 5, "2020-05-15"),
            (3, 6, "2020-06-18"),
            (4, 6, "2020-06-19"),
            (3, 7, "2020-07-16"),
            (4, 7, "2020-07-17"),
            (3, 8, "2020-08-20"),
            (4, 8, "2020-08-21"),
            (3, 9, "2020-09-17"),
            (4, 9, "2020-09-18"),
            (3, 10, "2020-10-15"),
            (4, 10, "2020-10-16"),
            (3, 11, "2020-11-19"),
            (4, 11, "2020-11-20"),
            (3, 12, "2020-12-17"),
            (4, 12, "2020-12-18"),
        ),
    )
    def test_get_third_day_of_week_in_month_offset_class_parametrized(
        self, day_of_week: int, month: int, expected: str
    ):
        assert (
            get_third_day_of_week_in_month_offset_class(day_of_week, month)().holiday(
                2020
            )
            == pd.Timestamp(f"{expected}").date()
        )

    @pytest.mark.parametrize(
        "month, expected",
        (
            (1, "2020-01-31"),
            (2, "2020-02-29"),
            (3, "2020-03-31"),
            (4, "2020-04-30"),
            (5, "2020-05-31"),
            (6, "2020-06-30"),
            (7, "2020-07-31"),
            (8, "2020-08-31"),
            (9, "2020-09-30"),
            (10, "2020-10-31"),
            (11, "2020-11-30"),
            (12, "2020-12-31"),
        ),
    )
    def test_get_last_day_of_month_offset_class_parametrized(
        self, month: int, expected: str
    ):
        assert (
            get_last_day_of_month_offset_class(month)().holiday(2020)
            == pd.Timestamp(f"{expected}").date()
        )
