"""Application code that logs without configuring SpectraLog itself."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from spectralog import get_logger  # noqa: E402
from spectralog import silence_application_logging  # noqa: E402


class OrderService:
    """Place orders and log them with a custom SUCCESS level."""

    def place_order(
        self,
        order_id: int,
    ) -> bool:
        """Place an order and emit log messages."""
        logger = get_logger()

        logger.info(
            f"Placing order {order_id}",
        )

        logger.success(
            f"Order {order_id} placed",
        )

        logger.log(
            "SUCCESS",
            f"Order {order_id} placed via log()",
        )

        return True

    @silence_application_logging
    def place_order_silently(
        self,
        order_id: int,
    ) -> bool:
        """Place an order without producing any logging output."""
        return self.place_order(
            order_id,
        )