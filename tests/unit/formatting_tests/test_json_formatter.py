from __future__ import annotations

import json
import logging
import sys
import unittest
from datetime import datetime
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa

from spectralog.configuration.json_logger_configuration import JsonLoggerConfiguration  # noqa: E402
from spectralog.formatting.json_formatter import JsonLoggerFormatter  # noqa: E402


class UnitTestJsonLoggerFormatter(unittest.TestCase):
    def test_format_contains_level_and_message(
        self,
    ) -> None:
        """Verifies that format always includes the log level and resolved message."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["level"],
            "INFO",
            "Expected the JSON log entry to contain the INFO level name.",
        )

        self.assertEqual(
            parsed_log_entry["message"],
            "Application started",
            "Expected the JSON log entry to contain the resolved log message.",
        )

    def test_format_returns_valid_json_string(
        self,
    ) -> None:
        """Verifies that format returns a valid JSON string."""
        configuration = JsonLoggerConfiguration()

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertIsInstance(
            formatted_log_entry,
            str,
            "Expected format() to return a string.",
        )

        self.assertIsInstance(
            parsed_log_entry,
            dict,
            "Expected the formatted string to contain a valid JSON object.",
        )

    def test_format_resolves_message_arguments(
        self,
    ) -> None:
        """Verifies that format uses LogRecord.getMessage to resolve message arguments."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Processed %d images",
            args=(42,),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["message"],
            "Processed 42 images",
            "Expected format() to resolve LogRecord message arguments.",
        )

    def test_format_preserves_non_ascii_characters(
        self,
    ) -> None:
        """Verifies that format preserves non-ASCII characters instead of escaping them."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        message = "Başlatıldı – 日本語"

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg=message,
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        self.assertIn(
            message,
            formatted_log_entry,
            "Expected the JSON output to preserve non-ASCII characters.",
        )

        self.assertNotIn(
            "\\u",
            formatted_log_entry,
            "Expected non-ASCII characters not to be converted to Unicode escape sequences.",
        )

    def test_format_includes_timestamp_when_enabled(
        self,
    ) -> None:
        """Verifies that format includes a UTC ISO timestamp when timestamp output is enabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=True,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        log_record.created = 1_700_000_000.0

        expected_timestamp = datetime.fromtimestamp(
            log_record.created,
            timezone.utc,
        ).isoformat()

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["timestamp"],
            expected_timestamp,
            "Expected the JSON timestamp to use the LogRecord creation time in UTC ISO format.",
        )

    def test_format_excludes_timestamp_when_disabled(
        self,
    ) -> None:
        """Verifies that format excludes the timestamp field when timestamp output is disabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertNotIn(
            "timestamp",
            parsed_log_entry,
            "Expected the timestamp field to be omitted when disabled.",
        )

    def test_format_includes_logger_name_when_enabled(
        self,
    ) -> None:
        """Verifies that format includes the logger name when logger name output is enabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=True,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog.application",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["logger"],
            "spectralog.application",
            "Expected the JSON log entry to contain the LogRecord logger name.",
        )

    def test_format_excludes_logger_name_when_disabled(
        self,
    ) -> None:
        """Verifies that format excludes the logger field when logger name output is disabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog.application",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertNotIn(
            "logger",
            parsed_log_entry,
            "Expected the logger field to be omitted when disabled.",
        )

    def test_format_includes_process_information_when_enabled(
        self,
    ) -> None:
        """Verifies that format includes process identifier and process name when process information is enabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=True,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        log_record.process = 12345
        log_record.processName = "WorkerProcess"

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["process_id"],
            12345,
            "Expected the JSON log entry to contain the LogRecord process identifier.",
        )

        self.assertEqual(
            parsed_log_entry["process_name"],
            "WorkerProcess",
            "Expected the JSON log entry to contain the LogRecord process name.",
        )

    def test_format_excludes_process_information_when_disabled(
        self,
    ) -> None:
        """Verifies that format excludes process fields when process information is disabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertNotIn(
            "process_id",
            parsed_log_entry,
            "Expected process_id to be omitted when process information is disabled.",
        )

        self.assertNotIn(
            "process_name",
            parsed_log_entry,
            "Expected process_name to be omitted when process information is disabled.",
        )

    def test_format_includes_thread_information_when_enabled(
        self,
    ) -> None:
        """Verifies that format includes thread identifier and thread name when thread information is enabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=True,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        log_record.thread = 67890
        log_record.threadName = "WorkerThread"

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["thread_id"],
            67890,
            "Expected the JSON log entry to contain the LogRecord thread identifier.",
        )

        self.assertEqual(
            parsed_log_entry["thread_name"],
            "WorkerThread",
            "Expected the JSON log entry to contain the LogRecord thread name.",
        )

    def test_format_excludes_thread_information_when_disabled(
        self,
    ) -> None:
        """Verifies that format excludes thread fields when thread information is disabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertNotIn(
            "thread_id",
            parsed_log_entry,
            "Expected thread_id to be omitted when thread information is disabled.",
        )

        self.assertNotIn(
            "thread_name",
            parsed_log_entry,
            "Expected thread_name to be omitted when thread information is disabled.",
        )

    def test_format_includes_all_optional_fields_with_default_configuration(
        self,
    ) -> None:
        """Verifies that the default JSON logger configuration includes all optional metadata fields."""
        configuration = JsonLoggerConfiguration()

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.WARNING,
            pathname=__file__,
            lineno=100,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        expected_fields = {
            "level",
            "message",
            "timestamp",
            "logger",
            "process_id",
            "process_name",
            "thread_id",
            "thread_name",
        }

        self.assertEqual(
            set(parsed_log_entry),
            expected_fields,
            "Expected the default JSON logger configuration to include all configured metadata fields.",
        )

    def test_format_contains_only_required_fields_when_all_optional_fields_are_disabled(
        self,
    ) -> None:
        """Verifies that only level and message remain when every optional JSON field is disabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=100,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry,
            {
                "level": "ERROR",
                "message": "Error message",
            },
            "Expected only level and message when all optional JSON metadata is disabled.",
        )

    def test_format_includes_exception_when_exception_information_is_present(
        self,
    ) -> None:
        """Verifies that format includes formatted exception information when the LogRecord contains exc_info."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        try:
            raise ValueError(
                "Invalid configuration",
            )
        except ValueError:
            exception_information = sys.exc_info()

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=100,
            msg="Operation failed",
            args=(),
            exc_info=exception_information,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertIn(
            "exception",
            parsed_log_entry,
            "Expected the JSON log entry to contain exception information.",
        )

        self.assertIn(
            "ValueError",
            parsed_log_entry["exception"],
            "Expected the formatted exception to contain the exception type.",
        )

        self.assertIn(
            "Invalid configuration",
            parsed_log_entry["exception"],
            "Expected the formatted exception to contain the exception message.",
        )

    def test_format_excludes_exception_when_exception_information_is_absent(
        self,
    ) -> None:
        """Verifies that format excludes the exception field when the LogRecord has no exception information."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertNotIn(
            "exception",
            parsed_log_entry,
            "Expected the exception field to be omitted when exc_info is absent.",
        )

    @patch(
        "spectralog.formatting.json_formatter.datetime",
    )
    def test_create_log_data_builds_timestamp_from_record_created_value(
        self,
        datetime_mock,
    ) -> None:
        """Verifies that timestamp generation uses the LogRecord creation time and UTC timezone."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=True,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        log_record.created = 1_700_000_000.0

        timestamp_mock = datetime_mock.fromtimestamp.return_value
        timestamp_mock.isoformat.return_value = "2023-11-14T22:13:20+00:00"

        log_data = formatter._create_log_data(
            record=log_record,
        )

        datetime_mock.fromtimestamp.assert_called_once_with(
            log_record.created,
            timezone.utc,
        )

        timestamp_mock.isoformat.assert_called_once_with()

        self.assertEqual(
            log_data["timestamp"],
            "2023-11-14T22:13:20+00:00",
            "Expected _create_log_data() to store the ISO-formatted timestamp.",
        )

    @patch(
        "spectralog.formatting.json_formatter.json.dumps",
    )
    def test_format_serializes_log_data_with_expected_json_options(
        self,
        json_dumps_mock,
    ) -> None:
        """Verifies that format serializes the generated log data with Unicode preservation and string fallback enabled."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        json_dumps_mock.return_value = '{"level": "INFO"}'

        formatted_log_entry = formatter.format(
            log_record,
        )

        expected_log_data = {
            "level": "INFO",
            "message": "Application started",
        }

        json_dumps_mock.assert_called_once_with(
            expected_log_data,
            ensure_ascii=False,
            default=str,
        )

        self.assertEqual(
            formatted_log_entry,
            '{"level": "INFO"}',
            "Expected format() to return the exact string produced by json.dumps().",
        )

    def test_create_log_data_returns_dictionary(
        self,
    ) -> None:
        """Verifies that _create_log_data returns a dictionary representation of the LogRecord."""
        configuration = JsonLoggerConfiguration()

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="Application started",
            args=(),
            exc_info=None,
        )

        log_data = formatter._create_log_data(
            record=log_record,
        )

        self.assertIsInstance(
            log_data,
            dict,
            "Expected _create_log_data() to return a dictionary.",
        )

    def test_format_supports_custom_log_level_name(
        self,
    ) -> None:
        """Verifies that format preserves a custom LogRecord level name in the JSON output."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=25,
            pathname=__file__,
            lineno=100,
            msg="Operation succeeded",
            args=(),
            exc_info=None,
        )

        log_record.levelname = "SUCCESS"

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["level"],
            "SUCCESS",
            "Expected the JSON formatter to preserve custom log level names.",
        )

    def test_format_handles_empty_message(
        self,
    ) -> None:
        """Verifies that format correctly serializes an empty log message."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg="",
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["message"],
            "",
            "Expected an empty log message to remain empty in the JSON output.",
        )

    def test_format_handles_none_message(
        self,
    ) -> None:
        """Verifies that format delegates None message conversion to LogRecord.getMessage."""
        configuration = JsonLoggerConfiguration(
            include_timestamp=False,
            include_logger_name=False,
            include_process_information=False,
            include_thread_information=False,
        )

        formatter = JsonLoggerFormatter(
            configuration=configuration,
        )

        log_record = logging.LogRecord(
            name="spectralog-test",
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg=None,
            args=(),
            exc_info=None,
        )

        formatted_log_entry = formatter.format(
            log_record,
        )

        parsed_log_entry = json.loads(
            formatted_log_entry,
        )

        self.assertEqual(
            parsed_log_entry["message"],
            "None",
            "Expected LogRecord.getMessage() to convert a None message to its string representation.",
        )


    def test_create_log_data_uses_exc_text_when_exc_info_is_missing(
        self,
    ) -> None:
        """Verifies that pre-rendered exception text is reported when exc_info is unavailable."""
        json_logger_formatter = JsonLoggerFormatter(
            JsonLoggerConfiguration(),
        )

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Request failed",
            args=None,
            exc_info=None,
        )

        record.exc_text = "Traceback (most recent call last):\nValueError: boom"

        log_data = json_logger_formatter._create_log_data(
            record,
        )

        self.assertEqual(
            log_data["exception"],
            record.exc_text,
            "Expected the exception field to fall back to exc_text.",
        )

        self.assertEqual(
            log_data["message"],
            "Request failed",
            "Expected the message field to exclude the exception text.",
        )