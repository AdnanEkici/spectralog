from __future__ import annotations

from logging import LogRecord
from multiprocessing.queues import Queue

from spectralog.configuration.configuration import LoggerConfiguration
from spectralog.core.builder import ApplicationLoggerBuilder
from spectralog.files.log_file_path_resolver import LogFilePathResolver
from spectralog.formatting.file_formatter_resolver import FileFormatterResolver
from spectralog.formatting.format_builder import LogFormatBuilder
from spectralog.formatting.formatter_factory import LoggerFormatterFactory
from spectralog.formatting.json_file_formatter_strategy import JsonFileFormatterStrategy
from spectralog.formatting.json_logger_formatter_factory import JsonLoggerFormatterFactory
from spectralog.formatting.plain_text_file_formatter_strategy import PlainTextFileFormatterStrategy
from spectralog.formatting.relative_path_filter import RelativePathFilter
from spectralog.handlers.console_handler_factory import ConsoleHandlerFactory
from spectralog.handlers.file_handler_factory import FileHandlerFactory
from spectralog.handlers.multiprocessing_handler_factory import MultiprocessingHandlerFactory
from spectralog.handlers.queue_file_handler_factory import QueueFileHandlerFactory
from spectralog.handlers.rich_console_handler_factory import RichConsoleHandlerFactory
from spectralog.handlers.syslog_handler_factory import SyslogHandlerFactory
from spectralog.levels.log_level_registry import LogLevelRegistry


class ApplicationLoggerBuilderFactory:
    """Compose the dependency graph required to build a SpectraLog application logger.

    ``ApplicationLoggerBuilderFactory`` is responsible for constructing and
    connecting the concrete formatter, handler, path-resolution, and
    multiprocessing components used by :class:`ApplicationLoggerBuilder`.

    The factory centralizes dependency composition so that
    :class:`ApplicationLoggerBuilder` can focus exclusively on logger construction
    and orchestration. Components are created with the dependencies they require
    and then assembled into a fully configured builder for the supplied
    :class:`LoggerConfiguration`.

    A shared :class:`LogLevelRegistry` is retained by the factory and passed to
    formatter infrastructure so that standard and dynamically registered log
    levels use a consistent set of severity and color definitions.

    A single :class:`RelativePathFilter` instance is shared by the standard
    console, file, and syslog handler factories. This ensures that relative source
    path information is populated consistently across supported logging
    destinations.

    File formatting is composed through a :class:`FileFormatterResolver` with
    ordered formatting strategies. JSON formatting is evaluated before plain-text
    formatting, allowing JSON logging configuration to select the JSON formatter
    while plain-text formatting remains the fallback strategy.

    The factory also assembles the multiprocessing file logging pipeline by
    combining the queue handler factory with the standard file handler factory.
    This allows the resulting builder to choose between direct file logging and
    queue-based multiprocessing logging according to the active configuration.

    When a worker log record queue is supplied, the resulting builder forwards
    file records from a worker process to that parent-owned queue instead of
    writing the log file itself.

    Calling :meth:`create` constructs a new dependency graph and returns a fully
    composed :class:`ApplicationLoggerBuilder`. The logger itself is not created
    until the returned builder's :meth:`ApplicationLoggerBuilder.build` method is
    invoked."""

    def __init__(
        self,
        log_level_registry: LogLevelRegistry,
    ) -> None:
        """Initialize the factory with the shared SpectraLog log-level registry.

        The supplied :class:`LogLevelRegistry` is reused when constructing formatter
        infrastructure so that standard and dynamically registered log levels share
        the same severity and color definitions.

        Args:
            log_level_registry:
                Registry containing the log levels known to SpectraLog. The same
                registry is passed to formatter components created by this factory."""
        self._log_level_registry = log_level_registry

    def create(
        self,
        configuration: LoggerConfiguration,
        worker_log_record_queue: Queue[LogRecord] | None = None,
    ) -> ApplicationLoggerBuilder:
        """Create a fully composed :class:`ApplicationLoggerBuilder`.

        Constructs the complete dependency graph required by
        :class:`ApplicationLoggerBuilder` for the supplied logger configuration.

        The factory creates the format builder, relative-path filter, formatter
        factories, file formatter strategies, handler factories, multiprocessing
        logging components, syslog handler factory, and log-file path resolver.

        A single :class:`RelativePathFilter` instance is shared by the standard
        console, file, and syslog handler factories so that source-path enrichment is
        applied consistently across those logging destinations.

        File formatting is resolved through ordered strategies. JSON formatting is
        evaluated before plain-text formatting so that a configured
        :class:`JsonLoggerConfiguration` selects the JSON formatter when applicable,
        while plain-text formatting acts as the fallback.

        The returned builder is configured with all collaborators required to build a
        logger, but no logger or handler is created until
        :meth:`ApplicationLoggerBuilder.build` is called.

        Args:
            configuration:
                The :class:`LoggerConfiguration` that will be associated with the
                created builder and used when the builder later constructs the
                application logger.

            worker_log_record_queue:
                Optional parent-owned multiprocessing queue. When supplied, the
                created builder runs in worker mode and forwards file records to this
                queue instead of opening the log file. Defaults to ``None``.

        Returns:
            ApplicationLoggerBuilder:
                A fully composed logger builder configured with formatter factories,
                handler factories, multiprocessing support, syslog support, relative
                path filtering, and log-file path resolution."""
        format_builder = LogFormatBuilder()

        relative_path_filter = RelativePathFilter()

        formatter_factory = LoggerFormatterFactory(
            format_builder=format_builder,
            log_level_registry=self._log_level_registry,
        )

        json_formatter_factory = JsonLoggerFormatterFactory()

        plain_text_file_formatter_strategy = PlainTextFileFormatterStrategy(
            formatter_factory=formatter_factory,
        )

        json_file_formatter_strategy = JsonFileFormatterStrategy(
            json_formatter_factory=json_formatter_factory,
        )

        file_formatter_resolver = FileFormatterResolver(
            formatter_strategies=(
                json_file_formatter_strategy,
                plain_text_file_formatter_strategy,
            ),
        )

        console_handler_factory = ConsoleHandlerFactory(
            formatter_factory=formatter_factory,
            relative_path_filter=relative_path_filter,
        )

        rich_console_handler_factory = RichConsoleHandlerFactory()

        file_handler_factory = FileHandlerFactory(
            file_formatter_resolver=file_formatter_resolver,
            relative_path_filter=relative_path_filter,
        )

        queue_file_handler_factory = QueueFileHandlerFactory()

        multiprocessing_handler_factory = MultiprocessingHandlerFactory(
            queue_file_handler_factory=queue_file_handler_factory,
            file_handler_factory=file_handler_factory,
        )

        syslog_handler_factory = SyslogHandlerFactory(
            formatter_factory=formatter_factory,
            relative_path_filter=relative_path_filter,
        )

        log_file_path_resolver = LogFilePathResolver()

        logger_builder = ApplicationLoggerBuilder(
            configuration=configuration,
            console_handler_factory=console_handler_factory,
            rich_console_handler_factory=rich_console_handler_factory,
            file_handler_factory=file_handler_factory,
            multiprocessing_handler_factory=multiprocessing_handler_factory,
            syslog_handler_factory=syslog_handler_factory,
            log_file_path_resolver=log_file_path_resolver,
            queue_file_handler_factory=queue_file_handler_factory,
            worker_log_record_queue=worker_log_record_queue,
        )

        created_logger_builder = logger_builder

        return created_logger_builder
