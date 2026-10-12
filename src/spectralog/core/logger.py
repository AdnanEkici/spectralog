from __future__ import annotations

import atexit
import json
import os
import sys
from collections.abc import Callable
from logging import LogRecord
from multiprocessing.queues import Queue
from pathlib import Path
from threading import Lock
from types import FrameType
from typing import Any

from spectralog.configuration.configuration import LoggerConfiguration
from spectralog.core.factory import ApplicationLoggerBuilderFactory
from spectralog.core.log_routing import SPECTRALOG_CONSOLE_ATTRIBUTE
from spectralog.core.log_routing import SPECTRALOG_FILE_ATTRIBUTE
from spectralog.core.models import LoggerBuildResult
from spectralog.core.protocols import LoggerBuilder
from spectralog.exceptions.exceptions import SpectraApplicationLoggerAlreadyInitializedError
from spectralog.exceptions.exceptions import SpectraApplicationLoggerNotInitializedError
from spectralog.exceptions.exceptions import SpectraApplicationLoggerReconfigurationError
from spectralog.levels.log_level_registry import LogLevelRegistry
from spectralog.runtime.multiprocessing_logging_runtime import (
    MultiprocessingLoggingRuntime,
)

_SPECTRALOG_PACKAGE_DIRECTORY = Path(__file__).resolve().parents[1]

SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE = "SPECTRALOG_CUSTOM_LOG_LEVELS"


class ApplicationLogger:
    """Provide the process-local SpectraLog application logger.

    ``ApplicationLogger`` is the central logging facade exposed by SpectraLog. It
    wraps a configured :class:`logging.Logger`, provides the standard logging
    methods, supports dynamically registered custom log levels, manages the
    optional multiprocessing logging runtime, and enforces process-local singleton
    semantics.

    Instances must not be constructed directly. Applications should initialize
    SpectraLog through :func:`CreateSpectraLogger` or retrieve the current logger
    through :func:`get_logger`.

    The singleton is protected by an internal lock so that initialization remains
    safe when multiple threads attempt to obtain the application logger
    concurrently.

    When the configured logger uses multiprocessing-safe file logging, the
    associated runtime is started automatically during initialization and stopped
    when :meth:`shutdown` is called. ``shutdown`` is also registered with
    :mod:`atexit` so that queued log records can be flushed during normal
    interpreter termination.

    Custom log levels registered through :meth:`add_log_level` become available as
    dynamic methods. For example, registering a ``NOTICE`` level allows
    ``logger.notice("message")`` to be used in the same manner as the built-in
    logging methods. Registered levels are also recorded in the environment so
    that child processes started afterwards can re-register them.
    """

    _instance: ApplicationLogger | None = None
    _instance_lock = Lock()
    _construction_token = object()

    def __init__(
        self,
        logger_builder: LoggerBuilder,
        log_level_registry: LogLevelRegistry,
        construction_token: object,
    ) -> None:
        """Initialize the application logger from a prepared logger builder.

        Construction is restricted to the internal singleton initialization path. A
        private construction token is required to prevent callers from bypassing
        :meth:`get_instance` and creating independent ``ApplicationLogger`` objects.

        The supplied builder creates the underlying :class:`logging.Logger` and
        returns its associated file and multiprocessing runtime metadata. If a
        multiprocessing logging runtime is present, it is started immediately.

        The logger's :meth:`shutdown` method is registered with :mod:`atexit`, and a
        warning is emitted when the builder reports that a new or empty log file has
        been created.

        Args:
            logger_builder:
                Builder responsible for constructing the underlying configured
                :class:`logging.Logger` and its associated runtime metadata.

            log_level_registry:
                Registry containing the standard and custom log levels known to this
                application logger.

            construction_token:
                Internal token used to verify that construction was initiated through
                SpectraLog's singleton lifecycle.

        Raises:
            SpectraApplicationLoggerAlreadyInitializedError:
                If construction is attempted directly without SpectraLog's internal
                construction token.
        """
        if construction_token is not self._construction_token:
            raise SpectraApplicationLoggerAlreadyInitializedError(
                "ApplicationLogger cannot be instantiated directly; " "use CreateSpectraLogger or get_logger.",
            )

        self._log_level_registry = log_level_registry

        self._multiprocessing_logging_runtime: (MultiprocessingLoggingRuntime | None) = None

        self._is_shutdown = False

        logger_build_result = logger_builder.build(
            self.__class__.__name__,
        )

        self._logger = logger_build_result.logger

        self._multiprocessing_logging_runtime = logger_build_result.multiprocessing_logging_runtime

        self._start_multiprocessing_runtime()

        atexit.register(
            self.shutdown,
        )

        self._handle_new_log_file(
            logger_build_result,
        )

    @classmethod
    def get_instance(
        cls,
        logger_builder: LoggerBuilder | None = None,
        log_level_registry: LogLevelRegistry | None = None,
    ) -> ApplicationLogger:
        """Return or explicitly initialize the process-local application logger singleton.

        If the application logger has not yet been initialized, configuration
        dependencies must be supplied. Calling this method without initialization
        dependencies before the singleton exists raises
        :class:`SpectraApplicationLoggerNotInitializedError`.

        Once initialized, calling this method without configuration arguments returns
        the existing process-local singleton.

        Supplying a logger builder or log-level registry after initialization is
        treated as an attempt to reconfigure the singleton and raises
        :class:`SpectraApplicationLoggerReconfigurationError`.

        Singleton access and initialization are protected by an internal lock so that
        multiple threads cannot independently create competing application logger
        instances.

        Args:
            logger_builder:
                Optional builder used to construct the underlying logger during initial
                configuration.

            log_level_registry:
                Optional registry containing the log levels available to the application
                logger during initial configuration.

        Raises:
            SpectraApplicationLoggerNotInitializedError:
                If the application logger has not been initialized and no initialization
                dependencies are supplied.

            SpectraApplicationLoggerReconfigurationError:
                If initialization dependencies are supplied after the singleton has
                already been initialized.

        Returns:
            ApplicationLogger:
                The process-local application logger singleton.
        """
        with cls._instance_lock:
            if cls._instance is None:
                if logger_builder is None and log_level_registry is None:
                    raise SpectraApplicationLoggerNotInitializedError(
                        "Application logger has not been initialized. " "Call CreateSpectraLogger() before get_logger().",
                    )

                resolved_log_level_registry = log_level_registry if log_level_registry is not None else LogLevelRegistry()

                resolved_logger_builder = (
                    logger_builder
                    if logger_builder is not None
                    else cls._create_default_logger_builder(
                        resolved_log_level_registry,
                    )
                )

                cls._instance = cls(
                    logger_builder=resolved_logger_builder,
                    log_level_registry=resolved_log_level_registry,
                    construction_token=cls._construction_token,
                )

            elif logger_builder is not None or log_level_registry is not None:
                raise SpectraApplicationLoggerReconfigurationError(
                    "Application logger has already been initialized " "and cannot be reconfigured.",
                )

            application_logger = cls._instance

        return application_logger

    @classmethod
    def _create_default_logger_builder(
        cls,
        log_level_registry: LogLevelRegistry,
    ) -> LoggerBuilder:
        """Create a logger builder using SpectraLog's default configuration.

        Constructs a default :class:`LoggerConfiguration`, creates an
        :class:`ApplicationLoggerBuilderFactory` using the supplied log-level
        registry, and returns the fully composed logger builder produced by that
        factory.

        This method is used when :meth:`get_instance` initializes SpectraLog before
        the application has explicitly supplied a logger configuration.

        Args:
            log_level_registry:
                Registry that should be shared with the default logger builder and the
                resulting :class:`ApplicationLogger`.

        Returns:
            LoggerBuilder:
                A fully composed logger builder configured with SpectraLog's default
                logger settings."""
        configuration = LoggerConfiguration()

        logger_builder_factory = ApplicationLoggerBuilderFactory(
            log_level_registry=log_level_registry,
        )

        logger_builder = logger_builder_factory.create(
            configuration=configuration,
        )

        created_logger_builder = logger_builder

        return created_logger_builder

    def __getattr__(
        self,
        attribute_name: str,
    ) -> Callable[..., None]:
        """Resolve a registered custom log level as a callable logging method.

        This method is invoked by Python when normal attribute lookup fails. The
        requested attribute name is normalized to uppercase and resolved through the
        application's :class:`~spectralog.levels.log_level_registry.LogLevelRegistry`.

        Names beginning with an underscore are never treated as log levels and raise
        :class:`AttributeError` immediately. This prevents infinite recursion when
        the instance is not fully initialized, for example while :mod:`copy` or
        :mod:`pickle` probe for special methods.

        When the requested name matches a registered custom log level, SpectraLog
        returns a dynamically created logging method that emits records using the
        severity associated with that level.

        The generated method supports the same deferred message interpolation pattern
        as Python's standard logging API. It also supports per-record destination
        routing through the ``console`` and ``file`` keyword-only arguments.

        By default, custom-level records are eligible for both console and file
        output. Either destination can be disabled independently for a particular
        record.

        Args:
            attribute_name:
                Attribute name requested from the application logger. Custom level
                lookup is case-insensitive because the name is normalized to
                uppercase before registry lookup.

        Raises:
            AttributeError:
                If ``attribute_name`` begins with an underscore or does not
                correspond to a registered SpectraLog log level.

        Returns:
            Callable[..., None]:
                A dynamically generated logging method associated with the registered
                custom level.

        Example:
            Register a custom ``NOTICE`` level::

                logger.add_log_level(
                    name="NOTICE",
                    color="purple",
                    severity=35,
                )

            Emit the custom level to all configured destinations::

                logger.notice(
                    "Deployment completed",
                )

            Emit the custom level only to console handlers::

                logger.notice(
                    "Interactive status message",
                    console=True,
                    file=False,
                )

            Emit the custom level only to file handlers::

                logger.notice(
                    "Persistent audit message",
                    console=False,
                    file=True,
                )
        """
        if attribute_name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute " f"'{attribute_name}'.",
            )

        normalized_level_name = attribute_name.upper()

        if not self._log_level_registry.contains(
            normalized_level_name,
        ):
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute " f"'{attribute_name}'.",
            )

        log_level = self._log_level_registry.get(
            normalized_level_name,
        )

        def dynamic_log_method(
            message: str,
            *arguments: object,
            console: bool = True,
            file: bool = True,
            **keyword_arguments: Any,
        ) -> None:
            """Emit a record using the dynamically resolved custom log level.

            The message is forwarded to :meth:`logging.Logger.log` using the
            severity registered for the custom level.

            ``console`` and ``file`` control whether the resulting
            :class:`logging.LogRecord` is accepted by SpectraLog's console and file
            routing filters. These options affect only the current record and do not
            modify the global logger configuration.

            Args:
                message:
                    Log message or formatting template.

                *arguments:
                    Optional positional values used by Python logging for deferred
                    message interpolation.

                console:
                    Whether the record should be eligible for output through
                    SpectraLog console handlers. Defaults to ``True``.

                file:
                    Whether the record should be eligible for output through
                    SpectraLog file handlers. Defaults to ``True``.

                **keyword_arguments:
                    Additional keyword arguments forwarded to
                    :meth:`logging.Logger.log`, such as ``exc_info``, ``extra``, or
                    ``stacklevel``.

                    When ``stacklevel`` is omitted, SpectraLog supplies its default
                    value. Any caller-provided ``extra`` mapping is preserved and
                    augmented with SpectraLog's routing metadata.
            """
            resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
                keyword_arguments,
                console=console,
                file=file,
            )

            self._logger.log(
                log_level.severity,
                message,
                *arguments,
                **resolved_keyword_arguments,
            )

        resolved_log_method = dynamic_log_method

        return resolved_log_method

    @property
    def multiprocessing_log_record_queue(self) -> Queue[LogRecord] | None:
        """Return the multiprocessing queue owned by this logger's runtime, if any.

        The queue is available only when the logger was built with
        ``multiprocessing_safe=True`` and file logging enabled in the parent process.
        It can be handed to worker processes so that their records are written by
        this process's listener instead of by separate file handlers.

        Returns:
            Queue[LogRecord] | None:
                The runtime's multiprocessing queue, or ``None`` when no
                multiprocessing logging runtime is configured."""
        multiprocessing_logging_runtime = self._multiprocessing_logging_runtime

        if multiprocessing_logging_runtime is None:
            return None

        log_record_queue = multiprocessing_logging_runtime.log_record_queue

        return log_record_queue

    def add_log_level(
        self,
        name: str,
        color: str,
        severity: int,
    ) -> None:
        """Register a custom application log level.

        The supplied definition is added to the application's
        :class:`~spectralog.levels.log_level_registry.LogLevelRegistry`. After
        registration, the level can be emitted either through :meth:`log` or through
        a dynamically resolved method whose name corresponds to the registered level.

        Dynamic method lookup is case-insensitive. For example, registering
        ``NOTICE`` makes ``logger.notice(...)`` available.

        Level names that collide with an existing ``ApplicationLogger`` attribute,
        such as ``SHUTDOWN`` or ``LOG``, are rejected. Normal attribute lookup takes
        precedence over dynamic level resolution, so such a level could never be
        emitted through its dynamic method.

        Compatible console formatter color mappings are refreshed immediately after
        registration so the newly registered color can be used without rebuilding the
        application logger.

        The level is also recorded in the ``SPECTRALOG_CUSTOM_LOG_LEVELS``
        environment variable. Child processes started after this call inherit it,
        and :func:`get_logger` re-registers the level when it rebuilds the logger in
        such a child.

        Destination routing is intentionally not part of the custom-level definition.
        Routing is selected independently for each emitted record using the
        ``console`` and ``file`` arguments supported by SpectraLog logging methods.

        Args:
            name:
                Name assigned to the custom log level. The name is registered in the
                application's log-level registry and is used for dynamic method
                resolution.

            color:
                Color name or formatter-compatible color specification associated
                with the custom level.

            severity:
                Integer severity assigned to the custom level. This value is passed to
                Python's logging machinery when records for the level are emitted.

        Raises:
            ValueError:
                If the lowercased ``name`` matches an existing ``ApplicationLogger``
                attribute.

        Example:
            Register a custom level::

                logger.add_log_level(
                    name="NOTICE",
                    color="purple",
                    severity=35,
                )

            Emit normally to all configured destinations::

                logger.notice(
                    "Application entered maintenance mode",
                )

            Emit only to the console::

                logger.notice(
                    "Temporary operator message",
                    console=True,
                    file=False,
                )

            Emit only to the log file::

                logger.notice(
                    "Persistent maintenance record",
                    console=False,
                    file=True,
                )
        """
        method_name = name.lower()

        if hasattr(
            type(self),
            method_name,
        ):
            raise ValueError(
                f"Log level name '{name}' conflicts with the existing " f"'{type(self).__name__}.{method_name}' attribute.",
            )

        self._log_level_registry.register(
            name=name,
            color=color,
            severity=severity,
        )

        self._refresh_console_colors()

        self._remember_custom_log_level_for_child_processes(
            name=name,
            color=color,
            severity=severity,
        )

    @staticmethod
    def _remember_custom_log_level_for_child_processes(
        name: str,
        color: str,
        severity: int,
    ) -> None:
        """Record a custom log level in the environment so child processes can re-register it.

        Levels are stored as a JSON list in ``SPECTRALOG_CUSTOM_LOG_LEVELS``. An
        existing entry with the same name is replaced, so registering the same level
        again does not duplicate it.

        Args:
            name:
                Name of the registered custom log level.

            color:
                Color associated with the custom log level.

            severity:
                Integer severity of the custom log level."""
        stored_levels = load_custom_log_levels_from_environment()

        remembered_levels = [stored_level for stored_level in stored_levels if stored_level["name"].upper() != name.upper()]

        remembered_levels.append(
            {
                "name": name,
                "color": color,
                "severity": severity,
            },
        )

        os.environ[SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE] = json.dumps(
            remembered_levels,
        )

    def log(
        self,
        level: str | int,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit a log record using a level name or numeric severity.

        ``level`` may be either an integer severity or the name of a level registered
        in the application's
        :class:`~spectralog.levels.log_level_registry.LogLevelRegistry`. This allows
        standard and custom SpectraLog levels to use the same generic logging API.

        Per-record destination routing is controlled through the ``console`` and
        ``file`` keyword-only arguments. Both destinations are enabled by default,
        preserving the behavior of logging calls that do not specify routing.

        Routing controls whether compatible SpectraLog handlers accept the record. It
        does not add or remove handlers and does not modify the logger's persistent
        configuration.

        Args:
            level:
                Registered log-level name or integer logging severity.

            message:
                Log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the record should be eligible for output through console
                handlers. Defaults to ``True``.

            file:
                Whether the record should be eligible for output through file
                handlers. Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.log`.

                Caller-supplied ``extra`` values are preserved and augmented with
                SpectraLog routing metadata. When ``stacklevel`` is omitted,
                SpectraLog supplies its default value.

        Returns:
            None:
                The method emits the record and does not return a value.

        Example:
            Emit a custom level to both destinations::

                logger.log(
                    "NOTICE",
                    "Deployment completed",
                )

            Emit only to console handlers::

                logger.log(
                    "NOTICE",
                    "Interactive notification",
                    file=False,
                )

            Emit only to file handlers::

                logger.log(
                    "NOTICE",
                    "Persistent notification",
                    console=False,
                )
        """
        severity = self._resolve_severity(
            level,
        )

        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.log(
            severity,
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def debug(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit a DEBUG-level log record.

        The message and optional interpolation arguments are forwarded to the
        underlying :class:`logging.Logger`.

        SpectraLog adds destination-routing metadata to the generated record so
        console and file output can be controlled independently for this individual
        logging call.

        If ``stacklevel`` is not explicitly supplied, SpectraLog provides its default
        value so source attribution generally points to the application call site
        rather than the SpectraLog wrapper.

        Args:
            message:
                DEBUG-level log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the record should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the record should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.debug`.

        Example:
            Emit to all configured destinations::

                logger.debug(
                    "Resolved configuration",
                )

            Emit only to the console::

                logger.debug(
                    "Temporary diagnostic information",
                    file=False,
                )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.debug(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def info(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit an INFO-level log record.

        The record is forwarded to the underlying :class:`logging.Logger` with
        SpectraLog destination-routing metadata attached.

        By default, INFO records remain eligible for both console and file output.
        Either destination may be disabled for the individual logging operation by
        setting ``console`` or ``file`` to ``False``.

        Args:
            message:
                INFO-level log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the record should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the record should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.info`. SpectraLog preserves caller-supplied
                logging options and adds a default ``stacklevel`` when necessary.

        Example:
            Emit normally::

                logger.info(
                    "Application started",
                )

            Emit only to the console::

                logger.info(
                    "Interactive status update",
                    file=False,
                )

            Emit only to the log file::

                logger.info(
                    "Persistent status update",
                    console=False,
                )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.info(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def warning(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit a WARNING-level log record.

        The warning is forwarded to the underlying :class:`logging.Logger` while
        preserving Python logging interpolation and keyword argument behavior.

        SpectraLog also attaches per-record destination metadata so console and file
        handlers can independently decide whether to emit the warning.

        Args:
            message:
                WARNING-level log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the warning should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the warning should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.warning`.

        Example:
            Emit a warning only to the console::

                logger.warning(
                    "Configuration uses a deprecated option",
                    file=False,
                )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.warning(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def error(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit an ERROR-level log record.

        The message and optional interpolation arguments are forwarded to the
        underlying :class:`logging.Logger`.

        Destination routing may be controlled independently for each record through
        the ``console`` and ``file`` keyword-only arguments. Both destinations are
        enabled by default.

        SpectraLog automatically supplies its default ``stacklevel`` unless the
        caller explicitly provides one.

        Args:
            message:
                ERROR-level log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the error record should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the error record should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.error`.

        Example:
            Emit an error normally::

                logger.error(
                    "Connection failed",
                )

            Persist the error without displaying it on the console::

                logger.error(
                    "Background connection failure",
                    console=False,
                    file=True,
                )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.error(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def critical(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit a CRITICAL-level log record.

        CRITICAL records are forwarded to the underlying
        :class:`logging.Logger` with SpectraLog's per-record routing metadata.

        Unless explicitly overridden, the record is eligible for both console and
        file output.

        Args:
            message:
                CRITICAL-level log message or formatting template.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the record should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the record should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.critical`.

        Example:
            Emit only to persistent file logging::

                logger.critical(
                    "Database integrity check failed",
                    console=False,
                )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.critical(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def exception(
        self,
        message: str,
        *arguments: object,
        console: bool = True,
        file: bool = True,
        **keyword_arguments: Any,
    ) -> None:
        """Emit an ERROR-level log record containing exception information.

        This method delegates to :meth:`logging.Logger.exception` and is intended for
        use while handling an active exception. Python logging includes information
        about the active exception by default.

        SpectraLog attaches destination-routing metadata to the generated record,
        allowing traceback output to be routed independently to console and file
        handlers.

        The ``console`` and ``file`` options affect only the current exception record
        and do not modify the logger's persistent handler configuration.

        Args:
            message:
                Log message or formatting template describing the exception.

            *arguments:
                Optional positional values used for deferred message interpolation.

            console:
                Whether the exception record should be eligible for console output.
                Defaults to ``True``.

            file:
                Whether the exception record should be eligible for file output.
                Defaults to ``True``.

            **keyword_arguments:
                Additional keyword arguments forwarded to
                :meth:`logging.Logger.exception`.

                ``exc_info`` may be supplied explicitly when custom exception
                information is required. SpectraLog also supplies its default
                ``stacklevel`` when the caller does not provide one.

        Example:
            Emit an exception to all destinations::

                try:
                    perform_operation()
                except RuntimeError:
                    logger.exception(
                        "Operation failed",
                    )

            Persist an exception without printing the traceback to the console::

                try:
                    perform_background_operation()
                except RuntimeError:
                    logger.exception(
                        "Background operation failed",
                        console=False,
                        file=True,
                    )
        """
        resolved_keyword_arguments = self._prepare_routing_keyword_arguments(
            keyword_arguments,
            console=console,
            file=file,
        )

        self._logger.exception(
            message,
            *arguments,
            **resolved_keyword_arguments,
        )

    def shutdown(self) -> None:
        """Shut down resources owned by the application logger.

        Stops the multiprocessing logging runtime when one is configured, allowing
        queued records to be processed and the runtime's resources to be released.

        Shutdown is idempotent. Subsequent calls after the first successful shutdown
        return immediately without attempting to stop the runtime again.

        This method is automatically registered with :mod:`atexit` during logger
        construction, but it may also be called explicitly when deterministic logging
        cleanup is required."""
        if self._is_shutdown:
            return

        multiprocessing_logging_runtime = self._multiprocessing_logging_runtime

        if multiprocessing_logging_runtime is not None:
            multiprocessing_logging_runtime.stop()

        self._is_shutdown = True

    def _resolve_severity(
        self,
        level: str | int,
    ) -> int:
        """Resolve a log-level identifier to its integer severity.

        Integer levels are returned unchanged. String level names are resolved through
        the application's :class:`LogLevelRegistry`, allowing registered custom levels
        to be used alongside the standard logging levels.

        Args:
            level:
                Integer severity or registered log-level name to resolve.

        Returns:
            int:
                Integer logging severity corresponding to ``level``."""
        if isinstance(level, int):
            resolved_severity = level

            return resolved_severity

        log_level = self._log_level_registry.get(
            level,
        )

        resolved_severity = log_level.severity

        return resolved_severity

    def _prepare_keyword_arguments(
        self,
        keyword_arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepare keyword arguments before forwarding a logging call.

        Creates a copy of the caller-supplied keyword argument dictionary so that the
        original mapping is not mutated.

        When ``stacklevel`` is absent, a default value of ``2`` is added. This adjusts
        source attribution so that pathname and line-number information generally
        refer to the application call site rather than SpectraLog's wrapper method.

        An explicitly supplied ``stacklevel`` is preserved unchanged.

        Args:
            keyword_arguments:
                Keyword arguments supplied to a SpectraLog logging method.

        Returns:
            dict[str, Any]:
                A copied keyword argument dictionary containing the caller's values
                and the default ``stacklevel`` when necessary."""
        resolved_keyword_arguments = dict(
            keyword_arguments,
        )

        if "stacklevel" not in resolved_keyword_arguments:
            resolved_keyword_arguments["stacklevel"] = 2

        return resolved_keyword_arguments

    def _start_multiprocessing_runtime(
        self,
    ) -> None:
        """Start the configured multiprocessing logging runtime when present.

        If the logger build result supplied a
        :class:`MultiprocessingLoggingRuntime`, its ``start`` method is invoked.
        When multiprocessing-safe logging is not configured, this method performs no
        operation."""
        multiprocessing_logging_runtime = self._multiprocessing_logging_runtime

        if multiprocessing_logging_runtime is not None:
            multiprocessing_logging_runtime.start()

    def _handle_new_log_file(
        self,
        logger_build_result: LoggerBuildResult,
    ) -> None:
        """Emit a warning when the logger build created a new or empty log file.

        The build result is inspected to determine whether file logging produced a new
        or empty log file. When both the new-file flag and resolved file path are
        present, a warning is emitted containing the resulting file name.

        The warning is attributed to the first call site outside the SpectraLog
        package, typically the application's ``CreateSpectraLogger`` call, rather than
        to SpectraLog's internal construction code.

        Args:
            logger_build_result:
                Result returned by the logger builder containing the resolved log file
                path and the flag indicating whether the file is new or empty."""
        if logger_build_result.is_new_log_file and logger_build_result.log_file_path is not None:
            log_file_name = logger_build_result.log_file_path.name

            self.warning(
                f"New log file created: {log_file_name}",
                stacklevel=self._resolve_external_stacklevel(),
            )

    @staticmethod
    def _resolve_external_stacklevel() -> int:
        """Return the ``stacklevel`` that attributes a record to the first non-SpectraLog caller.

        The count is relative to a :meth:`warning` call made from
        :meth:`_handle_new_log_file`: level ``2`` is ``_handle_new_log_file`` itself,
        and each further frame inside the SpectraLog package adds one.

        Returns:
            int:
                Stack level pointing at the first frame whose source file lies outside
                the SpectraLog package. Falls back to the outermost frame reached."""
        frame: FrameType | None = sys._getframe(1)
        stacklevel = 2

        while frame is not None:
            frame_path = Path(frame.f_code.co_filename).resolve()

            if not frame_path.is_relative_to(_SPECTRALOG_PACKAGE_DIRECTORY):
                return stacklevel

            frame = frame.f_back
            stacklevel += 1

        resolved_stacklevel = stacklevel - 1

        return resolved_stacklevel

    def _refresh_console_colors(
        self,
    ) -> None:
        """Refresh compatible handler formatter colors from the log-level registry.

        Retrieves the current color mapping from the application's
        :class:`LogLevelRegistry` and inspects each formatter attached to the
        underlying logger's handlers.

        Formatters exposing a dictionary-valued ``log_colors`` attribute are updated
        in place with the current registry colors. Formatters without a formatter,
        without ``log_colors``, or with a non-dictionary ``log_colors`` value are
        ignored.

        This allows newly registered custom log levels to become available to
        compatible colored console formatters without rebuilding the logger or its
        handlers."""
        current_colors = self._log_level_registry.colors

        for handler in self._logger.handlers:
            formatter = handler.formatter

            if formatter is None:
                continue

            log_colors = getattr(
                formatter,
                "log_colors",
                None,
            )

            if isinstance(
                log_colors,
                dict,
            ):
                log_colors.update(
                    current_colors,
                )

    def _prepare_routing_keyword_arguments(
        self,
        keyword_arguments: dict[str, Any],
        *,
        console: bool,
        file: bool,
    ) -> dict[str, Any]:
        """Prepare logging keyword arguments with destination-routing metadata.

        Creates a copy of the caller-supplied logging keyword arguments and augments
        the ``extra`` mapping with SpectraLog-specific routing attributes.

        These attributes become members of the resulting
        :class:`logging.LogRecord`. SpectraLog routing filters attached to console and
        file handlers inspect the values to determine whether the corresponding
        handler should emit the record.

        Caller-supplied ``extra`` values are preserved. SpectraLog's reserved routing
        keys are then written into that copied mapping so the explicit ``console`` and
        ``file`` arguments supplied to the logging method remain authoritative.

        After routing metadata has been added, the arguments are passed through
        :meth:`_prepare_keyword_arguments` so SpectraLog's normal keyword processing,
        including default ``stacklevel`` handling, remains consistent.

        Args:
            keyword_arguments:
                Keyword arguments supplied to a SpectraLog logging method. The
                original dictionary is not modified.

            console:
                Whether console handlers should be permitted to emit the resulting
                record.

            file:
                Whether file handlers should be permitted to emit the resulting
                record.

        Returns:
            dict[str, Any]:
                A new keyword-argument dictionary containing the caller's original
                values, SpectraLog routing metadata in ``extra``, and any standard
                SpectraLog logging defaults.

        Note:
            The keys identified by
            :data:`~spectralog.core.log_routing.SPECTRALOG_CONSOLE_ATTRIBUTE` and
            :data:`~spectralog.core.log_routing.SPECTRALOG_FILE_ATTRIBUTE` are
            reserved for SpectraLog routing.

            If the caller supplies those same keys in ``extra``, their values are
            replaced by the explicit ``console`` and ``file`` arguments passed to the
            logging method.
        """
        resolved_keyword_arguments = dict(
            keyword_arguments,
        )

        supplied_extra = resolved_keyword_arguments.get(
            "extra",
        )

        if supplied_extra is None:
            resolved_extra: dict[str, object] = {}
        else:
            resolved_extra = dict(
                supplied_extra,
            )

        resolved_extra[SPECTRALOG_CONSOLE_ATTRIBUTE] = console
        resolved_extra[SPECTRALOG_FILE_ATTRIBUTE] = file

        resolved_keyword_arguments["extra"] = resolved_extra

        prepared_keyword_arguments = self._prepare_keyword_arguments(
            resolved_keyword_arguments,
        )

        return prepared_keyword_arguments


def load_custom_log_levels_from_environment() -> list[dict[str, Any]]:
    """Return the custom log levels stored in the environment by this or a parent process.

    Returns:
        list[dict[str, Any]]:
            Stored level definitions with ``name``, ``color`` and ``severity`` keys.
            An empty list is returned when nothing is stored or the stored value is
            invalid."""
    serialized_levels = os.environ.get(
        SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE,
    )

    if not serialized_levels:
        return []

    try:
        stored_levels = json.loads(
            serialized_levels,
        )
    except ValueError:
        return []

    if not isinstance(
        stored_levels,
        list,
    ):
        return []

    valid_levels = [
        stored_level
        for stored_level in stored_levels
        if isinstance(stored_level, dict)
        and isinstance(stored_level.get("name"), str)
        and isinstance(stored_level.get("color"), str)
        and isinstance(stored_level.get("severity"), int)
    ]

    return valid_levels
