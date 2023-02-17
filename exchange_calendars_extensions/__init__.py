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


def set_extension(name, cls):
    """Set an extension for a given exchange calendar."""
    _extensions[name] = cls


__all__ = ["apply_extensions", "set_extension", "extend_class", "ExtendedExchangeCalendar"]
