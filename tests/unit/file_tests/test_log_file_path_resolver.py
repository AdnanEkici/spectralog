from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa
SRC_DIR = PROJECT_ROOT / "src"  # noqa
sys.path.insert(0, str(SRC_DIR))  # noqa


from spectralog.configuration.configuration import LoggerConfiguration  # noqa: E402
from spectralog.configuration.json_logger_configuration import JsonLoggerConfiguration  # noqa: E402
from spectralog.files.log_file_path_resolver import LogFilePathResolver  # noqa: E402


class UnitTestLogFilePathResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.log_file_path_resolver = LogFilePathResolver()

    def test_resolve_creates_logs_directory(
        self,
    ) -> None:
        """Verifies that resolve creates the configured logs directory when it does not already exist."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = (
                Path(
                    temporary_directory,
                )
                / "logs"
            )

            configuration = LoggerConfiguration(
                logs_directory=logs_directory,
            )

            self.assertFalse(
                logs_directory.exists(),
                "Expected the test logs directory not to exist before resolution.",
            )

            self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            self.assertTrue(
                logs_directory.exists(),
                "Expected resolve() to create the configured logs directory.",
            )

            self.assertTrue(
                logs_directory.is_dir(),
                "Expected the created logs path to be a directory.",
            )

    def test_resolve_returns_custom_log_file_path(
        self,
    ) -> None:
        """Verifies that resolve returns a custom log file path when log_file_name is configured."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = Path(
                temporary_directory,
            )

            configuration = LoggerConfiguration(
                logs_directory=logs_directory,
                log_file_name="application.log",
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "application.log"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected resolve() to return the configured custom log " "file path inside the resolved logs directory."),
            )

    def test_resolve_returns_daily_log_file_path_when_custom_name_is_absent(
        self,
    ) -> None:
        """Verifies that resolve returns a date-based log file path when no custom file name is configured."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name=None,
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / f"{date.today().isoformat()}.log"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected resolve() to create a daily .log path when " "no custom log file name is configured."),
            )

    def test_resolve_uses_jsonl_extension_for_daily_json_logging(
        self,
    ) -> None:
        """Verifies that resolve uses the JSON Lines extension for automatically generated JSON log file names."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                json_logger_configuration=JsonLoggerConfiguration(),
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / f"{date.today().isoformat()}.jsonl"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected JSON logging to generate a daily file with " "the .jsonl extension."),
            )

    def test_resolve_preserves_custom_log_extension_for_plain_text_logging(
        self,
    ) -> None:
        """Verifies that resolve preserves a custom file extension when JSON logging is disabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name="application.txt",
                json_logger_configuration=None,
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "application.txt"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected plain-text logging to preserve the custom " "log file extension."),
            )

    def test_resolve_replaces_custom_extension_with_jsonl_for_json_logging(
        self,
    ) -> None:
        """Verifies that resolve replaces the custom file extension with .jsonl when JSON logging is enabled."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name="application.log",
                json_logger_configuration=JsonLoggerConfiguration(),
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "application.jsonl"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected JSON logging to replace a custom file " "extension with .jsonl."),
            )

    def test_resolve_adds_jsonl_extension_to_custom_name_without_suffix(
        self,
    ) -> None:
        """Verifies that resolve adds the .jsonl extension to a custom file name without an existing suffix."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name="application",
                json_logger_configuration=JsonLoggerConfiguration(),
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "application.jsonl"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected JSON logging to add .jsonl to a custom file " "name that has no suffix."),
            )

    def test_resolve_preserves_nested_custom_log_file_path(
        self,
    ) -> None:
        """Verifies that resolve preserves nested path components contained in a custom log file name."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name="nested/application.log",
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "nested" / "application.log"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected nested path components in log_file_name to " "remain part of the resolved log file path."),
            )

    def test_resolve_does_not_create_nested_parent_directories_from_file_name(
        self,
    ) -> None:
        """Verifies that resolve only creates the configured logs directory and does not create nested custom file parent directories."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                log_file_name="nested/application.log",
            )

            self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            nested_directory = configuration.resolved_logs_directory / "nested"

            self.assertFalse(
                nested_directory.exists(),
                ("Expected resolve() not to create nested parent " "directories contained in log_file_name."),
            )

    def test_resolve_uses_resolved_logs_directory(
        self,
    ) -> None:
        """Verifies that resolve builds the final file path from LoggerConfiguration.resolved_logs_directory."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            logs_directory = Path(temporary_directory) / "logs" / ".." / "resolved-logs"

            configuration = LoggerConfiguration(
                logs_directory=logs_directory,
                log_file_name="application.log",
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "application.log"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected resolve() to construct the final path from " "the resolved logs directory."),
            )

    @patch(
        "spectralog.files.log_file_path_resolver.date",
    )
    def test_resolve_daily_log_file_uses_current_date(
        self,
        date_class_mock: MagicMock,
    ) -> None:
        """Verifies that daily log file generation uses the current date."""
        current_date = date(
            2026,
            8,
            25,
        )

        date_class_mock.today.return_value = current_date

        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "2026-08-25.log"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected the daily log file name to use the date " "returned by date.today()."),
            )

            date_class_mock.today.assert_called_once_with()

    @patch(
        "spectralog.files.log_file_path_resolver.date",
    )
    def test_resolve_daily_json_log_file_uses_current_date(
        self,
        date_class_mock: MagicMock,
    ) -> None:
        """Verifies that daily JSON log file generation combines the current date with the .jsonl extension."""
        current_date = date(
            2026,
            8,
            25,
        )

        date_class_mock.today.return_value = current_date

        with tempfile.TemporaryDirectory() as temporary_directory:
            configuration = LoggerConfiguration(
                logs_directory=temporary_directory,
                json_logger_configuration=JsonLoggerConfiguration(),
            )

            resolved_log_file_path = self.log_file_path_resolver.resolve(
                configuration=configuration,
            )

            expected_log_file_path = configuration.resolved_logs_directory / "2026-08-25.jsonl"

            self.assertEqual(
                resolved_log_file_path,
                expected_log_file_path,
                ("Expected the daily JSON log file name to combine the " "current date with the .jsonl extension."),
            )

    def test_resolve_custom_log_file_path_raises_when_name_is_missing(
        self,
    ) -> None:
        """Verifies that the custom path resolver raises ValueError when no custom log file name is available."""
        configuration = LoggerConfiguration(
            log_file_name=None,
        )

        logs_directory = Path(
            "logs",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Log file name is required when resolving a custom log file path.",
            msg=("Expected _resolve_custom_log_file_path() to raise " "ValueError when log_file_name is None."),
        ):
            self.log_file_path_resolver._resolve_custom_log_file_path(
                configuration=configuration,
                logs_directory=logs_directory,
            )

    def test_resolve_custom_log_file_path_returns_plain_text_path(
        self,
    ) -> None:
        """Verifies that the custom path resolver returns the configured file name unchanged for plain-text logging."""
        configuration = LoggerConfiguration(
            log_file_name="application.log",
            json_logger_configuration=None,
        )

        logs_directory = Path(
            "/tmp/logs",
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
            configuration=configuration,
            logs_directory=logs_directory,
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/application.log"),
            ("Expected the custom path resolver to preserve the custom " "file name for plain-text logging."),
        )

    def test_resolve_custom_log_file_path_returns_jsonl_path(
        self,
    ) -> None:
        """Verifies that the custom path resolver forces a .jsonl suffix when JSON logging is enabled."""
        configuration = LoggerConfiguration(
            log_file_name="application.log",
            json_logger_configuration=JsonLoggerConfiguration(),
        )

        logs_directory = Path(
            "/tmp/logs",
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
            configuration=configuration,
            logs_directory=logs_directory,
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/application.jsonl"),
            ("Expected the custom JSON path resolver to force the " ".jsonl file extension."),
        )

    @patch(
        "spectralog.files.log_file_path_resolver.date",
    )
    def test_resolve_daily_log_file_path_returns_plain_text_path(
        self,
        date_class_mock: MagicMock,
    ) -> None:
        """Verifies that the daily path resolver returns a .log path for plain-text logging."""
        current_date = date(
            2026,
            8,
            25,
        )

        date_class_mock.today.return_value = current_date

        configuration = LoggerConfiguration(
            json_logger_configuration=None,
        )

        logs_directory = Path(
            "/tmp/logs",
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_daily_log_file_path(
            configuration=configuration,
            logs_directory=logs_directory,
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/2026-08-25.log"),
            ("Expected the daily plain-text path resolver to produce a " ".log file."),
        )

    @patch(
        "spectralog.files.log_file_path_resolver.date",
    )
    def test_resolve_daily_log_file_path_returns_jsonl_path(
        self,
        date_class_mock: MagicMock,
    ) -> None:
        """Verifies that the daily path resolver returns a .jsonl path for JSON logging."""
        current_date = date(
            2026,
            8,
            25,
        )

        date_class_mock.today.return_value = current_date

        configuration = LoggerConfiguration(
            json_logger_configuration=JsonLoggerConfiguration(),
        )

        logs_directory = Path(
            "/tmp/logs",
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_daily_log_file_path(
            configuration=configuration,
            logs_directory=logs_directory,
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/2026-08-25.jsonl"),
            ("Expected the daily JSON path resolver to produce a " ".jsonl file."),
        )


    def test_resolve_custom_log_file_path_keeps_non_log_suffix_for_json_logging(
        self,
    ) -> None:
        """Verifies that a dotted part of the custom name that is not a log extension is kept and .jsonl is appended."""
        configuration = LoggerConfiguration(
            log_file_name="service.v2",
            json_logger_configuration=JsonLoggerConfiguration(),
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
            configuration=configuration,
            logs_directory=Path(
                "/tmp/logs",
            ),
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/service.v2.jsonl"),
            ("Expected JSON logging to keep the '.v2' part of the custom file " "name and append .jsonl instead of replacing it."),
        )

    def test_resolve_custom_log_file_path_keeps_multiple_dotted_parts_for_json_logging(
        self,
    ) -> None:
        """Verifies that a custom name with several dotted parts keeps all of them when JSON logging is enabled."""
        configuration = LoggerConfiguration(
            log_file_name="release.2026.10",
            json_logger_configuration=JsonLoggerConfiguration(),
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
            configuration=configuration,
            logs_directory=Path(
                "/tmp/logs",
            ),
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/release.2026.10.jsonl"),
            ("Expected JSON logging to keep every dotted part of the custom " "file name and append .jsonl."),
        )

    def test_resolve_custom_log_file_path_replaces_known_log_extensions_for_json_logging(
        self,
    ) -> None:
        """Verifies that recognized log extensions are replaced with .jsonl when JSON logging is enabled."""
        for log_file_name in (
            "application.log",
            "application.txt",
            "application.json",
            "application.jsonl",
            "application.LOG",
        ):
            with self.subTest(
                log_file_name=log_file_name,
            ):
                configuration = LoggerConfiguration(
                    log_file_name=log_file_name,
                    json_logger_configuration=JsonLoggerConfiguration(),
                )

                resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
                    configuration=configuration,
                    logs_directory=Path(
                        "/tmp/logs",
                    ),
                )

                self.assertEqual(
                    resolved_log_file_path,
                    Path("/tmp/logs/application.jsonl"),
                    f"Expected the '{log_file_name}' extension to be replaced with .jsonl.",
                )

    def test_resolve_keeps_non_log_suffix_unchanged_for_plain_text_logging(
        self,
    ) -> None:
        """Verifies that plain-text logging leaves a dotted custom name such as service.v2 untouched."""
        configuration = LoggerConfiguration(
            log_file_name="service.v2",
            json_logger_configuration=None,
        )

        resolved_log_file_path = self.log_file_path_resolver._resolve_custom_log_file_path(
            configuration=configuration,
            logs_directory=Path(
                "/tmp/logs",
            ),
        )

        self.assertEqual(
            resolved_log_file_path,
            Path("/tmp/logs/service.v2"),
            "Expected plain-text logging to keep the custom file name unchanged.",
        )