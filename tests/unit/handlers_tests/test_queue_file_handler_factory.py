from __future__ import annotations

import logging
import multiprocessing
import pickle
import sys
import unittest
from logging.handlers import QueueHandler
from multiprocessing.queues import Queue
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


from spectralog.handlers.queue_file_handler_factory import ExceptionPreservingQueueHandler  # noqa: E402
from spectralog.handlers.queue_file_handler_factory import QueueFileHandlerFactory  # noqa: E402


class UnitTestQueueFileHandlerFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.queue_file_handler_factory = QueueFileHandlerFactory()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_returns_created_queue_handler(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create returns the QueueHandler instance produced by the handler constructor."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        created_handler = self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.INFO,
        )

        self.assertIs(
            created_handler,
            queue_handler,
            ("Expected create() to return the same QueueHandler instance " "created by the QueueHandler constructor."),
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_constructs_queue_handler_with_supplied_queue(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes the supplied multiprocessing queue to the QueueHandler constructor."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler_class_mock.return_value = MagicMock(
            spec=QueueHandler,
        )

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.INFO,
        )

        queue_handler_class_mock.assert_called_once_with(
            log_record_queue,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_info_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the QueueHandler with the supplied INFO log level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.INFO,
        )

        queue_handler.setLevel.assert_called_once_with(
            logging.INFO,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_debug_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the QueueHandler with the supplied DEBUG log level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.DEBUG,
        )

        queue_handler.setLevel.assert_called_once_with(
            logging.DEBUG,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_warning_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the QueueHandler with the supplied WARNING log level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.WARNING,
        )

        queue_handler.setLevel.assert_called_once_with(
            logging.WARNING,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_error_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the QueueHandler with the supplied ERROR log level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.ERROR,
        )

        queue_handler.setLevel.assert_called_once_with(
            logging.ERROR,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_critical_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the QueueHandler with the supplied CRITICAL log level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.CRITICAL,
        )

        queue_handler.setLevel.assert_called_once_with(
            logging.CRITICAL,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_sets_custom_numeric_log_level(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create accepts and assigns a custom numeric logging level."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.return_value = queue_handler

        custom_log_level = 25

        self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=custom_log_level,
        )

        queue_handler.setLevel.assert_called_once_with(
            custom_log_level,
        )

        log_record_queue.close()
        log_record_queue.join_thread()

    @patch(
        "spectralog.handlers.queue_file_handler_factory.ExceptionPreservingQueueHandler",
    )
    def test_create_configures_only_supplied_queue_handler(
        self,
        queue_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures only the QueueHandler instance created for the supplied queue."""
        multiprocessing_context = multiprocessing.get_context()

        first_log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        second_log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        first_queue_handler = MagicMock(
            spec=QueueHandler,
        )

        second_queue_handler = MagicMock(
            spec=QueueHandler,
        )

        queue_handler_class_mock.side_effect = (
            first_queue_handler,
            second_queue_handler,
        )

        first_created_handler = self.queue_file_handler_factory.create(
            log_record_queue=first_log_record_queue,
            log_level=logging.INFO,
        )

        second_created_handler = self.queue_file_handler_factory.create(
            log_record_queue=second_log_record_queue,
            log_level=logging.DEBUG,
        )

        self.assertIs(
            first_created_handler,
            first_queue_handler,
            ("Expected the first create() call to return the QueueHandler " "constructed for the first multiprocessing queue."),
        )

        self.assertIs(
            second_created_handler,
            second_queue_handler,
            ("Expected the second create() call to return the QueueHandler " "constructed for the second multiprocessing queue."),
        )

        first_queue_handler.setLevel.assert_called_once_with(
            logging.INFO,
        )

        second_queue_handler.setLevel.assert_called_once_with(
            logging.DEBUG,
        )

        self.assertEqual(
            queue_handler_class_mock.call_count,
            2,
            ("Expected QueueHandler to be constructed exactly once for " "each create() invocation."),
        )

        first_log_record_queue.close()
        first_log_record_queue.join_thread()

        second_log_record_queue.close()
        second_log_record_queue.join_thread()

    def test_create_returns_real_queue_handler_when_not_mocked(self) -> None:
        """Verifies that create constructs a real exception-preserving QueueHandler backed by the supplied multiprocessing queue."""
        multiprocessing_context = multiprocessing.get_context()

        log_record_queue = cast(
            Queue,
            multiprocessing_context.Queue(),
        )

        created_handler = self.queue_file_handler_factory.create(
            log_record_queue=log_record_queue,
            log_level=logging.INFO,
        )

        self.assertIsInstance(
            created_handler,
            ExceptionPreservingQueueHandler,
            ("Expected create() to return an ExceptionPreservingQueueHandler when the " "handler constructor is not mocked."),
        )

        self.assertIs(
            created_handler.queue,
            log_record_queue,
            ("Expected the real QueueHandler to retain the exact " "multiprocessing queue supplied to the factory."),
        )

        self.assertEqual(
            created_handler.level,
            logging.INFO,
            ("Expected the real QueueHandler to use the supplied INFO " "logging level."),
        )

        created_handler.close()

        log_record_queue.close()
        log_record_queue.join_thread()


class UnitTestExceptionPreservingQueueHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.queue_handler = ExceptionPreservingQueueHandler(
            MagicMock(),
        )

    def _create_exception_record(self) -> logging.LogRecord:
        try:
            raise ValueError("boom")
        except ValueError:
            exception_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Request %s failed",
            args=("ABC",),
            exc_info=exception_info,
        )

        created_record = record

        return created_record

    def test_prepare_keeps_traceback_out_of_message(
        self,
    ) -> None:
        """Verifies that prepare interpolates the message without appending the traceback to it."""
        prepared_record = self.queue_handler.prepare(
            self._create_exception_record(),
        )

        self.assertEqual(
            prepared_record.getMessage(),
            "Request ABC failed",
            "Expected the prepared message to contain only the interpolated log message.",
        )

        self.assertNotIn(
            "Traceback",
            prepared_record.msg,
            "Expected the traceback not to be folded into the prepared message.",
        )

    def test_prepare_stores_traceback_in_exc_text(
        self,
    ) -> None:
        """Verifies that prepare renders the exception into exc_text and clears exc_info."""
        prepared_record = self.queue_handler.prepare(
            self._create_exception_record(),
        )

        self.assertIsNone(
            prepared_record.exc_info,
            "Expected exc_info to be cleared so the record can be pickled.",
        )

        self.assertIn(
            "ValueError: boom",
            prepared_record.exc_text or "",
            "Expected the rendered traceback to be preserved in exc_text.",
        )

    def test_prepare_returns_picklable_copy_without_mutating_original(
        self,
    ) -> None:
        """Verifies that prepare returns a picklable copy and leaves the original record unchanged."""
        original_record = self._create_exception_record()

        prepared_record = self.queue_handler.prepare(
            original_record,
        )

        pickle.dumps(
            prepared_record,
        )

        self.assertIsNot(
            prepared_record,
            original_record,
            "Expected prepare() to return a copy of the record.",
        )

        self.assertIsNotNone(
            original_record.exc_info,
            "Expected the original record to keep its exc_info.",
        )

        self.assertEqual(
            original_record.args,
            ("ABC",),
            "Expected the original record to keep its args.",
        )