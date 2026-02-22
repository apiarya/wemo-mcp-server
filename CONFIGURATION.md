# WeMo MCP Server Configuration Guide

Complete guide to configuring the WeMo MCP Server for your environment.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Methods](#configuration-methods)
- [Configuration Reference](#configuration-reference)
- [Example Configurations](#example-configurations)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Method 1: Environment Variables (Recommended)

Quickest way to customize settings:

```bash
# Set your network subnet
export WEMO_MCP_DEFAULT_SUBNET="192.168.1.0/24"

# Extend cache lifetime to 2 hours
export WEMO_MCP_CACHE_TTL=7200

# Enable debug logging
export WEMO_MCP_LOG_LEVEL=DEBUG

# Start the server
uvx wemo-mcp-server
```

### Method 2: YAML Configuration File

For persistent configuration:

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit with your preferred editor
nano config.yaml

# Server will automatically load config.yaml if present
```

---

## Configuration Methods

The server loads configuration in this priority order (highest to lowest):

1. **Environment Variables** - Override everything
2. **YAML Config File** - Persistent settings
3. **Default Values** - Built-in defaults

### Environment Variables

All settings can be configured with the `WEMO_MCP_` prefix:

```bash
WEMO_MCP_DEFAULT_SUBNET=192.168.1.0/24
WEMO_MCP_SCAN_TIMEOUT=0.6
WEMO_MCP_MAX_WORKERS=60
WEMO_MCP_CACHE_ENABLED=true
WEMO_MCP_CACHE_FILE=~/.wemo_mcp_cache.json
WEMO_MCP_CACHE_TTL=3600
WEMO_MCP_LOG_LEVEL=INFO
```

**Load from .env file:**
```bash
cp .env.example .env
# Edit .env with your settings
source .env  # or use dotenv loader
```

### YAML Configuration File

The server looks for `config.yaml` in these locations (in order):

1. Current working directory: `./config.yaml`
2. User config directory: `~/.config/wemo-mcp/config.yaml`
3. System config directory: `/etc/wemo-mcp/config.yaml`

**Example config.yaml:**
```yaml
network:
  default_subnet: "192.168.1.0/24"
  scan_timeout: 0.6
  max_workers: 60
  retry_attempts: 3
  retry_delay: 0.5

cache:
  enabled: true
  file_path: "~/.wemo_mcp_cache.json"
  ttl_seconds: 3600

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Configuration Reference

### Network Settings

#### `default_subnet`
- **Environment**: `WEMO_MCP_DEFAULT_SUBNET`
- **Default**: `192.168.1.0/24`
- **Format**: CIDR notation (e.g., `192.168.1.0/24`, `10.0.0.0/16`)
- **Description**: Network subnet to scan when not specified in scan_network call
- **Examples**:
  - `192.168.1.0/24` - Single /24 network (254 hosts)
  - `10.0.0.0/16` - Large /16 network (65,534 hosts)
  - `192.168.0.0/16` - Two /16 networks

#### `scan_timeout`
- **Environment**: `WEMO_MCP_SCAN_TIMEOUT`
- **Default**: `0.6`
- **Range**: `0.1` - `5.0` seconds
- **Description**: Connection timeout for port probing during network scan
- **Tips**:
  - Lower values = faster scan, may miss slow devices
  - Higher values = slower scan, catches all devices
  - Use `1.0` for large networks or WiFi devices
  - Use `0.4` for wired networks with fast devices

#### `max_workers`
- **Environment**: `WEMO_MCP_MAX_WORKERS`
- **Default**: `60`
- **Range**: `1` - `200`
- **Description**: Maximum concurrent threads for parallel scanning
- **Tips**:
  - Higher values = faster scan, may overwhelm network/router
  - Lower values = slower scan, gentler on network
  - Use `30-60` for home networks
  - Use `100-150` for enterprise networks
  - Reduce if experiencing network issues

#### `retry_attempts`
- **Environment**: `WEMO_MCP_RETRY_ATTEMPTS`
- **Default**: `3`
- **Range**: `1` - `10`
- **Description**: Number of retry attempts for device operations
- **Note**: Applied to control/status operations with exponential backoff

#### `retry_delay`
- **Environment**: `WEMO_MCP_RETRY_DELAY`
- **Default**: `0.5`
- **Range**: `0.1` - `5.0` seconds
- **Description**: Initial delay between retries (doubles each retry)

### Cache Settings

#### `enabled`
- **Environment**: `WEMO_MCP_CACHE_ENABLED`
- **Default**: `true`
- **Values**: `true`, `false`, `1`, `0`, `yes`, `no`
- **Description**: Enable/disable persistent device caching
- **Benefits**:
  - Faster startup (no scan needed)
  - Survives server restarts
  - Reduces network traffic

#### `file_path`
- **Environment**: `WEMO_MCP_CACHE_FILE`
- **Default**: `~/.wemo_mcp_cache.json`
- **Format**: Absolute or relative path
- **Description**: Location of cache file
- **Examples**:
  - `~/.wemo_mcp_cache.json` - User home directory
  - `/var/cache/wemo-mcp/devices.json` - System cache
  - `./cache.json` - Current directory

#### `ttl_seconds`
- **Environment**: `WEMO_MCP_CACHE_TTL`
- **Default**: `3600` (1 hour)
- **Range**: `0` - unlimited
- **Description**: Cache time-to-live in seconds
- **Special**: `0` = never expire
- **Examples**:
  - `300` - 5 minutes (frequent changes)
  - `3600` - 1 hour (balanced)
  - `7200` - 2 hours (stable network)
  - `86400` - 24 hours (rare changes)

### Logging Settings

#### `level`
- **Environment**: `WEMO_MCP_LOG_LEVEL`
- **Default**: `INFO`
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging verbosity level
- **Recommendations**:
  - `DEBUG` - Development, troubleshooting
  - `INFO` - Production, normal operation
  - `WARNING` - Production, only warnings/errors
  - `ERROR` - Production, only errors

#### `format`
- **Environment**: `WEMO_MCP_LOG_FORMAT`
- **Default**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Description**: Python logging format string
- **Examples**:
  - `%(levelname)s: %(message)s` - Simple format
  - `%(asctime)s [%(levelname)s] %(message)s` - Compact format
  - `%(asctime)s - %(name)s - %(levelname)s - %(message)s` - Full format

---

## Example Configurations

### Home Network (Default)

Simple home network with standard settings:

```bash
export WEMO_MCP_DEFAULT_SUBNET="192.168.1.0/24"
export WEMO_MCP_SCAN_TIMEOUT=0.6
export WEMO_MCP_MAX_WORKERS=60
```

### Large Network

Enterprise or multi-subnet setup:

```bash
export WEMO_MCP_DEFAULT_SUBNET="10.0.0.0/16"
export WEMO_MCP_SCAN_TIMEOUT=1.0
export WEMO_MCP_MAX_WORKERS=100
export WEMO_MCP_CACHE_TTL=7200  # 2 hours
```

### IoT/Guest Network

Isolated network with limited devices:

```bash
export WEMO_MCP_DEFAULT_SUBNET="192.168.99.0/24"
export WEMO_MCP_SCAN_TIMEOUT=0.8
export WEMO_MCP_MAX_WORKERS=30
export WEMO_MCP_CACHE_TTL=3600
```

### Development/Debug

Maximum verbosity for troubleshooting:

```bash
export WEMO_MCP_DEFAULT_SUBNET="192.168.1.0/24"
export WEMO_MCP_LOG_LEVEL=DEBUG
export WEMO_MCP_CACHE_TTL=300  # 5 minutes
export WEMO_MCP_CACHE_ENABLED=false  # Disable for testing
```

### Docker/Container

Environment-based configuration for containers:

```dockerfile
# Dockerfile or docker-compose.yml
ENV WEMO_MCP_DEFAULT_SUBNET=192.168.1.0/24
ENV WEMO_MCP_CACHE_FILE=/var/cache/wemo/devices.json
ENV WEMO_MCP_CACHE_TTL=7200
ENV WEMO_MCP_LOG_LEVEL=INFO
```

### Multiple Subnets

Scan multiple networks (requires multiple scans):

```bash
# First subnet
claude chat "Scan 192.168.1.0/24 for devices"

# Second subnet
claude chat "Scan 10.0.0.0/16 for devices"

# Results are merged in cache
```

---

## Troubleshooting

### No Devices Found

**Problem**: `scan_network` finds 0 devices

**Solutions**:
1. **Check subnet**:
   ```bash
   # Find your subnet (macOS/Linux)
   ifconfig | grep "inet "
   # or
   ip addr show

   # Use correct subnet
   export WEMO_MCP_DEFAULT_SUBNET="your.subnet.0/24"
   ```

2. **Increase timeout**:
   ```bash
   export WEMO_MCP_SCAN_TIMEOUT=1.5
   ```

3. **Check network connectivity**:
   ```bash
   # Ping a known WeMo device
   ping 192.168.1.100
   ```

### Slow Scanning

**Problem**: Network scan takes too long

**Solutions**:
1. **Reduce workers** (if overwhelming network):
   ```bash
   export WEMO_MCP_MAX_WORKERS=30
   ```

2. **Reduce timeout** (if devices respond quickly):
   ```bash
   export WEMO_MCP_SCAN_TIMEOUT=0.4
   ```

3. **Use smaller subnet**:
   ```bash
   export WEMO_MCP_DEFAULT_SUBNET="192.168.1.0/28"  # Only 14 hosts
   ```

### Cache Issues

**Problem**: Devices not updating or cache corruption

**Solutions**:
1. **Clear cache manually**:
   ```bash
   claude chat "Clear the device cache"
   ```

2. **Delete cache file**:
   ```bash
   rm ~/.wemo_mcp_cache.json
   ```

3. **Disable caching**:
   ```bash
   export WEMO_MCP_CACHE_ENABLED=false
   ```

4. **Reduce TTL**:
   ```bash
   export WEMO_MCP_CACHE_TTL=300  # 5 minutes
   ```

### Device Control Failures

**Problem**: Devices found but control commands fail

**Solutions**:
1. **Enable debug logging**:
   ```bash
   export WEMO_MCP_LOG_LEVEL=DEBUG
   ```

2. **Check device responsiveness**:
   ```bash
   # Use WeMo app to control device
   # If WeMo app works, MCP should work
   ```

3. **Rescan network**:
   ```bash
   claude chat "Clear cache and scan for devices"
   ```

### Configuration Not Loading

**Problem**: Environment variables or config file ignored

**Solutions**:
1. **Verify environment variables**:
   ```bash
   env | grep WEMO_MCP
   ```

2. **Check config file location**:
   ```bash
   ls -la ~/.config/wemo-mcp/config.yaml
   ls -la ./config.yaml
   ```

3. **Use get_configuration tool**:
   ```bash
   claude chat "Show me the current configuration"
   ```

4. **Restart server/client** after configuration changes

---

## Advanced Topics

### Dynamic Configuration

Change settings without restarting:

```bash
# Use get_configuration to verify current settings
claude chat "Show current configuration"

# MCP tools respect current environment
# Export new values before next operation
export WEMO_MCP_SCAN_TIMEOUT=1.0
claude chat "Scan for devices"  # Uses new timeout
```

### Configuration Precedence

When multiple configuration sources exist:

```
Environment Variables  (highest priority)
    ↓
YAML Config File
    ↓
Default Values       (lowest priority)
```

Example:
- `config.yaml` sets `scan_timeout: 0.8`
- Environment has `WEMO_MCP_SCAN_TIMEOUT=1.0`
- **Result**: Uses `1.0` (environment wins)

### Sharing Configuration

**For teams:**
1. Commit `config.example.yaml` to git
2. Team members copy and customize locally
3. Add `config.yaml` to `.gitignore` (already done)

**For deployment:**
1. Use environment variables in production
2. Use config files for local development
3. Document settings in README or wiki

---

## Getting Help

If you're still having issues:

1. **Enable debug logging**:
   ```bash
   export WEMO_MCP_LOG_LEVEL=DEBUG
   ```

2. **Check logs** for error messages

3. **Verify settings**:
   ```bash
   claude chat "Show configuration"
   ```

4. **Test basic connectivity**:
   ```bash
   claude chat "Scan for devices"
   ```

5. **Open an issue** on GitHub with:
   - Configuration (sanitize IP addresses)
   - Debug logs
   - Network setup description
   - Expected vs actual behavior

---

## See Also

- [README.md](README.md) - Main documentation
- [config.example.yaml](config.example.yaml) - Complete YAML config template
- [.env.example](.env.example) - Environment variable template
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
