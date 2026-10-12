from __future__ import annotations

import multiprocessing
import subprocess
import sys
import textwrap
import unittest
from logging.handlers import QueueHandler
from logging.handlers import QueueListener
from multiprocessing.queues import Queue
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from spectralog.runtime.multiprocessing_logging_runtime import MultiprocessingLoggingRuntime  # noqa: E402


class UnitTestMultiprocessingLoggingRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.queue_handler = MagicMock(
            spec=QueueHandler,
        )

        self.queue_listener = MagicMock(
            spec=QueueListener,
        )

        self.log_record_queue = MagicMock(
            spec=Queue,
        )

        self.multiprocessing_logging_runtime = MultiprocessingLoggingRuntime(
            queue_handler=self.queue_handler,
            queue_listener=self.queue_listener,
            log_record_queue=self.log_record_queue,
        )

    def test_queue_handler_returns_configured_queue_handler(
        self,
    ) -> None:
        """Verifies that queue_handler returns the QueueHandler supplied during runtime construction."""
        returned_queue_handler = self.multiprocessing_logging_runtime.queue_handler

        self.assertIs(
            returned_queue_handler,
            self.queue_handler,
            ("Expected queue_handler to return the exact QueueHandler " "supplied during runtime construction."),
        )

    def test_is_running_is_false_after_initialization(
        self,
    ) -> None:
        """Verifies that the multiprocessing logging runtime is not running immediately after construction."""
        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertFalse(
            is_running,
            ("Expected the multiprocessing logging runtime to be stopped " "immediately after construction."),
        )

    def test_start_starts_queue_listener(
        self,
    ) -> None:
        """Verifies that start starts the configured QueueListener when the runtime is initially stopped."""
        self.multiprocessing_logging_runtime.start()

        self.queue_listener.start.assert_called_once_with()

    def test_start_marks_runtime_as_running(
        self,
    ) -> None:
        """Verifies that start marks the multiprocessing logging runtime as running."""
        self.multiprocessing_logging_runtime.start()

        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertTrue(
            is_running,
            ("Expected the multiprocessing logging runtime to report " "running after start() completes."),
        )

    def test_start_does_not_start_listener_more_than_once(
        self,
    ) -> None:
        """Verifies that repeated start calls do not start the QueueListener more than once."""
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.start()

        self.queue_listener.start.assert_called_once_with()

    def test_start_keeps_runtime_running_after_repeated_calls(
        self,
    ) -> None:
        """Verifies that repeated start calls leave the runtime in the running state."""
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.start()

        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertTrue(
            is_running,
            ("Expected repeated start() calls to leave the runtime in " "the running state."),
        )

    def test_stop_stops_listener_when_runtime_is_running(
        self,
    ) -> None:
        """Verifies that stop stops the QueueListener when the runtime is currently running."""
        self.multiprocessing_logging_runtime.start()

        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.stop.assert_called_once_with()

    def test_stop_marks_runtime_as_not_running(
        self,
    ) -> None:
        """Verifies that stop marks a previously running runtime as not running."""
        self.multiprocessing_logging_runtime.start()

        self.multiprocessing_logging_runtime.stop()

        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertFalse(
            is_running,
            ("Expected the multiprocessing logging runtime to report " "not running after stop() completes."),
        )

    def test_stop_closes_queue_handler(
        self,
    ) -> None:
        """Verifies that stop closes the configured QueueHandler."""
        self.multiprocessing_logging_runtime.stop()

        self.queue_handler.close.assert_called_once_with()

    def test_stop_closes_log_record_queue(
        self,
    ) -> None:
        """Verifies that stop closes the multiprocessing log record queue."""
        self.multiprocessing_logging_runtime.stop()

        self.log_record_queue.close.assert_called_once_with()

    def test_stop_joins_log_record_queue_thread(
        self,
    ) -> None:
        """Verifies that stop joins the background queue thread after closing the multiprocessing queue."""
        self.multiprocessing_logging_runtime.stop()

        self.log_record_queue.join_thread.assert_called_once_with()

    def test_stop_does_not_stop_listener_when_runtime_was_never_started(
        self,
    ) -> None:
        """Verifies that stop does not stop the QueueListener when the runtime was never started."""
        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.stop.assert_not_called()

    def test_stop_still_closes_resources_when_runtime_was_never_started(
        self,
    ) -> None:
        """Verifies that stop closes owned resources even when the runtime was never started."""
        self.multiprocessing_logging_runtime.stop()

        self.queue_handler.close.assert_called_once_with()
        self.log_record_queue.close.assert_called_once_with()
        self.log_record_queue.join_thread.assert_called_once_with()

    def test_stop_is_idempotent(
        self,
    ) -> None:
        """Verifies that repeated stop calls do not close or stop runtime resources more than once."""
        self.multiprocessing_logging_runtime.start()

        self.multiprocessing_logging_runtime.stop()
        self.multiprocessing_logging_runtime.stop()
        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.stop.assert_called_once_with()
        self.queue_handler.close.assert_called_once_with()
        self.log_record_queue.close.assert_called_once_with()
        self.log_record_queue.join_thread.assert_called_once_with()

    def test_start_does_not_restart_runtime_after_stop(
        self,
    ) -> None:
        """Verifies that a runtime cannot be restarted after stop permanently closes its resources."""
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.start.reset_mock()

        self.multiprocessing_logging_runtime.start()

        self.queue_listener.start.assert_not_called()

    def test_runtime_remains_not_running_when_start_is_called_after_stop(
        self,
    ) -> None:
        """Verifies that calling start after stop does not transition a closed runtime back to running."""
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.stop()

        self.multiprocessing_logging_runtime.start()

        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertFalse(
            is_running,
            ("Expected a closed multiprocessing logging runtime to remain " "not running when start() is called again."),
        )

    def test_stop_closes_resources_in_expected_order_when_running(
        self,
    ) -> None:
        """Verifies that stop stops the listener before closing the handler and multiprocessing queue resources."""
        parent_mock = MagicMock()

        parent_mock.attach_mock(
            self.queue_listener.stop,
            "listener_stop",
        )

        parent_mock.attach_mock(
            self.queue_handler.close,
            "handler_close",
        )

        parent_mock.attach_mock(
            self.log_record_queue.close,
            "queue_close",
        )

        parent_mock.attach_mock(
            self.log_record_queue.join_thread,
            "queue_join_thread",
        )

        self.multiprocessing_logging_runtime.start()

        parent_mock.reset_mock()

        self.multiprocessing_logging_runtime.stop()

        expected_method_calls = [
            call.listener_stop(),
            call.handler_close(),
            call.queue_close(),
            call.queue_join_thread(),
        ]

        self.assertEqual(
            parent_mock.method_calls,
            expected_method_calls,
            ("Expected stop() to stop the listener, close the queue " "handler, close the queue, and then join the queue thread."),
        )

    def test_stop_closes_resources_in_expected_order_when_not_running(
        self,
    ) -> None:
        """Verifies that stop closes handler and queue resources in the expected order when the listener was never started."""
        parent_mock = MagicMock()

        parent_mock.attach_mock(
            self.queue_handler.close,
            "handler_close",
        )

        parent_mock.attach_mock(
            self.log_record_queue.close,
            "queue_close",
        )

        parent_mock.attach_mock(
            self.log_record_queue.join_thread,
            "queue_join_thread",
        )

        self.multiprocessing_logging_runtime.stop()

        expected_method_calls = [
            call.handler_close(),
            call.queue_close(),
            call.queue_join_thread(),
        ]

        self.assertEqual(
            parent_mock.method_calls,
            expected_method_calls,
            ("Expected stop() to close the queue handler, close the queue, " "and then join the queue thread when the listener was not running."),
        )

    def test_stop_does_not_close_resources_again_after_runtime_is_closed(
        self,
    ) -> None:
        """Verifies that stop immediately returns without touching resources after the runtime has already been closed."""
        self.multiprocessing_logging_runtime.stop()

        self.queue_handler.reset_mock()
        self.queue_listener.reset_mock()
        self.log_record_queue.reset_mock()

        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.stop.assert_not_called()
        self.queue_handler.close.assert_not_called()
        self.log_record_queue.close.assert_not_called()
        self.log_record_queue.join_thread.assert_not_called()

    @patch(
        "spectralog.runtime.multiprocessing_logging_runtime.RLock",
    )
    def test_constructor_creates_reentrant_lock(
        self,
        reentrant_lock_class_mock: MagicMock,
    ) -> None:
        """Verifies that construction creates a reentrant lock used to protect runtime state transitions."""
        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_listener = MagicMock(
            spec=QueueListener,
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        reentrant_lock = MagicMock()

        reentrant_lock_class_mock.return_value = reentrant_lock

        MultiprocessingLoggingRuntime(
            queue_handler=queue_handler,
            queue_listener=queue_listener,
            log_record_queue=log_record_queue,
        )

        reentrant_lock_class_mock.assert_called_once_with()

    def test_is_running_can_be_read_multiple_times_without_state_change(
        self,
    ) -> None:
        """Verifies that reading is_running repeatedly does not mutate the runtime state."""
        first_is_running = self.multiprocessing_logging_runtime.is_running
        second_is_running = self.multiprocessing_logging_runtime.is_running

        self.assertFalse(
            first_is_running,
            ("Expected the initial is_running read to report that the " "runtime is not running."),
        )

        self.assertFalse(
            second_is_running,
            ("Expected repeated is_running reads to preserve the stopped " "runtime state."),
        )

    def test_start_after_initialization_does_not_close_any_resources(
        self,
    ) -> None:
        """Verifies that starting the runtime does not close the handler or multiprocessing queue resources."""
        self.multiprocessing_logging_runtime.start()

        self.queue_handler.close.assert_not_called()
        self.log_record_queue.close.assert_not_called()
        self.log_record_queue.join_thread.assert_not_called()

    def test_stop_after_start_performs_complete_runtime_shutdown(
        self,
    ) -> None:
        """Verifies that starting and stopping the runtime performs the complete expected lifecycle."""
        self.multiprocessing_logging_runtime.start()
        self.multiprocessing_logging_runtime.stop()

        self.queue_listener.start.assert_called_once_with()
        self.queue_listener.stop.assert_called_once_with()
        self.queue_handler.close.assert_called_once_with()
        self.log_record_queue.close.assert_called_once_with()
        self.log_record_queue.join_thread.assert_called_once_with()

        is_running = self.multiprocessing_logging_runtime.is_running

        self.assertFalse(
            is_running,
            ("Expected the runtime to report not running after completing " "the full start and stop lifecycle."),
        )

    def test_runtime_with_real_multiprocessing_queue_can_be_stopped_safely(
        self,
    ) -> None:
        """Verifies that the runtime can close and join a real multiprocessing queue without leaving it running."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = multiprocessing_context.Queue()

        queue_handler = QueueHandler(
            log_record_queue,
        )

        queue_listener = MagicMock(
            spec=QueueListener,
        )

        multiprocessing_logging_runtime = MultiprocessingLoggingRuntime(
            queue_handler=queue_handler,
            queue_listener=queue_listener,
            log_record_queue=log_record_queue,
        )

        multiprocessing_logging_runtime.stop()

        is_running = multiprocessing_logging_runtime.is_running

        self.assertFalse(
            is_running,
            ("Expected a runtime backed by a real multiprocessing queue " "to report not running after stop() completes."),
        )

    def test_start_registers_stop_as_multiprocessing_exit_finalizer(
        self,
    ) -> None:
        """Verifies that start registers stop to run before multiprocessing closes its queues on process exit."""
        with patch(
            "spectralog.runtime.multiprocessing_logging_runtime.Finalize",
        ) as finalize:
            self.multiprocessing_logging_runtime.start()
            self.multiprocessing_logging_runtime.start()

        finalize.assert_called_once()

        finalize_arguments = finalize.call_args

        self.assertEqual(
            finalize_arguments.args[1],
            self.multiprocessing_logging_runtime.stop,
            "Expected start() to register the runtime's stop method as the finalizer callback.",
        )

        self.assertGreater(
            finalize_arguments.kwargs["exitpriority"],
            10,
            ("Expected the finalizer to outrank multiprocessing's queue close finalizer " "(exitpriority 10) so the listener stops first."),
        )

    def test_spawned_child_process_exits_without_listener_thread_error(
        self,
    ) -> None:
        """Verifies that a spawned child owning a multiprocessing-safe logger exits without a listener thread traceback."""
        source_directory = Path(__file__).resolve().parents[3] / "src"

        child_script = textwrap.dedent(
            """
            import multiprocessing
            import sys
            import threading
            import time

            sys.path.insert(0, sys.argv[1])


            def child(logs_directory):
                from spectralog import CreateSpectraLogger

                logger = CreateSpectraLogger(
                    multiprocessing_safe=True,
                    logs_directory=logs_directory,
                    log_file_name="child.log",
                )
                logger.info("child record", console=False)

                # Keep the child alive after multiprocessing's exit finalizers run,
                # as slow framework teardown (e.g. CUDA/NCCL) does.
                threading.Thread(target=time.sleep, args=(0.5,)).start()


            if __name__ == "__main__":
                process = multiprocessing.get_context("spawn").Process(
                    target=child,
                    args=(sys.argv[2],),
                )
                process.start()
                process.join()
                sys.exit(process.exitcode)
            """,
        )

        with TemporaryDirectory() as temporary_directory:
            script_path = Path(temporary_directory) / "spawn_child.py"
            script_path.write_text(
                child_script,
                encoding="utf-8",
            )

            completed_process = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    str(source_directory),
                    temporary_directory,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            log_file_content = (Path(temporary_directory) / "child.log").read_text(
                encoding="utf-8",
            )

        self.assertEqual(
            completed_process.returncode,
            0,
            f"Expected the spawned child to exit cleanly. stderr:\n{completed_process.stderr}",
        )

        self.assertNotIn(
            "Traceback",
            completed_process.stderr,
            f"Expected no listener thread traceback on child exit. stderr:\n{completed_process.stderr}",
        )

        self.assertIn(
            "child record",
            log_file_content,
            "Expected the child's record to be drained to the log file before exit.",
        )