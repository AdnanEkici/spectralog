from __future__ import annotations

import multiprocessing
from logging import LogRecord
from logging.handlers import QueueListener
from multiprocessing.queues import Queue
from pathlib import Path
from typing import cast

from spectralog.configuration.configuration import LoggerConfiguration
from spectralog.core.protocols import FileHandlerFactoryProtocol
from spectralog.handlers.queue_file_handler_factory import (
    QueueFileHandlerFactory,
)
from spectralog.runtime.multiprocessing_logging_runtime import (
    MultiprocessingLoggingRuntime,
)


class MultiprocessingHandlerFactory:
    """Create the queue-based logging infrastructure used for multiprocessing-safe file logging.

    ``MultiprocessingHandlerFactory`` assembles the components required to route
    log records through a multiprocessing queue before they are written to the
    configured file handler.

    The factory creates a process-compatible log-record queue, a queue handler
    that publishes records into that queue, a file handler that performs the
    actual persistent write, and a :class:`logging.handlers.QueueListener` that
    consumes queued records and forwards them to the file handler.

    The listener is configured with ``respect_handler_level=True`` so that the
    effective level configured on the downstream file handler remains authoritative.

    The resulting components are wrapped in a
    :class:`MultiprocessingLoggingRuntime`, which owns their lifecycle and is
    responsible for starting and stopping the listener and releasing queue-related
    resources.

    This factory creates the multiprocessing logging infrastructure but does not
    start it. Runtime startup is handled by :class:`ApplicationLogger`."""

    def __init__(
        self,
        queue_file_handler_factory: QueueFileHandlerFactory,
        file_handler_factory: FileHandlerFactoryProtocol,
    ) -> None:
        """Initialize the multiprocessing handler factory with its dependencies.

        Args:
            queue_file_handler_factory:
                Factory responsible for creating the queue handler that publishes log
                records into the multiprocessing queue.

            file_handler_factory:
                Factory responsible for creating the downstream file handler that
                receives records from the queue listener and writes them to the
                resolved log file."""
        self._queue_file_handler_factory = queue_file_handler_factory
        self._file_handler_factory = file_handler_factory

    def create(
        self,
        configuration: LoggerConfiguration,
        log_file_path: Path,
    ) -> MultiprocessingLoggingRuntime:
        """Create the multiprocessing logging runtime for a log file.

        A multiprocessing-compatible queue is created first. The configured queue
        handler factory then creates a handler that publishes log records into that
        queue using the effective logger level.

        A regular file handler is created for the supplied log file path and attached
        to a :class:`logging.handlers.QueueListener`. The listener consumes queued log
        records and forwards them to the file handler while respecting the file
        handler's configured logging level.

        The queue handler, queue listener, and multiprocessing queue are packaged into
        a :class:`MultiprocessingLoggingRuntime` and returned without being started.

        Args:
            configuration:
                Logger configuration controlling the effective log level, file
                formatting, rotation settings, and other persistent logging behavior.

            log_file_path:
                Resolved path of the log file that should receive records consumed by
                the queue listener.

        Returns:
            MultiprocessingLoggingRuntime:
                A runtime containing the queue handler, queue listener, and
                multiprocessing queue required for queue-based file logging."""
        log_record_queue = self._create_log_record_queue()

        queue_handler = self._queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=configuration.log_level,
        )

        file_handler = self._file_handler_factory.create(
            configuration=configuration,
            log_file_path=log_file_path,
        )

        queue_listener = QueueListener(
            log_record_queue,
            file_handler,
            respect_handler_level=True,
        )

        multiprocessing_logging_runtime = MultiprocessingLoggingRuntime(
            queue_handler=queue_handler,
            queue_listener=queue_listener,
            log_record_queue=log_record_queue,
        )

        created_runtime = multiprocessing_logging_runtime

        return created_runtime

    def _create_log_record_queue(
        self,
    ) -> Queue[LogRecord]:
        """Create the multiprocessing queue used to transport log records.

        The queue is always created from the ``spawn`` multiprocessing context. A
        spawn-context queue can be shared with worker processes started by any
        start method: ``fork`` children inherit it directly, while ``spawn`` and
        ``forkserver`` children receive it through pickling. A queue created from the
        ``fork`` context, the default on Linux before Python 3.14, cannot be sent to
        ``spawn`` workers and fails with a ``SemLock`` context error.

        The returned queue is used by the queue handler to publish log records and by
        the queue listener to consume them.

        Returns:
            Queue[LogRecord]:
                A multiprocessing queue suitable for transporting logging records
                between the queue handler, queue listener, and worker processes.
        """
        multiprocessing_context = multiprocessing.get_context(
            "spawn",
        )

        log_record_queue = cast(
            "Queue[LogRecord]",
            multiprocessing_context.Queue(),
        )

        created_log_record_queue = log_record_queue

        return created_log_record_queue
