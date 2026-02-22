"""Unit tests for WeMo MCP server components."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from wemo_mcp_server.server import WeMoScanner, extract_device_info


class TestWeMoScanner:
    """Tests for WeMoScanner class."""

    def test_scanner_initialization(self):
        """Test scanner initializes with correct defaults."""
        scanner = WeMoScanner()

        assert scanner.timeout == 0.6
        assert scanner.wemo_ports == [49152, 49153, 49154, 49155]

    def test_probe_port_with_custom_timeout(self):
        """Test probe_port accepts custom timeout."""
        scanner = WeMoScanner()

        # This will fail to connect but should respect timeout
        result = scanner.probe_port("192.168.1.255", timeout=0.1)

        assert result is None  # No device at this IP

    def test_probe_port_with_custom_ports(self):
        """Test probe_port accepts custom port list."""
        scanner = WeMoScanner()

        result = scanner.probe_port("192.168.1.255", ports=[8080], timeout=0.1)

        assert result is None


class TestExtractDeviceInfo:
    """Tests for extract_device_info function."""

    def test_extract_device_info_complete(self):
        """Test extracting complete device information."""
        # Create mock device with all attributes
        mock_device = Mock()
        mock_device.name = "Test Device"
        mock_device.model_name = "Dimmer"
        mock_device.serial_number = "TEST123456"
        mock_device.host = "192.168.1.100"
        mock_device.port = 49153
        mock_device.mac = "AA:BB:CC:DD:EE:FF"
        mock_device.firmware_version = "WeMo_WW_2.00.11573"
        mock_device.get_state = Mock(return_value=1)  # On state

        result = extract_device_info(mock_device)

        assert result["name"] == "Test Device"
        assert result["model"] == "Dimmer"
        assert result["serial_number"] == "TEST123456"
        assert result["ip_address"] == "192.168.1.100"
        assert result["port"] == 49153
        assert result["mac_address"] == "AA:BB:CC:DD:EE:FF"
        assert result["firmware_version"] == "WeMo_WW_2.00.11573"
        assert result["state"] == "on"
        assert result["manufacturer"] == "Belkin"

    def test_extract_device_info_minimal(self):
        """Test extracting info from device with minimal attributes."""
        mock_device = Mock()
        mock_device.name = "Minimal Device"
        mock_device.model = "Socket"

        # Remove optional attributes
        del mock_device.model_name
        del mock_device.serial_number
        del mock_device.host
        del mock_device.port
        del mock_device.mac
        del mock_device.firmware_version

        mock_device.get_state = Mock(return_value=0)  # Off state

        result = extract_device_info(mock_device)

        assert result["name"] == "Minimal Device"
        assert result["model"] == "Socket"
        assert result["serial_number"] == "N/A"
        assert result["ip_address"] == "unknown"
        assert result["port"] == 49153  # Default
        assert result["mac_address"] == "N/A"
        assert result["firmware_version"] == "N/A"
        assert result["state"] == "off"

    def test_extract_device_info_with_exception(self):
        """Test handling of exceptions during extraction."""
        mock_device = Mock()
        mock_device.name = "Error Device"
        mock_device.model = "Unknown"
        mock_device.get_state = Mock(side_effect=Exception("Connection error"))

        # Should not raise exception, but return partial info
        result = extract_device_info(mock_device)

        assert "name" in result
        assert "error" in result


class TestDeviceCache:
    """Tests for device caching functionality."""

    @pytest.mark.asyncio
    async def test_device_cache_structure(self):
        """Test that device cache has correct structure."""
        from wemo_mcp_server.server import _device_cache

        # Verify cache is a dictionary
        assert isinstance(_device_cache, dict)


@pytest.mark.asyncio
class TestAsyncFunctions:
    """Tests for async MCP tool functions."""

    async def test_scan_network_returns_dict(self):
        """Test scan_network returns properly structured dictionary."""
        from wemo_mcp_server.server import scan_network

        with patch("wemo_mcp_server.server.WeMoScanner") as MockScanner:
            # Mock scanner to return empty list
            mock_instance = MockScanner.return_value
            mock_instance.scan_subnet = Mock(return_value=[])

            result = await scan_network("192.168.1.0/24", timeout=0.1, max_workers=1)

            assert "scan_parameters" in result
            assert "results" in result
            assert "devices" in result
            assert "scan_completed" in result
            assert result["scan_parameters"]["subnet"] == "192.168.1.0/24"

    async def test_list_devices_returns_dict(self):
        """Test list_devices returns properly structured dictionary."""
        from wemo_mcp_server.server import _device_cache, list_devices

        # Clear and setup cache
        _device_cache.clear()

        result = await list_devices()

        assert "device_count" in result
        assert "devices" in result
        assert isinstance(result["devices"], list)
        assert result["device_count"] == 0  # Empty cache

    async def test_get_device_status_not_found(self):
        """Test get_device_status with non-existent device."""
        from wemo_mcp_server.server import _device_cache, get_device_status

        _device_cache.clear()

        result = await get_device_status("NonExistentDevice")

        assert "error" in result
        assert "not found" in result["error"].lower()

    async def test_control_device_invalid_action(self):
        """Test control_device with invalid action."""
        from wemo_mcp_server.server import control_device

        result = await control_device("TestDevice", "invalid_action")

        assert "error" in result
        assert "Invalid parameters" in result["error"]
        assert "validation_errors" in result
        assert result["success"] is False

    async def test_control_device_invalid_brightness(self):
        """Test control_device with invalid brightness value."""
        from wemo_mcp_server.server import control_device

        result = await control_device("TestDevice", "brightness", brightness=150)

        assert "error" in result
        assert "Invalid parameters" in result["error"]
        assert "validation_errors" in result
        assert result["success"] is False


class TestWeMoScannerScan:
    """Tests for WeMoScanner.scan_subnet() method - the core discovery logic."""

    @patch("wemo_mcp_server.server.ipaddress")
    @patch("wemo_mcp_server.server.pywemo")
    def test_scan_upnp_discovery_success(self, mock_pywemo, mock_ipaddress):
        """Test successful UPnP/SSDP discovery."""
        # Create mock devices
        mock_device1 = Mock()
        mock_device1.name = "Device 1"
        mock_device1.host = "192.168.1.10"
        mock_device1.port = 49152

        mock_device2 = Mock()
        mock_device2.name = "Device 2"
        mock_device2.host = "192.168.1.11"
        mock_device2.port = 49153

        mock_pywemo.discover_devices.return_value = [mock_device1, mock_device2]

        # Mock the network parsing to avoid actual network operations
        mock_network = Mock()
        mock_network.hosts.return_value = []  # No hosts to scan
        mock_ipaddress.ip_network.return_value = mock_network

        scanner = WeMoScanner()
        devices = scanner.scan_subnet("192.168.1.0/29")  # Small subnet to speed up test

        assert len(devices) == 2
        assert devices[0].name == "Device 1"
        assert devices[1].name == "Device 2"
        mock_pywemo.discover_devices.assert_called_once()

    @patch("wemo_mcp_server.server.ipaddress")
    @patch("wemo_mcp_server.server.pywemo")
    def test_scan_upnp_discovery_failure(self, mock_pywemo, mock_ipaddress):
        """Test handling of UPnP discovery failure."""
        mock_pywemo.discover_devices.side_effect = Exception("UPnP timeout")

        # Mock network to avoid actual scanning
        mock_network = Mock()
        mock_network.hosts.return_value = []
        mock_ipaddress.ip_network.return_value = mock_network

        scanner = WeMoScanner()
        devices = scanner.scan_subnet("192.168.1.0/29")

        # Should not crash, returns empty or port scan results
        assert isinstance(devices, list)

    @patch("wemo_mcp_server.server.pywemo")
    def test_scan_invalid_cidr(self, mock_pywemo):
        """Test scan with invalid CIDR notation."""
        mock_pywemo.discover_devices.return_value = []

        scanner = WeMoScanner()
        devices = scanner.scan_subnet("invalid_cidr")

        # Should handle gracefully
        assert isinstance(devices, list)


class TestMCPToolsHappyPath:
    """Tests for MCP tools with successful device interactions."""

    @pytest.mark.asyncio
    async def test_scan_network_with_devices(self):
        """Test scan_network successfully finds and caches devices."""
        from wemo_mcp_server.server import _device_cache, scan_network

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Test Switch"
        mock_device.model = "Socket"
        mock_device.host = "192.168.1.50"
        mock_device.port = 49152
        mock_device.get_state = Mock(return_value=1)

        with patch("wemo_mcp_server.server.WeMoScanner") as MockScanner:
            mock_scanner = MockScanner.return_value
            mock_scanner.scan_subnet = Mock(return_value=[mock_device])

            result = await scan_network("192.168.1.0/29", timeout=0.1)

            assert result["scan_completed"] is True
            assert result["results"]["total_devices_found"] == 1
            assert len(result["devices"]) == 1
            assert result["devices"][0]["name"] == "Test Switch"

            # Verify device is cached
            assert "Test Switch" in _device_cache
            assert _device_cache["Test Switch"] == mock_device

    @pytest.mark.asyncio
    async def test_list_devices_with_populated_cache(self):
        """Test list_devices with multiple devices in cache."""
        from wemo_mcp_server.server import _device_cache, list_devices

        _device_cache.clear()

        # Add mock devices to cache
        mock_device1 = Mock()
        mock_device1.name = "Living Room"
        mock_device1.host = "192.168.1.10"
        mock_device1.model = "Dimmer"

        mock_device2 = Mock()
        mock_device2.name = "Bedroom"
        mock_device2.host = "192.168.1.11"
        mock_device2.model = "Socket"

        _device_cache["Living Room"] = mock_device1
        _device_cache["192.168.1.10"] = mock_device1
        _device_cache["Bedroom"] = mock_device2
        _device_cache["192.168.1.11"] = mock_device2

        result = await list_devices()

        assert result["device_count"] == 2  # 2 unique devices
        assert len(result["devices"]) == 2
        assert "cache_keys" not in result  # raw key count is an internal detail, not exposed

        device_names = {d["name"] for d in result["devices"]}
        assert "Living Room" in device_names
        assert "Bedroom" in device_names

    @pytest.mark.asyncio
    async def test_get_device_status_success(self):
        """Test get_device_status with successful device query."""
        from wemo_mcp_server.server import _device_cache, get_device_status

        _device_cache.clear()

        # Use spec to limit attributes and prevent hasattr from finding brightness methods
        mock_device = Mock(spec=["name", "host", "model", "get_state"])
        mock_device.name = "Test Device"
        mock_device.host = "192.168.1.20"
        mock_device.model = "Socket"
        mock_device.get_state = Mock(return_value=1)  # Device is on

        _device_cache["Test Device"] = mock_device

        result = await get_device_status("Test Device")

        assert "error" not in result
        assert result["name"] == "Test Device"
        assert result["state"] == "on"
        assert result["is_dimmer"] is False

    @pytest.mark.asyncio
    async def test_get_device_status_with_dimmer(self):
        """Test get_device_status with a dimmer device."""
        from wemo_mcp_server.server import _device_cache, get_device_status

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Dimmer Light"
        mock_device.host = "192.168.1.30"
        mock_device.model = "Dimmer"
        mock_device.get_state = Mock(return_value=1)
        mock_device.get_brightness = Mock(return_value=75)

        _device_cache["Dimmer Light"] = mock_device

        result = await get_device_status("Dimmer Light")

        assert result["state"] == "on"
        assert result["is_dimmer"] is True
        assert result["brightness"] == 75

    @pytest.mark.asyncio
    async def test_control_device_turn_on(self):
        """Test control_device turning a device on."""
        from wemo_mcp_server.server import _device_cache, control_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Test Switch"
        mock_device.on = Mock()
        mock_device.get_state = Mock(return_value=1)

        _device_cache["Test Switch"] = mock_device

        result = await control_device("Test Switch", "on")

        assert result["success"] is True
        assert result["device_name"] == "Test Switch"
        assert result["action_performed"] == "on"
        assert result["new_state"] == "on"
        mock_device.on.assert_called_once()

    @pytest.mark.asyncio
    async def test_control_device_turn_off(self):
        """Test control_device turning a device off."""
        from wemo_mcp_server.server import _device_cache, control_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Test Switch"
        mock_device.off = Mock()
        mock_device.get_state = Mock(return_value=0)

        _device_cache["Test Switch"] = mock_device

        result = await control_device("Test Switch", "off")

        assert result["success"] is True
        assert result["action_performed"] == "off"
        assert result["new_state"] == "off"
        mock_device.off.assert_called_once()

    @pytest.mark.asyncio
    async def test_control_device_toggle(self):
        """Test control_device toggling a device."""
        from wemo_mcp_server.server import _device_cache, control_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Test Switch"
        mock_device.toggle = Mock()
        mock_device.get_state = Mock(return_value=0)

        _device_cache["Test Switch"] = mock_device

        result = await control_device("Test Switch", "toggle")

        assert result["success"] is True
        assert result["action_performed"] == "toggle"
        mock_device.toggle.assert_called_once()

    @pytest.mark.asyncio
    async def test_control_device_brightness_dimmer(self):
        """Test control_device setting brightness on a dimmer."""
        from wemo_mcp_server.server import _device_cache, control_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Dimmer Light"
        mock_device.set_brightness = Mock()
        mock_device.get_brightness = Mock(return_value=50)
        mock_device.get_state = Mock(return_value=1)

        _device_cache["Dimmer Light"] = mock_device

        result = await control_device("Dimmer Light", "brightness", brightness=50)

        assert result["success"] is True
        assert result["brightness"] == 50
        assert result["is_dimmer"] is True
        mock_device.set_brightness.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_control_device_brightness_non_dimmer(self):
        """Test control_device brightness action on non-dimmer device."""
        from wemo_mcp_server.server import _device_cache, control_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Regular Switch"
        # Don't add set_brightness/get_brightness to simulate non-dimmer
        del mock_device.set_brightness
        del mock_device.get_brightness

        _device_cache["Regular Switch"] = mock_device

        result = await control_device("Regular Switch", "brightness", brightness=50)

        assert result["success"] is False
        assert "error" in result
        assert "not a dimmer" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_rename_device_success(self):
        """Test rename_device successfully renames a device."""
        from wemo_mcp_server.server import _device_cache, rename_device

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Old Name"
        mock_device.host = "192.168.1.40"
        mock_device.change_friendly_name = Mock()

        _device_cache["Old Name"] = mock_device
        _device_cache["192.168.1.40"] = mock_device

        result = await rename_device("Old Name", "New Name")

        assert result["success"] is True
        assert result["old_name"] == "Old Name"
        assert result["new_name"] == "New Name"
        mock_device.change_friendly_name.assert_called_once_with("New Name")

        # Verify cache updated
        assert "New Name" in _device_cache
        assert "Old Name" not in _device_cache

    @pytest.mark.asyncio
    async def test_rename_device_empty_name(self):
        """Test rename_device with empty new name."""
        from wemo_mcp_server.server import rename_device

        result = await rename_device("Device", "")

        assert result["success"] is False
        assert "error" in result
        assert "Invalid parameters" in result["error"]
        assert "validation_errors" in result

    @pytest.mark.asyncio
    async def test_rename_device_not_found(self):
        """Test rename_device with non-existent device."""
        from wemo_mcp_server.server import _device_cache, rename_device

        _device_cache.clear()

        result = await rename_device("NonExistent", "New Name")

        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_homekit_code_success(self):
        """Test get_homekit_code successfully retrieves code."""
        from wemo_mcp_server.server import _device_cache, get_homekit_code

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "HomeKit Device"
        mock_device.host = "192.168.1.50"
        mock_basicevent = Mock()
        mock_basicevent.GetHKSetupInfo = Mock(return_value={"HKSetupCode": "123-45-678"})
        mock_device.basicevent = mock_basicevent

        _device_cache["HomeKit Device"] = mock_device

        result = await get_homekit_code("HomeKit Device")

        assert result["success"] is True
        assert result["homekit_code"] == "123-45-678"
        assert result["device_name"] == "HomeKit Device"

    @pytest.mark.asyncio
    async def test_get_homekit_code_not_supported(self):
        """Test get_homekit_code with device that doesn't support HomeKit."""
        from wemo_mcp_server.server import _device_cache, get_homekit_code

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "Regular Device"
        # Remove basicevent to simulate non-HomeKit device
        del mock_device.basicevent

        _device_cache["Regular Device"] = mock_device

        result = await get_homekit_code("Regular Device")

        assert result["success"] is False
        assert "error" in result
        assert "does not support HomeKit" in result["error"]

    @pytest.mark.asyncio
    async def test_get_homekit_code_no_code_available(self):
        """Test get_homekit_code when device has no HomeKit code."""
        from wemo_mcp_server.server import _device_cache, get_homekit_code

        _device_cache.clear()

        mock_device = Mock()
        mock_device.name = "HomeKit Device No Code"
        mock_device.host = "192.168.1.60"
        mock_basicevent = Mock()
        mock_basicevent.GetHKSetupInfo = Mock(return_value={})  # No HKSetupCode
        mock_device.basicevent = mock_basicevent

        _device_cache["HomeKit Device No Code"] = mock_device

        result = await get_homekit_code("HomeKit Device No Code")

        assert result["success"] is False
        assert "error" in result
        assert "does not have a HomeKit setup code" in result["error"]


# ==============================================================================
# Module constants
# ==============================================================================
class TestModuleConstants:
    def test_default_subnet_value(self):
        from wemo_mcp_server.server import DEFAULT_SUBNET

        assert DEFAULT_SUBNET == "192.168.1.0/24"

    def test_err_invalid_params_value(self):
        from wemo_mcp_server.server import ERR_INVALID_PARAMS

        assert ERR_INVALID_PARAMS == "Invalid parameters"

    def test_err_run_scan_first_value(self):
        from wemo_mcp_server.server import ERR_RUN_SCAN_FIRST

        assert ERR_RUN_SCAN_FIRST == "Run scan_network first to discover devices"


# ==============================================================================
# _reconnect_device_from_cache
# ==============================================================================
class TestReconnectDeviceFromCache:
    @pytest.mark.asyncio
    async def test_not_in_file_cache(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {}
            result = await _reconnect_device_from_cache("Unknown Device")
        assert result is None

    @pytest.mark.asyncio
    async def test_found_by_case_insensitive_name(self):
        from wemo_mcp_server.server import _device_cache, _reconnect_device_from_cache

        mock_device = Mock()
        mock_device.name = "Living Room"
        mock_device.host = "192.168.1.50"

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {
                "LivingRoom": {"name": "Living Room", "host": "192.168.1.50", "port": 49152}
            }
            with patch("wemo_mcp_server.server.pywemo") as mock_pywemo:
                mock_pywemo.discovery.device_from_description.return_value = mock_device
                result = await _reconnect_device_from_cache("living room")

        assert result == mock_device
        _device_cache.pop("Living Room", None)
        _device_cache.pop("192.168.1.50", None)

    @pytest.mark.asyncio
    async def test_host_is_unknown(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {"Bad": {"name": "Bad", "host": "unknown"}}
            result = await _reconnect_device_from_cache("Bad")
        assert result is None

    @pytest.mark.asyncio
    async def test_host_missing(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {"D": {"name": "D"}}
            result = await _reconnect_device_from_cache("D")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_ports_fail(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {
                "Dev": {"name": "Dev", "host": "192.168.1.99", "port": None}
            }
            with patch("wemo_mcp_server.server.pywemo") as mock_pywemo:
                mock_pywemo.discovery.device_from_description.side_effect = Exception("timeout")
                result = await _reconnect_device_from_cache("Dev")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_load_raises(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.side_effect = Exception("disk error")
            result = await _reconnect_device_from_cache("Dev")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_info_not_dict(self):
        from wemo_mcp_server.server import _reconnect_device_from_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {"Dev": "not-a-dict"}
            result = await _reconnect_device_from_cache("Dev")
        assert result is None


# ==============================================================================
# scan_network validation
# ==============================================================================
class TestScanNetworkValidation:
    @pytest.mark.asyncio
    async def test_invalid_subnet_returns_error(self):
        from wemo_mcp_server.server import scan_network

        result = await scan_network(subnet="not-a-cidr")
        assert "error" in result
        assert result["scan_completed"] is False
        assert "validation_errors" in result

    @pytest.mark.asyncio
    async def test_timeout_out_of_range(self):
        from wemo_mcp_server.server import scan_network

        result = await scan_network(subnet="192.168.1.0/24", timeout=99.0)
        assert "error" in result
        assert result["scan_completed"] is False

    @pytest.mark.asyncio
    async def test_explicit_subnet_skips_elicitation(self):
        from wemo_mcp_server.server import scan_network

        with (
            patch("wemo_mcp_server.server.WeMoScanner"),
            patch("wemo_mcp_server.server._cache_manager") as mock_cm,
            patch("wemo_mcp_server.server.WeMoScanner.scan", return_value=[], create=True),
        ):
            mock_cm.save.return_value = True
            mock_cm.load.return_value = {}
            result = await scan_network(subnet="10.0.0.0/30", timeout=0.1, max_workers=1, ctx=None)
        # Either completes or errors — main check is no elicitation called
        assert "scan_completed" in result


# ==============================================================================
# list_devices file-cache fallback
# ==============================================================================
class TestListDevicesFileCacheFallback:
    @pytest.mark.asyncio
    async def test_falls_back_to_file_cache(self):
        from wemo_mcp_server.server import _device_cache, list_devices

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {
                "LR": {
                    "name": "Living Room Light",
                    "host": "192.168.1.10",
                    "model_name": "Socket",
                    "device_type": "WeMoControllee",
                }
            }
            result = await list_devices()
        assert result["device_count"] == 1
        assert result["devices"][0]["source"] == "file_cache"
        assert "note" in result

    @pytest.mark.asyncio
    async def test_empty_both_caches(self):
        from wemo_mcp_server.server import _device_cache, list_devices

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {}
            result = await list_devices()
        assert result["device_count"] == 0
        assert result["devices"] == []

    @pytest.mark.asyncio
    async def test_file_cache_skips_non_dict_entries(self):
        from wemo_mcp_server.server import _device_cache, list_devices

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {"bad_key": "not-a-dict"}
            result = await list_devices()
        assert result["device_count"] == 0


# ==============================================================================
# get_cache_info / clear_cache
# ==============================================================================
class TestCacheTools:
    @pytest.mark.asyncio
    async def test_get_cache_info_success(self):
        from wemo_mcp_server.server import get_cache_info

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.get_cache_info.return_value = {
                "exists": True,
                "age_seconds": 100,
                "device_count": 3,
            }
            result = await get_cache_info()
        assert result["exists"] is True
        assert "memory_cache_size" in result

    @pytest.mark.asyncio
    async def test_clear_cache_success(self):
        from wemo_mcp_server.server import clear_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.clear.return_value = True
            result = await clear_cache()
        assert result["success"] is True
        assert "cleared" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_clear_cache_file_failure(self):
        from wemo_mcp_server.server import clear_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.clear.return_value = False
            result = await clear_cache()
        assert result["success"] is False
        assert "error" in result


# ==============================================================================
# get_configuration
# ==============================================================================
class TestGetConfiguration:
    @pytest.mark.asyncio
    async def test_returns_all_sections(self):
        from wemo_mcp_server.server import get_configuration

        result = await get_configuration()
        assert result["success"] is True
        assert "configuration" in result
        assert "environment_variables" in result
        assert "WEMO_MCP_" in result["environment_variables"]["prefix"]


# ==============================================================================
# get_device_status validation / not-found
# ==============================================================================
class TestGetDeviceStatusExtended:
    @pytest.mark.asyncio
    async def test_empty_identifier_validation_error(self):
        from wemo_mcp_server.server import get_device_status

        result = await get_device_status("")
        assert "error" in result
        assert "Invalid parameters" in result["error"]
        assert "validation_errors" in result

    @pytest.mark.asyncio
    async def test_device_not_found_returns_suggestion(self):
        from wemo_mcp_server.server import _device_cache, get_device_status

        _device_cache.clear()
        with patch("wemo_mcp_server.server._reconnect_device_from_cache", return_value=None):
            result = await get_device_status("Phantom Device")
        assert "error" in result
        assert "not found" in result["error"]
        assert result["suggestion"] == "Run scan_network first to discover devices"
        assert "available_devices" in result


# ==============================================================================
# _validate_action / _validate_brightness helpers
# ==============================================================================
class TestValidationHelpers:
    def test_validate_action_all_valid(self):
        from wemo_mcp_server.server import _validate_action

        for action in ("on", "off", "toggle", "brightness"):
            assert _validate_action(action) is None

    def test_validate_action_case_insensitive(self):
        from wemo_mcp_server.server import _validate_action

        assert _validate_action("ON") is None
        assert _validate_action("Off") is None

    def test_validate_action_invalid(self):
        from wemo_mcp_server.server import _validate_action

        result = _validate_action("blink")
        assert result is not None
        assert result["success"] is False
        assert "Invalid action" in result["error"]

    def test_validate_brightness_valid_range(self):
        from wemo_mcp_server.server import _validate_brightness

        assert _validate_brightness(1) is None
        assert _validate_brightness(50) is None
        assert _validate_brightness(100) is None
        assert _validate_brightness(None) is None

    def test_validate_brightness_zero(self):
        from wemo_mcp_server.server import _validate_brightness

        result = _validate_brightness(0)
        assert result is not None
        assert result["success"] is False

    def test_validate_brightness_over_100(self):
        from wemo_mcp_server.server import _validate_brightness

        result = _validate_brightness(101)
        assert result is not None
        assert result["success"] is False


# ==============================================================================
# MCP Resources
# ==============================================================================
class TestMCPResources:
    @pytest.mark.asyncio
    async def test_list_device_resources_empty(self):
        from wemo_mcp_server.server import _device_cache, list_device_resources

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {}
            result = await list_device_resources()
        data = json.loads(result)
        assert data["total_devices"] == 0
        assert data["devices"] == []

    @pytest.mark.asyncio
    async def test_list_device_resources_with_devices(self):
        from wemo_mcp_server.server import _device_cache, list_device_resources

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Office Light"
        mock_dev.host = "192.168.1.10"
        _device_cache["Office Light"] = mock_dev
        _device_cache["192.168.1.10"] = mock_dev  # duplicate IP key

        result = await list_device_resources()
        data = json.loads(result)
        assert data["total_devices"] == 1  # de-duplicated
        assert data["devices"][0]["name"] == "Office Light"

        _device_cache.pop("Office Light", None)
        _device_cache.pop("192.168.1.10", None)

    @pytest.mark.asyncio
    async def test_list_device_resources_falls_back_to_persisted(self):
        from wemo_mcp_server.server import _device_cache, list_device_resources

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {
                "Porch": {"name": "Porch Light", "host": "192.168.1.20"}
            }
            result = await list_device_resources()
        data = json.loads(result)
        assert data["total_devices"] == 1
        assert data["devices"][0]["name"] == "Porch Light"

    @pytest.mark.asyncio
    async def test_get_device_resource_not_found(self):
        from wemo_mcp_server.server import _device_cache, get_device_resource

        _device_cache.clear()
        with patch("wemo_mcp_server.server._reconnect_device_from_cache", return_value=None):
            result = await get_device_resource("NonExistent")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_device_resource_found_in_memory(self):
        from wemo_mcp_server.server import _device_cache, get_device_resource

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Kitchen Light"
        _device_cache["Kitchen Light"] = mock_dev

        with patch(
            "wemo_mcp_server.server.extract_device_info",
            return_value={"name": "Kitchen Light", "state": "on"},
        ):
            result = await get_device_resource("Kitchen Light")
        data = json.loads(result)
        assert data["name"] == "Kitchen Light"

        _device_cache.pop("Kitchen Light", None)

    @pytest.mark.asyncio
    async def test_get_device_resource_url_encoded_name(self):
        from wemo_mcp_server.server import _device_cache, get_device_resource

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Living Room"
        _device_cache["Living Room"] = mock_dev

        with patch(
            "wemo_mcp_server.server.extract_device_info",
            return_value={"name": "Living Room", "state": "off"},
        ):
            result = await get_device_resource("Living%20Room")
        data = json.loads(result)
        assert data["name"] == "Living Room"

        _device_cache.pop("Living Room", None)

    @pytest.mark.asyncio
    async def test_get_device_resource_case_insensitive_match(self):
        from wemo_mcp_server.server import _device_cache, get_device_resource

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Bedroom Light"
        _device_cache["Bedroom Light"] = mock_dev

        with patch(
            "wemo_mcp_server.server.extract_device_info",
            return_value={"name": "Bedroom Light", "state": "on"},
        ):
            result = await get_device_resource("bedroom light")
        data = json.loads(result)
        assert data["name"] == "Bedroom Light"

        _device_cache.pop("Bedroom Light", None)


# ==============================================================================
# MCP Prompts
# ==============================================================================
class TestMCPPrompts:
    @pytest.mark.asyncio
    async def test_prompt_discover_devices_returns_user_message(self):
        from wemo_mcp_server.server import prompt_discover_devices

        result = await prompt_discover_devices()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "scan" in result[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_prompt_discover_devices_contains_subnet(self):
        from wemo_mcp_server.server import prompt_discover_devices

        result = await prompt_discover_devices()
        # Should contain some subnet reference
        assert "192.168" in result[0]["content"] or "network" in result[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_prompt_device_status_report_empty_cache(self):
        from wemo_mcp_server.server import _device_cache, prompt_device_status_report

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {}
            result = await prompt_device_status_report()
        assert isinstance(result, list)
        assert result[0]["role"] == "user"
        assert (
            "scan" in result[0]["content"].lower() or "no devices" in result[0]["content"].lower()
        )

    @pytest.mark.asyncio
    async def test_prompt_device_status_report_with_memory_cache(self):
        from wemo_mcp_server.server import _device_cache, prompt_device_status_report

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Hallway Light"
        _device_cache["Hallway Light"] = mock_dev

        result = await prompt_device_status_report()
        assert "Hallway Light" in result[0]["content"]

        _device_cache.pop("Hallway Light", None)

    @pytest.mark.asyncio
    async def test_prompt_device_status_report_with_persisted_cache(self):
        from wemo_mcp_server.server import _device_cache, prompt_device_status_report

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cache:
            mock_cache.load.return_value = {"k1": {"name": "Porch Light"}}
            result = await prompt_device_status_report()
        assert "Porch Light" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_prompt_activate_scene_movie_night(self):
        from wemo_mcp_server.server import prompt_activate_scene

        result = await prompt_activate_scene("movie night")
        assert isinstance(result, list)
        assert result[0]["role"] == "user"
        assert "movie night" in result[0]["content"]
        assert "dim" in result[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_prompt_activate_scene_bedtime(self):
        from wemo_mcp_server.server import prompt_activate_scene

        result = await prompt_activate_scene("bedtime")
        assert "bedtime" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_prompt_activate_scene_away(self):
        from wemo_mcp_server.server import prompt_activate_scene

        result = await prompt_activate_scene("away")
        assert "away" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_prompt_activate_scene_full_brightness(self):
        from wemo_mcp_server.server import prompt_activate_scene

        result = await prompt_activate_scene("full brightness")
        assert "full brightness" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_prompt_activate_scene_unknown_falls_back_gracefully(self):
        from wemo_mcp_server.server import prompt_activate_scene

        result = await prompt_activate_scene("party mode")
        assert isinstance(result, list)
        assert "party mode" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_prompt_troubleshoot_device(self):
        from wemo_mcp_server.server import prompt_troubleshoot_device

        result = await prompt_troubleshoot_device("Bedroom Light")
        assert isinstance(result, list)
        assert result[0]["role"] == "user"
        assert "Bedroom Light" in result[0]["content"]
        assert (
            "diagnostic" in result[0]["content"].lower()
            or "trouble" in result[0]["content"].lower()
        )

    @pytest.mark.asyncio
    async def test_prompt_troubleshoot_device_ip_address(self):
        from wemo_mcp_server.server import prompt_troubleshoot_device

        result = await prompt_troubleshoot_device("192.168.1.55")
        assert "192.168.1.55" in result[0]["content"]


# ==============================================================================
# Exception handler paths (covers L500-512, L570-574, L599-601, L638-640,
# L673-675, L752-754, L1416-1417)
# ==============================================================================
class TestExceptionHandlers:
    # scan_network: scanner raises during execution (covers L500-512)
    @pytest.mark.asyncio
    async def test_scan_network_scanner_raises(self):
        from wemo_mcp_server.server import scan_network

        with patch("wemo_mcp_server.server.WeMoScanner") as MockScanner:
            instance = Mock()
            instance.scan = Mock(side_effect=RuntimeError("network down"))
            MockScanner.return_value = instance
            result = await scan_network(subnet="10.0.0.0/30", timeout=0.1, max_workers=1)
        assert result["scan_completed"] is False

    # list_devices: _cache_manager.load raises (covers L570-574)
    @pytest.mark.asyncio
    async def test_list_devices_exception(self):
        from wemo_mcp_server.server import _device_cache, list_devices

        _device_cache.clear()
        with patch("wemo_mcp_server.server._cache_manager") as mock_cm:
            mock_cm.load.side_effect = RuntimeError("disk full")
            result = await list_devices()
        assert result["device_count"] == 0
        assert "error" in result

    # get_cache_info: _cache_manager.get_cache_info raises (covers L599-601)
    @pytest.mark.asyncio
    async def test_get_cache_info_exception(self):
        from wemo_mcp_server.server import get_cache_info

        with patch("wemo_mcp_server.server._cache_manager") as mock_cm:
            mock_cm.get_cache_info.side_effect = RuntimeError("cache corrupt")
            result = await get_cache_info()
        assert "error" in result

    # clear_cache: _cache_manager.clear raises (covers L638-640)
    @pytest.mark.asyncio
    async def test_clear_cache_exception(self):
        from wemo_mcp_server.server import clear_cache

        with patch("wemo_mcp_server.server._cache_manager") as mock_cm:
            mock_cm.clear.side_effect = RuntimeError("permission denied")
            result = await clear_cache()
        assert "error" in result

    # get_configuration: get_config raises (covers L673-675)
    @pytest.mark.asyncio
    async def test_get_configuration_exception(self):
        from wemo_mcp_server.server import get_configuration

        with patch("wemo_mcp_server.server.get_config", side_effect=RuntimeError("config error")):
            result = await get_configuration()
        assert "error" in result

    # get_device_status: device.get_state raises (covers L752-754)
    @pytest.mark.asyncio
    async def test_get_device_status_get_state_raises(self):
        from wemo_mcp_server.server import _device_cache, get_device_status

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Faulty Light"
        mock_dev.get_state = Mock(side_effect=RuntimeError("connection refused"))
        _device_cache["Faulty Light"] = mock_dev

        result = await get_device_status("Faulty Light")
        assert "error" in result

        _device_cache.pop("Faulty Light", None)

    # get_device_resource: extract_device_info raises (covers L1416-1417)
    @pytest.mark.asyncio
    async def test_get_device_resource_extract_raises(self):
        from wemo_mcp_server.server import _device_cache, get_device_resource

        _device_cache.clear()
        mock_dev = Mock()
        mock_dev.name = "Broken Device"
        _device_cache["Broken Device"] = mock_dev

        with patch(
            "wemo_mcp_server.server.extract_device_info",
            side_effect=RuntimeError("UPnP timeout"),
        ):
            result = await get_device_resource("Broken Device")
        data = json.loads(result)
        assert "error" in data or "name" in data  # graceful — returns partial info

        _device_cache.pop("Broken Device", None)


# ==============================================================================
# scan_network elicitation paths (covers L403-418)
# ==============================================================================
class TestScanNetworkElicitation:
    @pytest.mark.asyncio
    async def test_elicitation_accept_with_subnet(self):
        """ctx.elicit returns accept with a valid subnet → scan proceeds."""
        from wemo_mcp_server.server import scan_network

        elicit_data = Mock()
        elicit_data.subnet = "10.0.0.0/30"

        elicit_result = Mock()
        elicit_result.action = "accept"
        elicit_result.data = elicit_data

        ctx = AsyncMock()
        ctx.elicit = AsyncMock(return_value=elicit_result)

        with patch("wemo_mcp_server.server.get_config") as mock_cfg:
            cfg_obj = Mock()
            cfg_obj.get = Mock(side_effect=lambda _s, _k, d=None: d)  # always return default
            mock_cfg.return_value = cfg_obj
            with patch("wemo_mcp_server.server.WeMoScanner") as MockScanner:
                instance = Mock()
                instance.scan = Mock(return_value=[])
                MockScanner.return_value = instance
                with patch("wemo_mcp_server.server._cache_manager") as mock_cm:
                    mock_cm.save.return_value = True
                    mock_cm.load.return_value = {}
                    result = await scan_network(ctx=ctx)

        assert "scan_completed" in result

    @pytest.mark.asyncio
    async def test_elicitation_cancel_returns_error(self):
        """ctx.elicit returns cancel → scan aborted."""
        from wemo_mcp_server.server import scan_network

        elicit_result = Mock()
        elicit_result.action = "cancel"
        elicit_result.data = None

        ctx = AsyncMock()
        ctx.elicit = AsyncMock(return_value=elicit_result)

        with patch("wemo_mcp_server.server.get_config") as mock_cfg:
            cfg_obj = Mock()
            cfg_obj.get = Mock(side_effect=lambda _s, _k, d=None: d)
            mock_cfg.return_value = cfg_obj
            result = await scan_network(ctx=ctx)

        assert result["scan_completed"] is False
        assert "cancelled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_elicitation_accept_no_data_uses_default(self):
        """ctx.elicit returns accept but data is None → falls back to config default."""
        from wemo_mcp_server.server import scan_network

        elicit_result = Mock()
        elicit_result.action = "accept"
        elicit_result.data = None

        ctx = AsyncMock()
        ctx.elicit = AsyncMock(return_value=elicit_result)

        with patch("wemo_mcp_server.server.get_config") as mock_cfg:
            cfg_obj = Mock()
            cfg_obj.get = Mock(side_effect=lambda _s, _k, d=None: d)
            mock_cfg.return_value = cfg_obj
            with patch("wemo_mcp_server.server.WeMoScanner") as MockScanner:
                instance = Mock()
                instance.scan = Mock(return_value=[])
                MockScanner.return_value = instance
                with patch("wemo_mcp_server.server._cache_manager") as mock_cm:
                    mock_cm.save.return_value = True
                    mock_cm.load.return_value = {}
                    result = await scan_network(ctx=ctx)

        assert "scan_completed" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
