<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# WeMo MCP Server - Copilot Instructions

**Production-ready MCP Server for WeMo smart home device control via AI assistants.**

## Project Identity
- **Repository**: https://github.com/apiarya/wemo-mcp-server
- **Package**: `wemo-mcp-server` (PyPI)
- **MCP Name**: `io.github.apiarya/wemo`
- **Version**: v1.1.1 (stable)
- **Status**: Production • Published on PyPI and MCP Registry

## Project Type & Architecture
- **Type**: Model Context Protocol (MCP) Server
- **Framework**: FastMCP (mcp>=1.2.0)
- **Language**: Python 3.10+ with type hints
- **Transport**: stdio (JSON-RPC over stdin/stdout)
- **Package Manager**: uv (with uv.lock for reproducible builds)
- **Build System**: Hatchling

## Core Functionality
Natural language control of WeMo smart home devices through AI assistants:
- Multi-phase device discovery (UPnP/SSDP + network scanning)
- Real-time device control (on/off/toggle/brightness)
- Device management (rename, HomeKit codes)
- Status monitoring
- Automatic device caching

## Project Structure
```
wemo-mcp-server/
├── src/wemo_mcp_server/
│   ├── __init__.py          # Package init and version (__version__ = "1.1.1")
│   ├── __main__.py          # Entry point for python -m wemo_mcp_server
│   └── server.py            # Main server (701 lines) - all MCP tools and logic
├── tests/
│   ├── __init__.py
│   ├── test_server.py       # Unit tests (15 tests)
│   └── test_e2e.py          # End-to-end tests with real devices
├── .github/
│   ├── workflows/
│   │   └── pypi-publish.yml # Automated publishing (PyPI + MCP Registry)
│   ├── copilot-instructions.md  # This file
│   ├── PYPI_PUBLISHING.md       # PyPI trusted publishing docs
│   └── PUBLISHING_AUTOMATION.md # Automation guide
├── assets/
│   └── claude-example.png   # Screenshot for README
├── pyproject.toml           # Package config (version, dependencies, metadata)
├── server.json              # MCP Registry metadata
├── uv.lock                  # Locked dependencies (291KB)
├── README.md                # Comprehensive docs (456 lines)
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT License
├── MIGRATION.md             # Migration documentation
├── RELEASE.md               # Release process guide
├── RELEASE_CHECKLIST.md     # Quick release checklist
├── RELEASE_NOTES_v1.1.0.md  # v1.1.0 release notes
├── RELEASE_NOTES_v1.1.1.md  # v1.1.1 release notes
└── MCP_REGISTRY_SUBMISSION.md  # Registry submission docs
```

## MCP Tools (6 Total) - server.py
All tools are async and decorated with `@mcp.tool()`:

### 1. `scan_network(subnet, timeout, max_workers)`
- **Purpose**: Discover WeMo devices on network
- **Method**: Multi-phase (UPnP/SSDP first, then port scanning backup)
- **Returns**: Device list with full details + caches devices
- **Performance**: ~23-30s for full /24 subnet with 60 workers

### 2. `list_devices()`
- **Purpose**: List cached devices from previous scans
- **Returns**: Device count and device list
- **Note**: Run scan_network first to populate cache

### 3. `get_device_status(device_identifier)`
- **Purpose**: Get real-time device state
- **Input**: Device name or IP address
- **Returns**: State (on/off), brightness (if dimmer), device info

### 4. `control_device(device_identifier, action, brightness)`
- **Purpose**: Control devices
- **Actions**: "on", "off", "toggle", "brightness"
- **Brightness**: 1-100 for dimmers
- **Returns**: Success status, new state, brightness

### 5. `rename_device(device_identifier, new_name)`
- **Purpose**: Change device friendly name
- **Updates**: Device cache and WeMo device itself
- **Returns**: Old name, new name, success status

### 6. `get_homekit_code(device_identifier)`
- **Purpose**: Extract HomeKit setup code
- **Note**: Not all devices support HomeKit
- **Returns**: HomeKit code (format: XXX-XX-XXX)

## Development Guidelines

### Code Style
- **Async/await**: All MCP tools must be async
- **Type hints**: Use throughout (strict mypy)
- **Logging**: Use `logging` module, log to stderr only (never stdout)
- **Error handling**: Try/except with informative error dictionaries
- **Docstrings**: Google-style docstrings for all functions

### MCP Server Patterns
- Use `FastMCP` for server initialization: `mcp = FastMCP("wemo-mcp-server")`
- Tools return Dict[str, Any] with consistent structure
- Include "error" key in results when operations fail
- Provide "suggestion" keys for common issues
- Cache devices in global `_device_cache` dict

### Network Operations
- Use `pywemo` library for WeMo device interaction
- Run sync operations in thread pool: `loop.run_in_executor(None, func)`
- Keep network scanning non-invasive (timeout 0.6s default)
- Parallel scanning with ThreadPoolExecutor (60 workers default)
- Multi-phase discovery: UPnP/SSDP primary, port scanning backup

### Version Management
**CRITICAL**: Keep versions synchronized across 3 files:
1. `pyproject.toml` - Line 7: `version = "X.Y.Z"`
2. `src/wemo_mcp_server/__init__.py` - Line 3: `__version__ = "X.Y.Z"`
3. `server.json` - Line 10: `"version": "X.Y.Z"`

GitHub Actions workflow verifies version consistency before publishing.

## Testing

### Unit Tests (test_server.py)
- 15 tests covering core functionality
- Mock-based testing for network operations
- Tests WeMoScanner, extract_device_info, all MCP tools
- Run: `pytest tests/test_server.py -v`

### E2E Tests (test_e2e.py)
- Requires actual WeMo devices on network
- Tests all 6 MCP tools end-to-end
- Configurable device count and control testing
- Run: `python tests/test_e2e.py`

### Test Commands
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=wemo_mcp_server --cov-report=html

# Run E2E tests (needs real devices)
python tests/test_e2e.py
```

## Common Development Commands

```bash
# Run server locally
uvx wemo-mcp-server
# or
python -m wemo_mcp_server

# Run tests
pytest tests/ -v

# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/

# Build package
python -m build

# Install locally for testing
pip install -e .
```

## Commit Practices

### Pre-Commit Documentation Check ⚠️ REQUIRED
**Before every commit**, verify if documentation needs updates:

#### Files to Check:
1. **README.md**
   - [ ] Are new features documented?
   - [ ] Are installation instructions still accurate?
   - [ ] Are example prompts up-to-date?
   - [ ] Are MCP tool descriptions current?

2. **CHANGELOG.md**
   - [ ] Is the change documented under appropriate version?
   - [ ] Are breaking changes clearly marked?
   - [ ] Is the change categorized correctly (Added/Changed/Fixed/etc.)?

3. **Copilot Instructions** (`.github/copilot-instructions.md`)
   - [ ] Does code structure match documented structure?
   - [ ] Are new tools/functions documented?
   - [ ] Are dependencies list current?
   - [ ] Are development commands accurate?

4. **Version Files** (if version bump)
   - [ ] `pyproject.toml` - version field
   - [ ] `src/wemo_mcp_server/__init__.py` - __version__
   - [ ] `server.json` - version field
   - [ ] All three must match exactly!

5. **Tool Docstrings** (in `server.py`)
   - [ ] Do docstrings match actual behavior?
   - [ ] Are parameters documented correctly?
   - [ ] Are return values accurate?

#### Quick Check Command:
```bash
# Before committing, ask yourself:
# "What documentation might be affected by my changes?"

# Then review relevant files:
git diff README.md
git diff CHANGELOG.md
git diff .github/copilot-instructions.md
git diff server.json pyproject.toml src/wemo_mcp_server/__init__.py
```

#### Common Documentation Updates:
- **New MCP Tool** → Update README.md (tools section), copilot-instructions.md
- **Bug Fix** → Update CHANGELOG.md
- **New Dependency** → Update README.md, pyproject.toml, copilot-instructions.md
- **API Change** → Update README.md, tool docstrings, CHANGELOG.md (breaking changes)
- **Version Bump** → Update 3 version files + CHANGELOG.md
- **New Feature** → Update README.md, CHANGELOG.md, copilot-instructions.md

#### Documentation Debt
If you can't update documentation immediately:
```bash
# Create a TODO comment in the commit message
git commit -m "Add feature X

TODO: Update README.md with new feature documentation
TODO: Add example prompts for feature X"
```

Then create a GitHub issue to track the documentation update.

## Publishing & CI/CD

### Automated Publishing (✅ ACTIVE)
**GitHub Actions workflow**: `.github/workflows/pypi-publish.yml`

**Process**: Create GitHub release → Automated publish to PyPI + MCP Registry

**Features**:
- ✅ PyPI publishing via trusted publishing (OIDC)
- ✅ MCP Registry publishing via github-oidc authentication
- ✅ Version verification (pyproject.toml + server.json)
- ✅ No secrets/tokens needed (all OIDC-based)
- ✅ Detailed release summary

**Security**: All publishing uses short-lived OIDC tokens (no API keys)

### Manual Release Process
```bash
# 1. Update versions (3 files)
vim pyproject.toml src/wemo_mcp_server/__init__.py server.json

# 2. Update CHANGELOG.md
vim CHANGELOG.md

# 3. Commit and push
git add -A
git commit -m "Release vX.Y.Z"
git push origin main

# 4. Create tag and GitHub release
git tag vX.Y.Z
git push origin vX.Y.Z

# 5. Create release on GitHub
# → Workflow publishes to PyPI + MCP Registry automatically!
```

See `.github/PUBLISHING_AUTOMATION.md` for comprehensive automation guide.

## MCP Client Testing

### Claude Desktop
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "wemo": {
      "command": "uvx",
      "args": ["wemo-mcp-server"]
    }
  }
}
```

### VS Code
```json
// ~/.vscode/mcp.json
{
  "servers": {
    "wemo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["wemo-mcp-server"]
    }
  }
}
```

Test prompts:
- "Scan for WeMo devices on my network"
- "Turn on the office light"
- "What's the brightness of the bedroom dimmer?"

## Key Dependencies

### Production
- `mcp>=1.2.0` - Model Context Protocol SDK
- `httpx>=0.25.0` - Async HTTP client
- `pywemo>=1.4.0` - WeMo device control library

### Development
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `black>=23.0.0` - Code formatter
- `isort>=5.12.0` - Import sorter
- `mypy>=1.0.0` - Type checker
- `ruff>=0.1.0` - Fast linter

## Important Notes

### Device Cache
- Global `_device_cache` dict stores discovered devices
- Keyed by both device name and IP address
- Persists during server lifetime
- Cleared on server restart

### Logging
- **CRITICAL**: Only log to stderr (not stdout)
- stdout is reserved for MCP JSON-RPC protocol
- Use `logger.info()`, `logger.error()`, etc.
- Configured in server.py with stderr stream

### Error Handling
- Always return Dict with "error" key on failures
- Include "suggestion" for common issues
- List "available_devices" when device not found
- Use try/except blocks for all external operations

### Network Discovery
- UPnP/SSDP is primary method (most reliable)
- Port scanning (49152-49155) is backup
- Parallel probing with 60 concurrent workers
- Configurable timeout (default 0.6s per port)

## Documentation Standards

- Keep README.md current with features and installation
- Update CHANGELOG.md for every release
- Document breaking changes prominently
- Include example prompts in tool docstrings
- Maintain comprehensive release notes

## Git Workflow

- **Main branch**: Production-ready code
- **Tags**: Version format `vX.Y.Z` (e.g., `v1.1.1`)
- **Commits**: Descriptive messages with context
- **Pre-commit checks**: Always verify documentation needs updates (see Commit Practices section)
- **No direct commits to main**: Use feature branches for major changes

## Support & Community

- **Issues**: https://github.com/apiarya/wemo-mcp-server/issues
- **Discussions**: GitHub Discussions tab
- **PyPI**: https://pypi.org/project/wemo-mcp-server/
- **MCP Registry**: https://registry.modelcontextprotocol.io/?q=apiarya/wemo

## Related Projects
- **pywemo**: https://github.com/pywemo/pywemo (underlying library)
- **WeMo Ops Center**: https://github.com/qrussell/wemo-ops-center (desktop app)

---

**Last Updated**: February 21, 2026 (v1.1.1 + automated publishing)