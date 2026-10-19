"""Run the application with logging configured and silence one operation."""

from __future__ import annotations

from examples.misc.logging_setup import configure_logging
from order_service import OrderService


def main() -> None:
    """Configure logging, log normally, then run a silenced operation."""
    configure_logging()

    order_service = OrderService()

    order_service.place_order(
        1,
    )

    order_service.place_order_silently(
        2,
    )

    order_service.place_order(
        3,
    )


if __name__ == "__main__":
    main()