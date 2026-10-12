from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

def _find_source_directory() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "src"

        if (candidate / "spectralog").is_dir():
            return candidate

    raise RuntimeError("Could not locate src/spectralog above this test file.")


SRC_DIR = _find_source_directory()  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


class IntegrationTestWorkerLogging(unittest.TestCase):
    def _run_script(
        self,
        script: str,
        temporary_directory: str,
    ) -> subprocess.CompletedProcess[str]:
        script_path = Path(temporary_directory) / "worker_script.py"

        script_path.write_text(
            textwrap.dedent(script),
            encoding="utf-8",
        )

        clean_environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("SPECTRALOG_")
        }

        completed_process = subprocess.run(
            [
                sys.executable,
                str(script_path),
                str(SRC_DIR),
                temporary_directory,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=clean_environment,
        )

        return completed_process

    def _read_log_file(
        self,
        completed_process: subprocess.CompletedProcess[str],
        temporary_directory: str,
        log_file_name: str,
    ) -> str:
        self.assertEqual(
            completed_process.returncode,
            0,
            f"Expected the script to exit cleanly. stderr:\n{completed_process.stderr}",
        )

        self.assertNotIn(
            "Traceback",
            completed_process.stderr,
            f"Expected no traceback. stderr:\n{completed_process.stderr}",
        )

        log_path = Path(temporary_directory) / log_file_name

        self.assertTrue(
            log_path.exists(),
            (
                f"Expected {log_file_name} to exist. "
                f"Files: {sorted(path.name for path in Path(temporary_directory).iterdir())}\n"
                f"stderr:\n{completed_process.stderr}"
            ),
        )

        return log_path.read_text(
            encoding="utf-8",
        )

    def test_spawn_pool_workers_log_through_parent_queue(
        self,
    ) -> None:
        """Verifies that spawned pool workers configured by the initializer log custom levels into the parent's file."""
        script = """
            import multiprocessing
            import sys

            sys.path.insert(0, sys.argv[1])

            from spectralog import CreateSpectraLogger
            from spectralog import get_logger
            from spectralog import get_worker_initializer


            def work(index):
                get_logger().notice("worker record %s", index)

                return index


            if __name__ == "__main__":
                logger = CreateSpectraLogger(
                    multiprocessing_safe=True,
                    logs_directory=sys.argv[2],
                    log_file_name="pool.log",
                )

                logger.add_log_level(
                    name="NOTICE",
                    color="purple",
                    severity=35,
                )

                initializer, initargs = get_worker_initializer()

                pool = multiprocessing.get_context("spawn").Pool(
                    2,
                    initializer=initializer,
                    initargs=initargs,
                )

                pool.map(work, range(4))
                pool.close()
                pool.join()

                logger.shutdown()
        """

        with TemporaryDirectory() as temporary_directory:
            completed_process = self._run_script(
                script,
                temporary_directory,
            )

            log_file_content = self._read_log_file(
                completed_process,
                temporary_directory,
                "pool.log",
            )

        for index in range(4):
            self.assertIn(
                f"worker record {index}",
                log_file_content,
                f"Expected worker record {index} to be written by the parent's listener.",
            )

    def test_spawned_child_rebuilds_logger_from_environment(
        self,
    ) -> None:
        """Verifies the fallback path where a spawned child only calls get_logger()."""
        script = """
            import multiprocessing
            import sys

            sys.path.insert(0, sys.argv[1])

            from spectralog import CreateSpectraLogger
            from spectralog import get_logger


            def child():
                get_logger().info("fallback record")


            if __name__ == "__main__":
                CreateSpectraLogger(
                    logs_directory=sys.argv[2],
                    log_file_name="fallback.log",
                )

                process = multiprocessing.get_context("spawn").Process(
                    target=child,
                )

                process.start()
                process.join()

                sys.exit(process.exitcode)
        """

        with TemporaryDirectory() as temporary_directory:
            completed_process = self._run_script(
                script,
                temporary_directory,
            )

            log_file_content = self._read_log_file(
                completed_process,
                temporary_directory,
                "fallback.log",
            )

        self.assertIn(
            "fallback record",
            log_file_content,
            "Expected the child's record in the log file after rebuilding from the environment.",
        )