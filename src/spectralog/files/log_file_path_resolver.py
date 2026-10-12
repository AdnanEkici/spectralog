from __future__ import annotations

from datetime import date
from pathlib import Path

from spectralog.configuration.configuration import LoggerConfiguration

_REPLACEABLE_LOG_FILE_EXTENSIONS = frozenset(
    {
        ".log",
        ".txt",
        ".json",
        ".jsonl",
    },
)


class LogFilePathResolver:
    """Resolve the effective file-system path used for SpectraLog file logging.

    ``LogFilePathResolver`` determines where SpectraLog should write persistent
    log output based on the active :class:`LoggerConfiguration`.

    The resolver ensures that the configured logs directory exists before
    constructing the final file path. When a custom ``log_file_name`` is supplied,
    that name is used relative to the configured logs directory. When no custom
    name is supplied, a daily file name is generated from the current local date.

    JSON logging changes the effective file extension to ``.jsonl``. A recognized
    log extension in a custom file name is replaced, while any other dotted part of
    the name is preserved and ``.jsonl`` is appended. Plain-text logging uses the
    supplied custom name unchanged, or ``.log`` for automatically generated daily
    files.

    The resolver is responsible only for determining the log file path and
    creating the top-level logs directory. It does not create or open the log file
    itself."""

    def resolve(
        self,
        configuration: LoggerConfiguration,
    ) -> Path:
        """Resolve the configured log file path and ensure the logs directory exists.

        The configured logs directory is obtained from
        :attr:`LoggerConfiguration.resolved_logs_directory` and created recursively
        when necessary.

        If ``configuration.log_file_name`` is provided, a custom log file path is
        resolved. Otherwise, a daily log file name based on the current date is
        generated.

        Args:
            configuration:
                Logger configuration containing the logs directory, optional custom
                file name, and optional JSON logging configuration.

        Returns:
            Path:
                The resolved log file path that should be used for persistent logging."""
        logs_directory = configuration.resolved_logs_directory

        logs_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if configuration.log_file_name is not None:
            log_file_path = self._resolve_custom_log_file_path(
                configuration=configuration,
                logs_directory=logs_directory,
            )
        else:
            log_file_path = self._resolve_daily_log_file_path(
                configuration=configuration,
                logs_directory=logs_directory,
            )

        resolved_log_file_path = log_file_path

        return resolved_log_file_path

    def _resolve_custom_log_file_path(
        self,
        configuration: LoggerConfiguration,
        logs_directory: Path,
    ) -> Path:
        """Resolve a custom log file path within the configured logs directory.

        The configured ``log_file_name`` is appended to ``logs_directory``. When JSON
        logging is enabled, the path is converted to a ``.jsonl`` file by
        :meth:`_to_json_lines_path`.

        Args:
            configuration:
                Logger configuration containing the required custom log file name and
                optional JSON logging configuration.

            logs_directory:
                Resolved directory under which the custom log file path should be
                constructed.

        Raises:
            ValueError:
                If ``configuration.log_file_name`` is ``None`` when this custom-path
                resolver is invoked.

        Returns:
            Path:
                The custom log file path, with a ``.jsonl`` extension when JSON logging
                is enabled."""
        log_file_name = configuration.log_file_name

        if log_file_name is None:
            raise ValueError(
                "Log file name is required when resolving a custom log file path.",
            )

        log_file_path = logs_directory / log_file_name

        if configuration.json_logger_configuration is not None:
            log_file_path = self._to_json_lines_path(
                log_file_path,
            )

        resolved_log_file_path = log_file_path

        return resolved_log_file_path

    @staticmethod
    def _to_json_lines_path(
        log_file_path: Path,
    ) -> Path:
        """Convert a log file path to use the ``.jsonl`` extension.

        A recognized log extension (``.log``, ``.txt``, ``.json`` or ``.jsonl``) is
        replaced with ``.jsonl``. Any other suffix, such as the ``.v2`` in
        ``service.v2``, is treated as part of the file name and kept, and ``.jsonl``
        is appended.

        Args:
            log_file_path:
                Log file path whose extension should be converted.

        Returns:
            Path:
                The path with a ``.jsonl`` extension."""
        if log_file_path.suffix.lower() in _REPLACEABLE_LOG_FILE_EXTENSIONS:
            json_lines_path = log_file_path.with_suffix(
                ".jsonl",
            )
        else:
            json_lines_path = log_file_path.with_name(
                f"{log_file_path.name}.jsonl",
            )

        return json_lines_path

    def _resolve_daily_log_file_path(
        self,
        configuration: LoggerConfiguration,
        logs_directory: Path,
    ) -> Path:
        """Resolve an automatically generated daily log file path.

        The file name is generated from :func:`datetime.date.today` using ISO date
        format, producing names such as ``2026-08-25.log``.

        When JSON logging is enabled, the generated file uses the ``.jsonl``
        extension instead of ``.log``.

        Args:
            configuration:
                Logger configuration used to determine whether JSON logging is
                enabled.

            logs_directory:
                Resolved directory in which the generated daily log file should be
                located.

        Returns:
            Path:
                The generated daily log file path using either the ``.log`` or
                ``.jsonl`` extension."""
        current_date = date.today().isoformat()

        file_extension = ".jsonl" if configuration.json_logger_configuration is not None else ".log"

        log_file_path = logs_directory / (f"{current_date}{file_extension}")

        resolved_log_file_path = log_file_path

        return resolved_log_file_path
