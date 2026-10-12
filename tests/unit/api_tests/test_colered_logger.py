from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


from spectralog.api.colored_logger import CreateSpectraLogger  # noqa: E402
from spectralog.api.colored_logger import get_logger  # noqa: E402
from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.configuration.json_logger_configuration import JsonLoggerConfiguration  # noqa: E402
from spectralog.configuration.rich_console_configuration import RichConsoleConfiguration  # noqa: E402
from spectralog.configuration.syslog_configuration import SyslogConfiguration  # noqa: E402
from spectralog.core.builder import ApplicationLoggerBuilder  # noqa: E402
from spectralog.core.factory import ApplicationLoggerBuilderFactory  # noqa: E402
from spectralog.core.logger import ApplicationLogger  # noqa: E402
from spectralog.levels.log_level_registry import LogLevelRegistry  # noqa: E402


class UnitTestColoredLogger(unittest.TestCase):
    
    def setUp(self):
        environment_patcher = patch.dict(os.environ, clear=False)
        environment_patcher.start()
        self.addCleanup(environment_patcher.stop)

        store_patcher = patch(
            "spectralog.api.colored_logger._store_configuration_for_child_processes"
        )
        self.mock_store_configuration = store_patcher.start()
        self.addCleanup(store_patcher.stop)
    
    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_constructs_configuration_with_default_values(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger constructs LoggerConfiguration using the public API default values."""
        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        logger_configuration_class_mock.assert_called_once_with(
            debug_mode=False,
            show_datetime=True,
            show_line=False,
            show_folder_name=False,
            logs_directory="logs",
            log_file_name=None,
            save_logs=True,
            multiprocessing_safe=False,
            syslog_configuration=None,
            rich_console_configuration=None,
            json_logger_configuration=None,
            console_format=None,
            file_format=None,
            date_format="%Y-%m-%d %H:%M:%S",
            max_bytes=20 * (1024**2),
            backup_count=1,
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_forwards_all_supplied_configuration_values(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger forwards every supplied public API option to LoggerConfiguration."""
        logs_directory = Path(
            "/var/log/spectralog",
        )

        syslog_configuration = SyslogConfiguration()

        rich_console_configuration = RichConsoleConfiguration()

        json_logger_configuration = JsonLoggerConfiguration()

        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger(
            debug_mode=True,
            show_datetime=False,
            show_line=True,
            show_folder_name=True,
            logs_directory=logs_directory,
            log_file_name="application.log",
            save_logs=False,
            multiprocessing_safe=True,
            syslog_configuration=syslog_configuration,
            rich_console_configuration=rich_console_configuration,
            json_logger_configuration=json_logger_configuration,
            console_format="CONSOLE FORMAT",
            file_format="FILE FORMAT",
            date_format="%d/%m/%Y %H:%M:%S",
            max_bytes=4096,
            backup_count=7,
        )

        logger_configuration_class_mock.assert_called_once_with(
            debug_mode=True,
            show_datetime=False,
            show_line=True,
            show_folder_name=True,
            logs_directory=logs_directory,
            log_file_name="application.log",
            save_logs=False,
            multiprocessing_safe=True,
            syslog_configuration=syslog_configuration,
            rich_console_configuration=rich_console_configuration,
            json_logger_configuration=json_logger_configuration,
            console_format="CONSOLE FORMAT",
            file_format="FILE FORMAT",
            date_format="%d/%m/%Y %H:%M:%S",
            max_bytes=4096,
            backup_count=7,
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    def test_create_spectra_logger_constructs_log_level_registry(
        self,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger constructs a LogLevelRegistry for the logger instance."""
        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        log_level_registry_class_mock.assert_called_once_with()

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    def test_create_spectra_logger_constructs_builder_factory_with_registry(
        self,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger supplies the newly created LogLevelRegistry to ApplicationLoggerBuilderFactory."""
        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        application_logger_builder_factory_class_mock.assert_called_once_with(
            log_level_registry=log_level_registry,
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_creates_builder_with_constructed_configuration(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger creates the logger builder using the exact constructed configuration."""
        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        logger_builder_factory.create.assert_called_once_with(
            configuration=configuration,
            worker_log_record_queue=None,
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    def test_create_spectra_logger_initializes_application_logger_with_builder_and_registry(
        self,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger initializes ApplicationLogger with the created builder and registry."""
        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        get_instance_mock.assert_called_once_with(
            logger_builder=logger_builder,
            log_level_registry=log_level_registry,
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    def test_create_spectra_logger_returns_application_logger_instance(
        self,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger returns the exact ApplicationLogger instance produced by get_instance."""
        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        created_application_logger = CreateSpectraLogger()

        self.assertIs(
            created_application_logger,
            application_logger,
            ("Expected CreateSpectraLogger() to return the exact " "ApplicationLogger instance produced by get_instance()."),
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_uses_same_registry_for_builder_factory_and_application_logger(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that the same LogLevelRegistry instance is shared between the builder graph and ApplicationLogger."""
        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        builder_factory_registry = application_logger_builder_factory_class_mock.call_args.kwargs["log_level_registry"]

        application_logger_registry = get_instance_mock.call_args.kwargs["log_level_registry"]

        self.assertIs(
            builder_factory_registry,
            log_level_registry,
            ("Expected ApplicationLoggerBuilderFactory to receive the " "exact LogLevelRegistry created by CreateSpectraLogger()."),
        )

        self.assertIs(
            application_logger_registry,
            log_level_registry,
            ("Expected ApplicationLogger.get_instance() to receive the " "same LogLevelRegistry used by the builder factory."),
        )

        self.assertIs(
            builder_factory_registry,
            application_logger_registry,
            ("Expected the builder factory and ApplicationLogger to " "share one LogLevelRegistry instance."),
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    def test_get_logger_requests_existing_application_logger_without_reconfiguration(
        self,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that get_logger retrieves ApplicationLogger without supplying reconfiguration dependencies."""
        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        get_instance_mock.return_value = application_logger

        get_logger()

        get_instance_mock.assert_called_once_with()

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    def test_get_logger_returns_existing_application_logger(
        self,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that get_logger returns the exact singleton instance produced by ApplicationLogger.get_instance."""
        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        get_instance_mock.return_value = application_logger

        returned_application_logger = get_logger()

        self.assertIs(
            returned_application_logger,
            application_logger,
            ("Expected get_logger() to return the exact ApplicationLogger " "instance produced by ApplicationLogger.get_instance()."),
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_constructs_dependencies_in_expected_order(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that CreateSpectraLogger composes configuration, registry, builder factory, builder, and singleton in the expected order."""
        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        parent_mock = MagicMock()

        parent_mock.attach_mock(
            logger_configuration_class_mock,
            "logger_configuration",
        )

        parent_mock.attach_mock(
            log_level_registry_class_mock,
            "log_level_registry",
        )

        parent_mock.attach_mock(
            application_logger_builder_factory_class_mock,
            "logger_builder_factory",
        )

        parent_mock.attach_mock(
            logger_builder_factory.create,
            "create_builder",
        )

        parent_mock.attach_mock(
            get_instance_mock,
            "get_instance",
        )

        CreateSpectraLogger()

        expected_method_names = [
            "logger_configuration",
            "log_level_registry",
            "logger_builder_factory",
            "create_builder",
            "get_instance",
        ]

        actual_method_names = [method_call[0] for method_call in parent_mock.mock_calls if method_call[0] in expected_method_names]

        self.assertEqual(
            actual_method_names,
            expected_method_names,
            ("Expected CreateSpectraLogger() to construct and connect " "its dependency graph in the defined order."),
        )

    def test_create_spectra_logger_accepts_path_logs_directory(
        self,
    ) -> None:
        """Verifies that the public creator accepts a pathlib.Path as the logs directory."""
        logs_directory = Path(
            "custom-logs",
        )

        with patch(
            "spectralog.api.colored_logger.LoggerConfiguration",
        ) as logger_configuration_class_mock:
            with patch(
                "spectralog.api.colored_logger.LogLevelRegistry",
            ) as log_level_registry_class_mock:
                with patch(
                    "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
                ) as application_logger_builder_factory_class_mock:
                    with patch(
                        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
                    ) as get_instance_mock:
                        configuration = MagicMock(
                            spec=LoggerConfiguration,
                        )

                        log_level_registry = MagicMock(
                            spec=LogLevelRegistry,
                        )

                        logger_builder_factory = MagicMock(
                            spec=ApplicationLoggerBuilderFactory,
                        )

                        logger_builder = MagicMock(
                            spec=ApplicationLoggerBuilder,
                        )

                        application_logger = MagicMock(
                            spec=ApplicationLogger,
                        )

                        logger_configuration_class_mock.return_value = configuration
                        log_level_registry_class_mock.return_value = log_level_registry
                        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
                        logger_builder_factory.create.return_value = logger_builder
                        get_instance_mock.return_value = application_logger

                        CreateSpectraLogger(
                            logs_directory=logs_directory,
                        )

        supplied_logs_directory = logger_configuration_class_mock.call_args.kwargs["logs_directory"]

        self.assertIs(
            supplied_logs_directory,
            logs_directory,
            ("Expected CreateSpectraLogger() to forward the exact Path " "instance supplied as logs_directory."),
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    @patch(
        "spectralog.api.colored_logger.LoggerConfiguration",
    )
    def test_create_spectra_logger_preserves_configuration_object_identity_through_builder_creation(
        self,
        logger_configuration_class_mock: MagicMock,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that the exact LoggerConfiguration returned by its constructor is passed to builder creation."""
        configuration = MagicMock(
            spec=LoggerConfiguration,
        )

        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        logger_configuration_class_mock.return_value = configuration
        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        supplied_configuration = logger_builder_factory.create.call_args.kwargs["configuration"]

        self.assertIs(
            supplied_configuration,
            configuration,
            ("Expected the builder factory to receive the exact " "LoggerConfiguration instance created by CreateSpectraLogger()."),
        )

    @patch(
        "spectralog.api.colored_logger.ApplicationLogger.get_instance",
    )
    @patch(
        "spectralog.api.colored_logger.ApplicationLoggerBuilderFactory",
    )
    @patch(
        "spectralog.api.colored_logger.LogLevelRegistry",
    )
    def test_create_spectra_logger_preserves_builder_object_identity_for_singleton_initialization(
        self,
        log_level_registry_class_mock: MagicMock,
        application_logger_builder_factory_class_mock: MagicMock,
        get_instance_mock: MagicMock,
    ) -> None:
        """Verifies that the exact builder produced by the factory is supplied to ApplicationLogger.get_instance."""
        log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        logger_builder_factory = MagicMock(
            spec=ApplicationLoggerBuilderFactory,
        )

        logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger = MagicMock(
            spec=ApplicationLogger,
        )

        log_level_registry_class_mock.return_value = log_level_registry
        application_logger_builder_factory_class_mock.return_value = logger_builder_factory
        logger_builder_factory.create.return_value = logger_builder
        get_instance_mock.return_value = application_logger

        CreateSpectraLogger()

        supplied_logger_builder = get_instance_mock.call_args.kwargs["logger_builder"]

        self.assertIs(
            supplied_logger_builder,
            logger_builder,
            ("Expected ApplicationLogger.get_instance() to receive the " "exact builder created by ApplicationLoggerBuilderFactory."),
        )
