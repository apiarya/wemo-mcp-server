"""Persistent device cache management for WeMo MCP server."""

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_FILE = Path.home() / ".wemo_mcp_cache.json"
CACHE_VERSION = "1.0"
CACHE_TTL_SECONDS = 3600  # 1 hour default TTL


class DeviceCache:
    """Manages persistent caching of discovered WeMo devices."""

    def __init__(
        self,
        cache_file: Path = CACHE_FILE,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        """Initialize device cache manager.

        Args:
        ----
            cache_file: Path to cache file (default: ~/.wemo_mcp_cache.json)
            ttl_seconds: Time-to-live for cache entries in seconds (default: 3600)

        """
        self.cache_file = cache_file
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        """Load device cache from disk.

        Returns
        -------
            Dictionary of cached device information

        """
        if not self.cache_file.exists():
            logger.info(f"No cache file found at {self.cache_file}")
            return {}

        try:
            with self.cache_file.open() as f:
                data = json.load(f)

            # Validate cache version
            if data.get("version") != CACHE_VERSION:
                logger.warning(
                    f"Cache version mismatch (found: {data.get('version')}, expected: {CACHE_VERSION}). "
                    "Clearing cache.",
                )
                return {}

            # Check if cache is expired
            cache_age = time.time() - data.get("timestamp", 0)
            if cache_age > self.ttl_seconds:
                logger.info(
                    f"Cache expired (age: {cache_age:.0f}s, TTL: {self.ttl_seconds}s). "
                    "Will rescan network.",
                )
                return {}

            devices = data.get("devices", {})
            logger.info(
                f"Loaded {len(devices)} devices from cache "
                f"(age: {cache_age:.0f}s, TTL: {self.ttl_seconds}s)",
            )

            self._cache = devices
            return dict(devices)

        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load cache from {self.cache_file}: {e}")
            return {}

    def save(self, devices: dict[str, dict[str, Any]]) -> bool:
        """Save device cache to disk.

        Args:
        ----
            devices: Dictionary of device information to cache

        Returns:
        -------
            True if save successful, False otherwise

        """
        try:
            # Prepare cache data
            cache_data = {
                "version": CACHE_VERSION,
                "timestamp": time.time(),
                "device_count": len(devices),
                "devices": devices,
            }

            # Create directory if it doesn't exist
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.cache_file.with_suffix(".tmp")
            with temp_file.open("w") as f:
                json.dump(cache_data, f, indent=2)

            # Atomic rename
            temp_file.replace(self.cache_file)

            logger.info(f"Saved {len(devices)} devices to cache at {self.cache_file}")
            self._cache = devices
            return True

        except (OSError, TypeError) as e:
            logger.error(f"Failed to save cache to {self.cache_file}: {e}")
            return False

    def clear(self) -> bool:
        """Clear the device cache (delete cache file).

        Returns
        -------
            True if cleared successfully, False otherwise

        """
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info(f"Cleared cache file at {self.cache_file}")

            self._cache = {}
            return True

        except OSError as e:
            logger.error(f"Failed to clear cache at {self.cache_file}: {e}")
            return False

    def is_expired(self) -> bool:
        """Check if the current cache is expired.

        Returns
        -------
            True if cache is expired or doesn't exist, False otherwise

        """
        if not self.cache_file.exists():
            return True

        try:
            with self.cache_file.open() as f:
                data = json.load(f)

            cache_age = time.time() - data.get("timestamp", 0)
            return bool(cache_age > self.ttl_seconds)

        except (json.JSONDecodeError, OSError, KeyError):
            return True

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the current cache.

        Returns
        -------
            Dictionary with cache metadata

        """
        if not self.cache_file.exists():
            return {
                "exists": False,
                "path": str(self.cache_file),
                "ttl_seconds": self.ttl_seconds,
            }

        try:
            with self.cache_file.open() as f:
                data = json.load(f)

            cache_age = time.time() - data.get("timestamp", 0)
            return {
                "exists": True,
                "path": str(self.cache_file),
                "version": data.get("version"),
                "device_count": data.get("device_count", 0),
                "age_seconds": round(cache_age, 2),
                "ttl_seconds": self.ttl_seconds,
                "expired": cache_age > self.ttl_seconds,
                "created": data.get("timestamp"),
            }

        except (json.JSONDecodeError, OSError, KeyError) as e:
            return {
                "exists": True,
                "path": str(self.cache_file),
                "error": str(e),
                "ttl_seconds": self.ttl_seconds,
            }


def serialize_device(device: Any) -> dict[str, Any]:
    """Serialize a pywemo device to JSON-compatible dictionary.

    Args:
    ----
        device: pywemo device object

    Returns:
    -------
        Dictionary with device information

    """
    return {
        "name": device.name,
        "host": getattr(device, "host", "unknown"),
        "port": getattr(device, "port", None),
        "model": getattr(device, "model", "Unknown"),
        "model_name": getattr(device, "model_name", "Unknown"),
        "serial_number": getattr(device, "serialnumber", ""),
        "firmware_version": getattr(device, "firmware_version", ""),
        "device_type": type(device).__name__,
        "cached_at": time.time(),
    }


# Global cache instance
_cache_manager = DeviceCache()
