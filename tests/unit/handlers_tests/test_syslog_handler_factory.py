from __future__ import annotations

import logging
import socket
import sys
import unittest
from logging.handlers import SysLogHandler
from pathlib import Path
from unittest.mock import ANY
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa

from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.configuration.syslog_configuration import SyslogConfiguration  # noqa: E402
from spectralog.core.log_routing import SPECTRALOG_CONSOLE_ATTRIBUTE  # noqa: E402
from spectralog.core.log_routing import SPECTRALOG_FILE_ATTRIBUTE  # noqa: E402
from spectralog.core.protocols import LoggerFormatterFactoryProtocol  # noqa: E402
from spectralog.handlers.syslog_handler_factory import SyslogHandlerFactory  # noqa: E402
from spectralog.handlers.syslog_handler_factory import SyslogRoutingFilter  # noqa: E402
from spectralog.formatting.relative_path_filter import RelativePathFilter  # noqa: E402


class UnitTestSyslogHandlerFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = logging.Formatter(
            "%(levelname)s | %(message)s",
        )

        self.formatter_factory = MagicMock(
            spec=LoggerFormatterFactoryProtocol,
        )

        self.formatter_factory.create_file_formatter.return_value = self.formatter

        self.relative_path_filter = MagicMock(
            spec=RelativePathFilter,
        )

        self.syslog_handler_factory = SyslogHandlerFactory(
            formatter_factory=self.formatter_factory,
            relative_path_filter=self.relative_path_filter,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_returns_configured_syslog_handler(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create returns the SysLogHandler instance produced by the handler constructor."""
        logger_configuration = LoggerConfiguration(
            debug_mode=False,
        )

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
            facility=SysLogHandler.LOG_USER,
            socket_type=socket.SOCK_DGRAM,
        )

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        created_handler = self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        self.assertIs(
            created_handler,
            syslog_handler,
            ("Expected create() to return the same SysLogHandler instance " "created by the SysLogHandler constructor."),
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_requests_file_formatter_using_logger_configuration(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create obtains the syslog formatter from the formatter factory using the supplied logger configuration."""
        logger_configuration = LoggerConfiguration(
            debug_mode=True,
        )

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
        )

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        self.formatter_factory.create_file_formatter.assert_called_once_with(
            logger_configuration,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_constructs_syslog_handler_with_configured_address(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes the configured host and port to the SysLogHandler constructor."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration(
            host="127.0.0.1",
            port=1514,
            facility=SysLogHandler.LOG_USER,
            socket_type=socket.SOCK_DGRAM,
        )

        syslog_handler_class_mock.return_value = MagicMock(
            spec=logging.Handler,
        )

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler_class_mock.assert_called_once_with(
            address=(
                syslog_configuration.host,
                syslog_configuration.port,
            ),
            facility=syslog_configuration.facility,
            socktype=syslog_configuration.socket_type,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_constructs_syslog_handler_with_configured_facility(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes the configured facility to the SysLogHandler constructor."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
            facility=SysLogHandler.LOG_LOCAL0,
            socket_type=socket.SOCK_DGRAM,
        )

        syslog_handler_class_mock.return_value = MagicMock(
            spec=logging.Handler,
        )

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler_class_mock.assert_called_once_with(
            address=(
                syslog_configuration.host,
                syslog_configuration.port,
            ),
            facility=SysLogHandler.LOG_LOCAL0,
            socktype=syslog_configuration.socket_type,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_constructs_syslog_handler_with_udp_socket_type(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes a configured UDP socket type to the SysLogHandler constructor."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
            facility=SysLogHandler.LOG_USER,
            socket_type=socket.SOCK_DGRAM,
        )

        syslog_handler_class_mock.return_value = MagicMock(
            spec=logging.Handler,
        )

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler_class_mock.assert_called_once_with(
            address=(
                syslog_configuration.host,
                syslog_configuration.port,
            ),
            facility=syslog_configuration.facility,
            socktype=socket.SOCK_DGRAM,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_constructs_syslog_handler_with_tcp_socket_type(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create passes a configured TCP socket type to the SysLogHandler constructor."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
            facility=SysLogHandler.LOG_USER,
            socket_type=socket.SOCK_STREAM,
        )

        syslog_handler_class_mock.return_value = MagicMock(
            spec=logging.Handler,
        )

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler_class_mock.assert_called_once_with(
            address=(
                syslog_configuration.host,
                syslog_configuration.port,
            ),
            facility=syslog_configuration.facility,
            socktype=socket.SOCK_STREAM,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_sets_info_level_when_debug_mode_is_disabled(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the syslog handler at INFO level when debug mode is disabled."""
        logger_configuration = LoggerConfiguration(
            debug_mode=False,
        )

        syslog_configuration = SyslogConfiguration()

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler.setLevel.assert_called_once_with(
            logging.INFO,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_sets_debug_level_when_debug_mode_is_enabled(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the syslog handler at DEBUG level when debug mode is enabled."""
        logger_configuration = LoggerConfiguration(
            debug_mode=True,
        )

        syslog_configuration = SyslogConfiguration()

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler.setLevel.assert_called_once_with(
            logging.DEBUG,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_sets_formatter_returned_by_formatter_factory(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create assigns the formatter returned by the formatter factory to the syslog handler."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration()

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler.setFormatter.assert_called_once_with(
            self.formatter,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_configures_handler_in_expected_order(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create configures the level, formatter, routing filter, and relative path filter in the expected order."""
        logger_configuration = LoggerConfiguration(
            debug_mode=True,
        )

        syslog_configuration = SyslogConfiguration()

        syslog_handler = MagicMock(
            spec=logging.Handler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        expected_method_calls = [
            call.setLevel(
                logging.DEBUG,
            ),
            call.setFormatter(
                self.formatter,
            ),
            call.addFilter(
                ANY,
            ),
            call.addFilter(
                self.relative_path_filter,
            ),
        ]

        self.assertEqual(
            syslog_handler.method_calls,
            expected_method_calls,
            ("Expected the syslog handler to be configured in the order " "setLevel(), setFormatter(), routing addFilter(), then relative path addFilter()."),
        )

        self.assertIsInstance(
            syslog_handler.method_calls[2].args[0],
            SyslogRoutingFilter,
            "Expected the first filter attached to the syslog handler to be a SyslogRoutingFilter.",
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_adds_relative_path_filter(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create attaches the supplied RelativePathFilter to the syslog handler."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration(
            host="localhost",
            port=514,
            socket_type=socket.SOCK_DGRAM,
        )

        syslog_handler = MagicMock(
            spec=SysLogHandler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        syslog_handler.addFilter.assert_any_call(
            self.relative_path_filter,
        )

    @patch(
        "spectralog.handlers.syslog_handler_factory.SysLogHandler",
    )
    def test_create_adds_syslog_routing_filter(
        self,
        syslog_handler_class_mock: MagicMock,
    ) -> None:
        """Verifies that create attaches a SyslogRoutingFilter to the syslog handler."""
        logger_configuration = LoggerConfiguration()

        syslog_configuration = SyslogConfiguration()

        syslog_handler = MagicMock(
            spec=SysLogHandler,
        )

        syslog_handler_class_mock.return_value = syslog_handler

        self.syslog_handler_factory.create(
            logger_configuration=logger_configuration,
            syslog_configuration=syslog_configuration,
        )

        attached_filters = [attached_filter_call.args[0] for attached_filter_call in syslog_handler.addFilter.call_args_list]

        self.assertTrue(
            any(isinstance(attached_filter, SyslogRoutingFilter) for attached_filter in attached_filters),
            "Expected create() to attach a SyslogRoutingFilter to the syslog handler.",
        )


class UnitTestSyslogRoutingFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.syslog_routing_filter = SyslogRoutingFilter()

    def _create_record(
        self,
        **routing_attributes: bool,
    ) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="message",
            args=None,
            exc_info=None,
        )

        for attribute_name, attribute_value in routing_attributes.items():
            setattr(
                record,
                attribute_name,
                attribute_value,
            )

        created_record = record

        return created_record

    def test_filter_rejects_record_with_console_and_file_disabled(
        self,
    ) -> None:
        """Verifies that records routed away from both console and file are not sent to syslog."""
        record = self._create_record(
            **{
                SPECTRALOG_CONSOLE_ATTRIBUTE: False,
                SPECTRALOG_FILE_ATTRIBUTE: False,
            },
        )

        self.assertFalse(
            self.syslog_routing_filter.filter(record),
            "Expected a record with console=False and file=False to be rejected for syslog.",
        )

    def test_filter_accepts_record_with_single_destination_enabled(
        self,
    ) -> None:
        """Verifies that records with at least one enabled destination are sent to syslog."""
        routing_combinations = [
            (True, False),
            (False, True),
            (True, True),
        ]

        for console_enabled, file_enabled in routing_combinations:
            with self.subTest(
                console=console_enabled,
                file=file_enabled,
            ):
                record = self._create_record(
                    **{
                        SPECTRALOG_CONSOLE_ATTRIBUTE: console_enabled,
                        SPECTRALOG_FILE_ATTRIBUTE: file_enabled,
                    },
                )

                self.assertTrue(
                    self.syslog_routing_filter.filter(record),
                    "Expected a record with at least one enabled destination to be accepted for syslog.",
                )

    def test_filter_accepts_record_without_routing_metadata(
        self,
    ) -> None:
        """Verifies that records emitted without SpectraLog routing metadata are sent to syslog."""
        record = self._create_record()

        self.assertTrue(
            self.syslog_routing_filter.filter(record),
            "Expected a record without routing metadata to be accepted for syslog.",
        )