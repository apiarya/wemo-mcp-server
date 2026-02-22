"""Error handling utilities for WeMo MCP server."""

import asyncio
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class WeMoError(Exception):
    """Base exception for WeMo-related errors."""

    def __init__(self, message: str, suggestion: str | None = None):
        """Initialize WeMo error with message and optional suggestion.

        Args:
        ----
            message: Error message
            suggestion: Optional actionable suggestion

        """
        super().__init__(message)
        self.suggestion = suggestion


class NetworkError(WeMoError):
    """Network-related errors (timeouts, connection failures)."""


class DeviceError(WeMoError):
    """Device-specific errors (not found, unsupported operation)."""


class ValidationError(WeMoError):
    """Input validation errors."""


def retry_on_network_error(
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: tuple = (ConnectionError, TimeoutError, OSError),
):
    """Decorator to retry async functions on network errors with exponential backoff.

    Args:
    ----
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 0.5)
        backoff_factor: Multiplier for delay on each retry (default: 2.0)
        exceptions: Tuple of exceptions to catch and retry (default: network errors)

    Returns:
    -------
        Decorated function with retry logic

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s...",
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}",
                        )

            # If we get here, all retries failed
            error_msg = f"Operation failed after {max_attempts} attempts: {last_exception}"
            raise NetworkError(
                error_msg,
                suggestion="Check network connectivity and ensure devices are online",
            )

        return wrapper

    return decorator


def classify_error(exception: Exception) -> dict[str, Any]:
    """Classify an exception and provide actionable suggestions.

    Args:
    ----
        exception: Exception to classify

    Returns:
    -------
        Dictionary with error classification and suggestions

    """
    error_type = type(exception).__name__
    error_msg = str(exception)

    # Network-related errors
    if isinstance(exception, ConnectionError | TimeoutError | OSError):
        return {
            "error_category": "network",
            "error_type": error_type,
            "message": error_msg,
            "suggestions": [
                "Verify network connectivity",
                "Check if devices are powered on",
                "Ensure devices are on the same network",
                "Try increasing timeout values",
            ],
            "recoverable": True,
        }

    # WeMo/pywemo specific errors
    if "pywemo" in error_msg.lower() or "wemo" in error_msg.lower():
        return {
            "error_category": "device",
            "error_type": error_type,
            "message": error_msg,
            "suggestions": [
                "Verify device is a WeMo device",
                "Check device firmware version",
                "Try power cycling the device",
                "Run scan_network to refresh device cache",
            ],
            "recoverable": True,
        }

    # IP/Network configuration errors
    if "address" in error_msg.lower() or "cidr" in error_msg.lower():
        return {
            "error_category": "configuration",
            "error_type": error_type,
            "message": error_msg,
            "suggestions": [
                "Verify subnet CIDR notation (e.g., '192.168.1.0/24')",
                "Check IP address format",
                "Ensure subnet matches your network",
            ],
            "recoverable": True,
        }

    # Generic error
    return {
        "error_category": "unknown",
        "error_type": error_type,
        "message": error_msg,
        "suggestions": [
            "Check application logs for details",
            "Verify all parameters are correct",
            "Report issue if problem persists",
        ],
        "recoverable": False,
    }


def build_error_response(
    exception: Exception,
    operation: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized error response dictionary.

    Args:
    ----
        exception: The exception that occurred
        operation: Name of the operation that failed
        context: Optional context information (params, device names, etc.)

    Returns:
    -------
        Standardized error response dictionary

    """
    classification = classify_error(exception)

    response = {
        "success": False,
        "error": f"{operation} failed: {classification['message']}",
        "error_details": {
            "category": classification["error_category"],
            "type": classification["error_type"],
            "recoverable": classification["recoverable"],
        },
        "suggestions": classification["suggestions"],
        "timestamp": time.time(),
    }

    if context:
        response["context"] = context

    return response
