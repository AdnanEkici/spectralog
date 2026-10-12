"""Logging from spawned worker processes with SpectraLog.

Run with:
    python examples/multiprocessing_pool_example.py

Every record, including those from workers and the custom NOTICE
level, ends up in logs/multiprocessing_example.log written by the parent.
"""

from __future__ import annotations

import multiprocessing
import os
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"
LOGS_DIRECTORY = PROJECT_ROOT / "logs"

sys.path.insert(
    0,
    str(SOURCE_DIRECTORY),
)

from spectralog import CreateSpectraLogger # noqa: E402
from spectralog import get_logger# noqa: E402
from spectralog import get_worker_initializer# noqa: E402


def process_item(item: int) -> int:
    """Runs inside a pool worker; the initializer already configured logging."""
    logger = get_logger()

    logger.info("Worker %s started item %s", os.getpid(), item)

    time.sleep(0.1)

    result = item * item

    logger.notice("Worker %s finished item %s -> %s", os.getpid(), item, result)

    return result


def standalone_child() -> None:
    """Runs in a plain spawned Process; get_logger() rebuilds from the parent's config."""
    get_logger().warning("Standalone child %s logging without an initializer", os.getpid())


def main() -> None:
    logger = CreateSpectraLogger(
        multiprocessing_safe=True,
        logs_directory="logs",
        log_file_name="multiprocessing_example.log",
    )

    logger.add_log_level(
        name="NOTICE",
        color="purple",
        severity=35,
    )

    logger.info("Parent %s starting pool", os.getpid())

    spawn_context = multiprocessing.get_context("spawn")

    initializer, initargs = get_worker_initializer()

    with spawn_context.Pool(
        processes=4,
        initializer=initializer,
        initargs=initargs,
    ) as pool:
        results = pool.map(process_item, range(8))

        pool.close()
        pool.join()

    logger.notice("Pool results: %s", results)

    child = spawn_context.Process(target=standalone_child)
    child.start()
    child.join()

    logger.info("All workers done")

    logger.shutdown()

    log_path = LOGS_DIRECTORY / "multiprocessing_example.log"

    notice_lines = [
        line
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if "NOTICE" in line
    ]

    print(f"\n{len(notice_lines)} NOTICE records in {log_path}:")

    for line in notice_lines:
        print(f"  {line}")

    logger.shutdown()


if __name__ == "__main__":
    main()