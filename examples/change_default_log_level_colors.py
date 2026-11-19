"""Demonstrate overriding SpectraLog's default log-level colors.

The built-in DEBUG, INFO, WARNING, ERROR, and CRITICAL levels ship with default
console colors. The ``level_colors`` option replaces any of them at creation
time; levels that are not listed keep their defaults.

Two kinds of color names are supported:

- Named colors such as ``"blue"``, ``"bold_red"``, or ``"light_purple"``.
- xterm 256-color foreground codes from ``"fg_0"`` to ``"fg_255"``.

This example creates a logger with named colors, then shows the same levels
using xterm 256 colors.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from spectralog import CreateSpectraLogger  # noqa: E402
from spectralog.core.logger import ApplicationLogger  # noqa: E402

NAMED_LEVEL_COLORS = {
    "DEBUG": "white",
    "INFO": "blue",
    "WARNING": "purple",
    "ERROR": "bold_red",
    "CRITICAL": "light_red",
}

XTERM_256_LEVEL_COLORS = {
    "DEBUG": "fg_245",
    "INFO": "fg_45",
    "WARNING": "fg_214",
    "ERROR": "fg_196",
    "CRITICAL": "fg_201",
}


def main() -> None:
    """Override the default level colors and emit records for each level."""
    logger: ApplicationLogger = CreateSpectraLogger(
        debug_mode=True,
        log_file_name="custom-level-colors-example.log",
        level_colors=NAMED_LEVEL_COLORS,
    )

    logger.debug(
        "DEBUG rendered in white",
    )

    logger.info(
        "INFO rendered in blue",
    )

    logger.warning(
        "WARNING rendered in purple",
    )

    logger.error(
        "ERROR rendered in bold red",
    )

    logger.critical(
        "CRITICAL rendered in light red",
    )


if __name__ == "__main__":
    main()