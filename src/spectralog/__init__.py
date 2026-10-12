from __future__ import annotations

from spectralog.api.colored_logger import CreateSpectraLogger
from spectralog.api.colored_logger import get_logger
from spectralog.api.colored_logger import get_worker_initializer
from spectralog.api.logging_control import disable_application_logging
from spectralog.api.logging_control import silence_application_logging
from spectralog.configuration.json_logger_configuration import JsonLoggerConfiguration
from spectralog.configuration.rich_console_configuration import RichConsoleConfiguration
from spectralog.configuration.syslog_configuration import SyslogConfiguration

__all__ = [
    "CreateSpectraLogger",
    "JsonLoggerConfiguration",
    "RichConsoleConfiguration",
    "SyslogConfiguration",
    "disable_application_logging",
    "silence_application_logging",
    "get_worker_initializer",
    "get_logger",
]
