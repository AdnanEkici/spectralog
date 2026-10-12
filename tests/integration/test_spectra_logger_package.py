from __future__ import annotations

import json
import socket

import tempfile
import unittest
from datetime import date
from pathlib import Path
from tests.support.spectra_logger_package_test_helpers import assert_consumer_succeeded
from tests.support.spectra_logger_package_test_helpers import run_consumer_script

class IntegrationTestSpectraLogPackage(unittest.TestCase):
    def test_package_can_be_imported_from_public_root(
        self,
    ) -> None:
        """Verifies that a consumer can import the supported SpectraLog API directly from the package root."""
        script = """
from spectralog import CreateSpectraLogger
from spectralog import get_logger
from spectralog import JsonLoggerConfiguration
from spectralog import RichConsoleConfiguration
from spectralog import SyslogConfiguration

print(CreateSpectraLogger.__name__)
print(get_logger.__name__)
print(JsonLoggerConfiguration.__name__)
print(RichConsoleConfiguration.__name__)
print(SyslogConfiguration.__name__)
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
        )

        self.assertIn(
            "CreateSpectraLogger",
            completed_process.stdout,
            "Expected CreateSpectraLogger to be publicly importable.",
        )

        self.assertIn(
            "get_logger",
            completed_process.stdout,
            "Expected get_logger to be publicly importable.",
        )

        self.assertIn(
            "JsonLoggerConfiguration",
            completed_process.stdout,
            "Expected JsonLoggerConfiguration to be publicly importable.",
        )

        self.assertIn(
            "RichConsoleConfiguration",
            completed_process.stdout,
            "Expected RichConsoleConfiguration to be publicly importable.",
        )

        self.assertIn(
            "SyslogConfiguration",
            completed_process.stdout,
            "Expected SyslogConfiguration to be publicly importable.",
        )

    def test_create_spectra_logger_returns_usable_logger(
        self,
    ) -> None:
        """Verifies that a consumer can create a logger and use all standard logging methods."""
        script = """
from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    save_logs=False,
)

logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
logger.critical("critical message")

print("LOGGER_USAGE_SUCCESS")
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
        )

        self.assertIn(
            "LOGGER_USAGE_SUCCESS",
            completed_process.stdout,
            "Expected the consumer to use all standard logger methods successfully.",
        )

    def test_get_logger_returns_initialized_singleton(
        self,
    ) -> None:
        """Verifies that get_logger returns the same ApplicationLogger instance created through the public factory."""
        script = """
from spectralog import CreateSpectraLogger
from spectralog import get_logger

created_logger = CreateSpectraLogger(
    save_logs=False,
)

retrieved_logger = get_logger()

print(created_logger is retrieved_logger)
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
        )

        self.assertIn(
            "True",
            completed_process.stdout,
            "Expected get_logger() to return the initialized singleton.",
        )

    def test_get_logger_raises_when_logger_is_not_initialized(
        self,
    ) -> None:
        """Verifies that get_logger rejects access before explicit logger initialization."""
        script = """
import os
os.environ.pop("SPECTRALOG_CONFIGURATION", None)
os.environ.pop("SPECTRALOG_CUSTOM_LOG_LEVELS", None)
from spectralog import get_logger
from spectralog.exceptions.exceptions import (
    SpectraApplicationLoggerNotInitializedError,
)

try:
    get_logger()
except SpectraApplicationLoggerNotInitializedError as exception:
    print(type(exception).__name__)
    print(str(exception))
else:
    raise AssertionError(
        "Expected get_logger() to raise "
        "SpectraApplicationLoggerNotInitializedError."
    )
    """

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

        self.assertIn(
            "SpectraApplicationLoggerNotInitializedError",
            completed_process.stdout,
            (
                "Expected get_logger() to raise the not-initialized "
                "SpectraLog exception."
            ),
        )

        self.assertIn(
            "Application logger has not been initialized",
            completed_process.stdout,
            (
                "Expected the exception message to explain that SpectraLog "
                "must be initialized first."
            ),
        )

    def test_second_explicit_initialization_is_rejected(
        self,
    ) -> None:
        """Verifies that a consumer cannot reconfigure the singleton through a second explicit CreateSpectraLogger call."""
        script = """
from spectralog import CreateSpectraLogger
from spectralog.exceptions.exceptions import SpectraApplicationLoggerReconfigurationError

CreateSpectraLogger(
    save_logs=False,
)

try:
    CreateSpectraLogger(
        debug_mode=True,
        save_logs=False,
    )
except SpectraApplicationLoggerReconfigurationError:
    print("RECONFIGURATION_REJECTED")
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
        )

        self.assertIn(
            "RECONFIGURATION_REJECTED",
            completed_process.stdout,
            ("Expected a second explicit logger initialization to be " "rejected."),
        )

    def test_plain_text_logging_creates_custom_log_file(
        self,
    ) -> None:
        """Verifies that ordinary package usage writes plain-text log messages to a custom file."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="application.log",
    save_logs=True,
)

logger.info("plain text integration message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
            )

            log_file_path = logs_directory / "application.log"

            self.assertTrue(
                log_file_path.exists(),
                "Expected plain-text logging to create application.log.",
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "plain text integration message",
                log_file_contents,
                "Expected the emitted INFO message to be written to the file.",
            )

    def test_default_file_name_uses_current_date(
        self,
    ) -> None:
        """Verifies that file logging without an explicit file name creates the current date log file."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    save_logs=True,
)

logger.info("daily log message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            expected_log_file_path = logs_directory / f"{date.today().isoformat()}.log"

            self.assertTrue(
                expected_log_file_path.exists(),
                ("Expected default file logging to create a file named " "using the current date."),
            )

    def test_debug_messages_are_excluded_when_debug_mode_is_disabled(
        self,
    ) -> None:
        """Verifies that DEBUG messages do not reach the file handler when debug mode is disabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=False,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="application.log",
)

logger.debug("debug message should not exist")
logger.info("info message should exist")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "application.log").read_text(
                encoding="utf-8",
            )

            self.assertNotIn(
                "debug message should not exist",
                log_file_contents,
                ("Expected DEBUG output to be filtered when debug mode " "is disabled."),
            )

            self.assertIn(
                "info message should exist",
                log_file_contents,
                "Expected INFO output to remain enabled.",
            )

    def test_debug_messages_are_written_when_debug_mode_is_enabled(
        self,
    ) -> None:
        """Verifies that DEBUG messages reach the configured file when debug mode is enabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="application.log",
)

logger.debug("debug integration message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "application.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "debug integration message",
                log_file_contents,
                "Expected DEBUG output to be written when debug mode is enabled.",
            )

    def test_file_format_can_be_customized_through_public_api(
        self,
    ) -> None:
        """Verifies that consumers can provide a custom plain-text file format."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="custom.log",
    file_format="%(levelname)s::%(message)s",
)

logger.warning("custom formatted message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "custom.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "WARNING::custom formatted message",
                log_file_contents,
                "Expected the custom file format to be applied.",
            )

    def test_json_logging_creates_json_lines_file(
        self,
    ) -> None:
        """Verifies that JSON logging creates a .jsonl file containing valid JSON records."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="application.log",
    json_logger_configuration=JsonLoggerConfiguration(),
)

logger.info("JSON integration message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            json_log_file_path = logs_directory / "application.jsonl"

            self.assertTrue(
                json_log_file_path.exists(),
                ("Expected JSON logging to replace the custom extension " "with .jsonl."),
            )

            log_lines = [
                line
                for line in json_log_file_path.read_text(
                    encoding="utf-8",
                ).splitlines()
                if line.strip()
            ]

            self.assertGreaterEqual(
                len(log_lines),
                1,
                "Expected the JSON Lines file to contain at least one record.",
            )

            decoded_entries = [
                json.loads(
                    line,
                )
                for line in log_lines
            ]

            messages = [entry["message"] for entry in decoded_entries]

            self.assertIn(
                "JSON integration message",
                messages,
                "Expected the JSON logger to persist the application message.",
            )

    def test_json_configuration_controls_optional_fields(
        self,
    ) -> None:
        """Verifies that JsonLoggerConfiguration controls optional JSON fields during real package usage."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="application",
    json_logger_configuration=JsonLoggerConfiguration(
        include_timestamp=False,
        include_logger_name=False,
        include_process_information=False,
        include_thread_information=False,
    ),
)

logger.error("minimal JSON message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            json_log_file_path = logs_directory / "application.jsonl"

            decoded_entries = [
                json.loads(
                    line,
                )
                for line in json_log_file_path.read_text(
                    encoding="utf-8",
                ).splitlines()
                if line.strip()
            ]

            matching_entries = [entry for entry in decoded_entries if entry.get("message") == "minimal JSON message"]

            self.assertEqual(
                len(matching_entries),
                1,
                "Expected exactly one JSON record for the test message.",
            )

            log_entry = matching_entries[0]

            self.assertEqual(
                log_entry["level"],
                "ERROR",
                "Expected the mandatory JSON level field to remain present.",
            )

            self.assertNotIn(
                "timestamp",
                log_entry,
                "Expected timestamp to be omitted by configuration.",
            )

            self.assertNotIn(
                "logger",
                log_entry,
                "Expected logger name to be omitted by configuration.",
            )

            self.assertNotIn(
                "process_id",
                log_entry,
                "Expected process information to be omitted by configuration.",
            )

            self.assertNotIn(
                "process_name",
                log_entry,
                "Expected process information to be omitted by configuration.",
            )

            self.assertNotIn(
                "thread_id",
                log_entry,
                "Expected thread information to be omitted by configuration.",
            )

            self.assertNotIn(
                "thread_name",
                log_entry,
                "Expected thread information to be omitted by configuration.",
            )

    def test_exception_information_is_written_to_json(
        self,
    ) -> None:
        """Verifies that exception logging produces an exception field in JSON output."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="exceptions",
    json_logger_configuration=JsonLoggerConfiguration(),
)

try:
    raise ValueError("integration failure")
except ValueError:
    logger.exception("operation failed")

logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            json_log_file_path = logs_directory / "exceptions.jsonl"

            decoded_entries = [
                json.loads(
                    line,
                )
                for line in json_log_file_path.read_text(
                    encoding="utf-8",
                ).splitlines()
                if line.strip()
            ]

            matching_entries = [entry for entry in decoded_entries if entry.get("message") == "operation failed"]

            self.assertEqual(
                len(matching_entries),
                1,
                "Expected one JSON exception log entry.",
            )

            exception_entry = matching_entries[0]

            self.assertIn(
                "exception",
                exception_entry,
                "Expected JSON exception output to include exception information.",
            )

            self.assertIn(
                "ValueError: integration failure",
                exception_entry["exception"],
                "Expected the serialized traceback to contain the original exception.",
            )

    def test_custom_log_level_can_be_registered_and_called_dynamically(
        self,
    ) -> None:
        """Verifies that consumers can register and invoke a custom logging level through dynamic attribute access."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="custom-level.log",
)

logger.add_log_level(
    name="NOTICE",
    color="cyan",
    severity=35,
)

logger.notice("custom notice message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "custom-level.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "NOTICE",
                log_file_contents,
                "Expected the custom level name to appear in file output.",
            )

            self.assertIn(
                "custom notice message",
                log_file_contents,
                "Expected the dynamic custom log method to emit its message.",
            )

    def test_generic_log_method_supports_string_custom_level(
        self,
    ) -> None:
        """Verifies that the generic log method can resolve and emit a registered string level."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="generic.log",
)

logger.add_log_level(
    name="NOTICE",
    color="cyan",
    severity=35,
)

logger.log(
    "NOTICE",
    "generic custom level message",
)

logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "generic.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "generic custom level message",
                log_file_contents,
                "Expected logger.log() to resolve the registered string level.",
            )

    def test_generic_log_method_supports_integer_level(
        self,
    ) -> None:
        """Verifies that consumers can log directly with an integer severity."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="integer-level.log",
)

logger.log(
    35,
    "integer severity message",
)

logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "integer-level.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "integer severity message",
                log_file_contents,
                "Expected an integer logging severity to be accepted.",
            )

    def test_message_interpolation_matches_standard_logging_usage(
        self,
    ) -> None:
        """Verifies that positional message interpolation behaves like standard Python logging."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="interpolation.log",
)

logger.info(
    "Experiment %s completed with score %.2f",
    "ABC",
    0.95,
)

logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "interpolation.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "Experiment ABC completed with score 0.95",
                log_file_contents,
                ("Expected standard logging interpolation arguments to " "be resolved correctly."),
            )

    def test_rich_console_logging_is_usable_from_public_api(
        self,
    ) -> None:
        """Verifies that consumers can replace the standard console handler with Rich output."""
        script = """
from spectralog import CreateSpectraLogger
from spectralog import RichConsoleConfiguration

logger = CreateSpectraLogger(
    save_logs=False,
    rich_console_configuration=RichConsoleConfiguration(
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    ),
)

logger.warning("rich console integration message")
logger.shutdown()
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
        )

        combined_output = completed_process.stdout + completed_process.stderr

        self.assertIn(
            "rich console integration message",
            combined_output,
            "Expected Rich console output to contain the emitted message.",
        )

    def test_multiprocessing_safe_file_logging_flushes_on_shutdown(
        self,
    ) -> None:
        """Verifies that multiprocessing-safe logging writes queued messages before application shutdown completes."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="multiprocessing.log",
    multiprocessing_safe=True,
)

logger.info("queued integration message")
logger.warning("queued warning message")

logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
                timeout_seconds=20,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_path = logs_directory / "multiprocessing.log"

            self.assertTrue(
                log_file_path.exists(),
                ("Expected multiprocessing-safe logging to create the " "configured log file."),
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "queued integration message",
                log_file_contents,
                ("Expected the QueueListener to flush the INFO message " "before shutdown completed."),
            )

            self.assertIn(
                "queued warning message",
                log_file_contents,
                ("Expected the QueueListener to flush the WARNING " "message before shutdown completed."),
            )

    def test_repeated_shutdown_is_safe_for_multiprocessing_logging(
        self,
    ) -> None:
        """Verifies that consumers can call shutdown repeatedly without failing or stopping the runtime multiple times."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="shutdown.log",
    multiprocessing_safe=True,
)

logger.info("shutdown integration message")

logger.shutdown()
logger.shutdown()
logger.shutdown()

print("REPEATED_SHUTDOWN_SUCCESS")
"""

            completed_process = run_consumer_script(
                script=script,
                timeout_seconds=20,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            self.assertIn(
                "REPEATED_SHUTDOWN_SUCCESS",
                completed_process.stdout,
                "Expected repeated shutdown calls to complete successfully.",
            )

    def test_syslog_udp_handler_sends_message_to_real_local_socket(
        self,
    ) -> None:
        """Verifies that the public syslog configuration sends a real UDP syslog record to a local endpoint."""
        syslog_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.addCleanup(
            syslog_socket.close,
        )

        syslog_socket.bind(
            (
                "127.0.0.1",
                0,
            ),
        )

        syslog_socket.settimeout(
            5.0,
        )

        host, port = syslog_socket.getsockname()

        script = f"""
import socket

from spectralog import CreateSpectraLogger
from spectralog import SyslogConfiguration

logger = CreateSpectraLogger(
    save_logs=False,
    syslog_configuration=SyslogConfiguration(
        host={host!r},
        port={port},
        socket_type=socket.SOCK_DGRAM,
    ),
)

logger.warning("real syslog integration message")
logger.shutdown()
"""

        completed_process = run_consumer_script(
            script=script,
        )

        assert_consumer_succeeded(
        test_case=self,
        completed_process=completed_process,
        )

        received_data, sender_address = syslog_socket.recvfrom(
            65535,
        )

        decoded_message = received_data.decode(
            "utf-8",
            errors="replace",
        )

        self.assertIn(
            "real syslog integration message",
            decoded_message,
            "Expected the local UDP syslog server to receive the emitted message.",
        )

        self.assertEqual(
            sender_address[0],
            "127.0.0.1",
            "Expected the syslog datagram to originate from the local machine.",
        )

    def test_folder_and_line_information_can_be_enabled(
        self,
    ) -> None:
        """Verifies that source location information is added to file output when folder and line display are enabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="locations.log",
    show_datetime=False,
    show_folder_name=True,
    show_line=True,
)

logger.info("location integration message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            log_file_contents = (logs_directory / "locations.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "location integration message",
                log_file_contents,
                "Expected the location-aware logger to emit its message.",
            )

            self.assertIn(
                "<string>:",
                log_file_contents,
                ("Expected subprocess consumer source information to " "contain the <string> source and a line number."),
            )

    def test_unicode_messages_are_preserved_in_json_output(
        self,
    ) -> None:
        """Verifies that JSON logging preserves Unicode application messages without ASCII escaping."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="unicode",
    json_logger_configuration=JsonLoggerConfiguration(),
)

logger.info("İstanbul — 日本語 — 🚀")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
                test_case=self,
                completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "unicode.jsonl").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "İstanbul — 日本語 — 🚀",
                log_file_contents,
                "Expected Unicode characters to remain readable in JSON output.",
            )

    def test_existing_log_file_is_appended_without_new_file_warning_in_file(
        self,
    ) -> None:
        """Verifies that logging appends to an existing non-empty file without treating it as newly created."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            logs_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            log_file_path = logs_directory / "existing.log"

            log_file_path.write_text(
                "existing content\n",
                encoding="utf-8",
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="existing.log",
)

logger.info("new appended content")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "existing content",
                log_file_contents,
                "Expected the existing file content to remain intact.",
            )

            self.assertIn(
                "new appended content",
                log_file_contents,
                "Expected new logging output to be appended to the existing file.",
            )

            self.assertNotIn(
                "New log file created: existing.log",
                log_file_contents,
                ("Expected an existing non-empty file not to receive " "the new-log-file warning."),
            )

    def test_new_log_file_contains_creation_warning(
        self,
    ) -> None:
        """Verifies that creation of a new log file emits the package's new-file warning into that file."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="new-file.log",
)

logger.info("application message")
logger.shutdown()
"""

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
            test_case=self,
            completed_process=completed_process,
            )

            log_file_contents = (logs_directory / "new-file.log").read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "New log file created: new-file.log",
                log_file_contents,
                ("Expected newly created files to contain the new-file " "warning."),
            )

            self.assertIn(
                "application message",
                log_file_contents,
                "Expected normal logging to continue after the creation warning.",
            )

    def test_disable_application_logging_prevents_file_creation(
        self,
    ) -> None:
        """Verifies that the public disabling decorator prevents logging infrastructure from creating files for a test class."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
import unittest
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import disable_application_logging


@disable_application_logging
class ConsumerTestCase(unittest.TestCase):
    pass


ConsumerTestCase.setUpClass()

try:
    logger = CreateSpectraLogger(
        logs_directory=Path({str(logs_directory)!r}),
        log_file_name="should-not-exist.log",
        save_logs=True,
        multiprocessing_safe=True,
    )

    logger.info("suppressed integration message")
finally:
    ConsumerTestCase.tearDownClass()

print("DISABLED_LOGGING_SUCCESS")
"""

            completed_process = run_consumer_script(
                script=script,
                timeout_seconds=20,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            self.assertIn(
                "DISABLED_LOGGING_SUCCESS",
                completed_process.stdout,
                ("Expected consumer code to continue functioning while " "application logging is disabled."),
            )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected disable_application_logging to prevent the " "logging infrastructure from creating the logs directory."),
            )

    def test_combined_rich_json_multiprocessing_and_syslog_configuration(
        self,
    ) -> None:
        """Verifies that Rich console, JSON files, multiprocessing-safe logging, and syslog can operate together."""
        syslog_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.addCleanup(
            syslog_socket.close,
        )

        syslog_socket.bind(
            (
                "127.0.0.1",
                0,
            ),
        )

        syslog_socket.settimeout(
            5.0,
        )

        host, port = syslog_socket.getsockname()

        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
import socket
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration
from spectralog import RichConsoleConfiguration
from spectralog import SyslogConfiguration

logger = CreateSpectraLogger(
    debug_mode=True,
    show_datetime=True,
    show_line=True,
    show_folder_name=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="combined.log",
    save_logs=True,
    multiprocessing_safe=True,
    syslog_configuration=SyslogConfiguration(
        host={host!r},
        port={port},
        socket_type=socket.SOCK_DGRAM,
    ),
    rich_console_configuration=RichConsoleConfiguration(
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    ),
    json_logger_configuration=JsonLoggerConfiguration(),
)

logger.add_log_level(
    name="NOTICE",
    color="cyan",
    severity=35,
)

logger.notice(
    "combined integration message",
)

logger.shutdown()
            """

            completed_process = run_consumer_script(
                script=script,
                timeout_seconds=20,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            combined_console_output = completed_process.stdout + completed_process.stderr

            self.assertIn(
                "combined integration message",
                combined_console_output,
                ("Expected the Rich console handler to emit the combined " "integration message."),
            )

            json_log_file_path = logs_directory / "combined.jsonl"

            self.assertTrue(
                json_log_file_path.exists(),
                ("Expected the combined configuration to create the " "JSON Lines log file."),
            )

            json_log_contents = json_log_file_path.read_text(
                encoding="utf-8",
            )

            json_entries = [
                json.loads(
                    line,
                )
                for line in json_log_contents.splitlines()
                if line.strip()
            ]

            matching_entries = [
                entry
                for entry in json_entries
                if entry.get(
                    "message",
                )
                == "combined integration message"
            ]

            self.assertEqual(
                len(
                    matching_entries,
                ),
                1,
                ("Expected the multiprocessing JSON pipeline to write " "the custom-level message exactly once."),
            )

            matching_entry = matching_entries[0]

            self.assertEqual(
                matching_entry["level"],
                "NOTICE",
                ("Expected the JSON file to preserve the custom log " "level name."),
            )

            self.assertEqual(
                matching_entry["message"],
                "combined integration message",
                ("Expected the JSON file to preserve the emitted " "application message."),
            )

            received_syslog_messages: list[str] = []
            matched_sender_address: tuple[str, int] | None = None

            while True:
                try:
                    received_data, sender_address = syslog_socket.recvfrom(
                        65535,
                    )
                except TimeoutError:
                    break

                decoded_syslog_message = received_data.decode(
                    "utf-8",
                    errors="replace",
                )

                received_syslog_messages.append(
                    decoded_syslog_message,
                )

                if "combined integration message" in decoded_syslog_message:
                    matched_sender_address = sender_address

                    break

            self.assertGreaterEqual(
                len(
                    received_syslog_messages,
                ),
                1,
                ("Expected the local syslog socket to receive at least " "one datagram."),
            )

            self.assertTrue(
                any("combined integration message" in syslog_message for syslog_message in received_syslog_messages),
                (
                    "Expected the syslog handler to receive the same "
                    "combined-configuration message.\n"
                    f"Received syslog messages: {received_syslog_messages}"
                ),
            )

            self.assertIsNotNone(
                matched_sender_address,
                ("Expected the matching combined integration syslog " "message to have a sender address."),
            )

            if matched_sender_address is not None:
                self.assertEqual(
                    matched_sender_address[0],
                    "127.0.0.1",
                    ("Expected the combined syslog message to originate " "from the local machine."),
                )

    def test_console_only_routing_writes_to_console_but_not_file(
        self,
    ) -> None:
        """Verifies that console-only routing emits to console output while excluding the record from file logging."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="routing.log",
    save_logs=True,
)

logger.info(
    "console-only integration message",
    console=True,
    file=False,
)

logger.shutdown()
    """

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            combined_output = (
                completed_process.stdout
                + completed_process.stderr
            )

            self.assertIn(
                "console-only integration message",
                combined_output,
                (
                    "Expected console-only routing to emit the message "
                    "through the configured console handler."
                ),
            )

            log_file_path = logs_directory / "routing.log"

            self.assertTrue(
                log_file_path.exists(),
                (
                    "Expected file logging infrastructure to remain configured "
                    "even when an individual record is routed away from the file."
                ),
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertNotIn(
                "console-only integration message",
                log_file_contents,
                (
                    "Expected console-only routing to exclude the message "
                    "from file output."
                ),
            )

    def test_json_logging_honors_file_routing(
        self,
    ) -> None:
        """Verifies that JSON file logging excludes records explicitly routed away from file handlers."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger
from spectralog import JsonLoggerConfiguration

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="routing",
    save_logs=True,
    json_logger_configuration=JsonLoggerConfiguration(),
)

logger.info(
    "json persisted message",
    console=False,
    file=True,
)

logger.info(
    "json excluded message",
    console=True,
    file=False,
)

logger.shutdown()
    """

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            json_log_file_path = (
                logs_directory
                / "routing.jsonl"
            )

            decoded_entries = [
                json.loads(
                    line,
                )
                for line in json_log_file_path.read_text(
                    encoding="utf-8",
                ).splitlines()
                if line.strip()
            ]

            messages = [
                entry["message"]
                for entry in decoded_entries
            ]

            self.assertIn(
                "json persisted message",
                messages,
                (
                    "Expected file-enabled JSON logging to persist "
                    "the routed record."
                ),
            )

            self.assertNotIn(
                "json excluded message",
                messages,
                (
                    "Expected file-disabled JSON logging to exclude "
                    "the routed record."
                ),
            )

    def test_custom_log_level_supports_destination_routing(
        self,
    ) -> None:
        """Verifies that dynamically registered custom log levels honor console and file routing."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    debug_mode=True,
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="custom-routing.log",
    save_logs=True,
)

logger.add_log_level(
    name="NOTICE",
    color="purple",
    severity=35,
)

logger.notice(
    "custom console-only message",
    console=True,
    file=False,
)

logger.notice(
    "custom file-only message",
    console=False,
    file=True,
)

logger.shutdown()
    """

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            combined_output = (
                completed_process.stdout
                + completed_process.stderr
            )

            self.assertIn(
                "custom console-only message",
                combined_output,
                (
                    "Expected the dynamically registered custom level "
                    "to honor console-only routing."
                ),
            )

            self.assertNotIn(
                "custom file-only message",
                combined_output,
                (
                    "Expected the dynamically registered custom level "
                    "to suppress console output for file-only routing."
                ),
            )

            log_file_contents = (
                logs_directory
                / "custom-routing.log"
            ).read_text(
                encoding="utf-8",
            )

            self.assertNotIn(
                "custom console-only message",
                log_file_contents,
                (
                    "Expected the dynamically registered custom level "
                    "to suppress file output for console-only routing."
                ),
            )

            self.assertIn(
                "custom file-only message",
                log_file_contents,
                (
                    "Expected the dynamically registered custom level "
                    "to honor file-only routing."
                ),
            )

    def test_disabled_console_and_file_routing_emits_to_neither_destination(
        self,
    ) -> None:
        """Verifies that disabling both destinations prevents the record from reaching console and file handlers."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="routing.log",
    save_logs=True,
)

logger.info(
    "fully suppressed integration message",
    console=False,
    file=False,
)

logger.shutdown()
    """

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            combined_output = (
                completed_process.stdout
                + completed_process.stderr
            )

            self.assertNotIn(
                "fully suppressed integration message",
                combined_output,
                (
                    "Expected a record routed away from console and file "
                    "not to appear in console output."
                ),
            )

            log_file_path = logs_directory / "routing.log"

            self.assertTrue(
                log_file_path.exists(),
                (
                    "Expected the logger configuration to retain its file "
                    "handler even when a specific record is suppressed."
                ),
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertNotIn(
                "fully suppressed integration message",
                log_file_contents,
                (
                    "Expected a record routed away from console and file "
                    "not to appear in file output."
                ),
            )

    def test_file_only_routing_writes_to_file_but_not_console(
        self,
    ) -> None:
        """Verifies that file-only routing persists the record while excluding it from console output."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            script = f"""
from pathlib import Path

from spectralog import CreateSpectraLogger

logger = CreateSpectraLogger(
    logs_directory=Path({str(logs_directory)!r}),
    log_file_name="routing.log",
    save_logs=True,
)

logger.info(
    "file-only integration message",
    console=False,
    file=True,
)

logger.shutdown()
    """

            completed_process = run_consumer_script(
                script=script,
            )

            assert_consumer_succeeded(
    test_case=self,
    completed_process=completed_process,
)

            combined_output = (
                completed_process.stdout
                + completed_process.stderr
            )

            self.assertNotIn(
                "file-only integration message",
                combined_output,
                (
                    "Expected file-only routing to exclude the message "
                    "from console output."
                ),
            )

            log_file_path = logs_directory / "routing.log"

            self.assertTrue(
                log_file_path.exists(),
                "Expected file-only routing to preserve file logging.",
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "file-only integration message",
                log_file_contents,
                (
                    "Expected file-only routing to persist the message "
                    "in the configured log file."
                ),
            )




    # def run_consumer_script(
    #     self,
    #     script: str,
    #     timeout_seconds: int = 15,
    # ) -> subprocess.CompletedProcess[str]:
    #     project_root = (
    #         Path(
    #             __file__,
    #         )
    #         .resolve()
    #         .parents[2]
    #     )

    #     source_directory = project_root / "src"

    #     environment = os.environ.copy()

    #     existing_python_path = environment.get(
    #         "PYTHONPATH",
    #     )

    #     if existing_python_path:
    #         environment["PYTHONPATH"] = f"{source_directory}{os.pathsep}{existing_python_path}"
    #     else:
    #         environment["PYTHONPATH"] = str(
    #             source_directory,
    #         )

    #     completed_process = subprocess.run(
    #         [
    #             sys.executable,
    #             "-c",
    #             script,
    #         ],
    #         capture_output=True,
    #         text=True,
    #         timeout=timeout_seconds,
    #         check=False,
    #         env=environment,
    #     )

    #     return completed_process

    # def assert_consumer_succeeded(
    #     self,
    #     completed_process: subprocess.CompletedProcess[str],
    # ) -> None:
    #     self.assertEqual(
    #         completed_process.returncode,
    #         0,
    #         ("Expected consumer process to exit successfully.\n" f"stdout:\n{completed_process.stdout}\n" f"stderr:\n{completed_process.stderr}"),
    #     )

