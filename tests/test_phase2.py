"""Tests for Phase 2 modules: error_handling, cache, and config."""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wemo_mcp_server.cache import CACHE_VERSION, DeviceCache, serialize_device
from wemo_mcp_server.config import Config, get_config, init_config
from wemo_mcp_server.error_handling import (
    DeviceError,
    NetworkError,
    ValidationError,
    WeMoError,
    build_error_response,
    classify_error,
    retry_on_network_error,
)

# ---------------------------------------------------------------------------
# error_handling.py tests
# ---------------------------------------------------------------------------


class TestWeMoExceptions:
    """Tests for custom exception classes."""

    def test_wemo_error_basic(self):
        """WeMoError stores message and suggestion."""
        err = WeMoError("something went wrong", suggestion="try again")
        assert str(err) == "something went wrong"
        assert err.suggestion == "try again"

    def test_wemo_error_no_suggestion(self):
        """WeMoError without suggestion defaults to None."""
        err = WeMoError("oops")
        assert err.suggestion is None

    def test_network_error_is_wemo_error(self):
        """NetworkError is a subclass of WeMoError."""
        err = NetworkError("timeout", suggestion="check network")
        assert isinstance(err, WeMoError)
        assert err.suggestion == "check network"

    def test_device_error_is_wemo_error(self):
        """DeviceError is a subclass of WeMoError."""
        err = DeviceError("device not found")
        assert isinstance(err, WeMoError)
        assert str(err) == "device not found"

    def test_validation_error_is_wemo_error(self):
        """ValidationError is a subclass of WeMoError."""
        err = ValidationError("invalid input")
        assert isinstance(err, WeMoError)


class TestRetryDecorator:
    """Tests for retry_on_network_error decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Function that succeeds returns result without retrying."""
        call_count = 0

        @retry_on_network_error(max_attempts=3)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self):
        """Function retries on ConnectionError and eventually succeeds."""
        call_count = 0

        @retry_on_network_error(max_attempts=3, initial_delay=0.01)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient failure")
            return "recovered"

        result = await flaky()
        assert result == "recovered"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_network_error_after_all_attempts(self):
        """Raises NetworkError after exhausting all retry attempts."""

        @retry_on_network_error(max_attempts=2, initial_delay=0.01)
        async def always_fail():
            raise ConnectionError("always failing")

        with pytest.raises(NetworkError) as exc_info:
            await always_fail()

        assert "2 attempts" in str(exc_info.value)
        assert exc_info.value.suggestion is not None

    @pytest.mark.asyncio
    async def test_does_not_retry_non_network_exceptions(self):
        """Does not retry on exceptions not in the exceptions list."""
        call_count = 0

        @retry_on_network_error(max_attempts=3, initial_delay=0.01)
        async def value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not a network error")

        with pytest.raises(ValueError, match="not a network error"):
            await value_error()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_timeout_error_triggers_retry(self):
        """TimeoutError is retried as a network error."""
        call_count = 0

        @retry_on_network_error(max_attempts=2, initial_delay=0.01)
        async def timeout_func():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("timed out")

        with pytest.raises(NetworkError):
            await timeout_func()

        assert call_count == 2


class TestClassifyError:
    """Tests for classify_error function."""

    def test_classify_connection_error(self):
        """ConnectionError is classified as network error."""
        result = classify_error(ConnectionError("refused"))
        assert result["error_category"] == "network"
        assert result["recoverable"] is True
        assert len(result["suggestions"]) > 0

    def test_classify_timeout_error(self):
        """TimeoutError is classified as network error."""
        result = classify_error(TimeoutError("timed out"))
        assert result["error_category"] == "network"
        assert result["recoverable"] is True

    def test_classify_os_error(self):
        """OSError is classified as network error."""
        result = classify_error(OSError("connection reset"))
        assert result["error_category"] == "network"

    def test_classify_wemo_error(self):
        """Exception with 'wemo' in the message is classified as device error."""
        result = classify_error(Exception("pywemo device not responding"))
        assert result["error_category"] == "device"
        assert result["recoverable"] is True

    def test_classify_cidr_error(self):
        """Exception with 'cidr' in message is classified as configuration error."""
        result = classify_error(ValueError("invalid cidr notation"))
        assert result["error_category"] == "configuration"
        assert result["recoverable"] is True

    def test_classify_address_error(self):
        """Exception with 'address' in message is classified as configuration error."""
        result = classify_error(ValueError("bad address format"))
        assert result["error_category"] == "configuration"

    def test_classify_unknown_error(self):
        """Unknown exceptions are classified as unknown."""
        result = classify_error(RuntimeError("something weird"))
        assert result["error_category"] == "unknown"
        assert result["recoverable"] is False

    def test_classify_includes_error_type(self):
        """Result includes the exception type name."""
        result = classify_error(ConnectionError("test"))
        assert result["error_type"] == "ConnectionError"

    def test_classify_includes_message(self):
        """Result includes the exception message."""
        result = classify_error(ConnectionError("specific message"))
        assert result["message"] == "specific message"


class TestBuildErrorResponse:
    """Tests for build_error_response function."""

    def test_response_has_success_false(self):
        """Error response always has success=False."""
        response = build_error_response(ConnectionError("fail"), "scan")
        assert response["success"] is False

    def test_response_includes_operation(self):
        """Error response includes the operation name."""
        response = build_error_response(ConnectionError("fail"), "scan_network")
        assert "scan_network" in response["error"]

    def test_response_includes_suggestions(self):
        """Error response includes actionable suggestions."""
        response = build_error_response(ConnectionError("fail"), "scan")
        assert "suggestions" in response
        assert len(response["suggestions"]) > 0

    def test_response_includes_error_details(self):
        """Error response includes error category details."""
        response = build_error_response(ConnectionError("fail"), "scan")
        assert "error_details" in response
        assert "category" in response["error_details"]

    def test_response_with_context(self):
        """Error response includes context when provided."""
        ctx = {"device": "Office Light", "action": "on"}
        response = build_error_response(ConnectionError("fail"), "control", context=ctx)
        assert response["context"] == ctx

    def test_response_without_context(self):
        """Error response without context doesn't include context key."""
        response = build_error_response(ConnectionError("fail"), "scan")
        assert "context" not in response


# ---------------------------------------------------------------------------
# cache.py tests
# ---------------------------------------------------------------------------


class TestDeviceCache:
    """Tests for DeviceCache class."""

    def _make_cache(self, tmp_path: Path, ttl: int = 3600) -> DeviceCache:
        """Helper to create a cache with a temp file path."""
        return DeviceCache(cache_file=tmp_path / "test_cache.json", ttl_seconds=ttl)

    def test_init_defaults(self, tmp_path: Path):
        """Cache initializes with correct defaults."""
        cache = self._make_cache(tmp_path)
        assert cache.ttl_seconds == 3600
        assert cache._cache == {}  # noqa: SLF001

    def test_load_no_file(self, tmp_path: Path):
        """Load returns empty dict when no cache file exists."""
        cache = self._make_cache(tmp_path)
        result = cache.load()
        assert result == {}

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        """Save and load roundtrip preserves device data."""
        cache = self._make_cache(tmp_path)
        devices = {
            "Office Light": {"name": "Office Light", "host": "192.168.1.100"},
            "192.168.1.100": {"name": "Office Light", "host": "192.168.1.100"},
        }
        assert cache.save(devices) is True
        loaded = cache.load()
        assert loaded == devices

    def test_save_creates_parent_directory(self, tmp_path: Path):
        """Save creates parent directories if they don't exist."""
        nested_path = tmp_path / "a" / "b" / "c" / "cache.json"
        cache = DeviceCache(cache_file=nested_path)
        cache.save({"device": {"name": "test"}})
        assert nested_path.exists()

    def test_load_expired_cache_returns_empty(self, tmp_path: Path):
        """Load returns empty dict when cache is expired."""
        cache = self._make_cache(tmp_path, ttl=1)
        devices = {"device": {"name": "test"}}
        cache.save(devices)

        # Manually set an old timestamp
        cache_data = json.loads(cache.cache_file.read_text())
        cache_data["timestamp"] = time.time() - 3600
        cache.cache_file.write_text(json.dumps(cache_data))

        result = cache.load()
        assert result == {}

    def test_load_version_mismatch_returns_empty(self, tmp_path: Path):
        """Load returns empty dict when cache version doesn't match."""
        cache = self._make_cache(tmp_path)
        # Write cache with wrong version
        cache_data = {"version": "999.0", "timestamp": time.time(), "devices": {"x": {}}}
        cache.cache_file.write_text(json.dumps(cache_data))
        result = cache.load()
        assert result == {}

    def test_load_corrupt_json_returns_empty(self, tmp_path: Path):
        """Load returns empty dict on JSON decode error."""
        cache = self._make_cache(tmp_path)
        cache.cache_file.write_text("not valid json{{{")
        result = cache.load()
        assert result == {}

    def test_clear_removes_file(self, tmp_path: Path):
        """Clear deletes the cache file."""
        cache = self._make_cache(tmp_path)
        cache.save({"x": {}})
        assert cache.cache_file.exists()
        assert cache.clear() is True
        assert not cache.cache_file.exists()

    def test_clear_no_file_returns_true(self, tmp_path: Path):
        """Clear returns True even if no cache file exists."""
        cache = self._make_cache(tmp_path)
        assert cache.clear() is True

    def test_clear_resets_in_memory_cache(self, tmp_path: Path):
        """Clear empties the in-memory cache."""
        cache = self._make_cache(tmp_path)
        cache._cache = {"device": {"name": "test"}}  # noqa: SLF001
        cache.clear()
        assert cache._cache == {}  # noqa: SLF001

    def test_is_expired_no_file(self, tmp_path: Path):
        """is_expired returns True when no cache file exists."""
        cache = self._make_cache(tmp_path)
        assert cache.is_expired() is True

    def test_is_expired_valid_cache(self, tmp_path: Path):
        """is_expired returns False for a fresh cache."""
        cache = self._make_cache(tmp_path, ttl=3600)
        cache.save({"x": {}})
        assert cache.is_expired() is False

    def test_is_expired_old_cache(self, tmp_path: Path):
        """is_expired returns True for an expired cache."""
        cache = self._make_cache(tmp_path, ttl=1)
        cache.save({"x": {}})
        # Set far-past timestamp
        data = json.loads(cache.cache_file.read_text())
        data["timestamp"] = time.time() - 7200
        cache.cache_file.write_text(json.dumps(data))
        assert cache.is_expired() is True

    def test_is_expired_corrupt_json(self, tmp_path: Path):
        """is_expired returns True for corrupt cache file."""
        cache = self._make_cache(tmp_path)
        cache.cache_file.write_text("{{bad json")
        assert cache.is_expired() is True

    def test_get_cache_info_no_file(self, tmp_path: Path):
        """get_cache_info returns exists=False when no file."""
        cache = self._make_cache(tmp_path)
        info = cache.get_cache_info()
        assert info["exists"] is False
        assert "path" in info

    def test_get_cache_info_valid_cache(self, tmp_path: Path):
        """get_cache_info returns metadata for a valid cache."""
        cache = self._make_cache(tmp_path)
        cache.save({"a": {}, "b": {}})
        info = cache.get_cache_info()
        assert info["exists"] is True
        assert info["device_count"] == 2
        assert info["version"] == CACHE_VERSION
        assert "age_seconds" in info
        assert "expired" in info

    def test_get_cache_info_corrupt_file(self, tmp_path: Path):
        """get_cache_info returns error key for corrupt file."""
        cache = self._make_cache(tmp_path)
        cache.cache_file.write_text("{{bad")
        info = cache.get_cache_info()
        assert "error" in info


class TestSerializeDevice:
    """Tests for serialize_device helper function."""

    def test_serializes_device_attributes(self):
        """serialize_device extracts standard device attributes."""
        mock_device = MagicMock()
        mock_device.name = "Office Light"
        mock_device.host = "192.168.1.100"
        mock_device.port = 49152
        mock_device.model = "LightSwitch"
        mock_device.model_name = "WeMo Light Switch"
        mock_device.serialnumber = "ABC123"

        result = serialize_device(mock_device)
        assert result["name"] == "Office Light"
        assert result["host"] == "192.168.1.100"
        assert result["port"] == 49152
        assert "cached_at" in result

    def test_serializes_missing_attributes_gracefully(self):
        """serialize_device uses defaults when attributes are missing."""
        mock_device = MagicMock(spec=[])
        mock_device.name = "Test"

        result = serialize_device(mock_device)
        assert result["host"] == "unknown"


# ---------------------------------------------------------------------------
# config.py tests
# ---------------------------------------------------------------------------


class TestConfig:
    """Tests for Config class."""

    def test_defaults_loaded(self):
        """Config loads default values on init."""
        config = Config()
        assert config.get("network", "default_subnet") == "192.168.1.0/24"
        assert config.get("network", "scan_timeout") == 0.6
        assert config.get("network", "max_workers") == 60
        assert config.get("cache", "enabled") is True
        assert config.get("cache", "ttl_seconds") == 3600
        assert config.get("logging", "level") == "INFO"

    def test_get_missing_key_returns_default(self):
        """get() returns default value for missing key."""
        config = Config()
        result = config.get("network", "nonexistent_key", default="fallback")
        assert result == "fallback"

    def test_get_missing_section_returns_default(self):
        """get() returns default for missing section."""
        config = Config()
        result = config.get("nonexistent", "key", default=42)
        assert result == 42

    def test_set_updates_value(self):
        """set() updates a configuration value."""
        config = Config()
        config.set("network", "max_workers", 100)
        assert config.get("network", "max_workers") == 100

    def test_set_creates_new_section(self):
        """set() creates a new section if it doesn't exist."""
        config = Config()
        config.set("custom", "my_key", "my_value")
        assert config.get("custom", "my_key") == "my_value"

    def test_get_section_returns_copy(self):
        """get_section() returns a copy of the section dict."""
        config = Config()
        section = config.get_section("network")
        assert isinstance(section, dict)
        assert "default_subnet" in section
        # Mutating the result should not affect config
        section["default_subnet"] = "10.0.0.0/16"
        assert config.get("network", "default_subnet") == "192.168.1.0/24"

    def test_get_section_missing_returns_empty(self):
        """get_section() returns empty dict for missing section."""
        config = Config()
        result = config.get_section("nonexistent")
        assert result == {}

    def test_get_all_returns_all_sections(self):
        """get_all() returns all sections."""
        config = Config()
        all_config = config.get_all()
        assert "network" in all_config
        assert "cache" in all_config
        assert "logging" in all_config

    def test_env_var_subnet_overrides_default(self):
        """WEMO_MCP_DEFAULT_SUBNET env var overrides default subnet."""
        with patch.dict(os.environ, {"WEMO_MCP_DEFAULT_SUBNET": "10.0.0.0/16"}):
            config = Config()
        assert config.get("network", "default_subnet") == "10.0.0.0/16"

    def test_env_var_scan_timeout_overrides(self):
        """WEMO_MCP_SCAN_TIMEOUT env var overrides default timeout."""
        with patch.dict(os.environ, {"WEMO_MCP_SCAN_TIMEOUT": "1.5"}):
            config = Config()
        assert config.get("network", "scan_timeout") == 1.5

    def test_env_var_invalid_timeout_keeps_default(self):
        """Invalid WEMO_MCP_SCAN_TIMEOUT keeps default value."""
        with patch.dict(os.environ, {"WEMO_MCP_SCAN_TIMEOUT": "not_a_number"}):
            config = Config()
        assert config.get("network", "scan_timeout") == 0.6

    def test_env_var_max_workers_overrides(self):
        """WEMO_MCP_MAX_WORKERS env var overrides default workers."""
        with patch.dict(os.environ, {"WEMO_MCP_MAX_WORKERS": "100"}):
            config = Config()
        assert config.get("network", "max_workers") == 100

    def test_env_var_invalid_workers_keeps_default(self):
        """Invalid WEMO_MCP_MAX_WORKERS keeps default value."""
        with patch.dict(os.environ, {"WEMO_MCP_MAX_WORKERS": "bad"}):
            config = Config()
        assert config.get("network", "max_workers") == 60

    def test_env_var_cache_enabled_false(self):
        """WEMO_MCP_CACHE_ENABLED=false disables cache."""
        with patch.dict(os.environ, {"WEMO_MCP_CACHE_ENABLED": "false"}):
            config = Config()
        assert config.get("cache", "enabled") is False

    def test_env_var_cache_enabled_true_variants(self):
        """WEMO_MCP_CACHE_ENABLED accepts 'true', '1', 'yes'."""
        for value in ("true", "1", "yes"):
            with patch.dict(os.environ, {"WEMO_MCP_CACHE_ENABLED": value}):
                config = Config()
            assert config.get("cache", "enabled") is True

    def test_env_var_cache_file_overrides(self, tmp_path: Path):
        """WEMO_MCP_CACHE_FILE overrides default cache path."""
        custom_path = str(tmp_path / "custom.json")
        with patch.dict(os.environ, {"WEMO_MCP_CACHE_FILE": custom_path}):
            config = Config()
        assert config.get("cache", "file_path") == custom_path

    def test_env_var_cache_ttl_overrides(self):
        """WEMO_MCP_CACHE_TTL overrides default TTL."""
        with patch.dict(os.environ, {"WEMO_MCP_CACHE_TTL": "7200"}):
            config = Config()
        assert config.get("cache", "ttl_seconds") == 7200

    def test_env_var_invalid_cache_ttl_keeps_default(self):
        """Invalid WEMO_MCP_CACHE_TTL keeps default value."""
        with patch.dict(os.environ, {"WEMO_MCP_CACHE_TTL": "bad"}):
            config = Config()
        assert config.get("cache", "ttl_seconds") == 3600

    def test_env_var_log_level_overrides(self):
        """WEMO_MCP_LOG_LEVEL overrides default log level."""
        with patch.dict(os.environ, {"WEMO_MCP_LOG_LEVEL": "debug"}):
            config = Config()
        assert config.get("logging", "level") == "DEBUG"

    def test_yaml_config_file_loaded(self, tmp_path: Path):
        """Config loads values from a YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("network:\n  max_workers: 150\n  scan_timeout: 2.0\n")

        config = Config(config_file=config_file)
        assert config.get("network", "max_workers") == 150
        assert config.get("network", "scan_timeout") == 2.0

    def test_yaml_config_missing_file_ignored(self, tmp_path: Path):
        """Config silently ignores a non-existent config file path."""
        nonexistent = tmp_path / "missing.yaml"
        config = Config(config_file=nonexistent)
        # Should use defaults
        assert config.get("network", "max_workers") == 60

    def test_yaml_config_without_pyyaml(self, tmp_path: Path):
        """Config gracefully handles missing PyYAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("network:\n  max_workers: 150\n")

        with patch("wemo_mcp_server.config.YAML_AVAILABLE", False):
            config = Config(config_file=config_file)
        # Uses defaults because YAML unavailable
        assert config.get("network", "max_workers") == 60

    def test_save_to_file(self, tmp_path: Path):
        """save_to_file writes YAML configuration to disk."""
        config = Config()
        config.set("network", "max_workers", 200)
        config_file = tmp_path / "saved.yaml"
        assert config.save_to_file(config_file) is True
        assert config_file.exists()

    def test_save_to_file_without_pyyaml(self, tmp_path: Path):
        """save_to_file returns False when PyYAML is unavailable."""
        config = Config()
        with patch("wemo_mcp_server.config.YAML_AVAILABLE", False):
            result = config.save_to_file(tmp_path / "config.yaml")
        assert result is False

    def test_env_overrides_yaml(self, tmp_path: Path):
        """Environment variables take precedence over YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("network:\n  max_workers: 50\n")

        with patch.dict(os.environ, {"WEMO_MCP_MAX_WORKERS": "99"}):
            config = Config(config_file=config_file)
        assert config.get("network", "max_workers") == 99


class TestConfigModuleFunctions:
    """Tests for module-level config functions."""

    def test_get_config_returns_config_instance(self):
        """get_config() returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_init_config_returns_new_instance(self):
        """init_config() returns a fresh Config instance."""
        config2 = init_config()
        assert isinstance(config2, Config)

    def test_init_config_with_file(self, tmp_path: Path):
        """init_config() loads from provided YAML config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("network:\n  max_workers: 77\n")
        config = init_config(config_file=config_file)
        assert config.get("network", "max_workers") == 77
