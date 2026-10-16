"""Test application code that uses a custom level without configuring logging."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from examples.misc.logging_setup import LOG_FILE_NAME  # noqa: E402
from examples.misc.logging_setup import LOGS_DIRECTORY  # noqa: E402
from examples.disable_logger_multi_module.order_service import OrderService  # noqa: E402

from spectralog import disable_application_logging  # noqa: E402


@disable_application_logging
class OrderServiceTest(unittest.TestCase):
    """Run application code whose custom levels are registered elsewhere."""

    def test_place_order_without_configuring_logging(
        self,
    ) -> None:
        """Verify that custom-level logging works without real logging setup."""
        result = OrderService().place_order(
            42,
        )

        self.assertTrue(
            result,
        )

        log_file_path = LOGS_DIRECTORY / LOG_FILE_NAME

        self.assertFalse(
            log_file_path.exists(),
            (
                "Expected disable_application_logging to prevent creation "
                "of the configured log file."
            ),
        )


if __name__ == "__main__":
    unittest.main()