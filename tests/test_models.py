"""Tests for pydantic validation models."""

import pytest
from pydantic import ValidationError
from wemo_mcp_server.models import (
    ControlDeviceParams,
    DeviceIdentifierParam,
    RenameDeviceParams,
    ScanNetworkParams,
)


class TestScanNetworkParams:
    """Test ScanNetworkParams validation."""

    def test_valid_params_defaults(self):
        """Test valid parameters with defaults."""
        params = ScanNetworkParams(subnet="192.168.1.0/24")
        assert params.subnet == "192.168.1.0/24"
        assert params.timeout == 0.6
        assert params.max_workers == 60

    def test_valid_params_custom(self):
        """Test valid parameters with custom values."""
        params = ScanNetworkParams(
            subnet="10.0.0.0/16",
            timeout=1.5,
            max_workers=100,
        )
        assert params.subnet == "10.0.0.0/16"
        assert params.timeout == 1.5
        assert params.max_workers == 100

    def test_invalid_cidr_no_slash(self):
        """Test CIDR notation without slash is accepted (defaults to /32 or /128)."""
        # ipaddress.ip_network accepts IPs without prefix and defaults to /32
        params = ScanNetworkParams(subnet="192.168.1.1")
        assert params.subnet == "192.168.1.1"

    def test_invalid_cidr_bad_ip(self):
        """Test invalid CIDR notation with bad IP."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="999.999.999.999/24")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("subnet",)
        assert "CIDR notation" in errors[0]["msg"]

    def test_invalid_cidr_bad_prefix(self):
        """Test invalid CIDR notation with bad prefix."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="192.168.1.0/33")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("subnet",)
        assert "CIDR notation" in errors[0]["msg"]

    def test_timeout_too_low(self):
        """Test timeout below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="192.168.1.0/24", timeout=0.05)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("timeout",) for e in errors)

    def test_timeout_too_high(self):
        """Test timeout above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="192.168.1.0/24", timeout=10.0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("timeout",) for e in errors)

    def test_max_workers_too_low(self):
        """Test max_workers below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="192.168.1.0/24", max_workers=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_workers",) for e in errors)

    def test_max_workers_too_high(self):
        """Test max_workers above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            ScanNetworkParams(subnet="192.168.1.0/24", max_workers=300)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_workers",) for e in errors)


class TestControlDeviceParams:
    """Test ControlDeviceParams validation."""

    def test_valid_params_on(self):
        """Test valid 'on' action."""
        params = ControlDeviceParams(
            device_identifier="Office Light",
            action="on",
        )
        assert params.device_identifier == "Office Light"
        assert params.action == "on"
        assert params.brightness is None

    def test_valid_params_brightness(self):
        """Test valid 'brightness' action with brightness value."""
        params = ControlDeviceParams(
            device_identifier="192.168.1.100",
            action="brightness",
            brightness=75,
        )
        assert params.device_identifier == "192.168.1.100"
        assert params.action == "brightness"
        assert params.brightness == 75

    def test_invalid_action(self):
        """Test invalid action."""
        with pytest.raises(ValidationError) as exc_info:
            ControlDeviceParams(device_identifier="Light", action="invalid")  # type: ignore[arg-type]

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("action",) for e in errors)

    def test_brightness_too_low(self):
        """Test brightness below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            ControlDeviceParams(
                device_identifier="Light",
                action="brightness",
                brightness=0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("brightness",) for e in errors)

    def test_brightness_too_high(self):
        """Test brightness above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            ControlDeviceParams(
                device_identifier="Light",
                action="brightness",
                brightness=101,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("brightness",) for e in errors)

    def test_empty_device_identifier(self):
        """Test empty device identifier."""
        with pytest.raises(ValidationError) as exc_info:
            ControlDeviceParams(device_identifier="", action="on")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("device_identifier",) for e in errors)

    def test_whitespace_only_device_identifier(self):
        """Test whitespace-only device identifier."""
        with pytest.raises(ValidationError) as exc_info:
            ControlDeviceParams(device_identifier="   ", action="on")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("device_identifier",) for e in errors)


class TestDeviceIdentifierParam:
    """Test DeviceIdentifierParam validation."""

    def test_valid_device_name(self):
        """Test valid device name."""
        param = DeviceIdentifierParam(device_identifier="Office Light")
        assert param.device_identifier == "Office Light"

    def test_valid_ip_address(self):
        """Test valid IP address."""
        param = DeviceIdentifierParam(device_identifier="192.168.1.100")
        assert param.device_identifier == "192.168.1.100"

    def test_empty_identifier(self):
        """Test empty device identifier."""
        with pytest.raises(ValidationError) as exc_info:
            DeviceIdentifierParam(device_identifier="")

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("device_identifier",)
        # Pydantic's min_length validator triggers first
        assert "at least 1 character" in errors[0]["msg"]

    def test_whitespace_only_identifier(self):
        """Test whitespace-only device identifier."""
        with pytest.raises(ValidationError) as exc_info:
            DeviceIdentifierParam(device_identifier="   ")

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("device_identifier",)
        assert "cannot be empty" in errors[0]["msg"]


class TestRenameDeviceParams:
    """Test RenameDeviceParams validation."""

    def test_valid_params(self):
        """Test valid parameters."""
        params = RenameDeviceParams(
            device_identifier="Old Name",
            new_name="New Name",
        )
        assert params.device_identifier == "Old Name"
        assert params.new_name == "New Name"

    def test_empty_device_identifier(self):
        """Test empty device identifier."""
        with pytest.raises(ValidationError) as exc_info:
            RenameDeviceParams(device_identifier="", new_name="New Name")

        errors = exc_info.value.errors()
        # Pydantic's min_length validator triggers first
        assert any(
            e["loc"] == ("device_identifier",) and "at least 1 character" in e["msg"]
            for e in errors
        )

    def test_empty_new_name(self):
        """Test empty new name."""
        with pytest.raises(ValidationError) as exc_info:
            RenameDeviceParams(device_identifier="Old Name", new_name="")

        errors = exc_info.value.errors()
        # Pydantic's min_length validator triggers first
        assert any(e["loc"] == ("new_name",) and "at least 1 character" in e["msg"] for e in errors)

    def test_whitespace_only_new_name(self):
        """Test whitespace-only new name."""
        with pytest.raises(ValidationError) as exc_info:
            RenameDeviceParams(device_identifier="Old Name", new_name="   ")

        errors = exc_info.value.errors()
        # Custom validator catches whitespace-only strings
        assert any(e["loc"] == ("new_name",) and "cannot be empty" in e["msg"] for e in errors)

    def test_new_name_too_long(self):
        """Test new name exceeding max length."""
        long_name = "A" * 256  # Exceeds 255 character limit
        with pytest.raises(ValidationError) as exc_info:
            RenameDeviceParams(device_identifier="Old Name", new_name=long_name)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("new_name",) for e in errors)

    def test_new_name_at_max_length(self):
        """Test new name at exactly max length (should be valid)."""
        max_name = "A" * 255  # Exactly 255 characters
        params = RenameDeviceParams(
            device_identifier="Old Name",
            new_name=max_name,
        )
        assert params.new_name == max_name
