"""Main MCP server implementation for WeMo device management."""

import asyncio
import concurrent.futures
import ipaddress
import json
import logging
import socket
import sys
import time
from typing import Any
from urllib.parse import unquote

import pywemo
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, ValidationError

from .cache import _cache_manager, serialize_device
from .config import get_config
from .error_handling import build_error_response, retry_on_network_error
from .models import (
    ControlDeviceParams,
    DeviceIdentifierParam,
    RenameDeviceParams,
    ScanNetworkParams,
)

# Configure logging to stderr for MCP
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("wemo-mcp-server")

# Global device cache to store discovered devices
_device_cache: dict[str, Any] = {}  # key: device name or IP, value: pywemo device object


# Elicitation schemas — lightweight Pydantic models used by ctx.elicit()
class _DeviceChoiceSchema(BaseModel):
    """User selects a device by name when the requested device is not found."""

    device_name: str


class _SubnetChoiceSchema(BaseModel):
    """User provides the subnet to scan when none is configured."""

    subnet: str


async def _reconnect_device_from_cache(identifier: str) -> Any | None:
    """Try to reconnect to a device using its cached IP address.

    When the in-memory cache is empty (e.g. after server restart), this looks up
    the device in the persistent JSON cache and re-establishes a live pywemo
    connection using the stored host/port.

    Args:
    ----
        identifier: Device name or IP address

    Returns:
    -------
        pywemo device object if reconnected successfully, None otherwise

    """
    try:
        cached_devices = _cache_manager.load()
        if not cached_devices:
            return None

        # Look up by exact identifier first, then case-insensitive name match
        device_info = cached_devices.get(identifier)
        if not device_info or not isinstance(device_info, dict):
            lower_id = identifier.lower()
            for data in cached_devices.values():
                if isinstance(data, dict) and data.get("name", "").lower() == lower_id:
                    device_info = data
                    break

        if not device_info or not isinstance(device_info, dict):
            return None

        host = device_info.get("host")
        port = device_info.get("port")
        if not host or host == "unknown":
            return None

        ports_to_try = [port] if port else [49152, 49153, 49154, 49155]

        def try_reconnect() -> Any | None:
            for p in ports_to_try:
                try:
                    url = f"http://{host}:{p}/setup.xml"
                    dev = pywemo.discovery.device_from_description(url)
                    if dev:
                        logger.info(f"Reconnected to {dev.name} at {host}:{p} from file cache")
                        return dev
                except Exception:
                    pass
            return None

        loop = asyncio.get_event_loop()
        device = await loop.run_in_executor(None, try_reconnect)

        if device:
            _device_cache[device.name] = device
            if hasattr(device, "host"):
                _device_cache[device.host] = device

        return device

    except Exception as e:
        logger.warning(f"Failed to reconnect device '{identifier}' from file cache: {e}")
        return None


# ==============================================================================
#  WeMo Device Scanner (using pywemo)
# ==============================================================================


class WeMoScanner:
    """Scanner for discovering WeMo devices on the network using pywemo."""

    def __init__(self):
        """Initialize the WeMo scanner with default timeout and port configuration."""
        self.timeout = 0.6
        self.wemo_ports = [49152, 49153, 49154, 49155]

    def probe_port(
        self, ip: str, ports: list[int] | None = None, timeout: float | None = None
    ) -> str | None:
        """Probe an IP address on common WeMo ports.

        Args:
        ----
            ip: IP address to probe
            ports: List of ports to check (default: WeMo ports)
            timeout: Connection timeout

        Returns:
        -------
            IP address if responsive, None otherwise

        """
        if ports is None:
            ports = self.wemo_ports
        if timeout is None:
            timeout = self.timeout

        for port in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                s.connect((str(ip), port))
                s.close()
                return str(ip)
            except:
                pass
            finally:
                s.close()
        return None

    def _run_upnp_discovery(self) -> list[Any]:
        """Run UPnP/SSDP discovery phase.

        Returns
        -------
            List of devices found via UPnP/SSDP

        """
        logger.info("Phase 1: Running UPnP/SSDP discovery (primary method)...")
        try:
            upnp_devices = pywemo.discover_devices()
            logger.info(f"UPnP/SSDP found {len(upnp_devices)} WeMo devices")
            for dev in upnp_devices:
                logger.info(f"  • {dev.name} at {dev.host}:{dev.port}")
            return list(upnp_devices)
        except Exception as e:
            logger.warning(f"UPnP discovery failed: {e}")
            return []

    def _parse_cidr_network(self, target_cidr: str) -> list[Any] | None:
        """Parse CIDR notation and return list of hosts.

        Args:
        ----
            target_cidr: CIDR notation subnet

        Returns:
        -------
            List of IP addresses to scan, or None if invalid

        """
        try:
            network = ipaddress.ip_network(target_cidr, strict=False)
            all_hosts = list(network.hosts())
            logger.info(f"Phase 2: Backup port scan on {len(all_hosts)} hosts in {target_cidr}")
            return all_hosts
        except Exception as e:
            logger.error(f"Invalid CIDR notation: {target_cidr} - {e}")
            return None

    def _probe_active_ips(self, all_hosts: list[Any], max_workers: int) -> list[str]:
        """Probe hosts for active IPs on WeMo ports.

        Args:
        ----
            all_hosts: List of IP addresses to probe
            max_workers: Maximum concurrent workers

        Returns:
        -------
            List of active IP addresses

        """
        active_ips = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.probe_port, ip): ip for ip in all_hosts}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    active_ips.append(result)
                    logger.debug(f"Active IP found: {result}")
        return active_ips

    def _verify_wemo_devices(
        self,
        active_ips_to_check: list[str],
        max_workers: int,
    ) -> list[Any]:
        """Verify if active IPs are WeMo devices.

        Args:
        ----
            active_ips_to_check: List of IPs to verify
            max_workers: Maximum concurrent workers

        Returns:
        -------
            List of verified WeMo device objects

        """
        if not active_ips_to_check:
            return []

        logger.info(f"Found {len(active_ips_to_check)} new active IPs to verify...")

        # Temporarily reduce pywemo's timeout to speed up scans
        original_timeout = pywemo.discovery.REQUESTS_TIMEOUT
        pywemo.discovery.REQUESTS_TIMEOUT = 5

        def verify_device(ip: str) -> Any | None:
            """Try to verify if an IP is a WeMo device."""
            for port in self.wemo_ports:
                try:
                    url = f"http://{ip}:{port}/setup.xml"
                    dev = pywemo.discovery.device_from_description(url)
                    if dev:
                        logger.info(f"WeMo device found via port scan: {dev.name} at {ip}:{port}")
                        return dev
                except Exception:
                    pass
            return None

        # Parallelize device verification
        verified_devices = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            verification_futures = {
                executor.submit(verify_device, ip): ip for ip in active_ips_to_check
            }
            for future in concurrent.futures.as_completed(verification_futures):
                device = future.result()
                if device:
                    verified_devices.append(device)

        # Restore original timeout
        pywemo.discovery.REQUESTS_TIMEOUT = original_timeout

        return verified_devices

    def scan_subnet(self, target_cidr: str, max_workers: int = 60) -> list[Any]:
        """Scan a subnet for WeMo devices.

        Uses UPnP/SSDP discovery FIRST (primary method), then port scanning as backup.
        This matches the proven approach from wemo-ops-center UI.

        Args:
        ----
            target_cidr: CIDR notation subnet (e.g., "192.168.1.0/24")
            max_workers: Maximum concurrent workers for scanning

        Returns:
        -------
            List of discovered pywemo device objects

        """
        # Phase 1: UPnP/SSDP Discovery (PRIMARY)
        found_devices = self._run_upnp_discovery()

        # Parse and validate CIDR network
        all_hosts = self._parse_cidr_network(target_cidr)
        if all_hosts is None:
            return found_devices

        # Phase 2: Probe for active IPs
        active_ips = self._probe_active_ips(all_hosts, max_workers)

        # Phase 3: Verify active IPs (only check IPs not already found via UPnP)
        found_ips = {d.host for d in found_devices if hasattr(d, "host")}
        active_ips_to_check = [ip for ip in active_ips if ip not in found_ips]

        verified_devices = self._verify_wemo_devices(active_ips_to_check, max_workers)
        found_devices.extend(verified_devices)

        logger.info(f"Scan complete. Found {len(found_devices)} WeMo devices total")
        return found_devices


def extract_device_info(device: Any) -> dict[str, Any]:
    """Extract device information from a pywemo device object.

    Args:
    ----
        device: pywemo device object

    Returns:
    -------
        Dictionary containing device information

    """
    try:
        return {
            "name": device.name,
            "model": device.model_name if hasattr(device, "model_name") else device.model,
            "serial_number": getattr(device, "serial_number", "N/A"),
            "ip_address": device.host if hasattr(device, "host") else "unknown",
            "port": device.port if hasattr(device, "port") else 49153,
            "mac_address": device.mac if hasattr(device, "mac") else "N/A",
            "firmware_version": (
                device.firmware_version if hasattr(device, "firmware_version") else "N/A"
            ),
            "state": (
                "on" if device.get_state() else "off" if hasattr(device, "get_state") else "unknown"
            ),
            "device_type": type(device).__name__,
            "manufacturer": "Belkin",
        }
    except Exception as e:
        logger.warning(f"Error extracting device info: {e}")
        return {
            "name": getattr(device, "name", "Unknown"),
            "model": getattr(device, "model", "Unknown"),
            "error": str(e),
        }


@mcp.tool()
async def scan_network(
    subnet: str | None = None,
    timeout: float | None = None,
    max_workers: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Scan network for WeMo devices using pywemo discovery.

    This tool scans the specified subnet for WeMo devices by:
    1. Probing all IPs in the subnet on common WeMo ports (49152-49155)
    2. Verifying responsive IPs by attempting to read device descriptions
    3. Using pywemo library to properly identify and parse WeMo devices

    Args:
    ----
        subnet: Network subnet in CIDR notation (default: from config or "192.168.1.0/24")
        timeout: Connection timeout in seconds for port probing (default: from config or 0.6)
        max_workers: Maximum concurrent workers for network scanning (default: from config or 60)
        ctx: MCP context injected by FastMCP; used to elicit the subnet when none is configured

    Returns:
    -------
        Dictionary containing:
        - scan_parameters: The parameters used for scanning
        - results: Summary with device counts
        - devices: List of discovered WeMo devices with full details

    """
    # Get configuration
    config = get_config()

    # Use config defaults if not provided
    if subnet is None:
        config_subnet = config.get("network", "default_subnet", "192.168.1.0/24")
        if config_subnet == "192.168.1.0/24" and ctx is not None:
            # No custom subnet configured — ask the user rather than scanning the wrong network
            elicit_result = await ctx.elicit(
                "No subnet is configured. Which subnet should I scan? "
                "(e.g. 192.168.1.0/24 — check your router for your local network range)",
                schema=_SubnetChoiceSchema,
            )
            if elicit_result.action == "accept" and elicit_result.data:
                subnet = elicit_result.data.subnet
            elif elicit_result.action != "accept":
                return {"error": "Scan cancelled by user", "scan_completed": False}
            else:
                subnet = config_subnet
        else:
            subnet = config_subnet
    if timeout is None:
        timeout = config.get("network", "scan_timeout", 0.6)
    if max_workers is None:
        max_workers = config.get("network", "max_workers", 60)

    # Validate inputs
    try:
        params = ScanNetworkParams(subnet=subnet, timeout=timeout, max_workers=max_workers)
    except ValidationError as e:
        return {
            "error": "Invalid parameters",
            "validation_errors": [
                {"field": err["loc"][0], "message": err["msg"], "input": err["input"]}
                for err in e.errors()
            ],
            "scan_completed": False,
        }

    start_time = time.time()

    try:
        logger.info(f"Starting WeMo network scan for subnet: {params.subnet}")

        # Create scanner instance
        scanner = WeMoScanner()
        scanner.timeout = params.timeout

        # Run the synchronous scan in a thread pool to keep async interface
        loop = asyncio.get_event_loop()
        devices = await loop.run_in_executor(
            None,
            scanner.scan_subnet,
            params.subnet,
            params.max_workers,
        )

        # Extract device information
        device_list = []
        for device in devices:
            device_info = extract_device_info(device)
            device_list.append(device_info)

            # Cache the device object for later control operations
            _device_cache[device.name] = device
            if hasattr(device, "host"):
                _device_cache[device.host] = device

        elapsed_time = time.time() - start_time

        # Save device info to persistent cache
        device_cache_data = {}
        for device in devices:
            device_cache_data[device.name] = serialize_device(device)
            if hasattr(device, "host"):
                device_cache_data[device.host] = serialize_device(device)

        cache_saved = _cache_manager.save(device_cache_data)

        scan_result = {
            "scan_parameters": {
                "subnet": params.subnet,
                "timeout": params.timeout,
                "max_workers": params.max_workers,
            },
            "results": {
                "total_devices_found": len(device_list),
                "wemo_devices": len(device_list),
                "scan_duration_seconds": round(elapsed_time, 2),
            },
            "devices": device_list,
            "scan_completed": True,
            "cache_saved": cache_saved,
            "timestamp": time.time(),
        }

        logger.info(
            f"Scan completed in {elapsed_time:.2f}s. Found {len(device_list)} WeMo devices. "
            f"Cache {'saved' if cache_saved else 'save failed'}.",
        )
        return scan_result

    except Exception as e:
        logger.error(f"Network scan error: {e!s}", exc_info=True)
        error_response = build_error_response(
            e,
            "Network scan",
            context={
                "subnet": params.subnet,
                "timeout": params.timeout,
                "max_workers": params.max_workers,
            },
        )
        error_response["scan_completed"] = False
        return error_response


@mcp.tool()
async def list_devices() -> dict[str, Any]:
    """List all discovered WeMo devices from the cache.

    Returns a list of devices that were found in previous network scans.
    Run scan_network first to populate the device cache.

    Returns
    -------
        Dictionary containing:
        - device_count: Number of cached devices
        - devices: List of device names and IPs

    """
    try:
        # Get unique devices from in-memory cache (device cache may have duplicates by name and IP)
        unique_devices: dict[str, dict[str, Any]] = {}
        for key, device in _device_cache.items():
            device_name = device.name
            if device_name not in unique_devices:
                unique_devices[device_name] = {
                    "name": device_name,
                    "ip_address": getattr(device, "host", "unknown"),
                    "model": getattr(device, "model", "Unknown"),
                    "type": type(device).__name__,
                    "source": "memory",
                }

        # If in-memory cache is empty, fall back to persistent JSON cache
        if not unique_devices:
            cached_data = _cache_manager.load()
            if cached_data:
                for _key, info in cached_data.items():
                    if not isinstance(info, dict):
                        continue
                    name = info.get("name", _key)
                    if name not in unique_devices:
                        unique_devices[name] = {
                            "name": name,
                            "ip_address": info.get("host", "unknown"),
                            "model": info.get("model_name") or info.get("model", "Unknown"),
                            "type": info.get("device_type", "Unknown"),
                            "source": "file_cache",
                        }

        result: dict[str, Any] = {
            "device_count": len(unique_devices),
            "devices": list(unique_devices.values()),
        }
        if unique_devices and all(d.get("source") == "file_cache" for d in unique_devices.values()):
            result["note"] = (
                "Devices loaded from persistent cache file (server was restarted). "
                "Control commands will automatically reconnect to devices as needed."
            )
        return result
    except Exception as e:
        logger.error(f"Error listing devices: {e}", exc_info=True)
        error_response = build_error_response(e, "List devices")
        error_response.update({"device_count": 0, "devices": []})
        return error_response


@mcp.tool()
async def get_cache_info() -> dict[str, Any]:
    """Get information about the persistent device cache.

    Returns information about the cache file including age, expiration status,
    and device count. Useful for determining if a rescan is needed.

    Returns
    -------
        Dictionary containing:
        - exists: Whether cache file exists
        - path: Path to cache file
        - age_seconds: Age of cache in seconds
        - expired: Whether cache has expired
        - device_count: Number of devices in cache
        - ttl_seconds: Time-to-live for cache entries

    """
    try:
        cache_info = _cache_manager.get_cache_info()
        cache_info["memory_cache_size"] = len(_device_cache)
        return cache_info
    except Exception as e:
        logger.error(f"Error getting cache info: {e}", exc_info=True)
        return build_error_response(e, "Get cache info")


@mcp.tool()
async def clear_cache() -> dict[str, Any]:
    """Clear the persistent device cache.

    Removes the cache file and clears in-memory cache. Useful when devices
    have changed or cache is corrupted. Run scan_network after clearing
    to rebuild the cache.

    Returns
    -------
        Dictionary containing:
        - success: Whether cache was cleared successfully
        - message: Descriptive message

    """
    try:
        # Clear persistent cache
        cache_cleared = _cache_manager.clear()

        # Clear in-memory cache
        _device_cache.clear()

        if cache_cleared:
            return {
                "success": True,
                "message": "Cache cleared successfully. Run scan_network to rebuild cache.",
                "timestamp": time.time(),
            }
        return {
            "success": False,
            "error": "Failed to clear cache file",
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return build_error_response(e, "Clear cache")


@mcp.tool()
async def get_configuration() -> dict[str, Any]:
    """Get current server configuration.

    Returns all configuration settings including network parameters,
    cache settings, and logging levels. Useful for debugging or verifying
    environment variable overrides.

    Returns
    -------
        Dictionary containing:
        - configuration: All configuration sections
        - source: Information about configuration sources (env vars, config file)

    """
    try:
        config = get_config()
        return {
            "success": True,
            "configuration": config.get_all(),
            "environment_variables": {
                "prefix": "WEMO_MCP_",
                "examples": [
                    "WEMO_MCP_DEFAULT_SUBNET=192.168.1.0/24",
                    "WEMO_MCP_CACHE_TTL=7200",
                    "WEMO_MCP_LOG_LEVEL=DEBUG",
                ],
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting configuration: {e}", exc_info=True)
        return build_error_response(e, "Get configuration")


@mcp.tool()
async def get_device_status(device_identifier: str) -> dict[str, Any]:
    """Get the current status of a WeMo device.

    Retrieves the current state and information for a device by name or IP address.
    The device must have been discovered via scan_network first.

    Args:
    ----
        device_identifier: Device name (e.g., "Office Light") or IP address (e.g., "192.168.1.100")

    Returns:
    -------
        Dictionary containing:
        - device_name: Name of the device
        - state: Current state ("on" or "off")
        - Additional device information

    """
    # Validate input
    try:
        param = DeviceIdentifierParam(device_identifier=device_identifier)
    except ValidationError as e:
        return {
            "error": "Invalid parameters",
            "validation_errors": [
                {"field": err["loc"][0], "message": err["msg"], "input": err["input"]}
                for err in e.errors()
            ],
        }

    try:
        # Try to find device in memory cache, then reconnect from file cache if needed
        device = _device_cache.get(param.device_identifier)
        if not device:
            device = await _reconnect_device_from_cache(param.device_identifier)

        if not device:
            return {
                "error": f"Device '{param.device_identifier}' not found in cache",
                "suggestion": "Run scan_network first to discover devices",
                "available_devices": [
                    k
                    for k in _device_cache
                    if isinstance(k, str) and not k.replace(".", "").isdigit()
                ],
            }

        # Get device state with retry
        state = await _get_device_state_with_retry(device)

        # Extract full device info
        device_info = extract_device_info(device)
        device_info["state"] = "on" if state else "off"
        device_info["status_retrieved_at"] = time.time()

        # Add brightness for dimmer devices
        if hasattr(device, "get_brightness"):
            brightness = await _get_device_brightness_with_retry(device)
            device_info["brightness"] = brightness
            device_info["is_dimmer"] = True
        else:
            device_info["is_dimmer"] = False

        logger.info(
            f"Status retrieved for {device.name}: {device_info['state']}"
            + (
                f" Brightness: {device_info.get('brightness')}"
                if device_info.get("is_dimmer")
                else ""
            ),
        )
        return device_info

    except Exception as e:
        logger.error(f"Error getting device status: {e}", exc_info=True)
        return build_error_response(
            e,
            "Get device status",
            context={"device_identifier": device_identifier},
        )


# ==============================================================================
#  Retry wrappers for device operations
# ==============================================================================


@retry_on_network_error(max_attempts=3, initial_delay=0.5)
async def _get_device_state_with_retry(device: Any) -> bool:
    """Get device state with automatic retry on network errors.

    Args:
    ----
        device: WeMo device object

    Returns:
    -------
        Device state (True=on, False=off)

    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, device.get_state, True)


@retry_on_network_error(max_attempts=3, initial_delay=0.5)
async def _get_device_brightness_with_retry(device: Any) -> int:
    """Get device brightness with automatic retry on network errors.

    Args:
    ----
        device: WeMo device object

    Returns:
    -------
        Brightness level (0-100)

    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, device.get_brightness, True)


@retry_on_network_error(max_attempts=3, initial_delay=0.5)
async def _set_device_state_with_retry(device: Any, state: bool) -> None:
    """Set device state with automatic retry on network errors.

    Args:
    ----
        device: WeMo device object
        state: Desired state (True=on, False=off)

    """
    loop = asyncio.get_event_loop()
    if state:
        await loop.run_in_executor(None, device.on)
    else:
        await loop.run_in_executor(None, device.off)


@retry_on_network_error(max_attempts=3, initial_delay=0.5)
async def _toggle_device_with_retry(device: Any) -> None:
    """Toggle device state with automatic retry on network errors.

    Args:
    ----
        device: WeMo device object

    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, device.toggle)


@retry_on_network_error(max_attempts=3, initial_delay=0.5)
async def _set_device_brightness_with_retry(device: Any, brightness: int) -> None:
    """Set device brightness with automatic retry on network errors.

    Args:
    ----
        device: WeMo device object
        brightness: Brightness level (1-100)

    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, device.set_brightness, brightness)


# ==============================================================================
#  Validation helper functions
# ==============================================================================


def _validate_action(action: str) -> dict[str, Any] | None:
    """Validate control action.

    Args:
    ----
        action: Action string to validate

    Returns:
    -------
        Error dict if invalid, None if valid

    """
    if action.lower() not in ["on", "off", "toggle", "brightness"]:
        return {
            "error": f"Invalid action '{action}'. Must be 'on', 'off', 'toggle', or 'brightness'",
            "success": False,
        }
    return None


def _validate_brightness(brightness: int | None) -> dict[str, Any] | None:
    """Validate brightness value.

    Args:
    ----
        brightness: Brightness value to validate

    Returns:
    -------
        Error dict if invalid, None if valid

    """
    if brightness is not None and (brightness < 1 or brightness > 100):
        return {
            "error": f"Invalid brightness '{brightness}'. Must be between 1 and 100",
            "success": False,
        }
    return None


async def _perform_device_action(
    device: Any,
    action: str,
    brightness: int | None,
    is_dimmer: bool,
) -> None:
    """Perform the requested action on device with automatic retry.

    Args:
    ----
        device: WeMo device object
        action: Action to perform
        brightness: Brightness value (if applicable)
        is_dimmer: Whether device is a dimmer

    """
    if action == "brightness":
        await _set_device_brightness_with_retry(device, brightness)
    elif action == "on":
        if is_dimmer and brightness is not None:
            await _set_device_brightness_with_retry(device, brightness)
        else:
            await _set_device_state_with_retry(device, True)
    elif action == "off":
        await _set_device_state_with_retry(device, False)
    elif action == "toggle":
        await _toggle_device_with_retry(device)


async def _build_control_result(device: Any, action: str, is_dimmer: bool) -> dict[str, Any]:
    """Build result dictionary after control action with retry.

    Args:
    ----
        device: WeMo device object
        action: Action that was performed
        is_dimmer: Whether device is a dimmer

    Returns:
    -------
        Result dictionary

    """
    new_state = await _get_device_state_with_retry(device)

    result = {
        "success": True,
        "device_name": device.name,
        "action_performed": action,
        "new_state": "on" if new_state else "off",
        "device_type": type(device).__name__,
        "timestamp": time.time(),
        "is_dimmer": is_dimmer,
    }

    if is_dimmer:
        current_brightness = await _get_device_brightness_with_retry(device)
        result["brightness"] = current_brightness

    return result


@mcp.tool()
async def control_device(
    device_identifier: str,
    action: str,
    brightness: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Control a WeMo device (turn on, off, toggle, or set brightness).

    Controls a device by sending turn on, turn off, or toggle commands.
    For dimmer devices, you can also set the brightness level (1-100).
    The device must have been discovered via scan_network first.

    Args:
    ----
        device_identifier: Device name (e.g., "Office Light") or IP address (e.g., "192.168.1.100")
        action: Action to perform - must be one of: "on", "off", "toggle", "brightness"
        brightness: Brightness level (1-100) - only used when action is "brightness" or "on" for dimmer devices
        ctx: MCP context injected by FastMCP; used to elicit the correct device when identifier is ambiguous

    Returns:
    -------
        Dictionary containing:
        - success: Boolean indicating if the action succeeded
        - device_name: Name of the device
        - action_performed: The action that was executed
        - new_state: The state after the action
        - brightness: Current brightness level (for dimmers)

    """
    # Validate inputs
    try:
        params = ControlDeviceParams(
            device_identifier=device_identifier,
            action=action,  # type: ignore[arg-type]
            brightness=brightness,
        )
    except ValidationError as e:
        return {
            "error": "Invalid parameters",
            "validation_errors": [
                {"field": err["loc"][0], "message": err["msg"], "input": err["input"]}
                for err in e.errors()
            ],
            "success": False,
        }

    try:
        # Find device in memory cache, then reconnect from file cache if needed
        device = _device_cache.get(params.device_identifier)
        if not device:
            device = await _reconnect_device_from_cache(params.device_identifier)

        if not device:
            available_names = [
                k for k in _device_cache if isinstance(k, str) and not k.replace(".", "").isdigit()
            ]
            if ctx is not None and available_names:
                # Elicit: find closest matches first, fall back to first 5
                partial_matches = [
                    n for n in available_names if params.device_identifier.lower() in n.lower()
                ]
                suggestions = partial_matches or available_names[:5]
                elicit_result = await ctx.elicit(
                    f"Device '{params.device_identifier}' not found. "
                    f"Did you mean one of these: {', '.join(suggestions)}?",
                    schema=_DeviceChoiceSchema,
                )
                if elicit_result.action == "accept" and elicit_result.data:
                    chosen = elicit_result.data.device_name
                    device = _device_cache.get(chosen)
                    if device:
                        params = ControlDeviceParams(
                            device_identifier=chosen,
                            action=params.action,
                            brightness=params.brightness,
                        )
            if not device:
                return {
                    "error": f"Device '{params.device_identifier}' not found in cache",
                    "suggestion": "Run scan_network first to discover devices",
                    "available_devices": available_names,
                    "success": False,
                }

        # Check if device is a dimmer
        is_dimmer = hasattr(device, "set_brightness") and hasattr(device, "get_brightness")

        # Validate brightness action for non-dimmers
        if params.action == "brightness":
            if not is_dimmer:
                return {
                    "error": f"Device '{device.name}' is not a dimmer and does not support brightness control",
                    "device_type": type(device).__name__,
                    "success": False,
                }
            if params.brightness is None:
                return {
                    "error": "Brightness value is required when action is 'brightness'",
                    "success": False,
                }

        # Perform the action
        await _perform_device_action(device, params.action, params.brightness, is_dimmer)

        # Wait for device to respond
        await asyncio.sleep(0.5)

        # Build and return result
        result = await _build_control_result(device, params.action, is_dimmer)

        logger.info(
            f"Device '{device.name}' {params.action} successful. New state: {result['new_state']}"
            + (f" Brightness: {result.get('brightness')}" if is_dimmer else ""),
        )
        return result

    except Exception as e:
        logger.error(f"Error controlling device: {e}", exc_info=True)
        return build_error_response(
            e,
            "Control device",
            context={
                "device_identifier": device_identifier,
                "action": action,
            },
        )


@mcp.tool()
async def rename_device(device_identifier: str, new_name: str) -> dict[str, Any]:
    """Rename a WeMo device (change its friendly name).

    Changes the friendly name of a WeMo device. This is the name that appears
    in the WeMo app and is used to identify the device. The device must have
    been discovered via scan_network first.

    After renaming, the device cache will be updated with the new name. You may
    want to run scan_network again to refresh the device list.

    Args:
    ----
        device_identifier: Current device name (e.g., "Office Dimmer") or IP address (e.g., "192.168.1.100")
        new_name: New friendly name for the device (e.g., "Office Light")

    Returns:
    -------
        Dictionary containing:
        - success: Boolean indicating if the rename succeeded
        - old_name: The previous name of the device
        - new_name: The new name of the device
        - device_ip: IP address of the device

    """
    # Validate inputs
    try:
        params = RenameDeviceParams(
            device_identifier=device_identifier,
            new_name=new_name,
        )
    except ValidationError as e:
        return {
            "error": "Invalid parameters",
            "validation_errors": [
                {"field": err["loc"][0], "message": err["msg"], "input": err["input"]}
                for err in e.errors()
            ],
            "success": False,
        }

    try:
        # Try to find device in memory cache, then reconnect from file cache if needed
        device = _device_cache.get(params.device_identifier)
        if not device:
            device = await _reconnect_device_from_cache(params.device_identifier)

        if not device:
            return {
                "error": f"Device '{params.device_identifier}' not found in cache",
                "suggestion": "Run scan_network first to discover devices",
                "available_devices": [
                    k
                    for k in _device_cache
                    if isinstance(k, str) and not k.replace(".", "").isdigit()
                ],
                "success": False,
            }

        old_name = device.name
        device_ip = getattr(device, "host", "unknown")

        # Perform the rename operation in a thread pool
        loop = asyncio.get_event_loop()

        # Try both methods for compatibility with different pywemo versions
        def rename_operation():
            if hasattr(device, "change_friendly_name"):
                device.change_friendly_name(params.new_name)
            elif hasattr(device, "basicevent"):
                device.basicevent.ChangeFriendlyName(FriendlyName=params.new_name)
            else:
                raise AttributeError("Device does not support renaming")

        await loop.run_in_executor(None, rename_operation)

        # Wait a moment for the device to respond
        await asyncio.sleep(0.5)

        # Update the cache with the new name
        # Remove old name entry and add new one
        _device_cache.pop(old_name, None)
        _device_cache[params.new_name] = device

        # Also update IP-based cache entry if it exists
        if device_ip in _device_cache:
            _device_cache[device_ip] = device

        result = {
            "success": True,
            "old_name": old_name,
            "new_name": params.new_name,
            "device_ip": device_ip,
            "message": f"Device renamed from '{old_name}' to '{params.new_name}'",
            "timestamp": time.time(),
        }

        logger.info(f"Device renamed: '{old_name}' -> '{params.new_name}' at {device_ip}")
        return result

    except Exception as e:
        logger.error(f"Error renaming device: {e}", exc_info=True)
        return build_error_response(
            e,
            "Rename device",
            context={
                "device_identifier": device_identifier,
                "new_name": new_name,
            },
        )


@mcp.tool()
async def get_homekit_code(device_identifier: str) -> dict[str, Any]:
    """Get the HomeKit setup code for a WeMo device.

    Retrieves the HomeKit setup code (HKSetupCode) for devices that support
    HomeKit integration. This code can be used to add the device to Apple Home.
    The device must have been discovered via scan_network first.

    Note: Not all WeMo devices support HomeKit. If a device doesn't support
    HomeKit or doesn't have a setup code, an error will be returned.

    Args:
    ----
        device_identifier: Device name (e.g., "Office Light") or IP address (e.g., "192.168.1.100")

    Returns:
    -------
        Dictionary containing:
        - success: Boolean indicating if the code was retrieved
        - device_name: Name of the device
        - homekit_code: The HomeKit setup code (format: XXX-XX-XXX)
        - device_ip: IP address of the device

    """
    # Validate input
    try:
        param = DeviceIdentifierParam(device_identifier=device_identifier)
    except ValidationError as e:
        return {
            "error": "Invalid parameters",
            "validation_errors": [
                {"field": err["loc"][0], "message": err["msg"], "input": err["input"]}
                for err in e.errors()
            ],
            "success": False,
        }

    try:
        # Try to find device in memory cache, then reconnect from file cache if needed
        device = _device_cache.get(param.device_identifier)
        if not device:
            device = await _reconnect_device_from_cache(param.device_identifier)

        if not device:
            return {
                "error": f"Device '{param.device_identifier}' not found in cache",
                "suggestion": "Run scan_network first to discover devices",
                "available_devices": [
                    k
                    for k in _device_cache
                    if isinstance(k, str) and not k.replace(".", "").isdigit()
                ],
                "success": False,
            }

        device_name = device.name
        device_ip = getattr(device, "host", "unknown")

        # Check if device has basicevent (required for HomeKit info)
        if not hasattr(device, "basicevent"):
            return {
                "error": f"Device '{device_name}' does not support HomeKit (no basicevent service)",
                "device_name": device_name,
                "device_type": type(device).__name__,
                "success": False,
            }

        # Get HomeKit setup info in a thread pool
        loop = asyncio.get_event_loop()

        def get_hk_info():
            return device.basicevent.GetHKSetupInfo()

        hk_info = await loop.run_in_executor(None, get_hk_info)

        # Extract the HomeKit code
        hk_code = hk_info.get("HKSetupCode")

        if not hk_code:
            return {
                "error": f"Device '{device_name}' does not have a HomeKit setup code",
                "device_name": device_name,
                "device_ip": device_ip,
                "device_type": type(device).__name__,
                "homekit_info_available": hk_info,
                "success": False,
            }

        result = {
            "success": True,
            "device_name": device_name,
            "homekit_code": hk_code,
            "device_ip": device_ip,
            "device_type": type(device).__name__,
            "message": f"HomeKit setup code for '{device_name}': {hk_code}",
            "timestamp": time.time(),
        }

        logger.info(f"HomeKit code retrieved for '{device_name}': {hk_code}")
        return result

    except Exception as e:
        logger.error(f"Error getting HomeKit code: {e}", exc_info=True)

        # Provide helpful error messages for common issues
        error_msg = str(e)
        if "UPnPError" in error_msg or "Action" in error_msg:
            error_msg = f"Device does not support HomeKit or the HomeKit feature is not available: {error_msg}"

        error_response = build_error_response(
            e,
            "Get HomeKit code",
            context={"device_identifier": device_identifier},
        )
        error_response["error"] = f"Failed to get HomeKit code: {error_msg}"
        return error_response


@mcp.resource("devices://")
async def list_device_resources() -> str:
    """List all discovered WeMo devices as MCP resources.

    Returns an index of every device currently in the cache, with a URI that can
    be fetched individually via the device://{device_id} resource.

    Useful for MCP clients that want to enumerate available devices without
    calling the scan_network or list_devices tools.
    """
    # De-duplicate: the in-memory cache stores both name and IP as keys
    seen: set[str] = set()
    entries = []

    source_cache: dict[str, Any] = {}

    if _device_cache:
        source_cache = _device_cache
    else:
        # Fall back to persistent JSON cache after a server restart
        persisted = _cache_manager.load()
        if persisted:
            source_cache = {k: v for k, v in persisted.items() if isinstance(v, dict)}

    for key, device in source_cache.items():
        # Only emit name-keyed entries (skip bare IP keys) to avoid duplicates
        name = getattr(device, "name", None) if not isinstance(device, dict) else device.get("name")
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        ip = (
            getattr(device, "host", "unknown")
            if not isinstance(device, dict)
            else device.get("host", "unknown")
        )
        entries.append(
            {
                "uri": f"device://{name}",
                "name": name,
                "ip_address": ip,
                "mime_type": "application/json",
            }
        )

    return json.dumps(
        {
            "total_devices": len(entries),
            "devices": entries,
        },
        indent=2,
    )


@mcp.resource(
    "device://{device_id}",
    mime_type="application/json",
    description="Real-time info and state for a single WeMo device. Use the device name or IP as device_id.",
)
async def get_device_resource(device_id: str) -> str:
    """Get full details and live state for a single WeMo device.

    Args:
    ----
        device_id: Device name (e.g. "Office Light") or IP address

    Returns:
    -------
        JSON string with device info and current state.

    """
    # URL-decode so 'Master%20Bed%20346' becomes 'Master Bed 346'
    device_id = unquote(device_id)

    # 1. Try in-memory cache first
    device = _device_cache.get(device_id)

    # 2. Try case-insensitive name match against in-memory cache
    if device is None:
        lower = device_id.lower()
        for key, dev in _device_cache.items():
            if getattr(dev, "name", "").lower() == lower:
                device = dev
                break

    # 3. Fall back to lazy reconnect from persistent cache
    if device is None:
        device = await _reconnect_device_from_cache(device_id)

    if device is None:
        available = sorted(
            {getattr(d, "name", k) for k, d in _device_cache.items() if not isinstance(d, dict)}
        )
        return json.dumps(
            {
                "error": f"Device '{device_id}' not found",
                "suggestion": "Run scan_network first, or check the devices:// resource for available names",
                "available_devices": available,
            },
            indent=2,
        )

    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(None, extract_device_info, device)
    except Exception as e:
        info = {
            "name": getattr(device, "name", device_id),
            "error": f"Could not fetch live state: {e}",
        }

    return json.dumps(info, indent=2)


# ---------------------------------------------------------------------------
# MCP Prompts
# ---------------------------------------------------------------------------
# Prompts are pre-written message templates the user can invoke from the
# client's prompt picker (e.g. Claude Desktop slash-commands, VS Code).
# They inject one or more messages into the conversation — the model then
# acts on them using the available tools.
# ---------------------------------------------------------------------------


@mcp.prompt(
    name="discover-devices",
    title="Discover WeMo Devices",
    description="Scan the network for WeMo devices and summarise what was found.",
)
async def prompt_discover_devices() -> list[dict]:
    """Scan the network and report all discovered WeMo smart home devices."""
    config = get_config()
    subnet = config.get("network", "default_subnet", "192.168.1.0/24")
    return [
        {
            "role": "user",
            "content": (
                f"Please scan my home network ({subnet}) for WeMo smart home devices. "
                "Use the scan_network tool, then give me a clear summary of:\n"
                "1. How many devices were found\n"
                "2. Each device's name, type (switch/dimmer), and current state (on/off)\n"
                "3. Any devices that could not be reached\n"
                "Present the results in a clean, readable format."
            ),
        }
    ]


@mcp.prompt(
    name="device-status-report",
    title="Device Status Report",
    description="Get a full status report of all known WeMo devices.",
)
async def prompt_device_status_report() -> list[dict]:
    """Check the status of every known device and produce a summary report."""
    # Pull device names from cache so the prompt is pre-populated
    persisted = _cache_manager.load()
    if _device_cache:
        names = sorted(
            {getattr(d, "name", k) for k, d in _device_cache.items() if not isinstance(d, dict)}
        )
    elif persisted:
        names = sorted(
            {v.get("name", "") for v in persisted.values() if isinstance(v, dict) and v.get("name")}
        )
    else:
        names = []

    if names:
        device_list = "\n".join(f"  - {n}" for n in names)
        device_context = f"Known devices:\n{device_list}\n\n"
    else:
        device_context = "No devices in cache yet — you may need to scan first.\n\n"

    return [
        {
            "role": "user",
            "content": (
                f"{device_context}"
                "Please check the current status of all my WeMo devices and give me a report. "
                "For each device include: name, type, state (on/off), and brightness if it's a dimmer. "
                "If a device is unreachable, flag it clearly. "
                "Finish with a one-line summary of how many devices are on vs off."
            ),
        }
    ]


@mcp.prompt(
    name="activate-scene",
    title="Activate a Lighting Scene",
    description="Set all WeMo devices to match a named scene (e.g. movie night, bedtime, wake up).",
)
async def prompt_activate_scene(
    scene: str = "movie night",
) -> list[dict]:
    """Activate a named lighting scene across all WeMo devices.

    Args:
    ----
        scene: Scene name such as 'movie night', 'bedtime', 'wake up', 'away', or 'full brightness'.

    """
    scene_hints = {
        "movie night": "dim all lights to around 20-30% brightness, turn off any bright overhead lights",
        "bedtime": "turn off all lights except any nightlights, set dimmers to minimum",
        "wake up": "gradually bring all lights to 70% brightness",
        "away": "turn off all lights completely",
        "full brightness": "turn on all lights and set all dimmers to 100%",
    }
    hint = scene_hints.get(scene.lower().strip(), f"configure lights to match the '{scene}' mood")

    return [
        {
            "role": "user",
            "content": (
                f"Please activate the '{scene}' scene on my WeMo smart home devices.\n\n"
                f"For this scene you should: {hint}.\n\n"
                "Use list_devices to see what's available, then control each device appropriately "
                "using control_device. After making the changes, confirm what you did."
            ),
        }
    ]


@mcp.prompt(
    name="troubleshoot-device",
    title="Troubleshoot a Device",
    description="Diagnose and attempt to fix issues with a specific WeMo device.",
)
async def prompt_troubleshoot_device(
    device_name: str,
) -> list[dict]:
    """Run a diagnostic sequence on a specific WeMo device.

    Args:
    ----
        device_name: Name or IP address of the device to troubleshoot.

    """
    return [
        {
            "role": "user",
            "content": (
                f"I'm having trouble with my WeMo device: '{device_name}'.\n\n"
                "Please run a diagnostic:\n"
                "1. Use get_device_status to check if it's reachable and what state it reports\n"
                "2. Try toggling it on and off with control_device to verify it responds to commands\n"
                "3. Check the cache with get_cache_info to see if the device info is stale\n"
                "4. If the device isn't found, suggest running scan_network to rediscover it\n\n"
                "After the diagnostic, tell me what you found and what was fixed or what to try next."
            ),
        }
    ]


def main() -> None:
    """Start the WeMo MCP server."""
    logger.info("Starting WeMo MCP Server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
