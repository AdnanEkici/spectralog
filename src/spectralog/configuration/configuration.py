from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from spectralog.configuration.json_logger_configuration import (
    JsonLoggerConfiguration,
)
from spectralog.configuration.rich_console_configuration import (
    RichConsoleConfiguration,
)
from spectralog.configuration.syslog_configuration import (
    SyslogConfiguration,
)


@dataclass(frozen=True, slots=True)
class LoggerConfiguration:
    """Store the complete configuration used to build a SpectraLog logger.

    This immutable configuration object defines logging behavior for console,
    file, Rich, JSON, syslog, and multiprocessing-safe logging.

    Instances are frozen and use slots, making configuration values immutable
    after construction and preventing dynamic attribute creation.

    Attributes:
        debug_mode:
            Enables DEBUG-level logging when ``True``. When ``False``, the
            effective logging level is INFO. Defaults to ``False``.

        show_datetime:
            Includes a timestamp in automatically generated plain-text log
            formats. Defaults to ``True``.

        show_line:
            Includes the source line number in automatically generated
            plain-text log formats. Defaults to ``False``.

        show_folder_name:
            Includes the source path relative to the project root in
            automatically generated plain-text log formats. Defaults to
            ``False``.

        logs_directory:
            Directory in which log files are written. Strings and
            :class:`pathlib.Path` instances are accepted. Defaults to
            ``"logs"``.

        log_file_name:
            Optional custom log file name. When omitted, SpectraLog may generate
            a file name automatically. Defaults to ``None``.

        save_logs:
            Enables persistent file logging when ``True``. Defaults to ``True``.

        multiprocessing_safe:
            Enables SpectraLog's multiprocessing queue and listener runtime for
            file logging when ``True``. Defaults to ``False``.

        syslog_configuration:
            Optional :class:`SyslogConfiguration` used to configure syslog
            output. Defaults to ``None``.

        rich_console_configuration:
            Optional :class:`RichConsoleConfiguration` used to configure Rich
            console output. Defaults to ``None``.

        json_logger_configuration:
            Optional :class:`JsonLoggerConfiguration` used to enable and
            configure JSON Lines file logging. Defaults to ``None``.

        console_format:
            Optional explicit format string for console log records. When
            supplied, it overrides the automatically generated console format.
            Defaults to ``None``.

        file_format:
            Optional explicit format string for plain-text file log records.
            When supplied, it overrides the automatically generated file format.
            Defaults to ``None``.

        date_format:
            Date and time format used by logging formatters that render
            ``%(asctime)s``. Defaults to ``"%Y-%m-%d %H:%M:%S"``.

        max_bytes:
            Maximum log file size, in bytes, before rotation occurs. Defaults to
            ``20 * (1024**2)``, or 20 MiB.

        backup_count:
            Number of rotated backup log files retained by the rotating file
            handler. Defaults to ``1``.

        level_colors:
            Optional mapping of built-in level names (DEBUG, INFO, WARNING,
            ERROR, CRITICAL) to colorlog-compatible color names. Supplied
            entries override SpectraLog's default level colors; omitted levels
            keep their defaults. Defaults to ``None``.
    """

    debug_mode: bool = False
    show_datetime: bool = True
    show_line: bool = False
    show_folder_name: bool = False
    logs_directory: str | Path = "logs"
    log_file_name: str | None = None
    save_logs: bool = True
    multiprocessing_safe: bool = False
    syslog_configuration: SyslogConfiguration | None = None
    rich_console_configuration: RichConsoleConfiguration | None = None
    json_logger_configuration: JsonLoggerConfiguration | None = None
    console_format: str | None = None
    file_format: str | None = None
    date_format: str = "%Y-%m-%d %H:%M:%S"
    max_bytes: int = 20 * (1024**2)
    backup_count: int = 1
    level_colors: dict[str, str] | None = None

    @property
    def log_level(self) -> int:
        """Return the effective standard-library logging level.

        The configured level is derived from :attr:`debug_mode`. DEBUG is returned
        when debug mode is enabled; otherwise INFO is returned.

        Returns:
            int:
                :data:`logging.DEBUG` when ``debug_mode`` is ``True``; otherwise
                :data:`logging.INFO`.
        """
        log_level = logging.DEBUG if self.debug_mode else logging.INFO

        return log_level

    @property
    def resolved_logs_directory(self) -> Path:
        """Return the normalized absolute path of the configured logs directory.

        The configured :attr:`logs_directory` value is converted to a
        :class:`pathlib.Path`, user-home markers such as ``~`` are expanded, and the
        result is resolved to an absolute path.

        This property only resolves the path. It does not create the directory.

        Returns:
            Path:
                The expanded and resolved absolute path representing the configured
                logs directory.
        """
        logs_directory = Path(
            self.logs_directory,
        ).expanduser()

        resolved_logs_directory = logs_directory.resolve()

        return resolved_logs_directory
