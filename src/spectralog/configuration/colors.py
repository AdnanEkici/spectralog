from __future__ import annotations

from enum import Enum


class LoggerColor(str, Enum):
    """Define the supported color names for SpectraLog log levels.

    Each enumeration member maps a semantic logging level to the color name used
    by SpectraLog's colored console formatter.

    The enumeration inherits from :class:`str`, allowing its members to be used
    directly in APIs that expect string-based color values, while
    :class:`enum.Enum` provides a fixed and discoverable set of supported default
    level colors.

    Attributes:
        DEBUG:
            Cyan color used for DEBUG-level log records.
        INFO:
            Green color used for INFO-level log records.
        WARNING:
            Bold yellow color used for WARNING-level log records.
        ERROR:
            Red color used for ERROR-level log records.
        CRITICAL:
            Bold red color used for CRITICAL-level log records.

    Example:
        Access a configured color through the enumeration::

            debug_color = LoggerColor.DEBUG
            warning_color = LoggerColor.WARNING

        Because ``LoggerColor`` inherits from :class:`str`, enum members can be
        passed to APIs that accept string color names.
    """

    DEBUG = "cyan"
    INFO = "blue"
    WARNING = "yellow"
    ERROR = "red"
    CRITICAL = "bold_red"
