from datetime import date


def third_day_of_week_in_month(day_of_week: int, month: int, year: int) -> date:
    """
    Return the third given day of the week in the given month and year.

    :param day_of_week: the day of the week, must be an integer between 0 (Monday) and 6 (Sunday).
    :param year: the year, must be an integer
    :param month: the month of the year, must be an integer between (inclusive) 1 and 12
    :return: the datetime.date representing the third Friday in the given month.
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
