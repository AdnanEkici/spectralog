from __future__ import annotations

import logging
import sys
import unittest
from logging.handlers import QueueHandler
from logging.handlers import QueueListener
from multiprocessing.queues import Queue
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.core.protocols import FileHandlerFactoryProtocol  # noqa: E402
from spectralog.handlers.multiprocessing_handler_factory import MultiprocessingHandlerFactory  # noqa: E402
from spectralog.handlers.queue_file_handler_factory import QueueFileHandlerFactory  # noqa: E402
from spectralog.runtime.multiprocessing_logging_runtime import MultiprocessingLoggingRuntime  # noqa: E402


class UnitTestMultiprocessingHandlerFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.queue_file_handler_factory = MagicMock(
            spec=QueueFileHandlerFactory,
        )

        self.file_handler_factory = MagicMock(
            spec=FileHandlerFactoryProtocol,
        )

        self.multiprocessing_handler_factory = MultiprocessingHandlerFactory(
            queue_file_handler_factory=self.queue_file_handler_factory,
            file_handler_factory=self.file_handler_factory,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory." "MultiprocessingLoggingRuntime",
    )
    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_returns_created_multiprocessing_logging_runtime(
        self,
        queue_listener_class_mock: MagicMock,
        multiprocessing_logging_runtime_class_mock: MagicMock,
    ) -> None:
        """Verifies that create returns the MultiprocessingLoggingRuntime instance produced by the runtime constructor."""
        configuration = LoggerConfiguration(
            debug_mode=True,
        )

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        file_handler = MagicMock(
            spec=logging.Handler,
        )

        queue_listener = MagicMock(
            spec=QueueListener,
        )

        multiprocessing_logging_runtime = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        self.queue_file_handler_factory.create.return_value = queue_handler

        self.file_handler_factory.create.return_value = file_handler

        queue_listener_class_mock.return_value = queue_listener

        multiprocessing_logging_runtime_class_mock.return_value = multiprocessing_logging_runtime

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            created_runtime = self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        self.assertIs(
            created_runtime,
            multiprocessing_logging_runtime,
            ("Expected create() to return the same " "MultiprocessingLoggingRuntime instance created by " "the runtime constructor."),
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_requests_queue_handler_with_created_queue_and_log_level(
        self,
        queue_listener_class_mock: MagicMock,
    ) -> None:
        """Verifies that create builds the queue handler with the created queue and configured logging level."""
        configuration = LoggerConfiguration(
            debug_mode=True,
        )

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        file_handler = MagicMock(
            spec=logging.Handler,
        )

        self.queue_file_handler_factory.create.return_value = queue_handler

        self.file_handler_factory.create.return_value = file_handler

        queue_listener_class_mock.return_value = MagicMock(
            spec=QueueListener,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        self.queue_file_handler_factory.create.assert_called_once_with(
            log_record_queue=log_record_queue,
            log_level=logging.DEBUG,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_requests_file_handler_with_configuration_and_path(
        self,
        queue_listener_class_mock: MagicMock,
    ) -> None:
        """Verifies that create builds the file handler using the supplied logger configuration and log file path."""
        configuration = LoggerConfiguration(
            debug_mode=False,
        )

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        file_handler = MagicMock(
            spec=logging.Handler,
        )

        self.queue_file_handler_factory.create.return_value = queue_handler

        self.file_handler_factory.create.return_value = file_handler

        queue_listener_class_mock.return_value = MagicMock(
            spec=QueueListener,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        self.file_handler_factory.create.assert_called_once_with(
            configuration=configuration,
            log_file_path=log_file_path,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_constructs_queue_listener_with_queue_and_file_handler(
        self,
        queue_listener_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs QueueListener with the created queue, file handler, and handler-level filtering enabled."""
        configuration = LoggerConfiguration()

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        file_handler = MagicMock(
            spec=logging.Handler,
        )

        self.queue_file_handler_factory.create.return_value = queue_handler

        self.file_handler_factory.create.return_value = file_handler

        queue_listener_class_mock.return_value = MagicMock(
            spec=QueueListener,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        queue_listener_class_mock.assert_called_once_with(
            log_record_queue,
            file_handler,
            respect_handler_level=True,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory." "MultiprocessingLoggingRuntime",
    )
    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_constructs_runtime_with_all_created_components(
        self,
        queue_listener_class_mock: MagicMock,
        multiprocessing_logging_runtime_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes the queue handler, queue listener, and queue into MultiprocessingLoggingRuntime."""
        configuration = LoggerConfiguration()

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        queue_handler = MagicMock(
            spec=QueueHandler,
        )

        file_handler = MagicMock(
            spec=logging.Handler,
        )

        queue_listener = MagicMock(
            spec=QueueListener,
        )

        self.queue_file_handler_factory.create.return_value = queue_handler

        self.file_handler_factory.create.return_value = file_handler

        queue_listener_class_mock.return_value = queue_listener

        multiprocessing_logging_runtime_class_mock.return_value = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        multiprocessing_logging_runtime_class_mock.assert_called_once_with(
            queue_handler=queue_handler,
            queue_listener=queue_listener,
            log_record_queue=log_record_queue,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_uses_info_level_when_debug_mode_is_disabled(
        self,
        queue_listener_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the queue handler with INFO level when debug mode is disabled."""
        configuration = LoggerConfiguration(
            debug_mode=False,
        )

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        self.queue_file_handler_factory.create.return_value = MagicMock(
            spec=QueueHandler,
        )

        self.file_handler_factory.create.return_value = MagicMock(
            spec=logging.Handler,
        )

        queue_listener_class_mock.return_value = MagicMock(
            spec=QueueListener,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        self.queue_file_handler_factory.create.assert_called_once_with(
            log_record_queue=log_record_queue,
            log_level=logging.INFO,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory.QueueListener",
    )
    def test_create_uses_debug_level_when_debug_mode_is_enabled(
        self,
        queue_listener_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the queue handler with DEBUG level when debug mode is enabled."""
        configuration = LoggerConfiguration(
            debug_mode=True,
        )

        log_file_path = Path(
            "logs/application.log",
        )

        log_record_queue = MagicMock(
            spec=Queue,
        )

        self.queue_file_handler_factory.create.return_value = MagicMock(
            spec=QueueHandler,
        )

        self.file_handler_factory.create.return_value = MagicMock(
            spec=logging.Handler,
        )

        queue_listener_class_mock.return_value = MagicMock(
            spec=QueueListener,
        )

        with patch.object(
            self.multiprocessing_handler_factory,
            "_create_log_record_queue",
            return_value=log_record_queue,
        ):
            self.multiprocessing_handler_factory.create(
                configuration=configuration,
                log_file_path=log_file_path,
            )

        self.queue_file_handler_factory.create.assert_called_once_with(
            log_record_queue=log_record_queue,
            log_level=logging.DEBUG,
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory." "multiprocessing.get_context",
    )
    def test_create_log_record_queue_requests_default_multiprocessing_context(
        self,
        get_context_mock: MagicMock,
    ) -> None:
        """Verifies that the queue creation helper obtains the active default multiprocessing context."""
        multiprocessing_context = MagicMock()

        log_record_queue = MagicMock(
            spec=Queue,
        )

        multiprocessing_context.Queue.return_value = log_record_queue

        get_context_mock.return_value = multiprocessing_context

        created_queue = self.multiprocessing_handler_factory._create_log_record_queue()

        get_context_mock.assert_called_once_with(
            "spawn",
        )

        self.assertIs(
            created_queue,
            log_record_queue,
            ("Expected the queue creation helper to return the queue " "created by the active multiprocessing context."),
        )

    @patch(
        "spectralog.handlers.multiprocessing_handler_factory." "multiprocessing.get_context",
    )
    def test_create_log_record_queue_creates_queue_from_context(
        self,
        get_context_mock: MagicMock,
    ) -> None:
        """Verifies that the queue creation helper creates exactly one queue from the selected multiprocessing context."""
        multiprocessing_context = MagicMock()

        log_record_queue = MagicMock(
            spec=Queue,
        )

        multiprocessing_context.Queue.return_value = log_record_queue

        get_context_mock.return_value = multiprocessing_context

        created_queue = self.multiprocessing_handler_factory._create_log_record_queue()

        multiprocessing_context.Queue.assert_called_once_with()

        self.assertIs(
            created_queue,
            log_record_queue,
            ("Expected the queue creation helper to return the exact queue " "created by multiprocessing context Queue()."),
        )

    def test_create_log_record_queue_returns_real_multiprocessing_queue(
        self,
    ) -> None:
        """Verifies that the queue creation helper returns a real multiprocessing queue when external dependencies are not mocked."""
        created_queue = self.multiprocessing_handler_factory._create_log_record_queue()

        self.assertIsInstance(
            created_queue,
            Queue,
            ("Expected the queue creation helper to return an instance " "of multiprocessing.queues.Queue."),
        )

        created_queue.close()
        created_queue.join_thread()

    @patch(
    "spectralog.handlers.multiprocessing_handler_factory.multiprocessing.get_context",
    )
    def test_create_log_record_queue_uses_spawn_context(
        self,
        get_context_mock: MagicMock,
    ) -> None:
        """Verifies that the log queue is created from the spawn context so it can be shared with any worker start method."""
        self.multiprocessing_handler_factory._create_log_record_queue()

        get_context_mock.assert_called_once_with(
            "spawn",
        )