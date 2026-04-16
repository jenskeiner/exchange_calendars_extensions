from exchange_calendars.pandas_extensions.offsets import (
    MultipleWeekmaskCustomBusinessDay,
)

# This module provides a version of MultipleWeekmaskCustomBusinessDay that is patched to remove a bug, if present.


def _is_ok():
    import pandas as pd

    business_day = MultipleWeekmaskCustomBusinessDay(
        weekmask="1111100",
        weekmasks=[
            (None, pd.Timestamp("2023-07-01"), "1111100"),
            (pd.Timestamp("2023-07-02"), None, "0000011"),
        ],
    )
    dates = pd.date_range(
        pd.Timestamp("2023-06-29"), pd.Timestamp("2023-07-07"), freq=business_day
    )

    if pd.Timestamp("2023-07-02") in dates:
        # ALl good.
        return True

    # 2023-07-02 should be in result.
    return False


if not _is_ok():
    from datetime import datetime

    from pandas._libs.tslibs.offsets import apply_wraps

    @apply_wraps
    def _apply(self, day):
        if isinstance(day, datetime):
            sign = 1 if self.n > 0 else -1
            moved = 0
            remaining = self.n - moved
            is_edge: bool = (
                False  # Whether the current day is at the edge of the current interval.
            )
            while remaining != 0:
                # Get business day and interval for current date. Set is_edge to True if
                # the day is at the edge of the current interval, so the call returns
                # the next adjacent interval.
                bday, interval = self._custom_business_day_for(
                    day, remaining, with_interval=True, is_edge=is_edge
                )
                # Next business day according to current interval.
                day_next = bday + day
                # Check if this falls outside the current interval.
                if interval.left <= day_next <= interval.right:
                    # Still in the current interval. Continue with next iteration.
                    moved += sign * max(
                        1, abs(int(self._moved(day, day_next, bday)))
                    )  # Must have moved at least one business day.
                    remaining = self.n - moved
                    day = day_next
                    is_edge = False
                    continue
                # Next day is outside the current interval. Clamp to interval bounds
                #  so when re-entering the loop, the next interval is considered.
                if day_next < interval.left:
                    day = interval.left
                elif day_next > interval.right:
                    day = interval.right
                else:
                    raise RuntimeError("Should not reach here")
                is_edge = True
            return day
        return super().apply(day)

    # Replace _apply and apply with the fixed version.
    MultipleWeekmaskCustomBusinessDay._apply = _apply
    MultipleWeekmaskCustomBusinessDay.apply = _apply

__all__ = ["MultipleWeekmaskCustomBusinessDay"]
