from __future__ import annotations

import base64
import os
import pickle
from collections.abc import Callable
from logging import LogRecord
from multiprocessing.queues import Queue
from pathlib import Path
from typing import Any

from spectralog.configuration.configuration import LoggerConfiguration
from spectralog.configuration.json_logger_configuration import JsonLoggerConfiguration
from spectralog.configuration.rich_console_configuration import RichConsoleConfiguration
from spectralog.configuration.syslog_configuration import SyslogConfiguration
from spectralog.core.factory import ApplicationLoggerBuilderFactory
from spectralog.core.logger import ApplicationLogger
from spectralog.core.logger import load_custom_log_levels_from_environment
from spectralog.exceptions.exceptions import SpectraApplicationLoggerNotInitializedError
from spectralog.exceptions.exceptions import SpectraApplicationLoggerReconfigurationError
from spectralog.levels.log_level_registry import LogLevelRegistry

SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE = "SPECTRALOG_CONFIGURATION"


def CreateSpectraLogger(
    debug_mode: bool = False,
    show_datetime: bool = True,
    show_line: bool = False,
    show_folder_name: bool = False,
    logs_directory: str | Path = "logs",
    log_file_name: str | None = None,
    save_logs: bool = True,
    multiprocessing_safe: bool = False,
    syslog_configuration: SyslogConfiguration | None = None,
    rich_console_configuration: RichConsoleConfiguration | None = None,
    json_logger_configuration: JsonLoggerConfiguration | None = None,
    console_format: str | None = None,
    file_format: str | None = None,
    date_format: str = "%Y-%m-%d %H:%M:%S",
    max_bytes: int = 20 * (1024**2),
    backup_count: int = 1,
) -> ApplicationLogger:
    """Create and configure the process-wide SpectraLog application logger.

    This function is the primary entry point for initializing SpectraLog.
    It creates a :class:`LoggerConfiguration`, composes the required logger
    infrastructure, and initializes the process-local
    :class:`ApplicationLogger` singleton.

    The application logger should normally be initialized once near the
    application's entry point. After initialization, other modules should use
    :func:`get_logger` to retrieve the existing logger rather than calling
    ``CreateSpectraLogger`` again.

    Worker processes should be configured with :func:`get_worker_initializer`.
    With ``multiprocessing_safe=True``, workers configured this way forward their
    file records to this process's queue, so a single listener writes the log
    file.

    As a fallback for workers that cannot be given an initializer, the
    configuration is also stored in the ``SPECTRALOG_CONFIGURATION`` environment
    variable. Child processes inherit the environment, so :func:`get_logger` in
    such a child rebuilds an equivalently configured logger, including custom
    levels registered before the child was started. That fallback logger writes
    the log file through its own handlers.

    Console logging is always configured. When ``save_logs`` is enabled,
    SpectraLog additionally creates a file handler using either plain-text or
    JSON Lines formatting. Rich console output, syslog output, and
    multiprocessing-safe file logging can be enabled independently through
    their corresponding configuration options.

    When ``json_logger_configuration`` is supplied, file logging uses JSON
    Lines format and the resolved log file has a ``.jsonl`` extension.
    Otherwise, standard text formatting is used.

    When ``rich_console_configuration`` is supplied, the Rich console handler
    is used instead of the standard colored console handler.

    Args:
        debug_mode:
            Enables debug-level logging when ``True``. The logger and its
            configured handlers use :data:`logging.DEBUG` as their minimum
            level. When ``False``, the minimum level is
            :data:`logging.INFO`. Defaults to ``False``.

        show_datetime:
            Includes the formatted timestamp in automatically generated
            plain-text console and file formats when ``True``. This option
            does not affect an explicitly supplied ``console_format`` or
            ``file_format``. Defaults to ``True``.

        show_line:
            Includes the source line number in automatically generated
            plain-text formats when ``True``. When
            ``show_folder_name`` is also enabled, the line number is appended
            to the relative source path. Otherwise, it is rendered as a
            standalone line component. Defaults to ``False``.

        show_folder_name:
            Includes the source file path relative to the detected project
            root in automatically generated plain-text formats when ``True``.
            The relative path is populated by SpectraLog's relative-path
            logging filter. Defaults to ``False``.

        logs_directory:
            Directory in which log files are created. A string or
            :class:`pathlib.Path` may be supplied. The directory is expanded,
            resolved, and created when file logging is enabled. Defaults to
            ``"logs"``.

        log_file_name:
            Optional custom log file name. When omitted, SpectraLog generates
            a daily file name from the current date. When JSON logging is
            enabled, a recognized log extension is replaced with ``.jsonl``
            and any other suffix is kept with ``.jsonl`` appended. Defaults to
            ``None``.

        save_logs:
            Enables persistent file logging when ``True``. When ``False``,
            SpectraLog does not resolve or create a log file and no file
            handler is attached. Console and optionally configured syslog
            logging remain available. Defaults to ``True``.

        multiprocessing_safe:
            Routes file log records through SpectraLog's multiprocessing
            queue and listener infrastructure when ``True``. This prevents
            the application's logger from writing directly to the file
            handler in the initializing process and ensures queued records
            are flushed during logger shutdown. Workers configured with
            :func:`get_worker_initializer` share this queue. Defaults to
            ``False``.

        syslog_configuration:
            Optional :class:`SyslogConfiguration` describing the remote
            syslog host, port, facility, and socket type. When supplied, a
            syslog handler is attached in addition to the configured console
            and file handlers. Defaults to ``None``.

        rich_console_configuration:
            Optional :class:`RichConsoleConfiguration` controlling Rich
            console rendering. When supplied, SpectraLog uses a Rich console
            handler instead of its standard colored console handler. Defaults
            to ``None``.

        json_logger_configuration:
            Optional :class:`JsonLoggerConfiguration` controlling structured
            file logging. When supplied, file records are serialized as
            JSON Lines and the log file uses the ``.jsonl`` extension.
            Defaults to ``None``.

        console_format:
            Optional explicit format string for the standard colored console
            formatter. When supplied, it overrides the console format that
            would otherwise be generated from ``show_datetime``,
            ``show_line``, and ``show_folder_name``. Defaults to ``None``.

            This setting applies to the standard console formatter and is not
            used to format Rich console output.

        file_format:
            Optional explicit format string for plain-text file logging.
            When supplied, it overrides the automatically generated file
            format. JSON logging uses its JSON formatter instead of this
            format string. Defaults to ``None``.

        date_format:
            Date and time format passed to logging formatters that render an
            ``%(asctime)s`` value. Defaults to
            ``"%Y-%m-%d %H:%M:%S"``.

        max_bytes:
            Maximum size, in bytes, of a plain or JSON log file before the
            rotating file handler performs a rollover. Defaults to
            ``20 * (1024**2)``, or 20 MiB.

        backup_count:
            Number of rotated backup log files retained by the rotating file
            handler. Defaults to ``1``.

    Returns:
        ApplicationLogger:
            The initialized process-local SpectraLog application logger.
            Subsequent calls to :func:`get_logger` return this same
            :class:`ApplicationLogger` instance.

    Raises:
        SpectraApplicationLoggerReconfigurationError:
            If ``CreateSpectraLogger`` is called after the application logger
            has already been initialized. SpectraLog does not permit the
            existing process-local singleton to be reconfigured.

    Example:
        Initialize SpectraLog once at the application entry point::

            from spectralog import CreateSpectraLogger

            logger = CreateSpectraLogger(
                debug_mode=True,
                logs_directory="logs",
                log_file_name="application.log",
            )

            logger.info("Application started")

        Retrieve the same logger elsewhere in the application with
        :func:`get_logger` rather than initializing it again.
    """
    configuration = LoggerConfiguration(
        debug_mode=debug_mode,
        show_datetime=show_datetime,
        show_line=show_line,
        show_folder_name=show_folder_name,
        logs_directory=logs_directory,
        log_file_name=log_file_name,
        save_logs=save_logs,
        multiprocessing_safe=multiprocessing_safe,
        syslog_configuration=syslog_configuration,
        rich_console_configuration=rich_console_configuration,
        json_logger_configuration=json_logger_configuration,
        console_format=console_format,
        file_format=file_format,
        date_format=date_format,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    application_logger = _create_application_logger(
        configuration,
    )

    _store_configuration_for_child_processes(
        configuration,
    )

    return application_logger


def get_logger() -> ApplicationLogger:
    """Return the process-local SpectraLog application logger.

    Returns the existing :class:`ApplicationLogger` singleton when SpectraLog has
    already been initialized, either by :func:`CreateSpectraLogger` or by the
    worker initializer returned from :func:`get_worker_initializer`.

    When no logger exists in the current process but a parent process stored its
    configuration in the ``SPECTRALOG_CONFIGURATION`` environment variable, an
    equivalently configured logger is rebuilt from that configuration and the
    parent's custom log levels are registered on it.

    Raises:
        SpectraApplicationLoggerNotInitializedError:
            If SpectraLog has not been initialized in this process and no parent
            configuration is available in the environment.

    Returns:
        ApplicationLogger:
            The process-local SpectraLog application logger instance. Repeated
            calls return the same singleton instance for the lifetime of the
            process.

    Example:
        Retrieve the existing logger from another module::

            from spectralog import get_logger

            logger = get_logger()
            logger.info("Processing started")
    """
    try:
        application_logger = ApplicationLogger.get_instance()
    except SpectraApplicationLoggerNotInitializedError:
        inherited_configuration = _load_configuration_from_parent_process()

        if inherited_configuration is None:
            raise

        try:
            application_logger = _create_application_logger(
                inherited_configuration,
            )
        except SpectraApplicationLoggerReconfigurationError:
            application_logger = ApplicationLogger.get_instance()
        else:
            _register_custom_log_levels(
                application_logger,
                load_custom_log_levels_from_environment(),
            )

    return application_logger


def get_worker_initializer() -> tuple[Callable[..., None], tuple[Any, ...]]:
    """Return an initializer that configures SpectraLog in worker processes.

    The returned callable and arguments are intended for
    ``multiprocessing.Pool(initializer=..., initargs=...)``, or for calling at the
    start of a :class:`multiprocessing.Process` target. Call this after
    :func:`CreateSpectraLogger` and after registering any custom log levels, and
    before starting the workers.

    When the parent logger uses ``multiprocessing_safe=True`` with file logging,
    workers forward their file records to the parent's queue, so the parent's
    listener is the only writer of the log file. Otherwise workers build an
    equivalently configured logger of their own.

    Raises:
        SpectraApplicationLoggerNotInitializedError:
            If SpectraLog has not been initialized in this process.

    Returns:
        tuple[Callable[..., None], tuple[Any, ...]]:
            :func:`initialize_spectralog_worker` and the arguments to call it with.

    Example:
        Configure pool workers::

            logger = CreateSpectraLogger(
                multiprocessing_safe=True,
                log_file_name="training.log",
            )

            initializer, initargs = get_worker_initializer()

            with multiprocessing.get_context("spawn").Pool(
                4,
                initializer=initializer,
                initargs=initargs,
            ) as pool:
                pool.map(work, items)
    """
    application_logger = ApplicationLogger.get_instance()

    configuration = _load_configuration_from_parent_process()

    if configuration is None:
        raise SpectraApplicationLoggerNotInitializedError(
            "No SpectraLog configuration is available. Call CreateSpectraLogger() before get_worker_initializer().",
        )

    worker_initializer_arguments = (
        configuration,
        application_logger.multiprocessing_log_record_queue,
        load_custom_log_levels_from_environment(),
    )

    return initialize_spectralog_worker, worker_initializer_arguments


def initialize_spectralog_worker(
    configuration: LoggerConfiguration,
    log_record_queue: Queue[LogRecord] | None,
    custom_log_levels: list[dict[str, Any]],
) -> None:
    """Configure SpectraLog in a worker process.

    This function is normally obtained through :func:`get_worker_initializer`
    rather than called with hand-built arguments.

    When ``log_record_queue`` is supplied, file records are forwarded to that
    parent-owned queue and the worker does not open the log file. Otherwise the
    worker builds a logger that writes according to ``configuration``. Custom log
    levels from the parent are registered on the worker's logger.

    If the worker already has an application logger, for example because it was
    started with the ``fork`` method and inherited the parent's logger, nothing is
    changed.

    Args:
        configuration:
            The parent's logger configuration.

        log_record_queue:
            The parent's multiprocessing log queue, or ``None`` when the parent does
            not use multiprocessing-safe file logging.

        custom_log_levels:
            Custom log level definitions with ``name``, ``color`` and ``severity``
            keys."""
    if ApplicationLogger._instance is not None:
        return

    try:
        application_logger = _create_application_logger(
            configuration,
            worker_log_record_queue=log_record_queue,
        )
    except SpectraApplicationLoggerReconfigurationError:
        return

    _register_custom_log_levels(
        application_logger,
        custom_log_levels,
    )

    _store_configuration_for_child_processes(
        configuration,
    )


def _create_application_logger(
    configuration: LoggerConfiguration,
    worker_log_record_queue: Queue[LogRecord] | None = None,
) -> ApplicationLogger:
    """Build and register the application logger singleton from a configuration.

    Args:
        configuration:
            Complete logger configuration used to compose the logger builder.

        worker_log_record_queue:
            Optional parent-owned queue. When supplied, the logger forwards file
            records to it instead of writing the log file.

    Raises:
        SpectraApplicationLoggerReconfigurationError:
            If the application logger has already been initialized.

    Returns:
        ApplicationLogger:
            The initialized process-local application logger."""
    log_level_registry = LogLevelRegistry()

    logger_builder_factory = ApplicationLoggerBuilderFactory(
        log_level_registry=log_level_registry,
    )

    logger_builder = logger_builder_factory.create(
        configuration=configuration,
        worker_log_record_queue=worker_log_record_queue,
    )

    application_logger = ApplicationLogger.get_instance(
        logger_builder=logger_builder,
        log_level_registry=log_level_registry,
    )

    return application_logger


def _register_custom_log_levels(
    application_logger: ApplicationLogger,
    custom_log_levels: list[dict[str, Any]],
) -> None:
    """Register custom log level definitions on an application logger.

    Args:
        application_logger:
            Logger on which the levels are registered.

        custom_log_levels:
            Level definitions with ``name``, ``color`` and ``severity`` keys."""
    for custom_log_level in custom_log_levels:
        application_logger.add_log_level(
            name=custom_log_level["name"],
            color=custom_log_level["color"],
            severity=custom_log_level["severity"],
        )


def _store_configuration_for_child_processes(
    configuration: LoggerConfiguration,
) -> None:
    """Store ``configuration`` in the environment so child processes can rebuild the logger.

    The configuration is pickled and base64-encoded into
    ``SPECTRALOG_CONFIGURATION``. Child processes inherit the variable at
    creation time.

    Args:
        configuration:
            Logger configuration to make available to child processes."""
    serialized_configuration = base64.b64encode(
        pickle.dumps(
            configuration,
        ),
    ).decode(
        "ascii",
    )

    os.environ[SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE] = serialized_configuration


def _load_configuration_from_parent_process() -> LoggerConfiguration | None:
    """Load a logger configuration stored in the environment, if one is available.

    Returns:
        LoggerConfiguration | None:
            The stored configuration, or ``None`` when the environment variable is
            absent or does not contain a valid ``LoggerConfiguration``."""
    serialized_configuration = os.environ.get(
        SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE,
    )

    if not serialized_configuration:
        return None

    try:
        configuration = pickle.loads(
            base64.b64decode(
                serialized_configuration,
            ),
        )
    except Exception:
        return None

    if not isinstance(
        configuration,
        LoggerConfiguration,
    ):
        return None

    loaded_configuration: LoggerConfiguration = configuration

    return loaded_configuration
