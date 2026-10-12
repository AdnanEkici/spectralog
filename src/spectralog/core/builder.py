from __future__ import annotations

import logging
from logging import LogRecord
from multiprocessing.queues import Queue

from spectralog.configuration.configuration import LoggerConfiguration
from spectralog.core.models import LoggerBuildResult
from spectralog.core.protocols import ConsoleHandlerFactoryProtocol
from spectralog.core.protocols import FileHandlerFactoryProtocol
from spectralog.core.protocols import LogFilePathResolverProtocol
from spectralog.core.protocols import MultiprocessingHandlerFactoryProtocol
from spectralog.core.protocols import RichConsoleHandlerFactoryProtocol
from spectralog.core.protocols import SyslogHandlerFactoryProtocol
from spectralog.handlers.queue_file_handler_factory import QueueFileHandlerFactory


class ApplicationLoggerBuilder:
    """Build and configure the standard-library logger used by SpectraLog.

    ``ApplicationLoggerBuilder`` is responsible for orchestrating construction of
    the underlying :class:`logging.Logger` used by :class:`ApplicationLogger`.

    The builder applies the active :class:`LoggerConfiguration`, resets any
    existing handlers on the target logger, configures the effective logging
    level, and attaches the appropriate console, file, multiprocessing, and syslog
    handlers.

    Handler construction is delegated to injected factories rather than performed
    directly by the builder. This keeps the class focused on composition and
    lifecycle orchestration while allowing individual handler implementations to
    remain independently configurable and testable.

    Console output is always configured. When Rich console configuration is
    present, the Rich handler factory is used; otherwise the standard console
    handler factory is selected.

    When persistent logging is enabled, the log file path is resolved before file
    output is configured. Depending on the ``multiprocessing_safe`` setting,
    records are written either through a direct file handler or through
    SpectraLog's multiprocessing logging runtime.

    When a ``worker_log_record_queue`` is supplied, the builder is operating in a
    worker process. File output is then routed to that queue, which is owned by the
    parent process's multiprocessing logging runtime, and no log file is opened or
    resolved in the worker.

    When syslog configuration is present, a syslog handler is attached in addition
    to the configured console and file-related handlers.

    Before applying a new configuration, all handlers currently attached to the
    named logger are removed and closed. Logger propagation is disabled after
    configuration to prevent duplicate records from being processed by ancestor
    loggers.

    The :meth:`build` method returns a :class:`LoggerBuildResult` containing the
    configured logger together with metadata required by
    :class:`ApplicationLogger`, including the resolved log file path, whether the
    log file is new or empty, and the optional multiprocessing logging runtime."""

    def __init__(
        self,
        configuration: LoggerConfiguration,
        console_handler_factory: ConsoleHandlerFactoryProtocol,
        rich_console_handler_factory: RichConsoleHandlerFactoryProtocol,
        file_handler_factory: FileHandlerFactoryProtocol,
        multiprocessing_handler_factory: MultiprocessingHandlerFactoryProtocol,
        syslog_handler_factory: SyslogHandlerFactoryProtocol,
        log_file_path_resolver: LogFilePathResolverProtocol,
        queue_file_handler_factory: QueueFileHandlerFactory | None = None,
        worker_log_record_queue: Queue[LogRecord] | None = None,
    ) -> None:
        """Initialize an application logger builder with its configuration and factories.

        The builder coordinates the components required to construct a fully
        configured :class:`logging.Logger`. Handler creation, file-path resolution,
        multiprocessing setup, and syslog setup are delegated to injected
        collaborators so that the builder remains responsible only for orchestration.

        Args:
            configuration:
                The :class:`LoggerConfiguration` that defines the logger level,
                output destinations, formatting-related options, file persistence,
                multiprocessing behavior, and optional Rich or syslog integration.

            console_handler_factory:
                Factory used to create the standard console handler when Rich console
                output is not configured.

            rich_console_handler_factory:
                Factory used to create the Rich console handler when
                ``configuration.rich_console_configuration`` is provided.

            file_handler_factory:
                Factory used to create the direct file handler when file logging is
                enabled and multiprocessing-safe logging is disabled.

            multiprocessing_handler_factory:
                Factory used to create the multiprocessing logging runtime when file
                logging is enabled together with ``multiprocessing_safe=True``.

            syslog_handler_factory:
                Factory used to create the syslog handler when a
                :class:`SyslogConfiguration` is present.

            log_file_path_resolver:
                Resolver used to determine the effective log file path when
                persistent file logging is enabled.

            queue_file_handler_factory:
                Factory used to create the queue handler that forwards worker records
                to the parent's queue. Required when ``worker_log_record_queue`` is
                supplied.

            worker_log_record_queue:
                Parent-owned multiprocessing queue. When supplied, file output is
                routed to this queue instead of a local file handler or runtime.

        Raises:
            ValueError:
                If ``worker_log_record_queue`` is supplied without a
                ``queue_file_handler_factory``."""
        if worker_log_record_queue is not None and queue_file_handler_factory is None:
            raise ValueError(
                "A queue_file_handler_factory is required when a worker_log_record_queue is supplied.",
            )

        self._configuration = configuration
        self._console_handler_factory = console_handler_factory
        self._rich_console_handler_factory = rich_console_handler_factory
        self._file_handler_factory = file_handler_factory
        self._multiprocessing_handler_factory = multiprocessing_handler_factory
        self._syslog_handler_factory = syslog_handler_factory
        self._log_file_path_resolver = log_file_path_resolver
        self._queue_file_handler_factory = queue_file_handler_factory
        self._worker_log_record_queue = worker_log_record_queue

    def build(
        self,
        name: str,
    ) -> LoggerBuildResult:
        """Build and configure the named standard-library logger.

        Retrieves the logger identified by ``name`` from Python's logging registry,
        removes and closes any handlers already attached to it, applies the configured
        logging level, and attaches the handlers required by the active
        :class:`LoggerConfiguration`.

        A Rich console handler is selected when Rich configuration is present;
        otherwise the standard console handler is used.

        When file logging is enabled in a worker process, file records are forwarded
        to the parent's queue and no log file is resolved or inspected. Otherwise the
        effective log path is resolved and inspected to determine whether it
        represents a new or empty log file, and file output is configured either
        through a direct file handler or through SpectraLog's multiprocessing logging
        runtime, depending on the ``multiprocessing_safe`` setting.

        If syslog configuration is present, a syslog handler is attached in addition
        to the console and file-related handlers.

        Logger propagation is disabled before the completed build result is returned,
        preventing records from being emitted again by ancestor loggers.

        Args:
            name:
                Name of the standard-library logger to retrieve and configure. The
                name is passed directly to :func:`logging.getLogger`.

        Returns:
            LoggerBuildResult:
                The completed logger build result containing the configured
                :class:`logging.Logger`, the resolved log file path when file logging
                is enabled outside a worker, whether that file is new or empty, and
                the optional multiprocessing logging runtime.

        Note:
            Building a logger is destructive with respect to handlers already attached
            to the same named logger. Existing handlers are removed and closed before
            the new SpectraLog configuration is applied."""
        logger = logging.getLogger(
            name,
        )

        self._reset_logger(
            logger,
        )

        logger.setLevel(
            self._configuration.log_level,
        )

        rich_console_configuration = self._configuration.rich_console_configuration

        if rich_console_configuration is not None:
            console_handler = self._rich_console_handler_factory.create(
                logger_configuration=self._configuration,
                rich_configuration=rich_console_configuration,
            )
        else:
            console_handler = self._console_handler_factory.create(
                self._configuration,
            )

        logger.addHandler(
            console_handler,
        )

        log_file_path = None
        is_new_log_file = False
        multiprocessing_logging_runtime = None

        if self._configuration.save_logs:
            if self._worker_log_record_queue is not None and self._queue_file_handler_factory is not None:
                worker_queue_handler = self._queue_file_handler_factory.create(
                    log_record_queue=self._worker_log_record_queue,
                    log_level=self._configuration.log_level,
                )

                logger.addHandler(
                    worker_queue_handler,
                )
            else:
                log_file_path = self._log_file_path_resolver.resolve(
                    self._configuration,
                )

                is_new_log_file = not log_file_path.exists() or log_file_path.stat().st_size == 0

                if self._configuration.multiprocessing_safe:
                    multiprocessing_logging_runtime = self._multiprocessing_handler_factory.create(
                        configuration=self._configuration,
                        log_file_path=log_file_path,
                    )

                    logger.addHandler(
                        multiprocessing_logging_runtime.queue_handler,
                    )
                else:
                    file_handler = self._file_handler_factory.create(
                        configuration=self._configuration,
                        log_file_path=log_file_path,
                    )

                    logger.addHandler(
                        file_handler,
                    )

        syslog_configuration = self._configuration.syslog_configuration

        if syslog_configuration is not None:
            syslog_handler = self._syslog_handler_factory.create(
                logger_configuration=self._configuration,
                syslog_configuration=syslog_configuration,
            )

            logger.addHandler(
                syslog_handler,
            )

        logger.propagate = False

        logger_build_result = LoggerBuildResult(
            logger=logger,
            log_file_path=log_file_path,
            is_new_log_file=is_new_log_file,
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        return logger_build_result

    def _reset_logger(
        self,
        logger: logging.Logger,
    ) -> None:
        """Remove and close all handlers currently attached to a logger.

        A snapshot of the logger's handler collection is created before mutation so
        that handlers can be safely removed while iterating. Each existing handler is
        detached from the logger and then closed to release any resources it owns,
        such as open file descriptors or network connections.

        This method is used before applying a new SpectraLog configuration to avoid
        duplicate output and stale handler state.

        Args:
            logger:
                The :class:`logging.Logger` whose currently attached handlers should
                be removed and closed."""
        existing_handlers = list(
            logger.handlers,
        )

        for existing_handler in existing_handlers:
            logger.removeHandler(
                existing_handler,
            )

            existing_handler.close()
