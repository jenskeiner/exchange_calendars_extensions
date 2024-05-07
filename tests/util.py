import datetime as dt
from typing import Union

import pandas as pd


def date2args(date: Union[dt.date, pd.Timestamp]) -> dict[str, int]:
    """
    Convert a date to a dictionary of arguments, including year, month and day.

    Parameters
    ----------
    date : Union[dt.date, pd.Timestamp]
        The date to convert.

    Returns
    -------
    Dict[str, int]
        A dictionary of arguments.
    """
    return {"year": date.year, "month": date.month, "day": date.day}


def roll_backward(d: pd.Timestamp) -> Union[pd.Timestamp, None]:
    return d - pd.Timedelta(days=1)


def roll_forward(d: pd.Timestamp) -> Union[pd.Timestamp, None]:
    return d + pd.Timedelta(days=1)
