from exchange_calendars import register_calendar_type
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar

from .holiday_calendar import extend_class, ExtendedExchangeCalendar

_extensions = {
    "XLON": extend_class(XLONExchangeCalendar, day_of_week_expiry=4),
}


def apply_extensions():
    """Apply extensions to exchange_calendars."""
    for k, v in _extensions.items():
        register_calendar_type(k, v, force=True)


def register_extension(name, cls):
    """Set an extension for a given exchange calendar."""
    _extensions[name] = cls


__all__ = ["apply_extensions", "register_extension", "extend_class", "ExtendedExchangeCalendar"]

__version__ = None

try:
    from importlib.metadata import version
    # get version from installed package
    __version__ = version("exchange_calendars_extensions")
except ImportError:
    pass

if __version__ is None:
    try:
        # if package not installed, get version as set when package built
        from ._version import version
    except Exception:
        # If package not installed and not built, leave __version__ as None
        pass
    else:
        __version__ = version

del version
