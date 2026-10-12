from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa

from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.core.builder import ApplicationLoggerBuilder  # noqa: E402
from spectralog.core.factory import ApplicationLoggerBuilderFactory  # noqa: E402
from spectralog.files.log_file_path_resolver import LogFilePathResolver  # noqa: E402
from spectralog.formatting.file_formatter_resolver import FileFormatterResolver  # noqa: E402
from spectralog.formatting.format_builder import LogFormatBuilder  # noqa: E402
from spectralog.formatting.formatter_factory import LoggerFormatterFactory  # noqa: E402
from spectralog.formatting.json_file_formatter_strategy import JsonFileFormatterStrategy  # noqa: E402
from spectralog.formatting.json_logger_formatter_factory import JsonLoggerFormatterFactory  # noqa: E402
from spectralog.formatting.plain_text_file_formatter_strategy import PlainTextFileFormatterStrategy  # noqa: E402
from spectralog.formatting.relative_path_filter import RelativePathFilter  # noqa: E402
from spectralog.handlers.console_handler_factory import ConsoleHandlerFactory  # noqa: E402
from spectralog.handlers.file_handler_factory import FileHandlerFactory  # noqa: E402
from spectralog.handlers.multiprocessing_handler_factory import MultiprocessingHandlerFactory  # noqa: E402
from spectralog.handlers.queue_file_handler_factory import QueueFileHandlerFactory  # noqa: E402
from spectralog.handlers.rich_console_handler_factory import RichConsoleHandlerFactory  # noqa: E402
from spectralog.handlers.syslog_handler_factory import SyslogHandlerFactory  # noqa: E402
from spectralog.levels.log_level_registry import LogLevelRegistry  # noqa: E402


class UnitTestApplicationLoggerBuilderFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.log_level_registry = MagicMock(
            spec=LogLevelRegistry,
        )

        self.application_logger_builder_factory = ApplicationLoggerBuilderFactory(
            log_level_registry=self.log_level_registry,
        )

    @patch(
        "spectralog.core.factory.ApplicationLoggerBuilder",
    )
    @patch(
        "spectralog.core.factory.LogFilePathResolver",
    )
    @patch(
        "spectralog.core.factory.SyslogHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.MultiprocessingHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.QueueFileHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.FileHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.RichConsoleHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.ConsoleHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.FileFormatterResolver",
    )
    @patch(
        "spectralog.core.factory.JsonFileFormatterStrategy",
    )
    @patch(
        "spectralog.core.factory.PlainTextFileFormatterStrategy",
    )
    @patch(
        "spectralog.core.factory.JsonLoggerFormatterFactory",
    )
    @patch(
        "spectralog.core.factory.LoggerFormatterFactory",
    )
    @patch(
        "spectralog.core.factory.RelativePathFilter",
    )
    @patch(
        "spectralog.core.factory.LogFormatBuilder",
    )
    def test_create_returns_created_application_logger_builder(
        self,
        log_format_builder_class_mock: MagicMock,
        relative_path_filter_class_mock: MagicMock,
        logger_formatter_factory_class_mock: MagicMock,
        json_logger_formatter_factory_class_mock: MagicMock,
        plain_text_file_formatter_strategy_class_mock: MagicMock,
        json_file_formatter_strategy_class_mock: MagicMock,
        file_formatter_resolver_class_mock: MagicMock,
        console_handler_factory_class_mock: MagicMock,
        rich_console_handler_factory_class_mock: MagicMock,
        file_handler_factory_class_mock: MagicMock,
        queue_file_handler_factory_class_mock: MagicMock,
        multiprocessing_handler_factory_class_mock: MagicMock,
        syslog_handler_factory_class_mock: MagicMock,
        log_file_path_resolver_class_mock: MagicMock,
        application_logger_builder_class_mock: MagicMock,
    ) -> None:
        """Verifies that create returns the ApplicationLoggerBuilder instance produced by the builder constructor."""
        configuration = LoggerConfiguration()

        application_logger_builder = MagicMock(
            spec=ApplicationLoggerBuilder,
        )

        application_logger_builder_class_mock.return_value = application_logger_builder

        created_builder = self.application_logger_builder_factory.create(
            configuration=configuration,
        )

        self.assertIs(
            created_builder,
            application_logger_builder,
            ("Expected create() to return the exact ApplicationLoggerBuilder " "instance produced by the builder constructor."),
        )

    @patch(
        "spectralog.core.factory.LogFormatBuilder",
    )
    def test_create_constructs_log_format_builder(
        self,
        log_format_builder_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a LogFormatBuilder."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        log_format_builder_class_mock.assert_called_once_with()

    @patch(
        "spectralog.core.factory.RelativePathFilter",
    )
    def test_create_constructs_relative_path_filter(
        self,
        relative_path_filter_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a RelativePathFilter shared by handlers requiring relative paths."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        relative_path_filter_class_mock.assert_called_once_with()

    @patch(
        "spectralog.core.factory.LoggerFormatterFactory",
    )
    def test_create_constructs_logger_formatter_factory_with_dependencies(
        self,
        logger_formatter_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs LoggerFormatterFactory with the format builder and log level registry."""
        configuration = LoggerConfiguration()

        format_builder = MagicMock(
            spec=LogFormatBuilder,
        )

        with patch(
            "spectralog.core.factory.LogFormatBuilder",
            return_value=format_builder,
        ):
            with patch(
                "spectralog.core.factory.ApplicationLoggerBuilder",
            ):
                self.application_logger_builder_factory.create(
                    configuration=configuration,
                )

        logger_formatter_factory_class_mock.assert_called_once_with(
            format_builder=format_builder,
            log_level_registry=self.log_level_registry,
        )

    @patch(
        "spectralog.core.factory.JsonLoggerFormatterFactory",
    )
    def test_create_constructs_json_logger_formatter_factory(
        self,
        json_logger_formatter_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a JsonLoggerFormatterFactory."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        json_logger_formatter_factory_class_mock.assert_called_once_with()

    @patch(
        "spectralog.core.factory.PlainTextFileFormatterStrategy",
    )
    def test_create_constructs_plain_text_strategy_with_formatter_factory(
        self,
        plain_text_file_formatter_strategy_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs the plain-text file formatter strategy with the logger formatter factory."""
        configuration = LoggerConfiguration()

        formatter_factory = MagicMock(
            spec=LoggerFormatterFactory,
        )

        with patch(
            "spectralog.core.factory.LoggerFormatterFactory",
            return_value=formatter_factory,
        ):
            with patch(
                "spectralog.core.factory.ApplicationLoggerBuilder",
            ):
                self.application_logger_builder_factory.create(
                    configuration=configuration,
                )

        plain_text_file_formatter_strategy_class_mock.assert_called_once_with(
            formatter_factory=formatter_factory,
        )

    @patch(
        "spectralog.core.factory.JsonFileFormatterStrategy",
    )
    def test_create_constructs_json_strategy_with_json_formatter_factory(
        self,
        json_file_formatter_strategy_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs the JSON file formatter strategy with the JSON formatter factory."""
        configuration = LoggerConfiguration()

        json_formatter_factory = MagicMock(
            spec=JsonLoggerFormatterFactory,
        )

        with patch(
            "spectralog.core.factory.JsonLoggerFormatterFactory",
            return_value=json_formatter_factory,
        ):
            with patch(
                "spectralog.core.factory.ApplicationLoggerBuilder",
            ):
                self.application_logger_builder_factory.create(
                    configuration=configuration,
                )

        json_file_formatter_strategy_class_mock.assert_called_once_with(
            json_formatter_factory=json_formatter_factory,
        )

    @patch(
        "spectralog.core.factory.FileFormatterResolver",
    )
    def test_create_constructs_file_formatter_resolver_with_strategy_order(
        self,
        file_formatter_resolver_class_mock: MagicMock,
    ) -> None:
        """Verifies that create registers JSON formatting before plain-text formatting in the resolver."""
        configuration = LoggerConfiguration()

        json_file_formatter_strategy = MagicMock(
            spec=JsonFileFormatterStrategy,
        )

        plain_text_file_formatter_strategy = MagicMock(
            spec=PlainTextFileFormatterStrategy,
        )

        with patch(
            "spectralog.core.factory.JsonFileFormatterStrategy",
            return_value=json_file_formatter_strategy,
        ):
            with patch(
                "spectralog.core.factory.PlainTextFileFormatterStrategy",
                return_value=plain_text_file_formatter_strategy,
            ):
                with patch(
                    "spectralog.core.factory.ApplicationLoggerBuilder",
                ):
                    self.application_logger_builder_factory.create(
                        configuration=configuration,
                    )

        file_formatter_resolver_class_mock.assert_called_once_with(
            formatter_strategies=(
                json_file_formatter_strategy,
                plain_text_file_formatter_strategy,
            ),
        )

    @patch(
        "spectralog.core.factory.ConsoleHandlerFactory",
    )
    def test_create_constructs_console_handler_factory_with_shared_dependencies(
        self,
        console_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs ConsoleHandlerFactory with the logger formatter factory and shared relative path filter."""
        configuration = LoggerConfiguration()

        formatter_factory = MagicMock(
            spec=LoggerFormatterFactory,
        )

        relative_path_filter = MagicMock(
            spec=RelativePathFilter,
        )

        with patch(
            "spectralog.core.factory.LoggerFormatterFactory",
            return_value=formatter_factory,
        ):
            with patch(
                "spectralog.core.factory.RelativePathFilter",
                return_value=relative_path_filter,
            ):
                with patch(
                    "spectralog.core.factory.ApplicationLoggerBuilder",
                ):
                    self.application_logger_builder_factory.create(
                        configuration=configuration,
                    )

        console_handler_factory_class_mock.assert_called_once_with(
            formatter_factory=formatter_factory,
            relative_path_filter=relative_path_filter,
        )

    @patch(
        "spectralog.core.factory.RichConsoleHandlerFactory",
    )
    def test_create_constructs_rich_console_handler_factory(
        self,
        rich_console_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a RichConsoleHandlerFactory."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        rich_console_handler_factory_class_mock.assert_called_once_with()

    @patch(
        "spectralog.core.factory.FileHandlerFactory",
    )
    def test_create_constructs_file_handler_factory_with_shared_dependencies(
        self,
        file_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs FileHandlerFactory with the file formatter resolver and shared relative path filter."""
        configuration = LoggerConfiguration()

        file_formatter_resolver = MagicMock(
            spec=FileFormatterResolver,
        )

        relative_path_filter = MagicMock(
            spec=RelativePathFilter,
        )

        with patch(
            "spectralog.core.factory.FileFormatterResolver",
            return_value=file_formatter_resolver,
        ):
            with patch(
                "spectralog.core.factory.RelativePathFilter",
                return_value=relative_path_filter,
            ):
                with patch(
                    "spectralog.core.factory.ApplicationLoggerBuilder",
                ):
                    self.application_logger_builder_factory.create(
                        configuration=configuration,
                    )

        file_handler_factory_class_mock.assert_called_once_with(
            file_formatter_resolver=file_formatter_resolver,
            relative_path_filter=relative_path_filter,
        )

    @patch(
        "spectralog.core.factory.QueueFileHandlerFactory",
    )
    def test_create_constructs_queue_file_handler_factory(
        self,
        queue_file_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a QueueFileHandlerFactory."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        queue_file_handler_factory_class_mock.assert_called_once_with()

    @patch(
        "spectralog.core.factory.MultiprocessingHandlerFactory",
    )
    def test_create_constructs_multiprocessing_handler_factory_with_dependencies(
        self,
        multiprocessing_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs MultiprocessingHandlerFactory with queue and file handler factories."""
        configuration = LoggerConfiguration()

        queue_file_handler_factory = MagicMock(
            spec=QueueFileHandlerFactory,
        )

        file_handler_factory = MagicMock(
            spec=FileHandlerFactory,
        )

        with patch(
            "spectralog.core.factory.QueueFileHandlerFactory",
            return_value=queue_file_handler_factory,
        ):
            with patch(
                "spectralog.core.factory.FileHandlerFactory",
                return_value=file_handler_factory,
            ):
                with patch(
                    "spectralog.core.factory.ApplicationLoggerBuilder",
                ):
                    self.application_logger_builder_factory.create(
                        configuration=configuration,
                    )

        multiprocessing_handler_factory_class_mock.assert_called_once_with(
            queue_file_handler_factory=queue_file_handler_factory,
            file_handler_factory=file_handler_factory,
        )

    @patch(
        "spectralog.core.factory.SyslogHandlerFactory",
    )
    def test_create_constructs_syslog_handler_factory_with_shared_dependencies(
        self,
        syslog_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs SyslogHandlerFactory with the logger formatter factory and shared relative path filter."""
        configuration = LoggerConfiguration()

        formatter_factory = MagicMock(
            spec=LoggerFormatterFactory,
        )

        relative_path_filter = MagicMock(
            spec=RelativePathFilter,
        )

        with patch(
            "spectralog.core.factory.LoggerFormatterFactory",
            return_value=formatter_factory,
        ):
            with patch(
                "spectralog.core.factory.RelativePathFilter",
                return_value=relative_path_filter,
            ):
                with patch(
                    "spectralog.core.factory.ApplicationLoggerBuilder",
                ):
                    self.application_logger_builder_factory.create(
                        configuration=configuration,
                    )

        syslog_handler_factory_class_mock.assert_called_once_with(
            formatter_factory=formatter_factory,
            relative_path_filter=relative_path_filter,
        )

    @patch(
        "spectralog.core.factory.LogFilePathResolver",
    )
    def test_create_constructs_log_file_path_resolver(
        self,
        log_file_path_resolver_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs a LogFilePathResolver."""
        configuration = LoggerConfiguration()

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        log_file_path_resolver_class_mock.assert_called_once_with()

   
    @patch(
        "spectralog.core.factory.ApplicationLoggerBuilder",
    )
    def test_create_constructs_application_logger_builder_with_all_dependencies(
        self,
        application_logger_builder_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs ApplicationLoggerBuilder with the complete dependency graph."""
        configuration = LoggerConfiguration()

        console_handler_factory = MagicMock(
            spec=ConsoleHandlerFactory,
        )

        rich_console_handler_factory = MagicMock(
            spec=RichConsoleHandlerFactory,
        )

        file_handler_factory = MagicMock(
            spec=FileHandlerFactory,
        )

        queue_file_handler_factory = MagicMock(
            spec=QueueFileHandlerFactory,
        )

        multiprocessing_handler_factory = MagicMock(
            spec=MultiprocessingHandlerFactory,
        )

        syslog_handler_factory = MagicMock(
            spec=SyslogHandlerFactory,
        )

        log_file_path_resolver = MagicMock(
            spec=LogFilePathResolver,
        )

        with patch(
            "spectralog.core.factory.ConsoleHandlerFactory",
            return_value=console_handler_factory,
        ):
            with patch(
                "spectralog.core.factory.RichConsoleHandlerFactory",
                return_value=rich_console_handler_factory,
            ):
                with patch(
                    "spectralog.core.factory.FileHandlerFactory",
                    return_value=file_handler_factory,
                ):
                    with patch(
                        "spectralog.core.factory.QueueFileHandlerFactory",
                        return_value=queue_file_handler_factory,
                    ):
                        with patch(
                            "spectralog.core.factory.MultiprocessingHandlerFactory",
                            return_value=multiprocessing_handler_factory,
                        ):
                            with patch(
                                "spectralog.core.factory.SyslogHandlerFactory",
                                return_value=syslog_handler_factory,
                            ):
                                with patch(
                                    "spectralog.core.factory.LogFilePathResolver",
                                    return_value=log_file_path_resolver,
                                ):
                                    self.application_logger_builder_factory.create(
                                        configuration=configuration,
                                    )

        application_logger_builder_class_mock.assert_called_once_with(
            configuration=configuration,
            console_handler_factory=console_handler_factory,
            rich_console_handler_factory=rich_console_handler_factory,
            file_handler_factory=file_handler_factory,
            multiprocessing_handler_factory=multiprocessing_handler_factory,
            syslog_handler_factory=syslog_handler_factory,
            log_file_path_resolver=log_file_path_resolver,
            queue_file_handler_factory=queue_file_handler_factory,
            worker_log_record_queue=None,
        )

    @patch(
        "spectralog.core.factory.ApplicationLoggerBuilder",
    )
    def test_create_passes_same_configuration_instance_to_builder(
        self,
        application_logger_builder_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes the exact LoggerConfiguration instance supplied by the caller to ApplicationLoggerBuilder."""
        configuration = LoggerConfiguration(
            debug_mode=True,
            save_logs=False,
        )

        self.application_logger_builder_factory.create(
            configuration=configuration,
        )

        supplied_configuration = application_logger_builder_class_mock.call_args.kwargs["configuration"]

        self.assertIs(
            supplied_configuration,
            configuration,
            ("Expected ApplicationLoggerBuilder to receive the exact " "LoggerConfiguration instance supplied to create()."),
        )

    @patch(
        "spectralog.core.factory.SyslogHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.FileHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.ConsoleHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.RelativePathFilter",
    )
    def test_create_shares_same_relative_path_filter_between_handler_factories(
        self,
        relative_path_filter_class_mock: MagicMock,
        console_handler_factory_class_mock: MagicMock,
        file_handler_factory_class_mock: MagicMock,
        syslog_handler_factory_class_mock: MagicMock,
    ) -> None:
        """Verifies that console, file, and syslog handler factories receive the same RelativePathFilter instance."""
        configuration = LoggerConfiguration()

        relative_path_filter = MagicMock(
            spec=RelativePathFilter,
        )

        relative_path_filter_class_mock.return_value = relative_path_filter

        with patch(
            "spectralog.core.factory.ApplicationLoggerBuilder",
        ):
            self.application_logger_builder_factory.create(
                configuration=configuration,
            )

        console_relative_path_filter = console_handler_factory_class_mock.call_args.kwargs["relative_path_filter"]

        file_relative_path_filter = file_handler_factory_class_mock.call_args.kwargs["relative_path_filter"]

        syslog_relative_path_filter = syslog_handler_factory_class_mock.call_args.kwargs["relative_path_filter"]

        self.assertIs(
            console_relative_path_filter,
            relative_path_filter,
            ("Expected ConsoleHandlerFactory to receive the shared " "RelativePathFilter instance."),
        )

        self.assertIs(
            file_relative_path_filter,
            relative_path_filter,
            ("Expected FileHandlerFactory to receive the shared " "RelativePathFilter instance."),
        )

        self.assertIs(
            syslog_relative_path_filter,
            relative_path_filter,
            ("Expected SyslogHandlerFactory to receive the shared " "RelativePathFilter instance."),
        )

    @patch(
        "spectralog.core.factory.ApplicationLoggerBuilder",
    )
    @patch(
        "spectralog.core.factory.LogFilePathResolver",
    )
    @patch(
        "spectralog.core.factory.SyslogHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.MultiprocessingHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.QueueFileHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.FileHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.RichConsoleHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.ConsoleHandlerFactory",
    )
    @patch(
        "spectralog.core.factory.FileFormatterResolver",
    )
    @patch(
        "spectralog.core.factory.JsonFileFormatterStrategy",
    )
    @patch(
        "spectralog.core.factory.PlainTextFileFormatterStrategy",
    )
    @patch(
        "spectralog.core.factory.JsonLoggerFormatterFactory",
    )
    @patch(
        "spectralog.core.factory.LoggerFormatterFactory",
    )
    @patch(
        "spectralog.core.factory.RelativePathFilter",
    )
    @patch(
        "spectralog.core.factory.LogFormatBuilder",
    )
    def test_create_constructs_dependency_graph_in_expected_order(
        self,
        log_format_builder_class_mock: MagicMock,
        relative_path_filter_class_mock: MagicMock,
        logger_formatter_factory_class_mock: MagicMock,
        json_logger_formatter_factory_class_mock: MagicMock,
        plain_text_file_formatter_strategy_class_mock: MagicMock,
        json_file_formatter_strategy_class_mock: MagicMock,
        file_formatter_resolver_class_mock: MagicMock,
        console_handler_factory_class_mock: MagicMock,
        rich_console_handler_factory_class_mock: MagicMock,
        file_handler_factory_class_mock: MagicMock,
        queue_file_handler_factory_class_mock: MagicMock,
        multiprocessing_handler_factory_class_mock: MagicMock,
        syslog_handler_factory_class_mock: MagicMock,
        log_file_path_resolver_class_mock: MagicMock,
        application_logger_builder_class_mock: MagicMock,
    ) -> None:
        """Verifies that create constructs the dependency graph in the expected composition order."""
        configuration = LoggerConfiguration()

        parent_mock = MagicMock()

        parent_mock.attach_mock(
            log_format_builder_class_mock,
            "log_format_builder",
        )

        parent_mock.attach_mock(
            relative_path_filter_class_mock,
            "relative_path_filter",
        )

        parent_mock.attach_mock(
            logger_formatter_factory_class_mock,
            "logger_formatter_factory",
        )

        parent_mock.attach_mock(
            json_logger_formatter_factory_class_mock,
            "json_logger_formatter_factory",
        )

        parent_mock.attach_mock(
            plain_text_file_formatter_strategy_class_mock,
            "plain_text_strategy",
        )

        parent_mock.attach_mock(
            json_file_formatter_strategy_class_mock,
            "json_strategy",
        )

        parent_mock.attach_mock(
            file_formatter_resolver_class_mock,
            "file_formatter_resolver",
        )

        parent_mock.attach_mock(
            console_handler_factory_class_mock,
            "console_handler_factory",
        )

        parent_mock.attach_mock(
            rich_console_handler_factory_class_mock,
            "rich_console_handler_factory",
        )

        parent_mock.attach_mock(
            file_handler_factory_class_mock,
            "file_handler_factory",
        )

        parent_mock.attach_mock(
            queue_file_handler_factory_class_mock,
            "queue_file_handler_factory",
        )

        parent_mock.attach_mock(
            multiprocessing_handler_factory_class_mock,
            "multiprocessing_handler_factory",
        )

        parent_mock.attach_mock(
            syslog_handler_factory_class_mock,
            "syslog_handler_factory",
        )

        parent_mock.attach_mock(
            log_file_path_resolver_class_mock,
            "log_file_path_resolver",
        )

        parent_mock.attach_mock(
            application_logger_builder_class_mock,
            "application_logger_builder",
        )

        self.application_logger_builder_factory.create(
            configuration=configuration,
        )

        expected_method_names = [
            "log_format_builder",
            "relative_path_filter",
            "logger_formatter_factory",
            "json_logger_formatter_factory",
            "plain_text_strategy",
            "json_strategy",
            "file_formatter_resolver",
            "console_handler_factory",
            "rich_console_handler_factory",
            "file_handler_factory",
            "queue_file_handler_factory",
            "multiprocessing_handler_factory",
            "syslog_handler_factory",
            "log_file_path_resolver",
            "application_logger_builder",
        ]

        actual_method_names = [method_call[0] for method_call in parent_mock.mock_calls if method_call[0] in expected_method_names]

        self.assertEqual(
            actual_method_names,
            expected_method_names,
            ("Expected the dependency graph to be constructed in the " "same order defined by ApplicationLoggerBuilderFactory.create()."),
        )

    def test_create_returns_real_application_logger_builder(
        self,
    ) -> None:
        """Verifies that create returns a real ApplicationLoggerBuilder when dependencies are not mocked."""
        configuration = LoggerConfiguration(
            save_logs=False,
        )

        log_level_registry = LogLevelRegistry()

        application_logger_builder_factory = ApplicationLoggerBuilderFactory(
            log_level_registry=log_level_registry,
        )

        created_builder = application_logger_builder_factory.create(
            configuration=configuration,
        )

        self.assertIsInstance(
            created_builder,
            ApplicationLoggerBuilder,
            ("Expected create() to return a real ApplicationLoggerBuilder " "instance when dependencies are not mocked."),
        )
