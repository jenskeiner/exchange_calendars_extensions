# conftest.py
import multiprocessing
from collections.abc import Callable
from typing import cast
from collections.abc import Generator

import exchange_calendars as ec
import pytest

from exchange_calendars_extensions import ExtendedExchangeCalendar
from tests.synthetic_calendar import add_test_calendar


def run_test_in_separate_process(test_function: Callable) -> Callable:
    """
    Return a new function that, when called with some arguments, runs the given test function with those arguments in a
    separate process and returns the result.

    Parameters
    ----------
    test_function : Callable
        The test function to run in a separate process.

    Returns
    -------
    Callable
        A new function that, when called with some arguments, runs the given test function with those arguments in a
        separate process and returns the result.
    """

    def wrapper(*args, **kwargs):
        with multiprocessing.Pool(1) as pool:
            result = pool.apply(test_function, args, kwargs)
        return result

    return wrapper


def pytest_configure(config):
    # Add the isolated marker.
    config.addinivalue_line(
        "markers", "isolated: mark test to run in a separate interpreter process"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    # Run the test in a separate process if the isolated marker is present.
    if "isolated" in pyfuncitem.keywords:
        original_func = pyfuncitem.obj
        pyfuncitem.obj = run_test_in_separate_process(original_func)

    yield


@pytest.fixture
def test_calendar() -> Generator[ExtendedExchangeCalendar]:
    add_test_calendar()
    yield cast(ExtendedExchangeCalendar, ec.get_calendar("TEST"))
