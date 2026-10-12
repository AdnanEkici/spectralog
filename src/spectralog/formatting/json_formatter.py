from __future__ import annotations

import json
import logging
from datetime import datetime
from datetime import timezone
from typing import Any

from spectralog.configuration.json_logger_configuration import (
    JsonLoggerConfiguration,
)


class JsonLoggerFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    ``JsonLoggerFormatter`` converts :class:`logging.LogRecord` instances into
    structured JSON suitable for JSON Lines log files.

    Every formatted record contains the log level and rendered message. Additional
    metadata such as timestamps, logger names, process information, and thread
    information is included according to the active
    :class:`JsonLoggerConfiguration`.

    Exception information is included automatically when the log record contains
    ``exc_info``, or ``exc_text`` for records that crossed a process boundary
    through SpectraLog's multiprocessing queue.

    The formatter serializes each record with :func:`json.dumps` using
    ``ensure_ascii=False`` so that Unicode characters are preserved. Values that
    are not directly JSON serializable are converted through ``str``.

    Each call to :meth:`format` returns one JSON object as a string, making the
    formatter suitable for line-oriented ``.jsonl`` log files."""

    def __init__(
        self,
        configuration: JsonLoggerConfiguration,
    ) -> None:
        """Initialize the JSON formatter with its metadata configuration.

        Args:
            configuration:
                Configuration controlling which optional metadata fields are included
                in each JSON log record."""
        super().__init__()
        self._configuration = configuration

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        """Format a log record as a JSON string.

        The supplied :class:`logging.LogRecord` is first converted into a structured
        dictionary by :meth:`_create_log_data`. The resulting mapping is then
        serialized with :func:`json.dumps`.

        Unicode characters are preserved because ``ensure_ascii`` is disabled, and
        values that are not directly JSON serializable are converted using ``str``.

        Args:
            record:
                Log record to serialize.

        Returns:
            str:
                A single JSON object representing the supplied log record."""
        log_data = self._create_log_data(
            record,
        )

        json_log_entry = json.dumps(
            log_data,
            ensure_ascii=False,
            default=str,
        )

        formatted_log_entry = json_log_entry

        return formatted_log_entry

    def _create_log_data(
        self,
        record: logging.LogRecord,
    ) -> dict[str, Any]:
        """Create the structured data representation of a log record.

        The resulting dictionary always contains ``level`` and ``message``.

        Optional metadata is included according to the active
        :class:`JsonLoggerConfiguration`:

        - ``timestamp`` contains the record creation time as an ISO 8601 UTC
          timestamp.
        - ``logger`` contains the originating logger name.
        - ``process_id`` and ``process_name`` contain process metadata.
        - ``thread_id`` and ``thread_name`` contain thread metadata.

        When the record contains exception information, an ``exception`` field is
        added. It contains the traceback text produced by
        :meth:`logging.Formatter.formatException` from ``exc_info``, or the
        pre-rendered ``exc_text`` when ``exc_info`` is no longer available.

        Args:
            record:
                Log record from which structured logging data should be extracted.

        Returns:
            dict[str, Any]:
                Dictionary containing the mandatory and configured optional fields for
                the JSON log entry."""
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if self._configuration.include_timestamp:
            timestamp = datetime.fromtimestamp(
                record.created,
                timezone.utc,
            )

            log_data["timestamp"] = timestamp.isoformat()

        if self._configuration.include_logger_name:
            log_data["logger"] = record.name

        if self._configuration.include_process_information:
            log_data["process_id"] = record.process
            log_data["process_name"] = record.processName

        if self._configuration.include_thread_information:
            log_data["thread_id"] = record.thread
            log_data["thread_name"] = record.threadName

        if record.exc_info is not None:
            exception_text = self.formatException(
                record.exc_info,
            )

            log_data["exception"] = exception_text

        elif record.exc_text:
            log_data["exception"] = record.exc_text

        created_log_data = log_data

        return created_log_data
