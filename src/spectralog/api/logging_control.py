from __future__ import annotations

import logging
import unittest
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import cast
from typing import ParamSpec
from typing import TypeVar
from unittest.mock import patch

from spectralog.core.logger import ApplicationLogger
from spectralog.core.models import LoggerBuildResult
from spectralog.core.protocols import LoggerBuilder
from spectralog.levels.log_level_registry import LogLevelRegistry


TestCaseClass = TypeVar(
    "TestCaseClass",
    bound=type[unittest.TestCase],
)

FunctionParameters = ParamSpec(
    "FunctionParameters",
)

FunctionReturnType = TypeVar(
    "FunctionReturnType",
)


_NO_OP_LOGGING_METHOD_NAMES: tuple[str, ...] = (
    "log",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
)


def _no_op_logging_method(
    *args: object,
    **kwargs: object,
) -> None:
    """Accept any logging call and discard it.

    This function replaces :class:`ApplicationLogger` logging methods while
    SpectraLog is disabled or silenced. It accepts the same positional and
    keyword arguments as any SpectraLog logging method, including routing
    options such as ``console`` and ``file``, and intentionally does nothing.

    Args:
        *args:
            Positional arguments supplied to the replaced logging method.

        **kwargs:
            Keyword arguments supplied to the replaced logging method.
    """


def _no_op_getattr(
    self: ApplicationLogger,
    attribute_name: str,
) -> Callable[..., None]:
    """Resolve any public dynamic log-level method to a no-op method.

    This function replaces :meth:`ApplicationLogger.__getattr__` while
    SpectraLog is disabled or silenced. Application code may therefore call
    custom log-level methods such as ``logger.success(...)`` even when the
    corresponding level was registered by setup code that the test never runs.

    Private attribute names are still rejected so internal attribute lookups
    and accidental private access keep failing normally.

    Args:
        self:
            The application logger on which the attribute lookup occurred.

        attribute_name:
            The name of the missing attribute being resolved.

    Raises:
        AttributeError:
            If ``attribute_name`` starts with an underscore.

    Returns:
        Callable[..., None]:
            A logging method that accepts any arguments and does nothing.
    """
    if attribute_name.startswith("_"):
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute '{attribute_name}'.",
        )

    return _no_op_logging_method


def _create_no_op_logging_patches() -> list[Any]:
    """Create patches that replace every SpectraLog logging method with a no-op.

    The returned patches replace the built-in logging methods ``log``,
    ``debug``, ``info``, ``warning``, ``error``, ``critical``, and
    ``exception``, together with dynamic custom-level resolution through
    ``__getattr__``. Non-logging methods such as ``add_log_level`` and
    ``shutdown`` keep their real behavior.

    The patches are created but not started. Callers are responsible for
    starting them and for stopping them in reverse order, which restores the
    original :class:`ApplicationLogger` methods.

    Returns:
        list[Any]:
            Unstarted patch objects for every replaced logging method.
    """
    logging_method_patches: list[Any] = [
        patch.object(
            ApplicationLogger,
            method_name,
            new=_no_op_logging_method,
        )
        for method_name in _NO_OP_LOGGING_METHOD_NAMES
    ]

    logging_method_patches.append(
        patch.object(
            ApplicationLogger,
            "__getattr__",
            new=_no_op_getattr,
        ),
    )

    return logging_method_patches


def disable_application_logging(
    test_class: TestCaseClass,
) -> TestCaseClass:
    """Disable SpectraLog output and logging side effects for a unittest class.

    This decorator is intended for test suites that execute application code
    which uses SpectraLog through its normal public API while preventing real
    logging infrastructure from being created.

    While the decorated test class runs, SpectraLog's application logger builder
    is patched so that logger construction produces a disabled standard-library
    logger. The disabled logger has no active handlers, does not propagate log
    records, does not create files, and does not initialize multiprocessing
    logging infrastructure.

    SpectraLog's ``atexit`` registration is also suppressed for the lifetime of
    the decorated test class so test execution does not accumulate shutdown
    callbacks.

    Every :class:`ApplicationLogger` logging method is replaced with a no-op
    for the lifetime of the decorated test class. This covers ``log``,
    ``debug``, ``info``, ``warning``, ``error``, ``critical``, ``exception``,
    and every dynamic custom-level method such as ``logger.success(...)``.
    Custom levels therefore do not need to be registered in tests, even when
    the application registers them in setup code the test never runs. The
    original methods are restored when the test class finishes.

    The :class:`ApplicationLogger` singleton is isolated independently for each
    test method. Before each test, any previously existing singleton is preserved
    and the singleton reference is cleared. After the test completes, any logger
    created during that test is shut down and the previously existing singleton
    is restored.

    The decorator also provides a lazy disabled fallback logger when application
    code calls :func:`get_logger` before :func:`CreateSpectraLogger`. Normal
    production behavior raises a not-initialized exception in that situation,
    but decorated tests instead receive a temporary disabled
    :class:`ApplicationLogger`.

    If :func:`CreateSpectraLogger` is subsequently called after the fallback
    logger has been created, the fallback logger is shut down and removed before
    explicit initialization continues. This prevents the temporary test logger
    from triggering SpectraLog's normal reconfiguration protection.

    Existing ``setUpClass``, ``tearDownClass``, ``setUp``, and ``tearDown``
    implementations are preserved and invoked as part of the wrapped lifecycle.

    Args:
        test_class:
            The :class:`unittest.TestCase` subclass for which SpectraLog output
            and logging side effects should be disabled.

    Returns:
        TestCaseClass:
            The same test class with wrapped class-level and per-test lifecycle
            methods that provide disabled logging, singleton isolation, and lazy
            fallback logger creation.

    Example:
        Apply the decorator directly to a unittest class::

            import unittest

            from spectralog import CreateSpectraLogger
            from spectralog import disable_application_logging
            from spectralog import get_logger


            @disable_application_logging
            class UnitTestApplication(unittest.TestCase):
                def test_retrieval_without_initialization(self) -> None:
                    logger = get_logger()

                    logger.info(
                        "This message produces no logging output",
                    )

                    logger.success(
                        "Custom levels work without registration",
                    )

                    self.assertTrue(
                        True,
                        "Expected application execution to succeed.",
                    )

                def test_explicit_initialization(self) -> None:
                    logger = CreateSpectraLogger(
                        debug_mode=True,
                        log_file_name="application.log",
                    )

                    logger.info(
                        "Logging remains disabled during the test",
                    )

                    self.assertTrue(
                        True,
                        "Expected explicit initialization to succeed.",
                    )

    Note:
        This decorator is designed specifically for
        :class:`unittest.TestCase` subclasses.

        The fallback logger exists only during a decorated test method. Production
        behavior is unchanged, so :func:`get_logger` continues to require prior
        initialization outside the decorator.

        Singleton isolation occurs per test method, allowing multiple tests in one
        decorated class to initialize SpectraLog independently.

        Because logging methods are no-ops, misspelled custom level names such
        as ``logger.sucess(...)`` do not fail inside decorated tests. They still
        fail normally outside the decorator.
    """
    original_set_up_class = test_class.setUpClass
    original_tear_down_class = test_class.tearDownClass
    original_set_up = test_class.setUp
    original_tear_down = test_class.tearDown

    original_get_instance = cast(
        Callable[
            [
                LoggerBuilder | None,
                LogLevelRegistry | None,
            ],
            ApplicationLogger,
        ],
        ApplicationLogger.get_instance,
    )

    def set_up_class(
        cls: type[unittest.TestCase],
    ) -> None:
        """Install disabled logging infrastructure for the test class."""
        disabled_logger = logging.getLogger(
            f"disabled-{cls.__module__}.{cls.__name__}",
        )

        existing_handlers = list(
            disabled_logger.handlers,
        )

        for existing_handler in existing_handlers:
            disabled_logger.removeHandler(
                existing_handler,
            )

            existing_handler.close()

        disabled_logger.disabled = True
        disabled_logger.propagate = False

        disabled_logger_build_result = LoggerBuildResult(
            logger=disabled_logger,
            log_file_path=None,
            is_new_log_file=False,
            multiprocessing_logging_runtime=None,
        )

        logger_build_patch = patch(
            "spectralog.core.builder.ApplicationLoggerBuilder.build",
            return_value=disabled_logger_build_result,
        )

        atexit_register_patch = patch(
            "spectralog.core.logger.atexit.register",
        )

        logger_build_patch.start()
        atexit_register_patch.start()

        no_op_logging_patches = _create_no_op_logging_patches()

        for no_op_logging_patch in no_op_logging_patches:
            no_op_logging_patch.start()

        setattr(
            cls,
            "_spectralog_no_op_logging_patches",
            no_op_logging_patches,
        )

        setattr(
            cls,
            "_spectralog_logger_build_patch",
            logger_build_patch,
        )

        setattr(
            cls,
            "_spectralog_atexit_register_patch",
            atexit_register_patch,
        )

        try:
            original_set_up_class()
        except Exception:
            for no_op_logging_patch in reversed(no_op_logging_patches):
                no_op_logging_patch.stop()

            try:
                atexit_register_patch.stop()
            finally:
                logger_build_patch.stop()

            raise

    def tear_down_class(
        cls: type[unittest.TestCase],
    ) -> None:
        """Remove disabled logging infrastructure after the test class."""
        logger_build_patch = getattr(
            cls,
            "_spectralog_logger_build_patch",
        )

        atexit_register_patch = getattr(
            cls,
            "_spectralog_atexit_register_patch",
        )

        no_op_logging_patches = getattr(
            cls,
            "_spectralog_no_op_logging_patches",
        )

        try:
            original_tear_down_class()
        finally:
            for no_op_logging_patch in reversed(no_op_logging_patches):
                no_op_logging_patch.stop()

            try:
                atexit_register_patch.stop()
            finally:
                logger_build_patch.stop()

    def set_up(
        self: unittest.TestCase,
    ) -> None:
        """Isolate singleton state and install lazy fallback logger behavior."""
        test_case_instance = self

        previous_application_logger_instance = ApplicationLogger._instance

        setattr(
            test_case_instance,
            "_spectralog_previous_application_logger_instance",
            previous_application_logger_instance,
        )

        setattr(
            test_case_instance,
            "_spectralog_dummy_application_logger_instance",
            None,
        )

        ApplicationLogger._instance = None

        def get_instance(
            logger_builder: LoggerBuilder | None = None,
            log_level_registry: LogLevelRegistry | None = None,
        ) -> ApplicationLogger:
            """Return or initialize the disabled logger for the current test.

            A retrieval request without explicit initialization dependencies
            creates a temporary disabled application logger when no singleton
            exists.

            If explicit initialization is requested after that temporary logger
            has been created, the temporary logger is shut down and removed before
            initialization proceeds through SpectraLog's normal singleton logic.

            Args:
                logger_builder:
                    Optional logger builder supplied by explicit SpectraLog
                    initialization.

                log_level_registry:
                    Optional log-level registry supplied by explicit SpectraLog
                    initialization.

            Returns:
                ApplicationLogger:
                    The disabled application logger associated with the current
                    test.
            """
            current_application_logger_instance = ApplicationLogger._instance

            dummy_application_logger_instance = cast(
                ApplicationLogger | None,
                getattr(
                    test_case_instance,
                    "_spectralog_dummy_application_logger_instance",
                ),
            )

            is_plain_retrieval = logger_builder is None and log_level_registry is None

            if current_application_logger_instance is None and is_plain_retrieval:
                default_log_level_registry = LogLevelRegistry()

                created_dummy_application_logger_instance = original_get_instance(
                    None,
                    default_log_level_registry,
                )

                setattr(
                    test_case_instance,
                    "_spectralog_dummy_application_logger_instance",
                    created_dummy_application_logger_instance,
                )

                return created_dummy_application_logger_instance

            is_explicit_initialization = logger_builder is not None or log_level_registry is not None

            if (
                dummy_application_logger_instance is not None
                and current_application_logger_instance is dummy_application_logger_instance
                and is_explicit_initialization
            ):
                dummy_application_logger_instance.shutdown()

                ApplicationLogger._instance = None

                setattr(
                    test_case_instance,
                    "_spectralog_dummy_application_logger_instance",
                    None,
                )

            application_logger = original_get_instance(
                logger_builder,
                log_level_registry,
            )

            return application_logger

        get_instance_patch = patch.object(
            ApplicationLogger,
            "get_instance",
            side_effect=get_instance,
        )

        get_instance_patch.start()

        setattr(
            test_case_instance,
            "_spectralog_get_instance_patch",
            get_instance_patch,
        )

        try:
            original_set_up(
                test_case_instance,
            )
        except Exception:
            try:
                current_application_logger_instance = ApplicationLogger._instance

                if current_application_logger_instance is not None:
                    current_application_logger_instance.shutdown()
            finally:
                ApplicationLogger._instance = previous_application_logger_instance

                get_instance_patch.stop()

            raise

    def tear_down(
        self: unittest.TestCase,
    ) -> None:
        """Shut down the test logger and restore previous singleton state."""
        test_case_instance = self

        previous_application_logger_instance = cast(
            ApplicationLogger | None,
            getattr(
                test_case_instance,
                "_spectralog_previous_application_logger_instance",
            ),
        )

        get_instance_patch = getattr(
            test_case_instance,
            "_spectralog_get_instance_patch",
        )

        try:
            original_tear_down(
                test_case_instance,
            )
        finally:
            try:
                current_application_logger_instance = ApplicationLogger._instance

                if current_application_logger_instance is not None:
                    current_application_logger_instance.shutdown()
            finally:
                ApplicationLogger._instance = previous_application_logger_instance

                get_instance_patch.stop()

    setattr(
        test_class,
        "setUpClass",
        classmethod(
            set_up_class,
        ),
    )

    setattr(
        test_class,
        "tearDownClass",
        classmethod(
            tear_down_class,
        ),
    )

    setattr(
        test_class,
        "setUp",
        set_up,
    )

    setattr(
        test_class,
        "tearDown",
        tear_down,
    )

    decorated_test_class = test_class

    return decorated_test_class


def silence_application_logging(
    function: Callable[
        FunctionParameters,
        FunctionReturnType,
    ],
) -> Callable[FunctionParameters, FunctionReturnType]:
    """Temporarily silence SpectraLog while a function executes.

    The decorator prevents SpectraLog from producing console, file, Rich,
    syslog, or multiprocessing logging output for the duration of the decorated
    function.

    Any existing process-local :class:`ApplicationLogger` singleton is preserved
    before the function runs and restored afterward.

    If the decorated function calls :func:`get_logger` before explicitly
    initializing SpectraLog, a temporary disabled application logger is created
    so the call succeeds without producing output.

    If the decorated function subsequently calls :func:`CreateSpectraLogger`,
    the temporary fallback logger is discarded and explicit initialization
    proceeds using disabled logging infrastructure.

    Any temporary application logger created while the decorated function runs
    is shut down before the previous singleton state is restored.

    Every :class:`ApplicationLogger` logging method, including dynamic
    custom-level methods such as ``logger.success(...)``, is replaced with a
    no-op while the decorated function runs. Custom levels therefore do not
    need to be registered first. The original methods are restored afterward.

    The previous logging state is restored even if the decorated function raises
    an exception.

    Args:
        function:
            The function or method whose SpectraLog activity should be
            temporarily silenced.

    Returns:
        Callable:
            A wrapped callable with the same parameters and return type as the
            original function.

    Example:
        Silence SpectraLog for a function::

            from spectralog import CreateSpectraLogger
            from spectralog import get_logger
            from spectralog import silence_application_logging


            @silence_application_logging
            def perform_operation() -> None:
                logger = get_logger()

                logger.info(
                    "This message is suppressed",
                )


            @silence_application_logging
            def initialize_and_run() -> None:
                logger = CreateSpectraLogger(
                    save_logs=True,
                )

                logger.info(
                    "No console or file output is produced",
                )
    """
    original_get_instance = cast(
        Callable[
            [
                LoggerBuilder | None,
                LogLevelRegistry | None,
            ],
            ApplicationLogger,
        ],
        ApplicationLogger.get_instance,
    )

    @wraps(
        function,
    )
    def wrapper(
        *args: FunctionParameters.args,
        **kwargs: FunctionParameters.kwargs,
    ) -> FunctionReturnType:
        previous_application_logger_instance = ApplicationLogger._instance

        previous_underlying_logger_disabled: bool | None = None

        if previous_application_logger_instance is not None:
            previous_underlying_logger_disabled = previous_application_logger_instance._logger.disabled

            previous_application_logger_instance._logger.disabled = True

        ApplicationLogger._instance = None

        dummy_application_logger_instance: ApplicationLogger | None = None

        disabled_logger = logging.getLogger(
            f"spectralog-silenced-{id(function)}",
        )

        existing_handlers = list(
            disabled_logger.handlers,
        )

        for existing_handler in existing_handlers:
            disabled_logger.removeHandler(
                existing_handler,
            )

            existing_handler.close()

        disabled_logger.disabled = True
        disabled_logger.propagate = False

        disabled_logger_build_result = LoggerBuildResult(
            logger=disabled_logger,
            log_file_path=None,
            is_new_log_file=False,
            multiprocessing_logging_runtime=None,
        )

        def get_instance(
            logger_builder: LoggerBuilder | None = None,
            log_level_registry: LogLevelRegistry | None = None,
        ) -> ApplicationLogger:
            """Return a temporary disabled logger for the decorated function."""
            nonlocal dummy_application_logger_instance

            current_application_logger_instance = ApplicationLogger._instance

            is_plain_retrieval = logger_builder is None and log_level_registry is None

            if current_application_logger_instance is None and is_plain_retrieval:
                default_log_level_registry = LogLevelRegistry()

                created_dummy_application_logger_instance = original_get_instance(
                    None,
                    default_log_level_registry,
                )

                dummy_application_logger_instance = created_dummy_application_logger_instance

                return created_dummy_application_logger_instance

            is_explicit_initialization = logger_builder is not None or log_level_registry is not None

            if (
                dummy_application_logger_instance is not None
                and current_application_logger_instance is dummy_application_logger_instance
                and is_explicit_initialization
            ):
                dummy_application_logger_instance.shutdown()

                ApplicationLogger._instance = None
                dummy_application_logger_instance = None

            application_logger = original_get_instance(
                logger_builder,
                log_level_registry,
            )

            return application_logger

        logger_build_patch = patch(
            "spectralog.core.builder.ApplicationLoggerBuilder.build",
            return_value=disabled_logger_build_result,
        )

        atexit_register_patch = patch(
            "spectralog.core.logger.atexit.register",
        )

        get_instance_patch = patch.object(
            ApplicationLogger,
            "get_instance",
            side_effect=get_instance,
        )

        no_op_logging_patches = _create_no_op_logging_patches()

        logger_build_patch.start()
        atexit_register_patch.start()
        get_instance_patch.start()

        for no_op_logging_patch in no_op_logging_patches:
            no_op_logging_patch.start()

        try:
            result = function(
                *args,
                **kwargs,
            )

            return result
        finally:
            try:
                current_application_logger_instance = ApplicationLogger._instance

                if current_application_logger_instance is not None:
                    current_application_logger_instance.shutdown()
            finally:
                ApplicationLogger._instance = previous_application_logger_instance

                if previous_application_logger_instance is not None and previous_underlying_logger_disabled is not None:
                    previous_application_logger_instance._logger.disabled = previous_underlying_logger_disabled

                for no_op_logging_patch in reversed(no_op_logging_patches):
                    no_op_logging_patch.stop()

                get_instance_patch.stop()
                atexit_register_patch.stop()
                logger_build_patch.stop()

    decorated_function = wrapper

    return decorated_function
