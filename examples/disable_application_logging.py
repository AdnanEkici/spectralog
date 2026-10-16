"""Demonstrate disabling SpectraLog for an entire unittest.TestCase class.

The disable_application_logging decorator is intended for tests that execute
real application code which normally initializes and uses SpectraLog.

It allows that code to keep using the normal logging API, including custom
log levels, while preventing real logging infrastructure, files, handlers,
and other logging side effects from being created during the test.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"
LOGS_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE_NAME = "disabled-log-example.log"

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from spectralog import CreateSpectraLogger  # noqa: E402
from spectralog import disable_application_logging  # noqa: E402
from spectralog import get_logger  # noqa: E402


class ExampleApplication:
    """Provide an example application that normally uses file logging."""

    def initialize_logging(
        self,
    ) -> None:
        """Initialize the application's SpectraLog configuration."""
        logger = CreateSpectraLogger(
            save_logs=True,
            logs_directory=LOGS_DIRECTORY,
            log_file_name=LOG_FILE_NAME,
        )

        logger.add_log_level(
            name="SUCCESS",
            color="bold_green",
            severity=25,
        )

    def execute(
        self,
    ) -> None:
        """Execute application logic that emits log messages."""
        logger = get_logger()

        logger.info(
            "Application started",
        )

        logger.success(  # type: ignore[attr-defined]
            "Application task completed",
        )

        logger.log(
            "SUCCESS",
            "SUCCESS emitted through logger.log()",
        )

        logger.warning(
            "Example warning",
        )

        logger.error(
            "Example error",
        )


@disable_application_logging
class ExampleApplicationTest(unittest.TestCase):
    """Demonstrate disabling SpectraLog for every test in a test class."""

    def test_application_executes_without_logging_side_effects(
        self,
    ) -> None:
        """Verify that normal application logging calls do not create log files."""
        application = ExampleApplication()

        application.initialize_logging()
        application.execute()

        log_file_path = LOGS_DIRECTORY / LOG_FILE_NAME

        self.assertFalse(
            log_file_path.exists(),
            (
                "Expected disable_application_logging to prevent creation "
                "of the configured log file."
            ),
        )

    def test_get_logger_can_be_used_without_initialization(
        self,
    ) -> None:
        """Verify that decorated tests can retrieve a disabled fallback logger."""
        logger = get_logger()

        logger.info(
            "This message is suppressed",
        )

        self.assertTrue(
            logger._logger.disabled,
            "Expected the fallback logger to be disabled.",
        )

    def test_custom_log_level_can_be_used_while_disabled(
        self,
    ) -> None:
        """Verify that custom levels register and emit on the disabled logger."""
        logger = get_logger()

        logger.add_log_level(
            name="NOTICE",
            color="purple",
            severity=35,
        )

        logger.notice(  # type: ignore[attr-defined]
            "This NOTICE message is suppressed",
        )

        logger.log(
            "NOTICE",
            "This NOTICE message is also suppressed",
        )

        self.assertTrue(
            logger._logger.disabled,
            "Expected the fallback logger to stay disabled with a custom level.",
        )


if __name__ == "__main__":
    unittest.main()