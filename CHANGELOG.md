# Changelog

All notable changes to the WeMo MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-02-21

### Fixed
- 🐛 **Cache not used after server restart** - All device-lookup tools now auto-reconnect
  to devices via the persistent JSON cache on restart, eliminating forced rescans
  (`get_device_status`, `control_device`, `rename_device`, `get_homekit_code`)
- 🐛 **`list_devices` ignores file cache on restart** - Falls back to `~/.wemo_mcp_cache.json`
  when in-memory cache is empty; includes note indicating devices loaded from file cache
- 🐛 **Misleading `cache_keys` in `list_devices` response** - Removed raw key count
  (always 2× device_count due to name+IP dual-indexing) which caused AI to report
  a false discrepancy; `device_count` is now the only count field

---

## [1.3.0] - 2026-02-21

### 🚀 Phase 2: Production-Grade Features

Major enhancement release adding error handling, persistent caching, and full configuration management.

### Added
- ✨ **3 New MCP Tools** (9 total, up from 6)
  - `get_cache_info` - Inspect cache status, age, and TTL
  - `clear_cache` - Force cache refresh
  - `get_configuration` - View current settings
- 🔄 **Automatic Retry Logic** - Exponential backoff for device operations
  - 3 retry attempts by default
  - Configurable retry delay (default: 0.5s, doubles each retry)
  - Applied to all network/device operations
- 💾 **Persistent Device Cache** 
  - JSON-based cache at `~/.wemo_mcp_cache.json`
  - 1-hour TTL (configurable)
  - Survives server restarts
  - 26+ cache entries per device (full metadata)
- ⚙️ **Configuration Management**
  - YAML config file support (`config.yaml`, requires optional `pyyaml`)
  - Environment variable overrides (`WEMO_MCP_*` prefix)
  - 11 configurable settings (network, cache, logging)
  - Priority: env vars > YAML > defaults
- 🛡️ **Enhanced Error Handling**
  - Error classification (network, device, configuration)
  - Actionable error messages with suggestions
  - Graceful degradation for cache/config failures
- 📝 **Input Validation** - Pydantic models for all tool inputs
  - `ScanNetworkInput`, `DeviceIdentifierInput`
  - `ControlDeviceInput`, `RenameDeviceInput`
  - Automatic validation with clear error messages
- 📚 **Documentation**
  - `CONFIGURATION.md` - Comprehensive configuration guide (400+ lines)
  - `config.example.yaml` - Full YAML template with examples
  - `.env.example` - Environment variable template

### Changed
- 📦 **server.py** - Expanded from 701 to 1100+ lines
  - Integrated error handling, caching, and configuration
  - Better code organization with helper modules
- 🧪 **Test Suite** - Expanded from 30 to 56 tests
  - Added 26 tests for Pydantic models
  - Coverage: 63.64% overall (78% for server.py)
  - All tests pass in ~3-5 seconds
- 📖 **README.md** - Updated with Phase 2 features
  - Added Configuration section with env vars table
  - Documented 3 new MCP tools
  - Updated Key Features (7 → 10 features)
  - Added quick config examples

### Performance
- ⚡ **Faster Startup** - Cache eliminates scan on repeated operations
- 🔄 **Better Reliability** - Retry logic handles transient network issues
- 🎯 **Optimized Scanning** - Configurable workers and timeout
- 💾 **Reduced Network Traffic** - Cache reduces repeated device queries

### Technical
- 📦 **New Modules**
  - `src/wemo_mcp_server/error_handling.py` (205 lines)
  - `src/wemo_mcp_server/cache.py` (222 lines)  
  - `src/wemo_mcp_server/config.py` (242 lines)
- 🔍 **Dependencies**
  - `pydantic>=2.0.0` - Input validation
  - `pyyaml>=6.0.0` - YAML config support (optional)

### Validated
- ✅ **E2E Testing** - All features validated with 13 real WeMo devices
  - scan_network: 20.49s scan time
  - Persistent cache: 26 entries saved
  - Retry logic: Handled device timeouts
  - Configuration: Loaded from env vars

## [1.2.0] - 2026-02-21

### 🏆 Repository Restructuring - Production Standards

Major repository reorganization to meet professional open-source standards and improve maintainability.

### Added
- 🔐 **SECURITY.md** - Comprehensive security policy and vulnerability reporting
- 🤝 **CONTRIBUTING.md** - Complete contribution guidelines and development workflow
- 📜 **CODE_OF_CONDUCT.md** - Contributor Covenant v2.1 for community standards
- 📋 **Issue Templates** - Structured templates for bugs, features, and questions (YAML format)
- 🔄 **PR Template** - Comprehensive pull request checklist
- 📚 **docs/** - New documentation directory structure
- 📖 **docs/PUBLISHING.md** - Consolidated publishing guide (single source of truth)
- 🗄️ **docs/archive/** - Historical documentation preserved

### Changed
- 📁 **Repository Structure** - Reorganized for clarity and professionalism
  - Root level: 14 files → 6 essential files (57% reduction)
  - Documentation: 3,385 lines → ~2,000 lines (41% reduction)
  - Consolidated 5 publishing docs into 1 comprehensive guide
- 📚 **Documentation Organization** - Moved historical docs to archive
  - MIGRATION.md → docs/archive/
  - RELEASE_NOTES_v1.1.x → docs/archive/
  - Publishing automation docs → docs/archive/

### Removed
- 🗑️ **Redundant Documentation** - Deleted 3 superseded publishing files
- 🔒 **Security Risk** - Removed MCP Registry token files from disk
  - .mcpregistry_github_token
  - .mcpregistry_registry_token
  - Verified not present in git history

### Security
- ✅ Token files removed and verified clean from git history
- ✅ Security policy established with vulnerability reporting process
- ✅ Pre-commit security checks documented in contribution guidelines

### GitHub Community Standards
Achieved **6/6** GitHub community standards:
- ✅ Description
- ✅ README
- ✅ Code of Conduct
- ✅ Contributing Guidelines
- ✅ License
- ✅ Security Policy

### Benefits
- 🎯 **Better Organization** - Clear separation of user docs, developer docs, and historical docs
- 🤝 **Contributor-Friendly** - Structured issue/PR process with templates and guidelines
- 🔒 **Enhanced Security** - No sensitive files, clear security practices
- 📊 **Professional Standards** - Matches industry best practices for open-source projects
- 🔍 **Better Discoverability** - Improved GitHub search ranking and community standards score

## [1.1.0] - 2026-02-21

### 🏠 Repository Migration - New Home!

The WeMo MCP Server has been migrated to its own dedicated repository for better discoverability and to comply with MCP Registry requirements.

**New Repository:** https://github.com/apiarya/wemo-mcp-server

### Changed
- 🏗️ **Repository structure** - Now a standalone repository (was `/mcp` subdirectory in monorepo)
- 🔖 **Version tags** - Simplified from `mcp-v*` to `v*` format (e.g., `v1.1.0`)
- 📦 **Package ownership** - Transferred to @apiarya for maintenance
- 🔧 **CI/CD pipeline** - Updated for standalone repository structure
- 🌐 **Repository URLs** - All references updated to new location
- 📝 **Documentation** - Updated with new repository links and structure

### Added
- 🔒 **uv.lock** - Added to version control for reproducible builds (285KB)
- 🤖 **GitHub Actions** - Automated PyPI publishing with Trusted Publishing (OIDC)
- 📋 **PYPI_PUBLISHING.md** - Comprehensive release and publishing documentation
- 🔄 **Workflow automation** - Automatic PyPI publish on GitHub release

### Why This Move?
1. **MCP Registry Compliance** - Registry requires base repository URLs without path components
2. **Better Discoverability** - Users from registry land directly on MCP documentation  
3. **Industry Standards** - Aligns with patterns used by major MCP servers (GitHub, Cloudflare)
4. **Clearer Separation** - Reduces confusion between desktop app and MCP server releases

### Migration Details
- **Git History** - Full commit history preserved (15 commits migrated)
- **Tags Migrated** - All historical tags including `mcp-v0.1.0`, `mcp-v1.0.0`, `mcp-v1.0.1`
- **No Breaking Changes** - Installation commands remain identical
- **Package Name** - Unchanged: `wemo-mcp-server` on PyPI

### For Users
**No action needed!** Install or upgrade as usual:
```bash
pip install --upgrade wemo-mcp-server
# or
uvx wemo-mcp-server@latest
```

### For Contributors
- **Issues:** https://github.com/apiarya/wemo-mcp-server/issues
- **Pull Requests:** https://github.com/apiarya/wemo-mcp-server/pulls
- **Related Project:** [WeMo Ops Center](https://github.com/qrussell/wemo-ops-center) (desktop & server applications)

## [1.0.1] - 2026-02-16

### Fixed
- 📝 **MCP Registry validation** - Added `mcp-name: io.github.qrussell/wemo` to package README for registry ownership validation
- 🔧 **Registry metadata** - Updated `server.json` to version 1.0.1

This patch release enables successful publication to the official MCP Registry at https://registry.modelcontextprotocol.io/

## [1.0.0] - 2026-02-16

### Added
- 🎉 **Initial stable release** of WeMo MCP Server
- 🔍 **Multi-phase device discovery** combining UPnP/SSDP and network scanning
- ⚡ **Fast parallel scanning** with 60 concurrent workers (~23-30s for full subnet)
- 🎛️ **Full device control** (on/off/toggle/brightness for dimmers)
- ✏️ **Device management** (rename devices, extract HomeKit codes)
- 📊 **Real-time status monitoring** of all WeMo devices
- 💾 **Automatic device caching** for quick access
- 🔌 **Universal MCP client support** (Claude Desktop, Claude Code CLI, VS Code, Cursor)
- 📚 **Comprehensive documentation** with table of contents
- 🚀 **One-click installation** badges for VS Code and Cursor
- 🔧 **Prerequisites section** explaining uvx/uv requirements
- 🖼️ **Example usage screenshots** showing Claude Desktop integration

### Documentation
- Complete README with installation guides for all MCP clients
- Table of contents for easy navigation
- Detailed tool documentation with example prompts and responses
- Multi-phase discovery explanation
- Feature comparison with wemo-ops-center project
- Development setup and contribution guidelines
- Release documentation and checklist

### Tools
- `scan_network` - Discover WeMo devices with intelligent multi-phase scanning
- `list_devices` - List all cached devices from previous scans
- `get_device_status` - Get current state and information for specific devices
- `control_device` - Control devices (on/off/toggle/brightness)
- `rename_device` - Rename devices (change friendly name)
- `get_homekit_code` - Extract HomeKit setup codes

### Infrastructure
- Automated PyPI publishing via GitHub Actions
- Trusted publishing support for secure releases
- Comprehensive test suite (unit + E2E tests)
- Type hints and linting with ruff/mypy
- Code formatting with black/isort

## [0.1.0] - 2026-02-15

### Added
- Initial beta release
- Basic device discovery and control functionality
- MCP server implementation
- PyPI packaging setup

[1.1.0]: https://github.com/apiarya/wemo-mcp-server/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/apiarya/wemo-mcp-server/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/apiarya/wemo-mcp-server/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/apiarya/wemo-mcp-server/releases/tag/v0.1.0
