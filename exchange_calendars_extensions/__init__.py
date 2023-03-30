import datetime

import pandas as pd
from exchange_calendars import register_calendar_type
from exchange_calendars.exchange_calendar_asex import ASEXExchangeCalendar
from exchange_calendars.exchange_calendar_xams import XAMSExchangeCalendar
from exchange_calendars.exchange_calendar_xbru import XBRUExchangeCalendar
from exchange_calendars.exchange_calendar_xbud import XBUDExchangeCalendar
from exchange_calendars.exchange_calendar_xcse import XCSEExchangeCalendar
from exchange_calendars.exchange_calendar_xdub import XDUBExchangeCalendar
from exchange_calendars.exchange_calendar_xetr import XETRExchangeCalendar
from exchange_calendars.exchange_calendar_xist import XISTExchangeCalendar
from exchange_calendars.exchange_calendar_xjse import XJSEExchangeCalendar
from exchange_calendars.exchange_calendar_xlis import XLISExchangeCalendar
from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar
from exchange_calendars.exchange_calendar_xmil import XMILExchangeCalendar
from exchange_calendars.exchange_calendar_xnys import XNYSExchangeCalendar
from exchange_calendars.exchange_calendar_xosl import XOSLExchangeCalendar
from exchange_calendars.exchange_calendar_xpar import XPARExchangeCalendar
from exchange_calendars.exchange_calendar_xpra import XPRAExchangeCalendar
from exchange_calendars.exchange_calendar_xsto import XSTOExchangeCalendar
from exchange_calendars.exchange_calendar_xswx import XSWXExchangeCalendar
from exchange_calendars.exchange_calendar_xtae import XTAEExchangeCalendar
from exchange_calendars.exchange_calendar_xtse import XTSEExchangeCalendar
from exchange_calendars.exchange_calendar_xwar import XWARExchangeCalendar
from exchange_calendars.exchange_calendar_xwbo import XWBOExchangeCalendar

from .changeset import ExchangeCalendarChangeSet
from .holiday_calendar import extend_class, ExtendedExchangeCalendar


# TODO: Add the following exchanges:
# class BMEXExchangeCalendar:
#     pass
#
#
# class XHELEXchangeCalendar:
#     pass
#
#
# class XNASExchangeCalendar:
#     pass


_changesets = dict()

_extensions = {
    "ASEX": extend_class(ASEXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("ASEX")),
    #"BMEX": extend_class(BMEXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("BMEX")),
    "XAMS": extend_class(XAMSExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XAMS")),
    "XBRU": extend_class(XBRUExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XBRU")),
    "XBUD": extend_class(XBUDExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XBUD")),
    "XCSE": extend_class(XCSEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XCSE")),
    "XDUB": extend_class(XDUBExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XDUB")),
    "XETR": extend_class(XETRExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XETR")),
    #"XHEL": extend_class(XHELEXchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XHEL")),
    "XIST": extend_class(XISTExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XIST")),
    "XJSE": extend_class(XJSEExchangeCalendar, day_of_week_expiry=3, changeset_provider=lambda: _changesets.get("XJSE")),
    "XLIS": extend_class(XLISExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XLIS")),
    "XLON": extend_class(XLONExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XLON")),
    "XMIL": extend_class(XMILExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XMIL")),
    #"XNAS": extend_class(XNASExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XNAS")),
    "XNYS": extend_class(XNYSExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XNYS")),
    "XOSL": extend_class(XOSLExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XOSL")),
    "XPAR": extend_class(XPARExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XPAR")),
    "XPRA": extend_class(XPRAExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XPRA")),
    "XSTO": extend_class(XSTOExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XSTO")),
    "XSWX": extend_class(XSWXExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XSWX")),
    "XTAE": extend_class(XTAEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XTAE")),
    "XTSE": extend_class(XTSEExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XTSE")),
    "XWAR": extend_class(XWARExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XWAR")),
    "XWBO": extend_class(XWBOExchangeCalendar, day_of_week_expiry=4, changeset_provider=lambda: _changesets.get("XWBO")),
}


def apply_extensions():
    """Apply extensions to exchange_calendars."""
    for k, v in _extensions.items():
        register_calendar_type(k, v, force=True)


def register_extension(name, cls):
    """Set an extension for a given exchange calendar."""
    _extensions[name] = cls


def add_holiday(exchange: str, date: pd.Timestamp, name: str = "Holiday"):
    """Add a holiday to an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.holidays_add.add((date, name))
    _changesets[exchange] = cs


def remove_holiday(exchange: str, date: pd.Timestamp):
    """Remove a holiday from an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.holidays_remove.add(date)
    _changesets[exchange] = cs


def add_special_close(exchange: str, date: pd.Timestamp, t: datetime.time, name: str = "Special Close"):
    """Add a special close to an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.special_closes_add.add((date, t, name))
    _changesets[exchange] = cs


def remove_special_close(exchange: str, date: pd.Timestamp):
    """Remove a special close from an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.special_closes_remove.add(date)
    _changesets[exchange] = cs


def add_special_open(exchange: str, date: pd.Timestamp, t: datetime.time, name: str = "Special Open"):
    """Add a special open to an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.special_opens_add.add((date, t, name))
    _changesets[exchange] = cs


def remove_special_open(exchange: str, date: pd.Timestamp):
    """Remove a special close from an exchange calendar."""
    cs = _changesets.get(exchange, ExchangeCalendarChangeSet())
    cs.special_opens_remove.add(date)
    _changesets[exchange] = cs


__all__ = ["apply_extensions", "register_extension", "extend_class", "add_holiday", "remove_holiday",
           "add_special_close", "remove_special_close", "add_special_open", "remove_special_open",
           "ExtendedExchangeCalendar"]

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
