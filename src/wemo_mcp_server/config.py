"""Configuration management for WeMo MCP server."""

import copy
import logging
import os
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "network": {
        "default_subnet": "192.168.1.0/24",
        "scan_timeout": 0.6,
        "max_workers": 60,
        "retry_attempts": 3,
        "retry_delay": 0.5,
    },
    "cache": {
        "enabled": True,
        "file_path": str(Path.home() / ".wemo_mcp_cache.json"),
        "ttl_seconds": 3600,  # 1 hour
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

# Environment variable prefix
ENV_PREFIX = "WEMO_MCP_"


class Config:
    """Manages configuration for WeMo MCP server."""

    def __init__(self, config_file: Path | None = None):
        """Initialize configuration manager.

        Args:
            config_file: Optional path to YAML configuration file

        """
        self._config: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self._config_file = config_file

        # Load from file if specified
        if config_file and config_file.exists():
            self._load_from_file(config_file)

        # Override with environment variables
        self._load_from_env()

    def _load_from_file(self, config_file: Path) -> None:
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file

        """
        if not YAML_AVAILABLE:
            logger.warning(
                "PyYAML not installed. Cannot load config file. "
                "Install with: pip install pyyaml",
            )
            return

        try:
            with config_file.open() as f:
                file_config = yaml.safe_load(f)

            if file_config:
                self._merge_config(file_config)
                logger.info(f"Loaded configuration from {config_file}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Network settings
        if subnet := os.getenv(f"{ENV_PREFIX}DEFAULT_SUBNET"):
            self._config["network"]["default_subnet"] = subnet

        if timeout := os.getenv(f"{ENV_PREFIX}SCAN_TIMEOUT"):
            try:
                self._config["network"]["scan_timeout"] = float(timeout)
            except ValueError:
                logger.warning(f"Invalid SCAN_TIMEOUT value: {timeout}")

        if workers := os.getenv(f"{ENV_PREFIX}MAX_WORKERS"):
            try:
                self._config["network"]["max_workers"] = int(workers)
            except ValueError:
                logger.warning(f"Invalid MAX_WORKERS value: {workers}")

        # Cache settings
        if cache_enabled := os.getenv(f"{ENV_PREFIX}CACHE_ENABLED"):
            self._config["cache"]["enabled"] = cache_enabled.lower() in ("true", "1", "yes")

        if cache_file := os.getenv(f"{ENV_PREFIX}CACHE_FILE"):
            self._config["cache"]["file_path"] = cache_file

        if ttl := os.getenv(f"{ENV_PREFIX}CACHE_TTL"):
            try:
                self._config["cache"]["ttl_seconds"] = int(ttl)
            except ValueError:
                logger.warning(f"Invalid CACHE_TTL value: {ttl}")

        # Logging settings
        if log_level := os.getenv(f"{ENV_PREFIX}LOG_LEVEL"):
            self._config["logging"]["level"] = log_level.upper()

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration into existing config.

        Args:
            new_config: Dictionary with new configuration values

        """
        for section, values in new_config.items():
            if section in self._config and isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: Configuration section (e.g., 'network', 'cache')
            key: Configuration key within section
            default: Default value if not found

        Returns:
            Configuration value or default

        """
        return self._config.get(section, {}).get(key, default)

    def get_section(self, section: str) -> dict[str, Any]:
        """Get entire configuration section.

        Args:
            section: Configuration section name

        Returns:
            Dictionary with section configuration

        """
        return dict(self._config.get(section, {}))

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set

        """
        if section not in self._config:
            self._config[section] = {}

        self._config[section][key] = value

    def get_all(self) -> dict[str, Any]:
        """Get all configuration.

        Returns:
            Complete configuration dictionary

        """
        return self._config.copy()

    def save_to_file(self, config_file: Path) -> bool:
        """Save current configuration to YAML file.

        Args:
            config_file: Path to save configuration

        Returns:
            True if saved successfully, False otherwise

        """
        if not YAML_AVAILABLE:
            logger.error(
                "PyYAML not installed. Cannot save config file. "
                "Install with: pip install pyyaml",
            )
            return False

        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with config_file.open("w") as f:
                yaml.safe_dump(self._config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved configuration to {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
            return False


# Global configuration instance
_config = Config()


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config instance

    """
    return _config


def init_config(config_file: Path | None = None) -> Config:
    """Initialize configuration with optional config file.

    Args:
        config_file: Optional path to YAML configuration file

    Returns:
        Config instance

    """
    global _config  # noqa: PLW0603
    _config = Config(config_file)
    return _config
