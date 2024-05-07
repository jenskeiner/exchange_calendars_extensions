from datetime import date
from datetime import timedelta


def get_month_name(month: int) -> str:
    """
    Convert month to capitalized name of month.

    Parameters
    ----------
    month : int
        Month number (1-12).

    Returns
    -------
    str
        Name of month.
    """
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    month_name = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ][month - 1]

    return month_name


def get_day_of_week_name(day_of_week: int) -> str:
    """
    Convert day of week number to name.

    Parameters
    ----------
    day_of_week : int
        Day of week number (0-6), where 0 is Monday and 6 is Sunday.

    Returns
    -------
    str
        Name of day of week.
    """
    if day_of_week < 0 or day_of_week > 6:
        raise ValueError("Day of week must be between 0 and 6.")

    day_of_week_name = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ][day_of_week]

    return day_of_week_name


def third_day_of_week_in_month(day_of_week: int, month: int, year: int) -> date:
    """
    Return the third given day of the week in the given month and year.

    Parameters
    ----------
    day_of_week : int
        the day of the week, must be an integer between 0 (Monday) and 6 (Sunday).
    year : int
        the year, must be an integer
    month : int
        the month of the year, must be an integer between (inclusive) 1 and 12

    Returns
    -------
    datetime.date
        the datetime.date representing the third Friday in the given month.
    """
    # The third given day in a month cannot be earlier than the 15th.
    third = date(year, month, 15)

    # Get day of week.
    w = third.weekday()

    # Adjust if necessary.
    if w != day_of_week:
        # Replace just the day of the month, adding a number of days, so that the day of the week is correct.
        third = third.replace(day=(15 + (day_of_week - w) % 7))
    return third


def last_day_in_month(month: int, year: int) -> date:
    """
    Return the last day in the given month and year.

    Parameters
    ----------
    month : int
        the month of the year, must be an integer between (inclusive) 1 and 12
    year : int
        the year, must be an integer

    Returns
    -------
    datetime.date
        the datetime.date representing the last day in the given month.
    """
    return (date(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )
