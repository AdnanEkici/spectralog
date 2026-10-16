"""Run the application normally with logging configured."""

from __future__ import annotations

from examples.misc.logging_setup import configure_logging
from order_service import OrderService


def main() -> None:
    """Configure logging, then run application code."""
    configure_logging()

    OrderService().place_order(
        1,
    )


if __name__ == "__main__":
    main()