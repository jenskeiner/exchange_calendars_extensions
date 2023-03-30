# conftest.py
import multiprocessing
import pytest


def run_test_in_separate_process(test_function):
    def wrapper(*args, **kwargs):
        with multiprocessing.Pool(1) as pool:
            result = pool.apply(test_function, args, kwargs)
        return result

    return wrapper


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "isolated: mark test to run in a separate process"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    if "isolated" in pyfuncitem.keywords:
        original_func = pyfuncitem.obj
        pyfuncitem.obj = run_test_in_separate_process(original_func)

    outcome = yield
