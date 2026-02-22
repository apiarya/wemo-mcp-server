"""Unit tests for WeMo MCP server components."""

from unittest.mock import Mock, patch

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
        assert result["cache_keys"] == 4  # 4 total cache entries (name + IP for each)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
