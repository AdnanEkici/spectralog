"""Configure SpectraLog once at the application's entry point."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"
LOGS_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE_NAME = "disabled-log-example.log"

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from spectralog import CreateSpectraLogger  # noqa: E402


def configure_logging() -> None:
    """Create the application logger and register custom log levels."""
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