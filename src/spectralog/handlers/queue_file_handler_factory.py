from __future__ import annotations

import copy
import logging
from logging import LogRecord
from logging.handlers import QueueHandler
from multiprocessing.queues import Queue


class ExceptionPreservingQueueHandler(QueueHandler):
    """Queue handler that keeps exception text separate from the log message.

    The standard :meth:`logging.handlers.QueueHandler.prepare` formats the record
    before enqueueing it, which appends any traceback to ``msg`` and clears the
    exception fields. Downstream formatters, such as SpectraLog's JSON formatter,
    then cannot report the exception as its own field.

    This handler merges only the interpolation arguments into ``msg`` and stores
    the rendered traceback in ``exc_text``. ``exc_info`` is cleared because
    traceback objects cannot be pickled across process boundaries."""

    _exception_formatter = logging.Formatter()

    def prepare(
        self,
        record: LogRecord,
    ) -> LogRecord:
        """Prepare a picklable copy of ``record`` with its exception text preserved.

        Args:
            record:
                Log record accepted by the handler.

        Returns:
            LogRecord:
                A shallow copy of ``record`` whose message is fully interpolated,
                whose ``exc_text`` holds the rendered traceback when present, and
                whose ``exc_info`` and ``args`` are cleared for safe transport."""
        prepared_record = copy.copy(
            record,
        )

        prepared_record.msg = record.getMessage()
        prepared_record.message = prepared_record.msg
        prepared_record.args = None

        if record.exc_info and not record.exc_text:
            prepared_record.exc_text = self._exception_formatter.formatException(
                record.exc_info,
            )

        prepared_record.exc_info = None

        return prepared_record


class QueueFileHandlerFactory:
    """Create queue handlers for SpectraLog multiprocessing file logging.

    ``QueueFileHandlerFactory`` constructs the queue handler used by SpectraLog's
    multiprocessing-safe logging pipeline.

    The queue handler does not write log records to a file directly. Instead, it
    places eligible records onto the supplied multiprocessing queue so that a
    separate :class:`logging.handlers.QueueListener` can forward them to the
    configured file handler.

    This separation allows application logging calls to avoid performing the file
    write directly while preserving the downstream file handler's formatting,
    rotation, and filtering behavior.

    An :class:`ExceptionPreservingQueueHandler` is used so that exception details
    reach downstream formatters separately from the log message.

    The factory configures the queue handler with the supplied logging threshold
    before returning it."""

    def create(
        self,
        log_record_queue: Queue[LogRecord],
        log_level: int,
    ) -> QueueHandler:
        """Create and configure a queue handler for log-record transport.

        Constructs an :class:`ExceptionPreservingQueueHandler` backed by the
        supplied multiprocessing queue and configures it with the requested logging
        level.

        Records accepted by this handler are placed onto ``log_record_queue`` for
        later processing by SpectraLog's queue listener and downstream file handler.

        Args:
            log_record_queue:
                Multiprocessing queue used to transport log records from the
                application logger to the queue listener.

            log_level:
                Minimum integer logging severity accepted by the queue handler.

        Returns:
            QueueHandler:
                A configured queue handler ready to be attached to the application
                logger."""
        queue_handler = ExceptionPreservingQueueHandler(
            log_record_queue,
        )

        queue_handler.setLevel(
            log_level,
        )

        configured_queue_handler = queue_handler

        return configured_queue_handler
