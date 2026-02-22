"""Pydantic models for input validation."""

import ipaddress
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ScanNetworkParams(BaseModel):
    """Parameters for network scanning."""

    subnet: str = Field(
        default="192.168.1.0/24",
        description="Network subnet in CIDR notation (e.g., '192.168.1.0/24')",
    )
    timeout: float = Field(
        default=0.6,
        ge=0.1,
        le=5.0,
        description="Connection timeout in seconds (0.1-5.0)",
    )
    max_workers: int = Field(
        default=60,
        ge=1,
        le=200,
        description="Maximum concurrent workers (1-200)",
    )

    @field_validator("subnet")
    @classmethod
    def validate_subnet(cls, v: str) -> str:
        """Validate CIDR notation."""
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError as e:
            error_msg = (
                f"Invalid CIDR notation '{v}'. Expected format: '192.168.1.0/24'. Error: {e}"
            )
            raise ValueError(error_msg) from e


class ControlDeviceParams(BaseModel):
    """Parameters for device control."""

    device_identifier: str = Field(
        min_length=1,
        max_length=255,
        description="Device name or IP address",
    )
    action: Literal["on", "off", "toggle", "brightness"] = Field(
        description="Action to perform: 'on', 'off', 'toggle', or 'brightness'",
    )
    brightness: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Brightness level (1-100, required for 'brightness' action)",
    )

    @field_validator("device_identifier")
    @classmethod
    def validate_device_identifier(cls, v: str) -> str:
        """Validate device identifier is not empty."""
        if not v.strip():
            raise ValueError("Device identifier cannot be empty")
        return v.strip()


class DeviceIdentifierParam(BaseModel):
    """Single device identifier parameter."""

    device_identifier: str = Field(
        min_length=1,
        max_length=255,
        description="Device name or IP address",
    )

    @field_validator("device_identifier")
    @classmethod
    def validate_device_identifier(cls, v: str) -> str:
        """Validate device identifier is not empty."""
        if not v.strip():
            raise ValueError("Device identifier cannot be empty")
        return v.strip()


class RenameDeviceParams(BaseModel):
    """Parameters for device renaming."""

    device_identifier: str = Field(
        min_length=1,
        max_length=255,
        description="Current device name or IP address",
    )
    new_name: str = Field(
        min_length=1,
        max_length=255,
        description="New friendly name for the device",
    )

    @field_validator("device_identifier", "new_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate strings are not empty."""
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()
