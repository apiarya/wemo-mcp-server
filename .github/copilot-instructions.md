<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# WeMo MCP Server - Copilot Instructions

## 🤖 Mandatory Rules for AI Agents

> These rules apply to GitHub Copilot and any AI assistant making changes in this repo.
> Violating them has caused CI failures and broken releases in the past.

### BEFORE EVERY `git commit` — no exceptions

1. **Run the full test suite** and confirm it passes:
   ```bash
   .venv/bin/python -m pytest tests/test_server.py tests/test_phase2.py tests/test_models.py -q --tb=short
   # Must show: X passed, 0 failed
   ```
   - This takes ~5 seconds. There is no acceptable reason to skip it.
   - Do NOT use `--no-verify`. Pre-commit hooks run black, ruff, mypy, and pytest automatically.
   - If a test fails, fix the test or the code before committing. Do not commit broken tests.

2. Only after the test suite passes, commit normally (no `--no-verify`):
   ```bash
   git commit -m "your message"
   ```
   The pre-commit hooks will run black, ruff, mypy, and pytest automatically.
   If any hook fails, fix the issue and retry.

### BEFORE EVERY `git push` — always ask the user first

Show the commit summary and wait for explicit confirmation before pushing:
```bash
git log origin/main..HEAD --oneline
```
Exception: user has explicitly said "push" or "commit and push" in their request.

### WHY THIS MATTERS

The `cache_keys` removal (Feb 21 2026) broke CI because tests were not run before committing.
A 5-second local test run would have caught it immediately.
**Never let a CI failure be the first signal that something is broken.**

**Production-ready MCP Server for WeMo smart home device control via AI assistants.**

## Project Identity
- **Repository**: https://github.com/apiarya/wemo-mcp-server
- **Package**: `wemo-mcp-server` (PyPI)
- **MCP Name**: `io.github.apiarya/wemo`
- **Version**: v1.4.0 (stable)
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
│   ├── __init__.py          # Package init and version (__version__ = "1.4.0")
│   ├── __main__.py          # Entry point for python -m wemo_mcp_server
│   ├── server.py            # Main server (~1570 lines) - tools, resources, prompts, elicitations
│   ├── cache.py             # Persistent JSON device cache (DeviceCache)
│   ├── config.py            # YAML + env var configuration management
│   ├── error_handling.py    # Retry decorator + error classification
│   └── models.py            # Pydantic request/response models
├── tests/
│   ├── __init__.py
│   ├── test_server.py       # Unit tests (30 tests, server.py)
│   ├── test_phase2.py       # Unit tests (72 tests, cache/config/error_handling)
│   ├── test_models.py       # Unit tests (Pydantic models)
│   └── test_e2e.py          # End-to-end tests with real devices
├── .github/
│   ├── workflows/
│   │   ├── ci.yml           # CI: multi-version tests + quality checks
│   │   └── release.yml      # Release: publish to PyPI + MCP Registry
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

## Recent Improvements - Phase 1 Complete ✅

**Quality Foundation (Weeks 1-5)** - Completed February 21, 2026

### CI/CD Pipeline
- ✅ GitHub Actions workflow with multi-version testing (Python 3.10-3.13)
- ✅ Automated quality checks (pytest, ruff, black, isort)
- ✅ Pre-commit hooks configured (`.pre-commit-config.yaml`)
- ✅ Coverage reporting integrated
- ✅ All checks passing on every push

### Test Suite Expansion
- **Before**: 12 tests, 32.14% coverage
- **After**: 30 tests, 78.14% coverage
- **Improvement**: +18 tests, +46pp coverage
- **Test Speed**: ~3.5 seconds for full suite
- **New Test File**: 580 lines with comprehensive coverage

### Code Quality Improvements
- ✅ Reduced code complexity:
  - `scan_subnet()`: Complexity 13 → 6 (extracted 4 helper methods)
  - `control_device()`: Complexity 13 → 6 (extracted 4 helper functions)
- ✅ All complexity violations resolved (C901, PLR0912)
- ✅ All docstring checks passing (D107, D205, D401)
- ✅ 22+ pragmatic linting rules configured
- ✅ Code formatted with black, imports sorted with isort

### Helper Functions Extracted
**WeMoScanner methods:**
- `_run_upnp_discovery()` - Phase 1 UPnP/SSDP discovery
- `_parse_cidr_network()` - CIDR validation and parsing
- `_probe_active_ips()` - Phase 2 parallel port probing
- `_verify_wemo_devices()` - Phase 3 device verification

**Module-level helpers:**
- `_validate_action()` - Action parameter validation
- `_validate_brightness()` - Brightness range validation
- `_perform_device_action()` - Execute device actions
- `_build_control_result()` - Build result dictionaries

### Local Validation Workflow
- ✅ Comprehensive pre-push checklist
- ✅ Quick validation script (`scripts/validate.sh`)
- ✅ Shift-left testing philosophy enforced
- ✅ All checks must pass locally before push

### Benefits Achieved
- 🚀 **Faster Development**: Instant local feedback, no CI wait time
- 🛡️ **Higher Quality**: 78% test coverage, automated enforcement
- 📈 **Better Maintainability**: Reduced complexity, clear structure
- ✅ **Professional Standards**: CI/CD pipeline, comprehensive testing

## Recent Improvements - Phase 3 Complete ✅

**MCP Primitives (v1.4.0)** - Completed February 22, 2026

### New MCP Primitives
- ✅ MCP Resources: `devices://` (static index) + `device://{device_id}` (live state, URL-decoded)
- ✅ MCP Prompts: 4 guided prompts (discover-devices, device-status-report, activate-scene, troubleshoot-device)
- ✅ MCP Elicitations: subnet confirmation in `scan_network` + device disambiguation in `control_device`

### Infrastructure
- ✅ CI/CD: multi-version (3.10–3.13), Dependabot weekly scans, pip-audit security checks
- ✅ Branch protection: 6 required status checks, no force-push/delete, auto-merge enabled
- ✅ Release gate: `release.yml` blocks publish if any CI check failed on the tagged commit
- ✅ 128 tests across 3 test files, ~82% overall coverage
- ✅ Release v1.4.0 published to PyPI + MCP Registry

## MCP Tools (9 Total) - server.py
All tools are async and decorated with `@mcp.tool()`:

### 1. `scan_network(subnet, timeout, max_workers)`
- **Purpose**: Discover WeMo devices on network
- **Method**: Multi-phase (UPnP/SSDP first, then port scanning backup)
- **Returns**: Device list with full details + caches devices
- **Performance**: ~23-30s for full /24 subnet with 60 workers

### 2. `list_devices()`
- **Purpose**: List cached devices from previous scans
- **Returns**: Device count and device list
- **Note**: Falls back to persistent JSON cache on restart — no rescan required

### 3. `get_device_status(device_identifier)`
- **Purpose**: Get real-time device state
- **Input**: Device name or IP address
- **Returns**: State (on/off), brightness (if dimmer), device info
- **Note**: Auto-reconnects from file cache if in-memory cache is empty

### 4. `control_device(device_identifier, action, brightness)`
- **Purpose**: Control devices
- **Actions**: "on", "off", "toggle", "brightness"
- **Brightness**: 1-100 for dimmers
- **Returns**: Success status, new state, brightness
- **Note**: Auto-reconnects from file cache if in-memory cache is empty

### 5. `rename_device(device_identifier, new_name)`
- **Purpose**: Change device friendly name
- **Updates**: Device cache and WeMo device itself
- **Returns**: Old name, new name, success status

### 6. `get_homekit_code(device_identifier)`
- **Purpose**: Extract HomeKit setup code
- **Note**: Not all devices support HomeKit
- **Returns**: HomeKit code (format: XXX-XX-XXX)

### 7. `get_cache_info()`
- **Purpose**: Inspect persistent cache status
- **Returns**: Cache age, TTL, device count, expiry status

### 8. `clear_cache()`
- **Purpose**: Clear file + in-memory cache to force fresh scan
- **Returns**: Success status

### 9. `get_configuration()`
- **Purpose**: View all current config settings
- **Returns**: Network, cache, and logging settings with active values

## MCP Resources (2 Total) - server.py
Decorated with `@mcp.resource()`:

### `devices://`
- **Purpose**: Static JSON index of all devices in the in-memory cache
- **Returns**: List of `{name, ip, type}` for every cached device

### `device://{device_id}`
- **Purpose**: Live state for a specific device (name or IP, URL-decoded)
- **Returns**: Current state (on/off), brightness (if dimmer), model info

## MCP Prompts (4 Total) - server.py
Decorated with `@mcp.prompt()`:

| Prompt | Description |
|--------|-------------|
| `discover-devices` | Guided network scan with subnet selection |
| `device-status-report` | Full status summary of all cached devices |
| `activate-scene` | Control multiple devices simultaneously as a scene |
| `troubleshoot-device` | Step-by-step diagnostic for a non-responsive device |

## MCP Elicitations
Triggered automatically when context is ambiguous. Schemas defined in `server.py` lines 43–55:

| Schema | Used by | Triggers when |
|--------|---------|---------------|
| `_SubnetChoiceSchema(subnet: str)` | `scan_network` | Default `192.168.1.0/24` with no `WEMO_MCP_DEFAULT_SUBNET` env override |
| `_DeviceChoiceSchema(device_name: str)` | `control_device` | Device identifier not found in in-memory or file cache |

**Client support**: Claude Desktop v1.1+ ✅ · MCP Inspector v0.20+ ✅ · VS Code ❌

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

### Unit Tests
- **128 tests** across 3 test files (30 + 72 + 26)
- **~81.88% overall coverage**
- All tests pass in ~4 seconds
- Run: `pytest tests/test_server.py tests/test_phase2.py tests/test_models.py -v`

### Test Coverage Breakdown
```
src/wemo_mcp_server/__init__.py       100.00% coverage
src/wemo_mcp_server/error_handling.py 100.00% coverage
src/wemo_mcp_server/cache.py           96.34% coverage
src/wemo_mcp_server/config.py          91.11% coverage
src/wemo_mcp_server/models.py          86.05% coverage
src/wemo_mcp_server/server.py          ~57% coverage
──────────────────────────────────────────────────────
TOTAL                                  ~81.88% coverage
```

### E2E Tests (test_e2e.py)
- Requires actual WeMo devices on network
- Tests all 9 MCP tools end-to-end
- Configurable device count and control testing
- **Not run in CI** (requires physical hardware)
- Run: `python tests/test_e2e.py`

### Test Commands
```bash
# Run all unit tests (fast, CI-compatible) — REQUIRED before every commit
.venv/bin/python -m pytest tests/test_server.py tests/test_phase2.py tests/test_models.py -q --tb=short

# Run with coverage
pytest tests/test_server.py tests/test_phase2.py tests/test_models.py --cov=wemo_mcp_server --cov-report=html

# Run E2E tests (needs real devices)
python tests/test_e2e.py

# Quick validation (all checks)
./scripts/validate.sh
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

### Pre-Commit Security Check 🔒 CRITICAL
**Before every commit**, scan for sensitive data and secrets:

#### What to Check:
1. **API Keys & Tokens**
   - [ ] No API keys (OpenAI, Anthropic, etc.)
   - [ ] No access tokens (GitHub, PyPI, etc.)
   - [ ] No authentication credentials

2. **Configuration Files**
   - [ ] No hardcoded passwords or secrets
   - [ ] No private keys or certificates
   - [ ] No database credentials

3. **Personal Information**
   - [ ] No email addresses (except public ones in documentation)
   - [ ] No phone numbers or addresses
   - [ ] No internal URLs or endpoints

4. **MCP Registry Tokens**
   - [ ] No `.mcpregistry_github_token` content
   - [ ] No `.mcpregistry_registry_token` content
   - [ ] These files should be in `.gitignore`

5. **Environment Files**
   - [ ] No `.env` files committed
   - [ ] No secrets in shell scripts
   - [ ] No hardcoded credentials in config files

#### Quick Security Scan Commands:
```bash
# Check for common secret patterns
git diff --cached | grep -iE '(api[_-]?key|secret|token|password|credential)'

# Check for potential secrets in all staged files
git diff --cached --name-only | xargs grep -iE '(api[_-]?key|secret|token|password|credential)' 2>/dev/null

# Check for email addresses
git diff --cached | grep -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# View all staged changes for manual review
git diff --cached
```

#### Common False Positives (OK to commit):
- ✅ Example API keys in documentation (clearly marked as examples)
- ✅ Public PyPI tokens in documentation (for educational purposes)
- ✅ "secret" or "token" in variable names or comments
- ✅ Public email addresses in LICENSE or CONTRIBUTORS

#### If You Find Secrets:
```bash
# Unstage the file
git reset HEAD <file>

# Remove the secret from the file
vim <file>

# Stage the cleaned file
git add <file>
```

**⚠️ If already committed but not pushed:**
```bash
# Amend the last commit
git commit --amend

# Or reset and recommit
git reset HEAD~1
# Clean files, then re-commit
```

**🚨 If already pushed:**
1. Immediately revoke the exposed credential
2. Generate a new credential
3. Update the code with new credential (via environment variables)
4. Consider using `git filter-branch` or BFG Repo-Cleaner to remove from history
5. Notify team/users if necessary

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

### Shift Left: Local Validation 🚀 CRITICAL
**Run ALL checks locally BEFORE committing or pushing!**

**Philosophy**: Catch issues early, fail fast locally, never waste time with CI failures.

#### Complete Pre-Commit/Pre-Push Checklist

**ALWAYS run these checks locally before committing:**

```bash
# 1. Run all tests (should take ~3-5 seconds)
pytest tests/test_server.py -v --tb=short
# Expected: 30 passed in ~3.5s

# 2. Run linting (should be instant)
ruff check src/ tests/
# Expected: All checks passed!

# 3. Check code formatting (should be instant)
black --check src/ tests/
# Expected: All done! ✨ 🍰 ✨ (6 files would be left unchanged)

# 4. Check import sorting (should be instant)
isort --check-only src/ tests/
# Expected: (no output = success)

# 5. Verify module imports (should be instant)
python -c "import wemo_mcp_server.server; print('✅ Module imports successfully')"
# Expected: ✅ Module imports successfully
```

#### Quick Validation Script

**Create this as `scripts/validate.sh` for one-command validation:**

```bash
#!/bin/bash
# Quick local validation script

set -e  # Exit on first error

echo "🧪 Running tests..."
pytest tests/test_server.py -v --tb=short

echo ""
echo "🔍 Running linting..."
ruff check src/ tests/

echo ""
echo "🎨 Checking code formatting..."
black --check src/ tests/

echo ""
echo "📦 Checking import sorting..."
isort --check-only src/ tests/

echo ""
echo "✅ Verifying module imports..."
python -c "import wemo_mcp_server.server; print('✅ Module imports successfully')"

echo ""
echo "✅✅✅ All local checks passed! Safe to commit/push. ✅✅✅"
```

**Usage:**
```bash
# Make executable
chmod +x scripts/validate.sh

# Run before every commit/push
./scripts/validate.sh
```

#### Auto-fix Common Issues

If checks fail, auto-fix formatting issues:

```bash
# Auto-fix formatting
black src/ tests/

# Auto-fix import sorting
isort src/ tests/

# Auto-fix some linting issues
ruff check src/ tests/ --fix

# Re-run validation
./scripts/validate.sh
```

#### Integration with Git Workflow

**Recommended workflow:**

```bash
# 1. Make code changes
vim src/wemo_mcp_server/server.py

# 2. Run tests first (fast check before committing)
.venv/bin/python -m pytest tests/test_server.py tests/test_phase2.py tests/test_models.py -q --tb=short

# 3. Commit — pre-commit hooks run automatically (black, ruff, mypy, pytest)
git add -A
git commit -m "Your commit message"
# Hooks auto-fix formatting; if they modify files, stage and commit again

# 4. Push (after user confirmation)
git push origin main
```

#### Why This Matters

**Time saved from CI failures:**
- Local check: ~5 seconds
- CI failure + debug + fix + repush: ~5-10 minutes
- **Savings: 60-120x faster feedback loop**

**Benefits:**
- ✅ Instant feedback (no waiting for CI)
- ✅ Catch issues before they reach origin
- ✅ Cleaner git history (fewer "fix CI" commits)
- ✅ Less context switching
- ✅ Respect for CI resources
- ✅ Professional development practice

**Golden Rule**: If it won't pass CI, don't push it. Run checks locally first!

### Before Pushing 🚨 ALWAYS ASK
**Never push without user confirmation!**

Before executing `git push`:
1. **Review what will be pushed**:
   ```bash
   # See commits that will be pushed
   git log origin/main..HEAD --oneline

   # See all changes that will be pushed
   git diff origin/main..HEAD
   ```

2. **Final security check**:
   ```bash
   # Scan all commits being pushed for secrets
   git log origin/main..HEAD -p | grep -iE '(api[_-]?key|secret|token|password|credential)'
   ```

3. **Ask the user**:
   - Show summary of commits being pushed
   - Show file changes summary
   - Wait for explicit confirmation before pushing
   - Example: "Ready to push 3 commits (modified: 5 files). Proceed? (y/n)"

4. **Only push after confirmation**:
   ```bash
   # User says yes
   git push origin main

   # User says no
   # Explain what needs to be fixed and wait for next instruction
   ```

**⚠️ IMPORTANT**: This is a safety mechanism to prevent accidental pushes of:
- Unreviewed code
- Sensitive data that passed initial checks
- Incomplete work
- Commits to wrong branch

**Exception**: Only skip confirmation for:
- Automated CI/CD workflows (GitHub Actions)
- Explicitly requested immediate pushes ("push now", "commit and push")

## Publishing & CI/CD

### Automated Publishing (✅ ACTIVE)
**GitHub Actions workflow**: `.github/workflows/release.yml`

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

**Last Updated**: February 22, 2026 (v1.4.0 + MCP Resources, Prompts, Elicitations + mandatory AI pre-commit rules)
