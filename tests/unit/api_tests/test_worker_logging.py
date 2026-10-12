from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa

from spectralog import CreateSpectraLogger  # noqa: E402
from spectralog import get_logger  # noqa: E402
from spectralog import get_worker_initializer  # noqa: E402
from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.core.logger import ApplicationLogger  # noqa: E402
from spectralog.core.logger import SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE  # noqa: E402
from spectralog.exceptions.exceptions import SpectraApplicationLoggerNotInitializedError  # noqa: E402

api_module = sys.modules[CreateSpectraLogger.__module__]


@patch.dict(
    os.environ,
    clear=False,
)
@patch(
    "spectralog.core.logger.atexit.register",
)
class UnitTestWorkerLogging(unittest.TestCase):
    def setUp(self) -> None:
        ApplicationLogger._instance = None

        os.environ.pop(
            api_module.SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE,
            None,
        )

        os.environ.pop(
            SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE,
            None,
        )

    def tearDown(self) -> None:
        application_logger = ApplicationLogger._instance

        if isinstance(application_logger, ApplicationLogger):
            application_logger.shutdown()

        ApplicationLogger._instance = None

    def test_create_spectra_logger_stores_configuration_for_children(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger stores a configuration that round-trips through the environment."""
        CreateSpectraLogger(
            save_logs=False,
            debug_mode=True,
        )

        loaded_configuration = api_module._load_configuration_from_parent_process()

        self.assertEqual(
            loaded_configuration,
            LoggerConfiguration(
                save_logs=False,
                debug_mode=True,
            ),
            "Expected the stored configuration to equal the one CreateSpectraLogger built.",
        )

    def test_get_logger_raises_without_instance_or_stored_configuration(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_logger still raises when nothing is initialized and nothing is inherited."""
        with self.assertRaises(
            SpectraApplicationLoggerNotInitializedError,
        ):
            get_logger()

    def test_get_logger_rebuilds_from_stored_configuration_with_custom_levels(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_logger rebuilds the logger and its custom levels from inherited environment values."""
        api_module._store_configuration_for_child_processes(
            LoggerConfiguration(
                save_logs=False,
            ),
        )

        os.environ[SPECTRALOG_CUSTOM_LOG_LEVELS_ENVIRONMENT_VARIABLE] = '[{"name": "NOTICE", "color": "purple", "severity": 35}]'

        application_logger = get_logger()

        self.assertIsInstance(
            application_logger,
            ApplicationLogger,
            "Expected get_logger() to rebuild an ApplicationLogger from the inherited configuration.",
        )

        self.assertTrue(
            application_logger._log_level_registry.contains("NOTICE"),
            "Expected the inherited NOTICE level to be registered on the rebuilt logger.",
        )

        self.assertIs(
            get_logger(),
            application_logger,
            "Expected later get_logger() calls to return the same rebuilt singleton.",
        )

    def test_get_logger_raises_for_corrupt_stored_configuration(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that an unreadable stored configuration is ignored and the usual error is raised."""
        os.environ[api_module.SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE] = "not valid base64 !!"

        with self.assertRaises(
            SpectraApplicationLoggerNotInitializedError,
        ):
            get_logger()

    def test_get_worker_initializer_raises_before_initialization(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_worker_initializer requires an initialized logger."""
        with self.assertRaises(
            SpectraApplicationLoggerNotInitializedError,
        ):
            get_worker_initializer()

    def test_get_worker_initializer_returns_initializer_and_arguments(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_worker_initializer returns the worker function with configuration, queue and levels."""
        application_logger = CreateSpectraLogger(
            save_logs=False,
        )

        application_logger.add_log_level(
            name="NOTICE",
            color="purple",
            severity=35,
        )

        initializer, initializer_arguments = get_worker_initializer()

        self.assertIs(
            initializer,
            api_module.initialize_spectralog_worker,
            "Expected the initializer to be initialize_spectralog_worker.",
        )

        configuration, log_record_queue, custom_log_levels = initializer_arguments

        self.assertEqual(
            configuration,
            LoggerConfiguration(
                save_logs=False,
            ),
            "Expected the initializer arguments to carry the parent configuration.",
        )

        self.assertIsNone(
            log_record_queue,
            "Expected no queue when multiprocessing-safe file logging is not configured.",
        )

        self.assertEqual(
            custom_log_levels,
            [
                {
                    "name": "NOTICE",
                    "color": "purple",
                    "severity": 35,
                },
            ],
            "Expected the initializer arguments to carry the registered custom levels.",
        )

    def test_initialize_worker_does_nothing_when_logger_already_exists(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that a worker which inherited a logger, for example through fork, is left unchanged."""
        existing_logger = MagicMock()

        ApplicationLogger._instance = existing_logger

        with patch.object(
            api_module,
            "_create_application_logger",
        ) as create_application_logger_mock:
            api_module.initialize_spectralog_worker(
                LoggerConfiguration(),
                MagicMock(),
                [],
            )

        create_application_logger_mock.assert_not_called()

        self.assertIs(
            ApplicationLogger._instance,
            existing_logger,
            "Expected the inherited logger to remain the singleton.",
        )

    def test_initialize_worker_uses_parent_queue_and_registers_levels(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that the worker initializer builds with the parent queue and registers the parent's levels."""
        configuration = LoggerConfiguration(
            multiprocessing_safe=True,
        )

        log_record_queue = MagicMock()

        worker_logger = MagicMock()

        with patch.object(
            api_module,
            "_create_application_logger",
            return_value=worker_logger,
        ) as create_application_logger_mock:
            api_module.initialize_spectralog_worker(
                configuration,
                log_record_queue,
                [
                    {
                        "name": "NOTICE",
                        "color": "purple",
                        "severity": 35,
                    },
                ],
            )

        create_application_logger_mock.assert_called_once_with(
            configuration,
            worker_log_record_queue=log_record_queue,
        )

        worker_logger.add_log_level.assert_called_once_with(
            name="NOTICE",
            color="purple",
            severity=35,
        )
