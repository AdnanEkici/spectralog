from __future__ import annotations

import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa

from spectralog import CreateSpectraLogger  # noqa: E402
from spectralog import disable_application_logging  # noqa: E402
from spectralog import get_logger  # noqa: E402
from spectralog import silence_application_logging  # noqa: E402
from spectralog.core.logger import ApplicationLogger  # noqa: E402


SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE = "SPECTRALOG_CONFIGURATION"

ORIGINAL_APPLICATION_LOGGER_METHODS = {
    method_name: ApplicationLogger.__dict__[method_name]
    for method_name in (
        "log",
        "debug",
        "info",
        "warning",
        "error",
        "critical",
        "exception",
        "__getattr__",
    )
}


class DummyCustomLevelApplication:
    """Application that registers custom levels in its own logging setup."""

    def __init__(
        self,
        logs_directory: Path,
    ) -> None:
        self._logs_directory = logs_directory

    def initialize_logger(
        self,
    ) -> None:
        logger = CreateSpectraLogger(
            logs_directory=self._logs_directory,
            log_file_name="dummy-custom-level-application.log",
            save_logs=True,
        )

        logger.add_log_level(
            name="SUCCESS",
            color="bold_green",
            severity=25,
        )

        logger.add_log_level(
            name="NOTICE",
            color="purple",
            severity=35,
        )

    def execute(
        self,
    ) -> None:
        logger = get_logger()

        logger.info(
            "Dummy custom level application started",
        )

        logger.success(
            "Dummy custom level application succeeded",
        )

        logger.notice(
            "Dummy custom level application notice",
        )

        logger.log(
            "SUCCESS",
            "Dummy custom level application succeeded through log()",
        )

        logger.error(
            "Dummy custom level application error",
        )


def _create_logs_directory_path(
    temporary_directory: str,
) -> Path:
    logs_directory = (
        Path(
            temporary_directory,
        )
        / "logs"
    )

    return logs_directory


def _assert_application_logger_methods_are_restored(
    test_case: unittest.TestCase,
) -> None:
    for method_name, original_method in ORIGINAL_APPLICATION_LOGGER_METHODS.items():
        test_case.assertIs(
            ApplicationLogger.__dict__[method_name],
            original_method,
            (f"Expected ApplicationLogger.{method_name} to be restored " "to its original implementation."),
        )


class IsolatedApplicationLoggerTestCase(unittest.TestCase):
    """Isolate the ApplicationLogger singleton for tests that use real logging."""

    def setUp(
        self,
    ) -> None:
        self._previous_application_logger_instance = ApplicationLogger._instance
        self._previous_spectralog_configuration = os.environ.get(
            SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE,
        )

        ApplicationLogger._instance = None

    def tearDown(
        self,
    ) -> None:
        current_application_logger_instance = ApplicationLogger._instance

        if current_application_logger_instance is not None:
            current_application_logger_instance.shutdown()

            for handler in list(
                current_application_logger_instance._logger.handlers,
            ):
                current_application_logger_instance._logger.removeHandler(
                    handler,
                )

                handler.close()

        ApplicationLogger._instance = self._previous_application_logger_instance

        if self._previous_spectralog_configuration is None:
            os.environ.pop(
                SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE,
                None,
            )
        else:
            os.environ[SPECTRALOG_CONFIGURATION_ENVIRONMENT_VARIABLE] = self._previous_spectralog_configuration


class IntegrationTestCustomLevelsLoggingEnabled(IsolatedApplicationLoggerTestCase):
    def test_dummy_application_writes_custom_levels_to_log_file(
        self,
    ) -> None:
        """Verifies that custom levels are written to the log file during normal package usage."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            dummy_application = DummyCustomLevelApplication(
                logs_directory=logs_directory,
            )

            dummy_application.initialize_logger()
            dummy_application.execute()

            log_file_path = logs_directory / "dummy-custom-level-application.log"

            self.assertTrue(
                log_file_path.exists(),
                ("Expected normal SpectraLog usage to create the " "dummy custom level application log file."),
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "Dummy custom level application succeeded",
                log_file_contents,
                ("Expected the dummy application's SUCCESS message to " "be written to the log file."),
            )

            self.assertIn(
                "Dummy custom level application notice",
                log_file_contents,
                ("Expected the dummy application's NOTICE message to " "be written to the log file."),
            )

            self.assertIn(
                "Dummy custom level application succeeded through log()",
                log_file_contents,
                ("Expected the SUCCESS message emitted through log() to " "be written to the log file."),
            )

    def test_unregistered_custom_level_method_still_raises_outside_decorators(
        self,
    ) -> None:
        """Verifies that unregistered custom level methods still fail during normal package usage."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            logger = CreateSpectraLogger(
                logs_directory=logs_directory,
                log_file_name="unregistered-custom-level.log",
                save_logs=False,
            )

            with self.assertRaises(
                AttributeError,
                msg=("Expected an unregistered custom level method to raise " "AttributeError outside the logging decorators."),
            ):
                logger.unregistered_level(
                    "This level was never registered",
                )

    def test_unregistered_custom_level_name_still_raises_through_log_outside_decorators(
        self,
    ) -> None:
        """Verifies that log() with an unregistered level name still fails during normal package usage."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            logger = CreateSpectraLogger(
                logs_directory=logs_directory,
                log_file_name="unregistered-custom-level.log",
                save_logs=False,
            )

            with self.assertRaises(
                Exception,
                msg=("Expected log() with an unregistered level name to raise " "outside the logging decorators."),
            ):
                logger.log(
                    "UNREGISTERED_LEVEL",
                    "This level was never registered",
                )


@disable_application_logging
class IntegrationTestCustomLevelsLoggingDisabled(unittest.TestCase):
    def test_custom_level_methods_work_without_explicit_initialization(
        self,
    ) -> None:
        """Verifies that custom level methods work when the application setup registering them never runs."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            dummy_application = DummyCustomLevelApplication(
                logs_directory=logs_directory,
            )

            try:
                dummy_application.execute()
            except Exception as exception:
                self.fail(
                    (
                        "Expected custom level methods to be no-ops while "
                        "logging is disabled, but an exception was raised: "
                        f"{exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected disabled logging to avoid creating the logs " "directory when custom level methods were called."),
            )

    def test_custom_level_methods_work_after_explicit_initialization(
        self,
    ) -> None:
        """Verifies that custom levels registered by explicit initialization can be used while logging is disabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            dummy_application = DummyCustomLevelApplication(
                logs_directory=logs_directory,
            )

            try:
                dummy_application.initialize_logger()
                dummy_application.execute()
            except Exception as exception:
                self.fail(
                    (
                        "Expected explicit initialization with custom levels "
                        "to succeed while logging is disabled, but an "
                        f"exception was raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected disable_application_logging to prevent log file " "creation after custom level registration."),
            )

    def test_custom_levels_can_be_registered_on_fallback_logger(
        self,
    ) -> None:
        """Verifies that add_log_level keeps working on the disabled fallback logger."""
        logger = get_logger()

        try:
            logger.add_log_level(
                name="SUCCESS",
                color="bold_green",
                severity=25,
            )

            logger.success(
                "Registered SUCCESS message is suppressed",
            )
        except Exception as exception:
            self.fail(
                (
                    "Expected add_log_level and the registered custom level "
                    "to work on the disabled fallback logger, but an "
                    f"exception was raised: {exception!r}"
                ),
            )

    def test_custom_level_methods_accept_routing_arguments(
        self,
    ) -> None:
        """Verifies that disabled custom level methods accept message arguments and routing options."""
        logger = get_logger()

        try:
            logger.success(
                "Order %s placed",
                42,
                console=True,
                file=False,
            )

            logger.notice(
                "Persistent notice",
                console=False,
                file=True,
            )

            logger.log(
                "AUDIT_EVENT",
                "Audit event %s",
                "created",
                console=False,
            )
        except Exception as exception:
            self.fail(
                (
                    "Expected disabled custom level methods to accept "
                    "message arguments and routing options, but an "
                    f"exception was raised: {exception!r}"
                ),
            )

    def test_built_in_logging_methods_are_no_ops(
        self,
    ) -> None:
        """Verifies that every built-in logging method can be called while logging is disabled."""
        logger = get_logger()

        try:
            logger.debug(
                "Debug message is suppressed",
            )

            logger.info(
                "Info message is suppressed",
            )

            logger.warning(
                "Warning message is suppressed",
            )

            logger.error(
                "Error message is suppressed",
            )

            logger.critical(
                "Critical message is suppressed",
            )

            logger.log(
                logging.INFO,
                "Numeric severity message is suppressed",
            )

            try:
                raise RuntimeError(
                    "Dummy application failure",
                )
            except RuntimeError:
                logger.exception(
                    "Exception message is suppressed",
                )
        except Exception as exception:
            self.fail(
                (
                    "Expected built-in logging methods to be no-ops while "
                    "logging is disabled, but an exception was raised: "
                    f"{exception!r}"
                ),
            )

    def test_logging_methods_return_none(
        self,
    ) -> None:
        """Verifies that disabled custom level methods return None like the real logging methods."""
        logger = get_logger()

        self.assertIsNone(
            logger.success(
                "SUCCESS message is suppressed",
            ),
            "Expected disabled custom level methods to return None.",
        )

    def test_private_attributes_still_raise_attribute_error(
        self,
    ) -> None:
        """Verifies that private attribute lookups are not converted into no-op logging methods."""
        logger = get_logger()

        with self.assertRaises(
            AttributeError,
            msg=("Expected private attribute lookups to keep raising " "AttributeError while logging is disabled."),
        ):
            getattr(
                logger,
                "_missing_private_attribute",
            )

    def test_logging_methods_are_replaced_while_decorated(
        self,
    ) -> None:
        """Verifies that ApplicationLogger logging methods are replaced inside decorated tests."""
        for method_name, original_method in ORIGINAL_APPLICATION_LOGGER_METHODS.items():
            self.assertIsNot(
                ApplicationLogger.__dict__[method_name],
                original_method,
                (f"Expected ApplicationLogger.{method_name} to be replaced " "while logging is disabled."),
            )


class IntegrationTestDisableApplicationLoggingRestoresMethods(unittest.TestCase):
    def test_logging_methods_are_restored_after_decorated_test_class(
        self,
    ) -> None:
        """Verifies that disable_application_logging restores the real logging methods after the test class."""

        @disable_application_logging
        class DecoratedCustomLevelTest(unittest.TestCase):
            def test_custom_level_is_suppressed(
                self,
            ) -> None:
                get_logger().success(
                    "SUCCESS message is suppressed",
                )

        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            DecoratedCustomLevelTest,
        )

        test_result = unittest.TestResult()

        test_suite.run(
            test_result,
        )

        self.assertTrue(
            test_result.wasSuccessful(),
            (f"Expected the decorated test class to succeed, but it reported " f"{test_result.errors + test_result.failures!r}."),
        )

        _assert_application_logger_methods_are_restored(
            self,
        )

    def test_logging_methods_are_restored_when_set_up_class_fails(
        self,
    ) -> None:
        """Verifies that disable_application_logging restores the real logging methods when setUpClass fails."""

        @disable_application_logging
        class FailingSetUpClassTest(unittest.TestCase):
            @classmethod
            def setUpClass(
                cls,
            ) -> None:
                raise RuntimeError(
                    "Dummy setUpClass failure",
                )

            def test_never_runs(
                self,
            ) -> None:
                get_logger().success(
                    "This test never runs",
                )

        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            FailingSetUpClassTest,
        )

        test_result = unittest.TestResult()

        test_suite.run(
            test_result,
        )

        self.assertFalse(
            test_result.wasSuccessful(),
            "Expected the failing setUpClass to be reported as an error.",
        )

        _assert_application_logger_methods_are_restored(
            self,
        )


class IntegrationTestSilenceApplicationLoggingCustomLevels(unittest.TestCase):
    def test_silenced_function_can_use_custom_levels_without_initialization(
        self,
    ) -> None:
        """Verifies that custom level methods work inside a silenced function without explicit initialization."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            dummy_application = DummyCustomLevelApplication(
                logs_directory=logs_directory,
            )

            @silence_application_logging
            def execute_dummy_application() -> None:
                dummy_application.execute()

            try:
                execute_dummy_application()
            except Exception as exception:
                self.fail(
                    (
                        "Expected custom level methods to be no-ops inside "
                        "silence_application_logging, but an exception was "
                        f"raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected silence_application_logging not to create the " "logs directory when custom level methods were called."),
            )

    def test_silenced_function_can_use_custom_levels_after_initialization(
        self,
    ) -> None:
        """Verifies that custom levels registered inside a silenced function can be used."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = _create_logs_directory_path(
                temporary_directory,
            )

            dummy_application = DummyCustomLevelApplication(
                logs_directory=logs_directory,
            )

            @silence_application_logging
            def execute_dummy_application() -> None:
                dummy_application.initialize_logger()
                dummy_application.execute()

            try:
                execute_dummy_application()
            except Exception as exception:
                self.fail(
                    (
                        "Expected explicit initialization with custom levels "
                        "to succeed inside silence_application_logging, but "
                        f"an exception was raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected silence_application_logging to prevent log file " "creation after custom level registration."),
            )

    def test_silenced_function_restores_logging_methods_after_return(
        self,
    ) -> None:
        """Verifies that silence_application_logging restores the real logging methods after the function returns."""
        replaced_method_names: list[str] = []

        @silence_application_logging
        def execute_dummy_application() -> None:
            for method_name, original_method in ORIGINAL_APPLICATION_LOGGER_METHODS.items():
                if ApplicationLogger.__dict__[method_name] is not original_method:
                    replaced_method_names.append(
                        method_name,
                    )

            get_logger().success(
                "SUCCESS message is suppressed",
            )

        execute_dummy_application()

        self.assertEqual(
            sorted(
                replaced_method_names,
            ),
            sorted(
                ORIGINAL_APPLICATION_LOGGER_METHODS,
            ),
            ("Expected silence_application_logging to replace every " "logging method while the function runs."),
        )

        _assert_application_logger_methods_are_restored(
            self,
        )

    def test_silenced_function_restores_logging_methods_after_exception(
        self,
    ) -> None:
        """Verifies that silence_application_logging restores the real logging methods when the function raises."""

        @silence_application_logging
        def execute_failing_application() -> None:
            get_logger().success(
                "SUCCESS message is suppressed",
            )

            raise RuntimeError(
                "Dummy application failure",
            )

        with self.assertRaisesRegex(
            RuntimeError,
            "Dummy application failure",
            msg=("Expected silence_application_logging to propagate " "exceptions raised by the decorated function."),
        ):
            execute_failing_application()

        _assert_application_logger_methods_are_restored(
            self,
        )


class DummyLoggedApplication:
    def __init__(
        self,
        logs_directory: Path,
    ) -> None:
        self._logs_directory = logs_directory

    def initialize_logger(
        self,
    ) -> None:
        CreateSpectraLogger(
            logs_directory=self._logs_directory,
            log_file_name="dummy-application.log",
            save_logs=True,
        )

    def execute(
        self,
    ) -> None:
        logger = get_logger()

        logger.info(
            "Dummy application started",
        )

        logger.warning(
            "Dummy application warning",
        )

        logger.error(
            "Dummy application error",
        )


class IntegrationTestApplicationLoggingEnabled(unittest.TestCase):
    def test_dummy_application_creates_and_writes_log_file(
        self,
    ) -> None:
        """Verifies that the dummy application creates and writes its log file during normal package usage."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            dummy_application.initialize_logger()

            try:
                dummy_application.execute()
            finally:
                logger = get_logger()
                logger.shutdown()

            log_file_path = logs_directory / "dummy-application.log"

            self.assertTrue(
                log_file_path.exists(),
                ("Expected normal SpectraLog usage to create the " "dummy application log file."),
            )

            log_file_contents = log_file_path.read_text(
                encoding="utf-8",
            )

            self.assertIn(
                "Dummy application started",
                log_file_contents,
                ("Expected the dummy application's INFO message to " "be written to the log file."),
            )

            self.assertIn(
                "Dummy application warning",
                log_file_contents,
                ("Expected the dummy application's WARNING message to " "be written to the log file."),
            )

            self.assertIn(
                "Dummy application error",
                log_file_contents,
                ("Expected the dummy application's ERROR message to " "be written to the log file."),
            )


@disable_application_logging
class IntegrationTestApplicationLoggingDisabled(unittest.TestCase):
    def test_dummy_application_does_not_create_log_file(
        self,
    ) -> None:
        """Verifies that the logging disable decorator prevents the dummy application from creating logging infrastructure."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            dummy_application.initialize_logger()
            dummy_application.execute()

            self.assertFalse(
                logs_directory.exists(),
                ("Expected disable_application_logging to prevent the " "dummy application from creating its logs directory."),
            )

    def test_dummy_application_can_still_use_logger_api(
        self,
    ) -> None:
        """Verifies that application code can continue calling the SpectraLog API while logging output is disabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            dummy_application.initialize_logger()

            try:
                dummy_application.execute()
            except Exception as exception:
                self.fail(
                    (
                        "Expected the dummy application to use the logger "
                        "normally while logging is disabled, but an "
                        f"exception was raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                ("Expected disabled logging to avoid creating the logs " "directory even though application logging methods were called."),
            )

    def test_dummy_application_can_use_get_logger_without_explicit_initialization(
        self,
    ) -> None:
        """Verifies that get_logger returns a disabled fallback logger before explicit initialization."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            try:
                dummy_application.execute()
            except Exception as exception:
                self.fail(
                    (
                        "Expected get_logger() to return a disabled fallback "
                        "logger before explicit initialization, but an "
                        f"exception was raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                (
                    "Expected fallback logging to avoid creating the logs "
                    "directory when CreateSpectraLogger was not called."
                ),
            )

    def test_dummy_application_can_initialize_after_fallback_logger_was_created(
        self,
    ) -> None:
        """Verifies that explicit initialization succeeds after a disabled fallback logger was created."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            fallback_logger = get_logger()

            try:
                dummy_application.initialize_logger()
                dummy_application.execute()
            except Exception as exception:
                self.fail(
                    (
                        "Expected explicit initialization to replace the "
                        "disabled fallback logger, but an exception was "
                        f"raised: {exception!r}"
                    ),
                )

            configured_logger = get_logger()

            self.assertIsNot(
                configured_logger,
                fallback_logger,
                (
                    "Expected CreateSpectraLogger to replace the temporary "
                    "fallback logger with a newly initialized logger."
                ),
            )

            self.assertFalse(
                logs_directory.exists(),
                (
                    "Expected disable_application_logging to continue "
                    "preventing log file creation after explicit initialization."
                ),
            )


class IntegrationTestSilenceApplicationLogging(unittest.TestCase):
    def test_silenced_function_does_not_create_log_file(
        self,
    ) -> None:
        """Verifies that silence_application_logging prevents log file creation inside a decorated function."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            @silence_application_logging
            def execute_dummy_application() -> None:
                dummy_application.initialize_logger()
                dummy_application.execute()

            execute_dummy_application()

            self.assertFalse(
                logs_directory.exists(),
                (
                    "Expected silence_application_logging to prevent the "
                    "dummy application from creating its logs directory."
                ),
            )

    def test_silenced_function_can_use_get_logger_without_initialization(
        self,
    ) -> None:
        """Verifies that get_logger works without explicit initialization inside a silenced function."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            @silence_application_logging
            def execute_dummy_application() -> None:
                dummy_application.execute()

            try:
                execute_dummy_application()
            except Exception as exception:
                self.fail(
                    (
                        "Expected get_logger() to return a disabled fallback "
                        "logger inside silence_application_logging, but an "
                        f"exception was raised: {exception!r}"
                    ),
                )

            self.assertFalse(
                logs_directory.exists(),
                (
                    "Expected fallback logging inside "
                    "silence_application_logging not to create the logs directory."
                ),
            )

    def test_silenced_function_can_initialize_after_fallback_logger_was_created(
        self,
    ) -> None:
        """Verifies that explicit initialization succeeds after fallback logger creation inside a silenced function."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            dummy_application = DummyLoggedApplication(
                logs_directory=logs_directory,
            )

            fallback_logger = None
            configured_logger = None

            @silence_application_logging
            def execute_dummy_application() -> None:
                nonlocal fallback_logger
                nonlocal configured_logger

                fallback_logger = get_logger()

                dummy_application.initialize_logger()

                configured_logger = get_logger()

                dummy_application.execute()

            try:
                execute_dummy_application()
            except Exception as exception:
                self.fail(
                    (
                        "Expected explicit initialization to replace the "
                        "disabled fallback logger inside "
                        "silence_application_logging, but an exception was "
                        f"raised: {exception!r}"
                    ),
                )

            self.assertIsNot(
                configured_logger,
                fallback_logger,
                (
                    "Expected CreateSpectraLogger to replace the temporary "
                    "fallback logger inside silence_application_logging."
                ),
            )

            self.assertFalse(
                logs_directory.exists(),
                (
                    "Expected silence_application_logging to prevent "
                    "log file creation after explicit initialization."
                ),
            )

    def test_silenced_function_preserves_return_value(
        self,
    ) -> None:
        """Verifies that silence_application_logging preserves the decorated function return value."""

        @silence_application_logging
        def calculate_value() -> int:
            return 42

        returned_value = calculate_value()

        self.assertEqual(
            returned_value,
            42,
            (
                "Expected silence_application_logging to preserve the "
                "decorated function return value."
            ),
        )

    def test_silenced_function_propagates_application_exception(
        self,
    ) -> None:
        """Verifies that silence_application_logging does not suppress exceptions raised by application code."""

        @silence_application_logging
        def execute_failing_application() -> None:
            raise RuntimeError(
                "Dummy application failure",
            )

        with self.assertRaisesRegex(
            RuntimeError,
            "Dummy application failure",
            msg=(
                "Expected silence_application_logging to propagate "
                "exceptions raised by the decorated function."
            ),
        ):
            execute_failing_application()
