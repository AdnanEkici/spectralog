from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch
import copy 

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.core.log_routing import SPECTRALOG_CONSOLE_ATTRIBUTE  # noqa: E402
from spectralog.core.log_routing import SPECTRALOG_FILE_ATTRIBUTE  # noqa: E402
from spectralog.core.logger import ApplicationLogger  # noqa: E402
from spectralog.core.models import LoggerBuildResult  # noqa: E402
from spectralog.core.protocols import LoggerBuilder  # noqa: E402
from spectralog.exceptions.exceptions import SpectraApplicationLoggerAlreadyInitializedError  # noqa: E402
from spectralog.exceptions.exceptions import SpectraApplicationLoggerReconfigurationError  # noqa: E402
from spectralog.exceptions.exceptions import SpectraApplicationLoggerNotInitializedError  # noqa: E402
from spectralog.levels.log_level_registry import LogLevelRegistry  # noqa: E402
from spectralog.runtime.multiprocessing_logging_runtime import MultiprocessingLoggingRuntime  # noqa: E402


class UnitTestApplicationLogger(unittest.TestCase):
    def setUp(self) -> None:
        ApplicationLogger._instance = None

        self.logger_builder = MagicMock(
            spec=LoggerBuilder,
        )

        self.log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        self.logger = MagicMock(
            spec=logging.Logger,
        )

        self.logger.handlers = []

    def tearDown(self) -> None:
        ApplicationLogger._instance = None

    def test_constructor_rejects_direct_instantiation_with_invalid_token(
        self,
    ) -> None:
        """Verifies that direct construction is rejected when the internal construction token is not supplied."""
        with self.assertRaisesRegex(
            SpectraApplicationLoggerAlreadyInitializedError,
            ("ApplicationLogger cannot be instantiated directly; " "use CreateSpectraLogger or get_logger."),
            msg=("Expected ApplicationLogger construction to fail when an " "invalid construction token is supplied."),
        ):
            ApplicationLogger(
                logger_builder=self.logger_builder,
                log_level_registry=self.log_level_registry,
                construction_token=object(),
            )

    def _create_build_result(
        self,
        log_file_path: Path | None = None,
        is_new_log_file: bool = False,
        multiprocessing_logging_runtime: MultiprocessingLoggingRuntime | None = None,
    ) -> LoggerBuildResult:
        logger_build_result = LoggerBuildResult(
            logger=self.logger,
            log_file_path=log_file_path,
            is_new_log_file=is_new_log_file,
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        created_logger_build_result = logger_build_result

        return created_logger_build_result

    def _create_application_logger(
        self,
        logger_build_result: LoggerBuildResult | None = None,
    ) -> ApplicationLogger:
        if logger_build_result is None:
            logger_build_result = self._create_build_result()

        self.logger_builder.build.return_value = logger_build_result

        with patch(
            "spectralog.core.logger.atexit.register",
        ):
            application_logger = ApplicationLogger(
                logger_builder=self.logger_builder,
                log_level_registry=self.log_level_registry,
                construction_token=ApplicationLogger._construction_token,
            )

        created_application_logger = application_logger

        return created_application_logger

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_builds_logger_using_application_logger_class_name(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction builds the underlying logger using the ApplicationLogger class name."""
        logger_build_result = self._create_build_result()

        self.logger_builder.build.return_value = logger_build_result

        ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.logger_builder.build.assert_called_once_with(
            "ApplicationLogger",
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_stores_logger_from_build_result(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction stores the logger returned by the configured logger builder."""
        logger_build_result = self._create_build_result()

        self.logger_builder.build.return_value = logger_build_result

        application_logger = ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.assertIs(
            application_logger._logger,
            self.logger,
            ("Expected ApplicationLogger to retain the exact logger " "returned in LoggerBuildResult."),
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_stores_log_level_registry(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction stores the supplied log level registry."""
        logger_build_result = self._create_build_result()

        self.logger_builder.build.return_value = logger_build_result

        application_logger = ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.assertIs(
            application_logger._log_level_registry,
            self.log_level_registry,
            ("Expected ApplicationLogger to retain the exact " "LogLevelRegistry supplied during construction."),
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_registers_shutdown_with_atexit(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction registers shutdown as an interpreter-exit callback."""
        logger_build_result = self._create_build_result()

        self.logger_builder.build.return_value = logger_build_result

        application_logger = ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        atexit_register_mock.assert_called_once_with(
            application_logger.shutdown,
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_starts_multiprocessing_runtime_when_present(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction starts the multiprocessing logging runtime when the builder supplies one."""
        multiprocessing_logging_runtime = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        logger_build_result = self._create_build_result(
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        self.logger_builder.build.return_value = logger_build_result

        ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        multiprocessing_logging_runtime.start.assert_called_once_with()

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_does_not_start_runtime_when_absent(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction succeeds without starting a multiprocessing runtime when none is configured."""
        logger_build_result = self._create_build_result(
            multiprocessing_logging_runtime=None,
        )

        self.logger_builder.build.return_value = logger_build_result

        application_logger = ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.assertIsNone(
            application_logger._multiprocessing_logging_runtime,
            ("Expected the multiprocessing runtime to remain None when " "the logger builder does not supply one."),
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_initializes_shutdown_state_to_false(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that a newly constructed application logger is initially active rather than shut down."""
        self.logger_builder.build.return_value = self._create_build_result()

        application_logger = ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.assertFalse(
            application_logger._is_shutdown,
            "Expected a newly constructed ApplicationLogger not to be shut down.",
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_warns_when_new_log_file_was_created(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction emits a warning attributed to the external caller when a new log file is created."""
        log_file_path = Path(
            "/tmp/application.log",
        )

        logger_build_result = self._create_build_result(
            log_file_path=log_file_path,
            is_new_log_file=True,
        )

        self.logger_builder.build.return_value = logger_build_result

        ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.logger.warning.assert_called_once_with(
            "New log file created: application.log",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=4,
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_does_not_warn_when_log_file_is_not_new(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction does not emit the new-file warning for an existing log file."""
        logger_build_result = self._create_build_result(
            log_file_path=Path(
                "/tmp/application.log",
            ),
            is_new_log_file=False,
        )

        self.logger_builder.build.return_value = logger_build_result

        ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.logger.warning.assert_not_called()

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_constructor_does_not_warn_when_new_file_has_no_path(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that construction does not emit a new-file warning when no log file path is available."""
        logger_build_result = self._create_build_result(
            log_file_path=None,
            is_new_log_file=True,
        )

        self.logger_builder.build.return_value = logger_build_result

        ApplicationLogger(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
            construction_token=ApplicationLogger._construction_token,
        )

        self.logger.warning.assert_not_called()

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_get_instance_creates_singleton_with_supplied_dependencies(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_instance creates the singleton using explicitly supplied dependencies."""
        self.logger_builder.build.return_value = self._create_build_result()

        application_logger = ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
        )

        self.assertIsInstance(
            application_logger,
            ApplicationLogger,
            "Expected get_instance() to create an ApplicationLogger singleton.",
        )

        self.assertIs(
            ApplicationLogger._instance,
            application_logger,
            ("Expected the singleton class state to reference the " "ApplicationLogger returned by get_instance()."),
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_get_instance_returns_existing_singleton(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that repeated calls without configuration return the same singleton instance."""
        self.logger_builder.build.return_value = self._create_build_result()

        first_application_logger = ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
        )

        second_application_logger = ApplicationLogger.get_instance()

        self.assertIs(
            second_application_logger,
            first_application_logger,
            ("Expected repeated get_instance() calls to return the exact " "same ApplicationLogger singleton."),
        )

        self.logger_builder.build.assert_called_once_with(
            "ApplicationLogger",
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_get_instance_rejects_logger_builder_reconfiguration(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that an initialized singleton cannot be reconfigured with another logger builder."""
        self.logger_builder.build.return_value = self._create_build_result()

        ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
        )

        replacement_logger_builder = MagicMock(
            spec=LoggerBuilder,
        )

        with self.assertRaisesRegex(
            SpectraApplicationLoggerReconfigurationError,
            ("Application logger has already been initialized " "and cannot be reconfigured."),
            msg=("Expected get_instance() to reject a logger builder after " "singleton initialization."),
        ):
            ApplicationLogger.get_instance(
                logger_builder=replacement_logger_builder,
            )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_get_instance_rejects_log_level_registry_reconfiguration(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that an initialized singleton cannot be reconfigured with another log level registry."""
        self.logger_builder.build.return_value = self._create_build_result()

        ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
        )

        replacement_log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        with self.assertRaisesRegex(
            SpectraApplicationLoggerReconfigurationError,
            ("Application logger has already been initialized " "and cannot be reconfigured."),
            msg=("Expected get_instance() to reject a log level registry " "after singleton initialization."),
        ):
            ApplicationLogger.get_instance(
                log_level_registry=replacement_log_level_registry,
            )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    def test_get_instance_rejects_complete_reconfiguration(
        self,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that an initialized singleton rejects simultaneous replacement of both dependencies."""
        self.logger_builder.build.return_value = self._create_build_result()

        ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
            log_level_registry=self.log_level_registry,
        )

        replacement_logger_builder = MagicMock(
            spec=LoggerBuilder,
        )

        replacement_log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        with self.assertRaises(
            SpectraApplicationLoggerReconfigurationError,
            msg=("Expected get_instance() to reject complete reconfiguration " "after singleton initialization."),
        ):
            ApplicationLogger.get_instance(
                logger_builder=replacement_logger_builder,
                log_level_registry=replacement_log_level_registry,
            )

    @patch(
    "spectralog.core.logger.ApplicationLogger._create_default_logger_builder",
    )
    @patch(
        "spectralog.core.logger.LogLevelRegistry",
    )
    def test_get_instance_raises_when_application_logger_is_not_initialized(
        self,
        log_level_registry_class_mock: MagicMock,
        create_default_logger_builder_mock: MagicMock,
    ) -> None:
        """Verifies that get_instance rejects retrieval before explicit initialization."""
        with self.assertRaises(
            SpectraApplicationLoggerNotInitializedError,
            msg=(
                "Expected get_instance to reject retrieval when the "
                "application logger has not been initialized."
            ),
        ):
            ApplicationLogger.get_instance()

        log_level_registry_class_mock.assert_not_called()
        create_default_logger_builder_mock.assert_not_called()

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    @patch(
        "spectralog.core.logger.ApplicationLogger._create_default_logger_builder",
    )
    def test_get_instance_uses_supplied_registry_with_default_builder(
        self,
        create_default_logger_builder_mock: MagicMock,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_instance builds a default logger builder around an explicitly supplied registry."""
        default_logger_builder = MagicMock(
            spec=LoggerBuilder,
        )

        default_logger_builder.build.return_value = self._create_build_result()

        create_default_logger_builder_mock.return_value = default_logger_builder

        application_logger = ApplicationLogger.get_instance(
            log_level_registry=self.log_level_registry,
        )

        create_default_logger_builder_mock.assert_called_once_with(
            self.log_level_registry,
        )

        self.assertIs(
            application_logger._log_level_registry,
            self.log_level_registry,
            ("Expected get_instance() to retain the explicitly supplied " "LogLevelRegistry."),
        )

    @patch(
        "spectralog.core.logger.atexit.register",
    )
    @patch(
        "spectralog.core.logger.LogLevelRegistry",
    )
    def test_get_instance_uses_supplied_builder_with_default_registry(
        self,
        log_level_registry_class_mock: MagicMock,
        atexit_register_mock: MagicMock,
    ) -> None:
        """Verifies that get_instance creates a default registry while retaining an explicitly supplied logger builder."""
        default_log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        log_level_registry_class_mock.return_value = default_log_level_registry
        self.logger_builder.build.return_value = self._create_build_result()

        application_logger = ApplicationLogger.get_instance(
            logger_builder=self.logger_builder,
        )

        log_level_registry_class_mock.assert_called_once_with()

        self.assertIs(
            application_logger._log_level_registry,
            default_log_level_registry,
            ("Expected get_instance() to use the automatically created " "LogLevelRegistry with the supplied builder."),
        )

    @patch(
        "spectralog.core.logger.ApplicationLoggerBuilderFactory",
    )
    def test_create_default_logger_builder_constructs_default_configuration(
        self,
        application_logger_builder_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that the default builder factory receives a default LoggerConfiguration."""
        logger_builder_factory = MagicMock()

        logger_builder = MagicMock(
            spec=LoggerBuilder,
        )

        logger_builder_factory.create.return_value = logger_builder
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory

        created_logger_builder = ApplicationLogger._create_default_logger_builder(
            log_level_registry=self.log_level_registry,
        )

        application_logger_builder_factory_class_mock.assert_called_once_with(
            log_level_registry=self.log_level_registry,
        )

        supplied_configuration = logger_builder_factory.create.call_args.kwargs["configuration"]

        self.assertIsInstance(
            supplied_configuration,
            LoggerConfiguration,
            ("Expected the default logger builder factory to receive a " "LoggerConfiguration instance."),
        )

        self.assertEqual(
            supplied_configuration,
            LoggerConfiguration(),
            ("Expected the automatically created logger configuration " "to contain the default configuration values."),
        )

        self.assertIs(
            created_logger_builder,
            logger_builder,
            ("Expected _create_default_logger_builder() to return the " "builder produced by ApplicationLoggerBuilderFactory."),
        )

    def test_dynamic_log_method_raises_attribute_error_for_unknown_level(
        self,
    ) -> None:
        """Verifies that dynamic attribute access raises AttributeError when the requested log level is not registered."""
        application_logger = self._create_application_logger()

        self.log_level_registry.contains.return_value = False

        with self.assertRaisesRegex(
            AttributeError,
            "'ApplicationLogger' has no attribute 'notice'.",
            msg=("Expected an unknown dynamic log method to raise " "AttributeError."),
        ):
            getattr(
                application_logger,
                "notice",
            )

        self.log_level_registry.contains.assert_called_once_with(
            "NOTICE",
        )

        self.log_level_registry.get.assert_not_called()

    def test_dynamic_log_method_normalizes_level_name_to_uppercase(
        self,
    ) -> None:
        """Verifies that dynamic log method lookup normalizes the requested attribute name to uppercase."""
        application_logger = self._create_application_logger()

        self.log_level_registry.contains.return_value = True

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        dynamic_log_method = getattr(
            application_logger,
            "notice",
        )

        self.assertTrue(
            callable(dynamic_log_method),
            "Expected a registered dynamic log level to produce a callable method.",
        )

        self.log_level_registry.contains.assert_called_once_with(
            "NOTICE",
        )

        self.log_level_registry.get.assert_called_once_with(
            "NOTICE",
        )

    def test_dynamic_log_method_logs_using_registered_severity(
        self,
    ) -> None:
        """Verifies that a dynamic log method delegates to logging.Logger.log using the registered severity."""
        application_logger = self._create_application_logger()

        self.log_level_registry.contains.return_value = True

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        dynamic_log_method = getattr(
            application_logger,
            "notice",
        )

        dynamic_log_method(
            "Request %s completed",
            "ABC",
        )

        self.logger.log.assert_called_once_with(
            35,
            "Request %s completed",
            "ABC",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_dynamic_log_method_preserves_explicit_stacklevel(
        self,
    ) -> None:
        """Verifies that a dynamic log method preserves an explicitly supplied stacklevel."""
        application_logger = self._create_application_logger()

        self.log_level_registry.contains.return_value = True

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        dynamic_log_method = getattr(
            application_logger,
            "notice",
        )

        dynamic_log_method(
            "Message",
            stacklevel=7,
        )

        self.logger.log.assert_called_once_with(
            35,
            "Message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=7,
        )

    @patch.object(
        ApplicationLogger,
        "_refresh_console_colors",
    )
    def test_add_log_level_registers_level(
        self,
        refresh_console_colors_mock: MagicMock,
    ) -> None:
        """Verifies that add_log_level delegates custom level registration to the log level registry."""
        application_logger = self._create_application_logger()

        application_logger.add_log_level(
            name="NOTICE",
            color="blue",
            severity=35,
        )

        self.log_level_registry.register.assert_called_once_with(
            name="NOTICE",
            color="blue",
            severity=35,
        )

    @patch.object(
        ApplicationLogger,
        "_refresh_console_colors",
    )
    def test_add_log_level_refreshes_console_colors_after_registration(
        self,
        refresh_console_colors_mock: MagicMock,
    ) -> None:
        """Verifies that add_log_level refreshes existing console formatter colors after registration."""
        application_logger = self._create_application_logger()

        parent_mock = MagicMock()

        parent_mock.attach_mock(
            self.log_level_registry.register,
            "register",
        )

        parent_mock.attach_mock(
            refresh_console_colors_mock,
            "refresh",
        )

        application_logger.add_log_level(
            name="NOTICE",
            color="blue",
            severity=35,
        )

        expected_method_calls = [
            call.register(
                name="NOTICE",
                color="blue",
                severity=35,
            ),
            call.refresh(),
        ]

        self.assertEqual(
            parent_mock.method_calls,
            expected_method_calls,
            ("Expected custom level registration to complete before " "console formatter colors are refreshed."),
        )

    def test_log_with_integer_level_uses_integer_directly(
        self,
    ) -> None:
        """Verifies that log accepts an integer severity without consulting the log level registry."""
        application_logger = self._create_application_logger()

        application_logger.log(
            45,
            "Custom message",
        )

        self.logger.log.assert_called_once_with(
            45,
            "Custom message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

        self.log_level_registry.get.assert_not_called()

    def test_log_with_string_level_resolves_registered_severity(
        self,
    ) -> None:
        """Verifies that log resolves string level names through the log level registry."""
        application_logger = self._create_application_logger()

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        application_logger.log(
            "NOTICE",
            "Custom message",
        )

        self.log_level_registry.get.assert_called_once_with(
            "NOTICE",
        )

        self.logger.log.assert_called_once_with(
            35,
            "Custom message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_log_forwards_positional_arguments(
        self,
    ) -> None:
        """Verifies that log forwards message interpolation arguments to the underlying logger."""
        application_logger = self._create_application_logger()

        application_logger.log(
            logging.INFO,
            "User %s has %d items",
            "Ada",
            4,
        )

        self.logger.log.assert_called_once_with(
            logging.INFO,
            "User %s has %d items",
            "Ada",
            4,
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_log_preserves_explicit_keyword_arguments(
        self,
    ) -> None:
        """Verifies that log forwards caller-supplied logging keyword arguments without modification."""
        application_logger = self._create_application_logger()

        application_logger.log(
            logging.ERROR,
            "Operation failed",
            exc_info=True,
            extra={
                "request_id": "ABC",
            },
            stacklevel=9,
        )

        self.logger.log.assert_called_once_with(
            logging.ERROR,
            "Operation failed",
            exc_info=True,
            extra={
                "request_id": "ABC",
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=9,
        )

    def test_debug_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that debug delegates the message and arguments to logging.Logger.debug."""
        application_logger = self._create_application_logger()

        application_logger.debug(
            "Debug value: %s",
            "value",
        )

        self.logger.debug.assert_called_once_with(
            "Debug value: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_info_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that info delegates the message and arguments to logging.Logger.info."""
        application_logger = self._create_application_logger()

        application_logger.info(
            "Information: %s",
            "value",
        )

        self.logger.info.assert_called_once_with(
            "Information: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_warning_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that warning delegates the message and arguments to logging.Logger.warning."""
        application_logger = self._create_application_logger()

        application_logger.warning(
            "Warning: %s",
            "value",
        )

        self.logger.warning.assert_called_once_with(
            "Warning: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_error_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that error delegates the message and arguments to logging.Logger.error."""
        application_logger = self._create_application_logger()

        application_logger.error(
            "Error: %s",
            "value",
        )

        self.logger.error.assert_called_once_with(
            "Error: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_critical_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that critical delegates the message and arguments to logging.Logger.critical."""
        application_logger = self._create_application_logger()

        application_logger.critical(
            "Critical: %s",
            "value",
        )

        self.logger.critical.assert_called_once_with(
            "Critical: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_exception_delegates_to_underlying_logger(
        self,
    ) -> None:
        """Verifies that exception delegates the message and arguments to logging.Logger.exception."""
        application_logger = self._create_application_logger()

        application_logger.exception(
            "Exception: %s",
            "value",
        )

        self.logger.exception.assert_called_once_with(
            "Exception: %s",
            "value",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_standard_log_methods_preserve_explicit_stacklevel(
        self,
    ) -> None:
        """Verifies that standard log methods preserve a caller-provided stacklevel rather than replacing it."""
        application_logger = self._create_application_logger()

        application_logger.info(
            "Message",
            stacklevel=6,
        )

        self.logger.info.assert_called_once_with(
            "Message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=6,
        )

    def test_dynamic_log_method_forwards_console_and_file_routing(
        self,
    ) -> None:
        """Verifies that a dynamic custom log method forwards per-record destination routing metadata."""
        application_logger = self._create_application_logger()

        self.log_level_registry.contains.return_value = True

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        dynamic_log_method = getattr(
            application_logger,
            "notice",
        )

        dynamic_log_method(
            "Console-only notice",
            console=True,
            file=False,
        )

        self.logger.log.assert_called_once_with(
            35,
            "Console-only notice",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: False,
            },
            stacklevel=2,
        )

    def test_log_forwards_console_and_file_routing(
        self,
    ) -> None:
        """Verifies that log forwards explicit console and file routing choices to the underlying logger."""
        application_logger = self._create_application_logger()

        application_logger.log(
            logging.INFO,
            "File-only message",
            console=False,
            file=True,
        )

        self.logger.log.assert_called_once_with(
            logging.INFO,
            "File-only message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_standard_log_method_forwards_console_and_file_routing(
        self,
    ) -> None:
        """Verifies that a standard logging method forwards explicit destination routing metadata."""
        application_logger = self._create_application_logger()

        application_logger.info(
            "Console-only message",
            console=True,
            file=False,
        )

        self.logger.info.assert_called_once_with(
            "Console-only message",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                SPECTRALOG_FILE_ATTRIBUTE: False,
            },
            stacklevel=2,
        )

    def test_exception_forwards_console_and_file_routing(
        self,
    ) -> None:
        """Verifies that exception supports the same destination routing controls as standard log methods."""
        application_logger = self._create_application_logger()

        application_logger.exception(
            "File-only exception",
            console=False,
            file=True,
        )

        self.logger.exception.assert_called_once_with(
            "File-only exception",
            extra={
                SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                SPECTRALOG_FILE_ATTRIBUTE: True,
            },
            stacklevel=2,
        )

    def test_resolve_severity_returns_integer_level_directly(
        self,
    ) -> None:
        """Verifies that _resolve_severity returns integer severities without registry lookup."""
        application_logger = self._create_application_logger()

        resolved_severity = application_logger._resolve_severity(
            logging.ERROR,
        )

        self.assertEqual(
            resolved_severity,
            logging.ERROR,
            ("Expected _resolve_severity() to return an integer severity " "unchanged."),
        )

        self.log_level_registry.get.assert_not_called()

    def test_resolve_severity_returns_registered_string_severity(
        self,
    ) -> None:
        """Verifies that _resolve_severity resolves string levels using the log level registry."""
        application_logger = self._create_application_logger()

        log_level = MagicMock()
        log_level.severity = 35

        self.log_level_registry.get.return_value = log_level

        resolved_severity = application_logger._resolve_severity(
            "NOTICE",
        )

        self.assertEqual(
            resolved_severity,
            35,
            ("Expected _resolve_severity() to return the severity of the " "registered string log level."),
        )

        self.log_level_registry.get.assert_called_once_with(
            "NOTICE",
        )

    def test_prepare_keyword_arguments_adds_default_stacklevel(
        self,
    ) -> None:
        """Verifies that _prepare_keyword_arguments adds stacklevel two when the caller does not provide one."""
        application_logger = self._create_application_logger()

        keyword_arguments = {
            "exc_info": True,
        }

        resolved_keyword_arguments = application_logger._prepare_keyword_arguments(
            keyword_arguments,
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "exc_info": True,
                "stacklevel": 2,
            },
            ("Expected _prepare_keyword_arguments() to retain existing " "arguments and add stacklevel two."),
        )

    def test_prepare_keyword_arguments_preserves_explicit_stacklevel(
        self,
    ) -> None:
        """Verifies that _prepare_keyword_arguments does not replace a caller-provided stacklevel."""
        application_logger = self._create_application_logger()

        resolved_keyword_arguments = application_logger._prepare_keyword_arguments(
            {
                "stacklevel": 8,
                "exc_info": True,
            },
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "stacklevel": 8,
                "exc_info": True,
            },
            ("Expected _prepare_keyword_arguments() to preserve the " "explicit stacklevel value."),
        )

    def test_prepare_keyword_arguments_returns_copy(
        self,
    ) -> None:
        """Verifies that _prepare_keyword_arguments does not mutate the caller-owned dictionary."""
        application_logger = self._create_application_logger()

        keyword_arguments = {
            "exc_info": True,
        }

        resolved_keyword_arguments = application_logger._prepare_keyword_arguments(
            keyword_arguments,
        )

        self.assertIsNot(
            resolved_keyword_arguments,
            keyword_arguments,
            ("Expected _prepare_keyword_arguments() to return a new " "dictionary rather than the caller-owned object."),
        )

        self.assertEqual(
            keyword_arguments,
            {
                "exc_info": True,
            },
            ("Expected the caller-owned keyword argument dictionary to " "remain unchanged."),
        )

    def test_prepare_routing_keyword_arguments_adds_destination_metadata(
        self,
    ) -> None:
        """Verifies that routing preparation adds console and file metadata together with the default stacklevel."""
        application_logger = self._create_application_logger()

        resolved_keyword_arguments = (
            application_logger._prepare_routing_keyword_arguments(
                {},
                console=False,
                file=True,
            )
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "extra": {
                    SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                    SPECTRALOG_FILE_ATTRIBUTE: True,
                },
                "stacklevel": 2,
            },
            (
                "Expected routing preparation to add the requested "
                "destination metadata and default stacklevel."
            ),
        )

    def test_prepare_routing_keyword_arguments_preserves_existing_extra_values(
        self,
    ) -> None:
        """Verifies that routing preparation preserves caller-owned extra fields while adding routing metadata."""
        application_logger = self._create_application_logger()

        resolved_keyword_arguments = (
            application_logger._prepare_routing_keyword_arguments(
                {
                    "extra": {
                        "request_id": "ABC",
                    },
                },
                console=True,
                file=False,
            )
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "extra": {
                    "request_id": "ABC",
                    SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                    SPECTRALOG_FILE_ATTRIBUTE: False,
                },
                "stacklevel": 2,
            },
            (
                "Expected routing preparation to retain caller-provided "
                "extra values while adding SpectraLog routing metadata."
            ),
        )

    def test_prepare_routing_keyword_arguments_overrides_reserved_routing_values(
        self,
    ) -> None:
        """Verifies that explicit routing arguments override conflicting reserved values supplied through extra."""
        application_logger = self._create_application_logger()

        resolved_keyword_arguments = (
            application_logger._prepare_routing_keyword_arguments(
                {
                    "extra": {
                        SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                        SPECTRALOG_FILE_ATTRIBUTE: True,
                    },
                },
                console=True,
                file=False,
            )
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "extra": {
                    SPECTRALOG_CONSOLE_ATTRIBUTE: True,
                    SPECTRALOG_FILE_ATTRIBUTE: False,
                },
                "stacklevel": 2,
            },
            (
                "Expected explicit routing arguments to override conflicting "
                "SpectraLog routing values supplied through extra."
            ),
        )

    def test_prepare_routing_keyword_arguments_does_not_mutate_caller_values(
        self,
    ) -> None:
        """Verifies that routing preparation does not mutate the caller-owned keyword or extra dictionaries."""
        application_logger = self._create_application_logger()

        extra_values = {
            "request_id": "ABC",
        }

        keyword_arguments = {
            "extra": extra_values,
            "stacklevel": 7,
        }

        resolved_keyword_arguments = (
            application_logger._prepare_routing_keyword_arguments(
                keyword_arguments,
                console=False,
                file=True,
            )
        )

        self.assertIsNot(
            resolved_keyword_arguments,
            keyword_arguments,
            (
                "Expected routing preparation to return a new keyword "
                "argument dictionary."
            ),
        )

        self.assertIsNot(
            resolved_keyword_arguments["extra"],
            extra_values,
            "Expected routing preparation to copy the caller-owned extra mapping.",
        )

        self.assertEqual(
            keyword_arguments,
            {
                "extra": {
                    "request_id": "ABC",
                },
                "stacklevel": 7,
            },
            (
                "Expected routing preparation not to mutate the caller-owned "
                "keyword arguments."
            ),
        )

        self.assertEqual(
            resolved_keyword_arguments,
            {
                "extra": {
                    "request_id": "ABC",
                    SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                    SPECTRALOG_FILE_ATTRIBUTE: True,
                },
                "stacklevel": 7,
            },
            (
                "Expected routing preparation to preserve caller values while "
                "adding the requested routing metadata."
            ),
        )

    def test_start_multiprocessing_runtime_starts_configured_runtime(
        self,
    ) -> None:
        """Verifies that _start_multiprocessing_runtime starts the configured multiprocessing runtime."""
        multiprocessing_logging_runtime = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        logger_build_result = self._create_build_result(
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        application_logger = self._create_application_logger(
            logger_build_result=logger_build_result,
        )

        multiprocessing_logging_runtime.start.reset_mock()

        application_logger._start_multiprocessing_runtime()

        multiprocessing_logging_runtime.start.assert_called_once_with()

    def test_start_multiprocessing_runtime_does_nothing_when_runtime_is_none(
        self,
    ) -> None:
        """Verifies that _start_multiprocessing_runtime safely performs no operation when multiprocessing is disabled."""
        application_logger = self._create_application_logger()

        application_logger._start_multiprocessing_runtime()

        self.assertIsNone(
            application_logger._multiprocessing_logging_runtime,
            ("Expected the multiprocessing runtime to remain None when " "multiprocessing logging is disabled."),
        )

    def test_shutdown_stops_multiprocessing_runtime(
        self,
    ) -> None:
        """Verifies that shutdown stops the multiprocessing logging runtime when one is configured."""
        multiprocessing_logging_runtime = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        logger_build_result = self._create_build_result(
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        application_logger = self._create_application_logger(
            logger_build_result=logger_build_result,
        )

        multiprocessing_logging_runtime.start.reset_mock()

        application_logger.shutdown()

        multiprocessing_logging_runtime.stop.assert_called_once_with()

    def test_shutdown_marks_application_logger_as_shutdown(
        self,
    ) -> None:
        """Verifies that shutdown records the terminal shutdown state."""
        application_logger = self._create_application_logger()

        application_logger.shutdown()

        self.assertTrue(
            application_logger._is_shutdown,
            "Expected shutdown() to mark the ApplicationLogger as shut down.",
        )

    def test_shutdown_without_multiprocessing_runtime_marks_logger_as_shutdown(
        self,
    ) -> None:
        """Verifies that shutdown completes successfully when multiprocessing logging is disabled."""
        application_logger = self._create_application_logger()

        application_logger.shutdown()

        self.assertTrue(
            application_logger._is_shutdown,
            ("Expected shutdown() to complete even when no " "multiprocessing runtime exists."),
        )

    def test_shutdown_is_idempotent(
        self,
    ) -> None:
        """Verifies that repeated shutdown calls stop the multiprocessing runtime only once."""
        multiprocessing_logging_runtime = MagicMock(
            spec=MultiprocessingLoggingRuntime,
        )

        logger_build_result = self._create_build_result(
            multiprocessing_logging_runtime=multiprocessing_logging_runtime,
        )

        application_logger = self._create_application_logger(
            logger_build_result=logger_build_result,
        )

        multiprocessing_logging_runtime.start.reset_mock()

        application_logger.shutdown()
        application_logger.shutdown()
        application_logger.shutdown()

        multiprocessing_logging_runtime.stop.assert_called_once_with()

        self.assertTrue(
            application_logger._is_shutdown,
            "Expected repeated shutdown calls to leave the logger shut down.",
        )

    @patch.object(
        ApplicationLogger,
        "warning",
    )
    def test_handle_new_log_file_warns_with_file_name_only(
        self,
        warning_mock: MagicMock,
    ) -> None:
        """Verifies that _handle_new_log_file reports only the newly created file name rather than the full path."""
        application_logger = self._create_application_logger()

        logger_build_result = self._create_build_result(
            log_file_path=Path(
                "/var/log/spectralog/application.jsonl",
            ),
            is_new_log_file=True,
        )

        application_logger._handle_new_log_file(
            logger_build_result=logger_build_result,
        )

        warning_mock.assert_called_once_with(
            "New log file created: application.jsonl",
            stacklevel=3,
        )

    @patch.object(
        ApplicationLogger,
        "warning",
    )
    def test_handle_new_log_file_does_not_warn_for_existing_file(
        self,
        warning_mock: MagicMock,
    ) -> None:
        """Verifies that _handle_new_log_file does not warn when the resolved log file already contains data."""
        application_logger = self._create_application_logger()

        logger_build_result = self._create_build_result(
            log_file_path=Path(
                "/var/log/spectralog/application.log",
            ),
            is_new_log_file=False,
        )

        application_logger._handle_new_log_file(
            logger_build_result=logger_build_result,
        )

        warning_mock.assert_not_called()

    @patch.object(
        ApplicationLogger,
        "warning",
    )
    def test_handle_new_log_file_does_not_warn_without_file_path(
        self,
        warning_mock: MagicMock,
    ) -> None:
        """Verifies that _handle_new_log_file does not warn when no file path is available."""
        application_logger = self._create_application_logger()

        logger_build_result = self._create_build_result(
            log_file_path=None,
            is_new_log_file=True,
        )

        application_logger._handle_new_log_file(
            logger_build_result=logger_build_result,
        )

        warning_mock.assert_not_called()

    def test_refresh_console_colors_updates_formatter_log_colors(
        self,
    ) -> None:
        """Verifies that _refresh_console_colors updates dictionary-based log_colors on existing formatters."""
        application_logger = self._create_application_logger()

        current_colors = {
            "DEBUG": "cyan",
            "NOTICE": "blue",
        }

        self.log_level_registry.colors = current_colors

        formatter = MagicMock()
        formatter.log_colors = {
            "DEBUG": "green",
        }

        handler = MagicMock(
            spec=logging.Handler,
        )

        handler.formatter = formatter

        self.logger.handlers = [
            handler,
        ]

        application_logger._refresh_console_colors()

        self.assertEqual(
            formatter.log_colors,
            {
                "DEBUG": "cyan",
                "NOTICE": "blue",
            },
            ("Expected _refresh_console_colors() to merge the current " "registry colors into formatter.log_colors."),
        )

    def test_refresh_console_colors_skips_handler_without_formatter(
        self,
    ) -> None:
        """Verifies that _refresh_console_colors safely skips handlers that do not have a formatter."""
        application_logger = self._create_application_logger()

        self.log_level_registry.colors = {
            "NOTICE": "blue",
        }

        handler = MagicMock(
            spec=logging.Handler,
        )

        handler.formatter = None

        self.logger.handlers = [
            handler,
        ]

        application_logger._refresh_console_colors()

        self.assertIsNone(
            handler.formatter,
            ("Expected a handler without a formatter to remain unchanged " "during console color refresh."),
        )

    def test_refresh_console_colors_skips_formatter_without_log_colors(
        self,
    ) -> None:
        """Verifies that _refresh_console_colors safely ignores formatters that do not expose log_colors."""
        application_logger = self._create_application_logger()

        self.log_level_registry.colors = {
            "NOTICE": "blue",
        }

        formatter = logging.Formatter(
            "%(message)s",
        )

        handler = MagicMock(
            spec=logging.Handler,
        )

        handler.formatter = formatter

        self.logger.handlers = [
            handler,
        ]

        application_logger._refresh_console_colors()

        self.assertFalse(
            hasattr(
                formatter,
                "log_colors",
            ),
            ("Expected a standard logging.Formatter not to gain a " "log_colors attribute during refresh."),
        )

    def test_refresh_console_colors_skips_non_dictionary_log_colors(
        self,
    ) -> None:
        """Verifies that _refresh_console_colors ignores formatter log_colors values that are not dictionaries."""
        application_logger = self._create_application_logger()

        self.log_level_registry.colors = {
            "NOTICE": "blue",
        }

        formatter = MagicMock()
        formatter.log_colors = (
            "DEBUG",
            "INFO",
        )

        handler = MagicMock(
            spec=logging.Handler,
        )

        handler.formatter = formatter

        self.logger.handlers = [
            handler,
        ]

        application_logger._refresh_console_colors()

        self.assertEqual(
            formatter.log_colors,
            (
                "DEBUG",
                "INFO",
            ),
            ("Expected non-dictionary log_colors values to remain " "unchanged during refresh."),
        )

    def test_refresh_console_colors_updates_all_compatible_handlers(
        self,
    ) -> None:
        """Verifies that _refresh_console_colors updates every handler whose formatter exposes dictionary-based log colors."""
        application_logger = self._create_application_logger()

        current_colors = {
            "NOTICE": "blue",
        }

        self.log_level_registry.colors = current_colors

        first_formatter = MagicMock()
        first_formatter.log_colors = {}

        second_formatter = MagicMock()
        second_formatter.log_colors = {
            "DEBUG": "cyan",
        }

        first_handler = MagicMock(
            spec=logging.Handler,
        )

        first_handler.formatter = first_formatter

        second_handler = MagicMock(
            spec=logging.Handler,
        )

        second_handler.formatter = second_formatter

        self.logger.handlers = [
            first_handler,
            second_handler,
        ]

        application_logger._refresh_console_colors()

        self.assertEqual(
            first_formatter.log_colors,
            {
                "NOTICE": "blue",
            },
            ("Expected the first compatible formatter to receive the " "current registry colors."),
        )

        self.assertEqual(
            second_formatter.log_colors,
            {
                "DEBUG": "cyan",
                "NOTICE": "blue",
            },
            ("Expected the second compatible formatter to receive the " "current registry colors without losing existing entries."),
        )


    @patch.object(
        ApplicationLogger,
        "_refresh_console_colors",
    )
    def test_add_log_level_rejects_names_that_clash_with_logger_attributes(
        self,
        refresh_console_colors_mock: MagicMock,
    ) -> None:
        """Verifies that add_log_level rejects level names matching existing ApplicationLogger attributes."""
        application_logger = self._create_application_logger()

        clashing_level_names = [
            "SHUTDOWN",
            "LOG",
            "EXCEPTION",
            "add_log_level",
            "Info",
        ]

        for clashing_level_name in clashing_level_names:
            with self.subTest(
                level_name=clashing_level_name,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    f"Log level name '{clashing_level_name}' conflicts",
                    msg=(f"Expected add_log_level() to reject '{clashing_level_name}' " "because it matches an existing ApplicationLogger attribute."),
                ):
                    application_logger.add_log_level(
                        name=clashing_level_name,
                        color="blue",
                        severity=35,
                    )

        self.log_level_registry.register.assert_not_called()
        refresh_console_colors_mock.assert_not_called()
        
        
    def test_dynamic_lookup_rejects_private_names_without_recursion(
        self,
    ) -> None:
        """Verifies that underscore attribute lookups fail fast instead of recursing through the registry."""
        uninitialized_application_logger = ApplicationLogger.__new__(
            ApplicationLogger,
        )

        with self.assertRaises(
            AttributeError,
            msg="Expected a private attribute lookup on an uninitialized logger to raise AttributeError.",
        ):
            getattr(
                uninitialized_application_logger,
                "_log_level_registry",
            )

        application_logger = self._create_application_logger()

        copied_application_logger = copy.copy(
            application_logger,
        )

        self.assertIsInstance(
            copied_application_logger,
            ApplicationLogger,
            "Expected copy.copy() to complete without RecursionError.",
        )
        
    def test_new_log_file_warning_is_attributed_to_caller_outside_spectralog(
        self,
    ) -> None:
        """Verifies that the new-log-file warning points at the external call site, not SpectraLog internals."""
        captured_records: list[logging.LogRecord] = []

        class CapturingHandler(logging.Handler):
            def emit(
                self,
                record: logging.LogRecord,
            ) -> None:
                captured_records.append(
                    record,
                )

        real_logger = logging.getLogger(
            "spectralog.tests.new_log_file_stacklevel",
        )

        real_logger.handlers = [
            CapturingHandler(),
        ]

        real_logger.setLevel(
            logging.DEBUG,
        )

        real_logger.propagate = False

        self.logger = real_logger

        logger_build_result = self._create_build_result(
            log_file_path=Path(
                "/tmp/application.log",
            ),
            is_new_log_file=True,
        )

        self._create_application_logger(
            logger_build_result=logger_build_result,
        )

        self.assertEqual(
            len(captured_records),
            1,
            "Expected exactly one new-log-file warning to be emitted.",
        )

        warning_record = captured_records[0]

        self.assertEqual(
            warning_record.getMessage(),
            "New log file created: application.log",
            "Expected the captured record to be the new-log-file warning.",
        )

        self.assertEqual(
            Path(warning_record.pathname).resolve(),
            Path(__file__).resolve(),
            (
                "Expected the warning to be attributed to the caller outside the "
                f"spectralog package, but it pointed at {warning_record.pathname}:{warning_record.lineno}."
            ),
        )

        real_logger.handlers = []