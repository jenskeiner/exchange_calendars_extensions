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

from .holiday_calendar import extend_class, ExtendedExchangeCalendar


class BMEXExchangeCalendar:
    pass


class XHELEXchangeCalendar:
    pass


class XNASExchangeCalendar:
    pass


_extensions = {
    "ASEX": extend_class(ASEXExchangeCalendar, day_of_week_expiry=4),
    "BMEX": extend_class(BMEXExchangeCalendar, day_of_week_expiry=4),
    "XAMS": extend_class(XAMSExchangeCalendar, day_of_week_expiry=4),
    "XBRU": extend_class(XBRUExchangeCalendar, day_of_week_expiry=4),
    "XBUD": extend_class(XBUDExchangeCalendar, day_of_week_expiry=4),
    "XCSE": extend_class(XCSEExchangeCalendar, day_of_week_expiry=4),
    "XDUB": extend_class(XDUBExchangeCalendar, day_of_week_expiry=4),
    "XETR": extend_class(XETRExchangeCalendar, day_of_week_expiry=4),
    "XHEL": extend_class(XHELEXchangeCalendar, day_of_week_expiry=4),
    "XIST": extend_class(XISTExchangeCalendar, day_of_week_expiry=4),
    "XJSE": extend_class(XJSEExchangeCalendar, day_of_week_expiry=3),
    "XLIS": extend_class(XLISExchangeCalendar, day_of_week_expiry=4),
    "XLON": extend_class(XLONExchangeCalendar, day_of_week_expiry=4),
    "XMIL": extend_class(XMILExchangeCalendar, day_of_week_expiry=4),
    "XNAS": extend_class(XNASExchangeCalendar, day_of_week_expiry=4),
    "XNYS": extend_class(XNYSExchangeCalendar, day_of_week_expiry=4),
    "XOSL": extend_class(XOSLExchangeCalendar, day_of_week_expiry=4),
    "XPAR": extend_class(XPARExchangeCalendar, day_of_week_expiry=4),
    "XPRA": extend_class(XPRAExchangeCalendar, day_of_week_expiry=4),
    "XSTO": extend_class(XSTOExchangeCalendar, day_of_week_expiry=4),
    "XSWX": extend_class(XSWXExchangeCalendar, day_of_week_expiry=4),
    "XTAE": extend_class(XTAEExchangeCalendar, day_of_week_expiry=4),
    "XTSE": extend_class(XTSEExchangeCalendar, day_of_week_expiry=4),
    "XWAR": extend_class(XWARExchangeCalendar, day_of_week_expiry=4),
    "XWBO": extend_class(XWBOExchangeCalendar, day_of_week_expiry=4),
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
