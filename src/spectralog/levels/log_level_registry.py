from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from threading import Lock

import colorlog
from spectralog.configuration.colors import LoggerColor
from spectralog.exceptions.exceptions import InvalidSpectraLogColorError
from spectralog.exceptions.exceptions import InvalidSpectraLogLevelNameError
from spectralog.exceptions.exceptions import InvalidSpectraLogLevelSeverityError
from spectralog.exceptions.exceptions import SpectraLogLevelAlreadyExistsError
from spectralog.exceptions.exceptions import SpectraLogLevelNotFoundError
from spectralog.levels.log_level import LogLevel


class LogLevelRegistry:
    """Manage SpectraLog log-level definitions, validation, and color mappings.

    ``LogLevelRegistry`` stores the standard and custom log levels available to a
    SpectraLog application logger.

    The registry initializes with the standard DEBUG, INFO, WARNING, ERROR, and
    CRITICAL levels and their default :class:`LoggerColor` values. Additional
    levels may be registered dynamically through :meth:`register`.

    Level names are normalized by trimming surrounding whitespace and converting
    the result to uppercase before validation and lookup. Valid names must begin
    with a letter and may contain only letters, numbers, and underscores.

    Custom colors are validated against the color names supported by
    ``colorlog``, and severity values must be positive integers. Boolean values are
    explicitly rejected even though ``bool`` is a subclass of ``int`` in Python.

    Both level names and numeric severities must remain unique within the
    registry. Registering a duplicate name or reusing a severity already assigned
    to another level raises :class:`SpectraLogLevelAlreadyExistsError`.

    Registration is protected by an internal lock so that validation against the
    current registry state and insertion of a new level occur atomically when
    multiple threads attempt to register levels concurrently.

    Registered levels are also published to Python's standard logging subsystem
    through :func:`logging.addLevelName`, allowing their numeric severities to be
    associated with the same normalized names outside the registry.

    The :attr:`colors` property exposes the current mapping between registered
    level names and their configured color values for use by compatible console
    formatters."""

    def __init__(
        self,
        default_colors: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the registry with SpectraLog's standard log levels.

        Creates the internal synchronization lock and level mapping, then registers
        the built-in DEBUG, INFO, WARNING, ERROR, and CRITICAL definitions using their
        standard-library severities and default SpectraLog colors.

        Args:
            default_colors:
                Optional mapping of built-in level names to colorlog-compatible
                color names. Supplied entries override the default
                :class:`LoggerColor` values; omitted levels keep their defaults.
                Level names are normalized before lookup.

        Raises:
            SpectraLogLevelNotFoundError:
                If ``default_colors`` contains a name that is not a built-in level.

            InvalidSpectraLogColorError:
                If ``default_colors`` contains a color not supported by colorlog."""
        self._lock = Lock()
        self._levels: dict[str, LogLevel] = {}
        self._register_default_levels(default_colors or {})

    @property
    def colors(self) -> dict[str, str]:
        """Return the current log-level color mapping.

        Builds a dictionary from the levels currently stored in the registry, mapping
        each normalized level name to its configured color value.

        A new dictionary is returned on every access, so modifying the returned
        mapping does not directly mutate the registry.

        Returns:
            dict[str, str]:
                Mapping of registered log-level names to colorlog-compatible color
                values."""
        colors = {log_level.name: log_level.color for log_level in self._levels.values()}

        return colors

    def register(
        self,
        name: str,
        color: str,
        severity: int,
    ) -> LogLevel:
        """Register a custom SpectraLog level.

        The supplied name is normalized by trimming surrounding whitespace and
        converting it to uppercase. The normalized name, color, and severity are then
        validated before registration.

        Registration is performed while holding the registry lock. Within that
        critical section, the method verifies that neither the normalized name nor the
        numeric severity is already assigned to another registered level.

        The level name is also registered with Python's standard logging subsystem
        through :func:`logging.addLevelName` before the resulting :class:`LogLevel` is
        stored in the registry.

        Args:
            name:
                Name of the level to register. Surrounding whitespace is removed and
                the name is converted to uppercase before validation.

            color:
                Colorlog-compatible color name used by SpectraLog's colored console
                formatter.

            severity:
                Positive integer logging severity associated with the new level.

        Raises:
            InvalidSpectraLogLevelNameError:
                If the normalized name is empty, does not begin with a letter, or
                contains characters other than letters, numbers, and underscores.

            InvalidSpectraLogColorError:
                If ``color`` is not present in colorlog's supported escape-code
                mapping.

            InvalidSpectraLogLevelSeverityError:
                If ``severity`` is not an integer, is a boolean value, or is less than
                or equal to zero.

            SpectraLogLevelAlreadyExistsError:
                If the normalized name is already registered or the supplied severity
                is already assigned to another registered level.

        Returns:
            LogLevel:
                The normalized and registered log-level definition."""
        normalized_name = self._normalize_name(name)

        self._validate_name(normalized_name)
        self._validate_color(color)
        self._validate_severity(severity)

        with self._lock:
            self._validate_level_does_not_exist(
                normalized_name,
                severity,
            )

            logging.addLevelName(
                severity,
                normalized_name,
            )

            log_level = LogLevel(
                name=normalized_name,
                severity=severity,
                color=color,
            )

            self._levels[normalized_name] = log_level

        registered_log_level = log_level
        return registered_log_level

    def get(
        self,
        name: str,
    ) -> LogLevel:
        """Return a registered log level by name.

        The supplied name is normalized by trimming surrounding whitespace and
        converting it to uppercase before lookup.

        Args:
            name:
                Name of the log level to retrieve.

        Raises:
            SpectraLogLevelNotFoundError:
                If no registered level matches the normalized name.

        Returns:
            LogLevel:
                The matching registered log-level definition."""
        normalized_name = self._normalize_name(name)

        log_level = self._levels.get(normalized_name)

        if log_level is None:
            raise SpectraLogLevelNotFoundError(
                f"Log level '{normalized_name}' is not registered.",
            )

        resolved_log_level = log_level
        return resolved_log_level

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a log-level name is registered.

        The supplied name is normalized using the same rules as registration and
        lookup before membership is checked.

        Args:
            name:
                Name of the log level to check.

        Returns:
            bool:
                ``True`` when the normalized name exists in the registry; otherwise
                ``False``."""
        normalized_name = self._normalize_name(name)
        contains_log_level = normalized_name in self._levels

        return contains_log_level

    def _register_default_levels(
        self,
        color_overrides: Mapping[str, str],
    ) -> None:
        """Populate the registry with SpectraLog's standard log levels.

        Registers DEBUG, INFO, WARNING, ERROR, and CRITICAL using the corresponding
        standard-library logging severities. Each level uses its color from
        ``color_overrides`` when supplied, otherwise its default
        :class:`LoggerColor` value.

        The default levels are inserted directly into the internal mapping because
        their definitions are controlled by SpectraLog and do not require the custom
        registration validation path. Only the override colors are validated.

        Args:
            color_overrides:
                Mapping of built-in level names to colorlog-compatible color names.

        Raises:
            SpectraLogLevelNotFoundError:
                If ``color_overrides`` contains a name that is not a built-in level.

            InvalidSpectraLogColorError:
                If ``color_overrides`` contains a color not supported by colorlog."""
        default_levels: dict[str, tuple[int, str]] = {
            "DEBUG": (logging.DEBUG, LoggerColor.DEBUG.value),
            "INFO": (logging.INFO, LoggerColor.INFO.value),
            "WARNING": (logging.WARNING, LoggerColor.WARNING.value),
            "ERROR": (logging.ERROR, LoggerColor.ERROR.value),
            "CRITICAL": (logging.CRITICAL, LoggerColor.CRITICAL.value),
        }

        normalized_overrides = {self._normalize_name(name): color for name, color in color_overrides.items()}

        for name, color in normalized_overrides.items():
            if name not in default_levels:
                raise SpectraLogLevelNotFoundError(
                    f"Cannot set default color for unknown log level '{name}'.",
                )

            self._validate_color(color)

        for name, (severity, default_color) in default_levels.items():
            self._levels[name] = LogLevel(
                name=name,
                severity=severity,
                color=normalized_overrides.get(name, default_color),
            )

    def _normalize_name(
        self,
        name: str,
    ) -> str:
        """Normalize a log-level name for registration and lookup.

        Surrounding whitespace is removed and the remaining name is converted to
        uppercase so that level-name operations are case-insensitive and consistent.

        Args:
            name:
                Raw log-level name to normalize.

        Returns:
            str:
                The stripped and uppercase log-level name."""
        normalized_name = name.strip().upper()
        return normalized_name

    def _validate_name(
        self,
        name: str,
    ) -> None:
        """Validate a normalized SpectraLog level name.

        A valid level name must be non-empty, begin with an uppercase letter, and
        contain only uppercase letters, decimal digits, and underscores.

        This method expects the name to have already been normalized by
        :meth:`_normalize_name`.

        Args:
            name:
                Normalized log-level name to validate.

        Raises:
            InvalidSpectraLogLevelNameError:
                If the name is empty or does not match the required
                ``^[A-Z][A-Z0-9_]*$`` pattern."""
        name_pattern = r"^[A-Z][A-Z0-9_]*$"

        if not name:
            raise InvalidSpectraLogLevelNameError(
                "Log level name cannot be empty.",
            )

        if re.fullmatch(name_pattern, name) is None:
            raise InvalidSpectraLogLevelNameError(
                "Log level name must start with a letter and contain " "only letters, numbers, and underscores.",
            )

    def _validate_color(
        self,
        color: str,
    ) -> None:
        """Validate a color against the color names supported by colorlog.

        The supplied value must exist in ``colorlog.escape_codes.escape_codes``.

        Args:
            color:
                Color name to validate.

        Raises:
            InvalidSpectraLogColorError:
                If the supplied color is not supported by colorlog."""
        available_colors = set(colorlog.escape_codes.escape_codes)

        if color not in available_colors:
            raise InvalidSpectraLogColorError(
                f"Unsupported logger color '{color}'.",
            )

    def _validate_severity(
        self,
        severity: int,
    ) -> None:
        """Validate a custom log-level severity.

        A valid severity must be an integer greater than zero. Boolean values are
        rejected explicitly because Python treats :class:`bool` as a subclass of
        :class:`int`.

        Args:
            severity:
                Numeric logging severity to validate.

        Raises:
            InvalidSpectraLogLevelSeverityError:
                If ``severity`` is a boolean value, is not an integer, or is less than
                or equal to zero."""
        if isinstance(severity, bool) or not isinstance(severity, int):
            raise InvalidSpectraLogLevelSeverityError(
                "Log level severity must be an integer.",
            )

        if severity <= 0:
            raise InvalidSpectraLogLevelSeverityError(
                "Log level severity must be greater than zero.",
            )

    def _validate_level_does_not_exist(
        self,
        name: str,
        severity: int,
    ) -> None:
        """Validate that a level name and severity are not already registered.

        The normalized level name must be unique, and the numeric severity must not be
        assigned to any existing log level.

        This method is called while the registry lock is held so that duplicate
        validation and insertion remain consistent during concurrent registration.

        Args:
            name:
                Normalized log-level name to check.

            severity:
                Numeric severity to check.

        Raises:
            SpectraLogLevelAlreadyExistsError:
                If ``name`` is already registered or ``severity`` is already assigned
                to another registered level."""
        if name in self._levels:
            raise SpectraLogLevelAlreadyExistsError(
                f"Log level '{name}' already exists.",
            )

        for existing_log_level in self._levels.values():
            if existing_log_level.severity == severity:
                raise SpectraLogLevelAlreadyExistsError(
                    f"Log level severity '{severity}' is already assigned " f"to '{existing_log_level.name}'.",
                )
