# WeMo MCP Server - Comprehensive Improvement Plan

**Generated**: February 21, 2026  
**Current Version**: v1.2.0  
**Project Health**: Production-ready, professionally structured

## Executive Summary

### Current State
- **Code**: 1,334 lines across 6 Python files
- **Tests**: 15 unit tests + 6 E2E tests  
- **Coverage**: ~45% (estimated, not measured)
- **Quality**: GitHub 6/6 community standards ✅
- **Status**: Production-ready, published on PyPI & MCP Registry

### Key Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | ~45% | 85%+ |
| Unit Tests | 15 | 60+ |
| Code Quality Score | B | A+ |
| CI/CD Checks | 1 (publish) | 5+ |
| Documentation Coverage | 70% | 95% |

---

## Priority Matrix

### 🔴 Critical (Must Have - Next Release)
1. **CI/CD Testing Pipeline** - Automated quality gates
2. **Test Coverage Reporting** - Measure and track quality
3. **Code Quality Automation** - Linting, formatting, type checking
4. **Error Handling Enhancement** - Robust error recovery
5. **Input Validation** - Security and reliability

### 🟠 High Priority (Should Have - 2-4 weeks)
6. **Expanded Test Suite** - Comprehensive test coverage
7. **Performance Optimization** - Caching, parallelization
8. **Persistent Device Cache** - Survive restarts
9. **Configuration Management** - User-configurable settings
10. **Observability** - Structured logging, metrics

### 🟡 Medium Priority (Nice to Have - 1-2 months)
11. **Code Modularization** - Split 701-line server.py
12. **Advanced Features** - Event subscriptions, device monitoring
13. **Documentation Enhancement** - Architecture, troubleshooting
14. **Developer Experience** - Pre-commit hooks, Docker, debug configs
15. **MCP Resources** - Expose device info as MCP resources

### 🟢 Low Priority (Future - 3+ months)
16. **Multi-subnet Support** - Scan multiple networks
17. **Device Simulator** - Testing without real hardware
18. **Performance Benchmarks** - Automated performance tracking
19. **Additional Features** - Color support, energy monitoring
20. **Alternative Distribution** - Docker, Homebrew, binaries

---

## Detailed Improvement Plan

## Phase 1: Quality Foundation (Week 1-2)

### 1.1 CI/CD Testing Pipeline 🔴
**Impact**: Critical | **Effort**: Medium | **Priority**: P0

**Problem**: No automated testing in CI; quality issues only caught manually.

**Solution**: Add comprehensive GitHub Actions workflow for PR validation.

**Implementation**:
```yaml
# .github/workflows/test.yml
name: Test & Quality Checks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov --cov-report=xml
      - run: mypy src/
      - run: ruff check src/ tests/
      - run: black --check src/ tests/
      - uses: codecov/codecov-action@v3
```

**Benefits**:
- Catch bugs before merge
- Ensure code quality standards
- Multi-version Python testing
- Public coverage reporting

**Acceptance Criteria**:
- ✅ Tests run on every PR
- ✅ Quality checks must pass to merge
- ✅ Coverage report published
- ✅ Works across Python 3.10-3.13

---

### 1.2 Test Coverage Reporting 🔴
**Impact**: High | **Effort**: Low | **Priority**: P0

**Problem**: No visibility into test coverage; untested code paths unknown.

**Solution**: Integrate pytest-cov and Codecov for coverage tracking.

**Implementation**:
```toml
# pyproject.toml
[tool.coverage.run]
source = ["src/wemo_mcp_server"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Add Badge to README**:
```markdown
[![codecov](https://codecov.io/gh/apiarya/wemo-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/apiarya/wemo-mcp-server)
```

**Benefits**:
- Visualize untested code
- Track coverage trends
- Set coverage targets (85%+)
- Public quality signal

**Acceptance Criteria**:
- ✅ Coverage reports generated
- ✅ Codecov integrated
- ✅ Badge in README
- ✅ Coverage ≥ 60% initially

---

### 1.3 Code Quality Automation 🔴
**Impact**: High | **Effort**: Low | **Priority**: P0

**Problem**: Code style inconsistencies; no automated enforcement of ruff/black/mypy.

**Solution**: Add pre-commit hooks and update CI to enforce.

**Implementation**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

**Benefits**:
- Consistent code style
- Catch type errors early
- Automatic formatting
- Reduced review friction

**Acceptance Criteria**:
- ✅ Pre-commit hooks configured
- ✅ All checks pass on current code
- ✅ Documentation updated
- ✅ CI enforces these checks

---

### 1.4 Enhanced Error Handling 🔴
**Impact**: High | **Effort**: Medium | **Priority**: P1

**Problem**: Basic error handling; network failures can crash tools.

**Solution**: Add retry logic, exponential backoff, detailed error messages.

**Implementation**:
```python
# src/wemo_mcp_server/retry.py
import functools
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in server.py
@retry_with_backoff(max_attempts=3, base_delay=0.5)
async def get_device_state(device):
    """Get device state with automatic retry."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, device.get_state, True)
```

**Benefits**:
- Robust network operations
- Better user experience
- Detailed error messages
- Graceful degradation

**Acceptance Criteria**:
- ✅ Retry logic for network ops
- ✅ Exponential backoff implemented
- ✅ User-friendly error messages
- ✅ Tests for error scenarios

---

### 1.5 Input Validation 🔴
**Impact**: Critical | **Effort**: Low | **Priority**: P1

**Problem**: No validation of CIDR notation, device identifiers, brightness values.

**Solution**: Add pydantic models for input validation.

**Implementation**:
```python
# src/wemo_mcp_server/models.py
from pydantic import BaseModel, Field, field_validator
import ipaddress

class ScanNetworkParams(BaseModel):
    """Parameters for network scanning."""
    subnet: str = Field(
        default="192.168.1.0/24",
        description="Network subnet in CIDR notation"
    )
    timeout: float = Field(
        default=0.6,
        gt=0.1,
        le=10.0,
        description="Connection timeout in seconds"
    )
    max_workers: int = Field(
        default=60,
        ge=1,
        le=200,
        description="Maximum concurrent workers"
    )
    
    @field_validator('subnet')
    @classmethod
    def validate_subnet(cls, v: str) -> str:
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {v}") from e

class ControlDeviceParams(BaseModel):
    """Parameters for device control."""
    device_identifier: str = Field(
        min_length=1,
        description="Device name or IP address"
    )
    action: str = Field(
        pattern="^(on|off|toggle|brightness)$",
        description="Action to perform"
    )
    brightness: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Brightness level (1-100)"
    )
```

**Benefits**:
- Prevent invalid inputs
- Better error messages
- Type safety
- Security enhancement

**Acceptance Criteria**:
- ✅ All inputs validated
- ✅ Clear error messages
- ✅ Tests for edge cases
- ✅ Documentation updated

---

## Phase 2: Testing Excellence (Week 3-4)

### 2.1 Expanded Unit Test Suite 🟠
**Impact**: High | **Effort**: High | **Priority**: P1

**Problem**: Only 15 unit tests; many code paths untested.

**Solution**: Achieve 85%+ test coverage with comprehensive unit tests.

**Test Coverage Goals**:
```python
# Target test files:
# tests/test_scanner.py        - WeMoScanner class (100%)
# tests/test_tools.py          - All 6 MCP tools (90%+)
# tests/test_cache.py          - Device cache operations (100%)
# tests/test_models.py         - Input validation (100%)
# tests/test_retry.py          - Retry logic (100%)
# tests/test_error_handling.py - Error scenarios (90%+)
```

**New Tests Needed**:
1. **WeMoScanner Tests** (15 tests)
   - Port probing edge cases
   - Timeout handling
   - Network errors
   - Parallel execution
   - UPnP discovery mocking

2. **MCP Tool Tests** (30 tests)
   - scan_network: success, partial failure, total failure
   - list_devices: empty, single, multiple
   - get_device_status: online, offline, error
   - control_device: all actions, dimmer, switch
   - rename_device: success, failure, duplicate name
   - get_homekit_code: supported, unsupported, error

3. **Cache Tests** (10 tests)
   - Add device
   - Remove device
   - Update device
   - Duplicate handling
   - Expiration (if implemented)

4. **Integration Tests** (5 tests)
   - End-to-end tool chaining
   - Multi-device scenarios
   - Concurrent operations

**Acceptance Criteria**:
- ✅ 60+ total unit tests
- ✅ 85%+ code coverage
- ✅ All critical paths tested
- ✅ CI tests pass consistently

---

### 2.2 Mock-Based Testing 🟠
**Impact**: Medium | **Effort**: Medium | **Priority**: P2

**Problem**: E2E tests require real devices; no CI testing possible.

**Solution**: Create comprehensive mocks for pywemo devices.

**Implementation**:
```python
# tests/fixtures.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_switch():
    """Mock WeMo Switch device."""
    device = Mock()
    device.name = "Test Switch"
    device.model = "Socket"
    device.host = "192.168.1.100"
    device.port = 49153
    device.mac = "AA:BB:CC:DD:EE:FF"
    device.get_state.return_value = 1  # ON
    device.on = Mock()
    device.off = Mock()
    device.toggle = Mock()
    return device

@pytest.fixture
def mock_dimmer():
    """Mock WeMo Dimmer device."""
    device = Mock()
    device.name = "Test Dimmer"
    device.model = "Dimmer"
    device.host = "192.168.1.101"
    device.port = 49153
    device.get_state.return_value = 1
    device.get_brightness.return_value = 75
    device.set_brightness = Mock()
    return device

@pytest.fixture
def mock_discovery():
    """Mock pywemo discovery."""
    with patch('pywemo.discover_devices') as mock:
        yield mock
```

**Benefits**:
- Test without hardware
- CI testing possible
- Faster test execution
- Deterministic results

**Acceptance Criteria**:
- ✅ Comprehensive device mocks
- ✅ All tools testable in CI
- ✅ Mock fixtures documented
- ✅ Tests run in < 10 seconds

---

### 2.3 Performance Benchmarks 🟡
**Impact**: Medium | **Effort**: Medium | **Priority**: P3

**Problem**: No performance tracking; regression detection impossible.

**Solution**: Add pytest-benchmark for performance testing.

**Implementation**:
```python
# tests/test_performance.py
import pytest

def test_scan_performance(benchmark):
    """Benchmark network scanning speed."""
    result = benchmark(
        lambda: asyncio.run(scan_network("192.168.1.0/24"))
    )
    assert result["results"]["scan_duration_seconds"] < 30

def test_cache_lookup_performance(benchmark):
    """Benchmark device cache lookups."""
    # Populate cache with 100 devices
    for i in range(100):
        _device_cache[f"device_{i}"] = mock_device()
    
    result = benchmark(lambda: _device_cache.get("device_50"))
    assert result is not None

@pytest.mark.parametrize("device_count", [1, 10, 50, 100])
def test_scaling(device_count, benchmark):
    """Test performance with varying device counts."""
    # Test scaling characteristics
    pass
```

**Benefits**:
- Detect performance regressions
- Optimize hot paths
- Track improvement trends
- Set performance SLOs

**Acceptance Criteria**:
- ✅ Benchmark suite created
- ✅ Baseline metrics recorded
- ✅ CI runs benchmarks
- ✅ Regression alerts configured

---

## Phase 3: Features & Performance (Week 5-8)

### 3.1 Persistent Device Cache 🟠
**Impact**: High | **Effort**: Medium | **Priority**: P1

**Problem**: Device cache cleared on server restart; must rescan.

**Solution**: Implement persistent cache with SQLite or JSON file.

**Implementation**:
```python
# src/wemo_mcp_server/cache.py
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

class DeviceCache:
    """Persistent device cache with expiration."""
    
    def __init__(self, cache_file: Path, ttl: int = 3600):
        self.cache_file = cache_file
        self.ttl = ttl  # Time to live in seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.load()
    
    def load(self) -> None:
        """Load cache from disk."""
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                data = json.load(f)
                # Filter expired entries
                now = time.time()
                self._cache = {
                    k: v for k, v in data.items()
                    if now - v.get('timestamp', 0) < self.ttl
                }
    
    def save(self) -> None:
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self._cache, f, indent=2)
    
    def get(self, key: str) -> Optional[Any]:
        """Get device from cache."""
        entry = self._cache.get(key)
        if entry and time.time() - entry['timestamp'] < self.ttl:
            return entry['device']
        return None
    
    def set(self, key: str, device: Any) -> None:
        """Add device to cache."""
        self._cache[key] = {
            'device': self._serialize_device(device),
            'timestamp': time.time()
        }
        self.save()
    
    def clear_expired(self) -> int:
        """Remove expired entries."""
        now = time.time()
        before = len(self._cache)
        self._cache = {
            k: v for k, v in self._cache.items()
            if now - v['timestamp'] < self.ttl
        }
        removed = before - len(self._cache)
        if removed > 0:
            self.save()
        return removed

# Usage
cache = DeviceCache(
    cache_file=Path.home() / ".cache" / "wemo-mcp" / "devices.json",
    ttl=3600  # 1 hour
)
```

**Configuration**:
```python
# src/wemo_mcp_server/config.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Server configuration."""
    cache_dir: Path = Path.home() / ".cache" / "wemo-mcp"
    cache_ttl: int = 3600  # 1 hour
    cache_enabled: bool = True
    
    class Config:
        env_prefix = "WEMO_"
        env_file = ".env"

settings = Settings()
```

**Benefits**:
- Instant device access
- Reduced network scans
- Better user experience
- Configurable TTL

**Acceptance Criteria**:
- ✅ Cache persists across restarts
- ✅ Expired entries auto-cleaned
- ✅ User-configurable settings
- ✅ Tests for cache operations

---

### 3.2 Configuration Management 🟠
**Impact**: High | **Effort**: Low | **Priority**: P1

**Problem**: Hard-coded settings; no user configuration.

**Solution**: Add configuration file support with pydantic-settings.

**Implementation**:
```python
# src/wemo_mcp_server/config.py
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """WeMo MCP Server configuration."""
    
    # Network scanning
    default_subnet: str = "192.168.1.0/24"
    scan_timeout: float = 0.6
    max_workers: int = 60
    wemo_ports: List[int] = [49152, 49153, 49154, 49155]
    
    # Caching
    cache_enabled: bool = True
    cache_dir: Path = Path.home() / ".cache" / "wemo-mcp"
    cache_ttl: int = 3600
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # or "text"
    
    # Performance
    retry_attempts: int = 3
    retry_base_delay: float = 0.5
    retry_max_delay: float = 10.0
    
    # Features
    enable_device_monitoring: bool = False
    enable_event_subscriptions: bool = False
    
    model_config = SettingsConfigDict(
        env_prefix="WEMO_",
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
```

**User Configuration File** (~/.config/wemo-mcp/config.toml):
```toml
[network]
default_subnet = "192.168.1.0/24"
scan_timeout = 0.8
max_workers = 100

[cache]
enabled = true
ttl = 7200  # 2 hours

[logging]
level = "DEBUG"
format = "json"
```

**Benefits**:
- User customization
- Environment-specific settings
- Easier debugging
- Better defaults

**Acceptance Criteria**:
- ✅ Config file support (.env, .toml)
- ✅ Environment variables work
- ✅ Documentation for all settings
- ✅ Sensible defaults

---

### 3.3 Performance Optimization 🟠
**Impact**: Medium | **Effort**: Medium | **Priority**: P2

**Problem**: Sequential operations; no connection pooling.

**Solution**: Optimize hot paths and add caching layers.

**Optimizations**:

1. **Parallel Device Queries**:
```python
async def get_multiple_device_status(
    device_identifiers: List[str]
) -> List[Dict[str, Any]]:
    """Get status of multiple devices in parallel."""
    tasks = [
        get_device_status(identifier)
        for identifier in device_identifiers
    ]
    return await asyncio.gather(*tasks)
```

2. **Connection Pooling**:
```python
# src/wemo_mcp_server/connection_pool.py
class DeviceConnectionPool:
    """Pool of device connections for reuse."""
    def __init__(self, max_size: int = 10):
        self.pool: Dict[str, Any] = {}
        self.max_size = max_size
    
    async def get_connection(self, device_ip: str):
        """Get or create device connection."""
        if device_ip not in self.pool:
            if len(self.pool) >= self.max_size:
                # Evict oldest connection
                oldest = next(iter(self.pool))
                del self.pool[oldest]
            self.pool[device_ip] = await self._create_connection(device_ip)
        return self.pool[device_ip]
```

3. **Caching Layer**:
```python
from functools import lru_cache, wraps
import time

def cached_with_ttl(ttl: int = 60):
    """Cache function results with TTL."""
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache and now - timestamps[key] < ttl:
                return cache[key]
            
            result = await func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = now
            return result
        
        return wrapper
    return decorator

@cached_with_ttl(ttl=30)
async def get_device_status_cached(device_identifier: str):
    """Get device status with 30s cache."""
    return await get_device_status(device_identifier)
```

**Benefits**:
- Faster response times
- Reduced network overhead
- Better scalability
- Lower device load

**Acceptance Criteria**:
- ✅ 30% faster scans
- ✅ Parallel queries implemented
- ✅ Benchmarks show improvement
- ✅ No functionality regression

---

### 3.4 Event Subscriptions 🟡
**Impact**: Medium | **Effort**: High | **Priority**: P3

**Problem**: Polling-only; no real-time state changes.

**Solution**: Implement pywemo event subscriptions for push notifications.

**Implementation**:
```python
# src/wemo_mcp_server/events.py
from typing import Callable, Dict, Any
import asyncio

class DeviceEventManager:
    """Manage device event subscriptions."""
    
    def __init__(self):
        self.subscriptions: Dict[str, Callable] = {}
        self._running = False
    
    async def subscribe(self, device: Any, callback: Callable) -> None:
        """Subscribe to device state changes."""
        device_id = f"{device.host}:{device.port}"
        self.subscriptions[device_id] = callback
        
        # pywemo subscription
        device.register_callback(lambda: self._handle_event(device_id))
    
    async def _handle_event(self, device_id: str) -> None:
        """Handle device event."""
        callback = self.subscriptions.get(device_id)
        if callback:
            await callback(device_id)
    
    async def unsubscribe(self, device: Any) -> None:
        """Unsubscribe from device events."""
        device_id = f"{device.host}:{device.port}"
        if device_id in self.subscriptions:
            del self.subscriptions[device_id]

# Usage
event_manager = DeviceEventManager()

async def on_device_change(device_id: str):
    """Handle device state change."""
    logger.info(f"Device {device_id} state changed")
    # Update cache, notify clients, etc.

await event_manager.subscribe(device, on_device_change)
```

**Benefits**:
- Real-time updates
- Reduced polling
- Better responsiveness
- Lower network usage

**Acceptance Criteria**:
- ✅ Event subscriptions work
- ✅ Automatic reconnection
- ✅ Memory leak free
- ✅ Documentation updated

---

## Phase 4: Code Architecture (Week 9-10)

### 4.1 Code Modularization 🟡
**Impact**: Medium | **Effort**: High | **Priority**: P2

**Problem**: 701-line server.py; hard to maintain and test.

**Solution**: Split into logical modules with clear separation of concerns.

**Proposed Structure**:
```
src/wemo_mcp_server/
├── __init__.py
├── __main__.py
├── server.py           # MCP server setup, main entry (50 lines)
├── config.py           # Configuration management (80 lines)
├── models.py           # Pydantic models (100 lines)
├── cache.py            # Device caching (150 lines)
├── scanner.py          # WeMoScanner class (200 lines)
├── retry.py            # Retry logic (80 lines)
├── events.py           # Event subscriptions (150 lines)
├── tools/              # MCP tool implementations
│   ├── __init__.py
│   ├── scan.py         # scan_network tool
│   ├── list.py         # list_devices tool
│   ├── status.py       # get_device_status tool
│   ├── control.py      # control_device tool
│   ├── rename.py       # rename_device tool
│   └── homekit.py      # get_homekit_code tool
└── utils/
    ├── __init__.py
    ├── logging.py      # Logging utilities
    └── device_info.py  # Device info extraction
```

**Benefits**:
- Better organization
- Easier testing
- Clear responsibilities
- Improved maintainability

**Acceptance Criteria**:
- ✅ All modules < 200 lines
- ✅ Clear module boundaries
- ✅ All tests still pass
- ✅ Documentation updated

---

## Phase 5: Documentation & DX (Week 11-12)

### 5.1 Architecture Documentation 🟡
**Impact**: Medium | **Effort**: Medium | **Priority**: P2

**Documents to Create**:

1. **ARCHITECTURE.md**:
   - System overview diagram
   - Component interactions
   - Data flow diagrams
   - Technology stack
   - Design decisions

2. **TROUBLESHOOTING.md**:
   - Common issues & solutions
   - Debug mode instructions
   - Log analysis guide
   - Network troubleshooting

3. **API_REFERENCE.md**:
   - All MCP tools with examples
   - Input/output schemas
   - Error codes
   - Best practices

4. **FAQ.md**:
   - Installation troubleshooting
   - Configuration questions
   - Feature comparisons
   - Migration guides

**Benefits**:
- Easier onboarding
- Reduced support burden
- Better contributor experience
- Professional appearance

---

### 5.2 Developer Experience 🟡
**Impact**: Medium | **Effort**: Medium | **Priority**: P2

**Improvements**:

1. **Pre-commit Hooks** (covered in 1.3)

2. **VS Code Debug Configuration**:
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug MCP Server",
      "type": "python",
      "request": "launch",
      "module": "wemo_mcp_server",
      "console": "integratedTerminal",
      "env": {
        "WEMO_LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

3. **Development Docker Container**:
```dockerfile
# Dockerfile.dev
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e ".[dev]"
CMD ["python", "-m", "wemo_mcp_server"]
```

4. **Makefile for Common Tasks**:
```makefile
.PHONY: test lint format install

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

ci: lint test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
```

**Benefits**:
- Faster development
- Consistent environment
- One-command operations
- Better tooling

---

## Phase 6: Security & Observability (Week 13-14)

### 6.1 Security Enhancements 🟠
**Impact**: High | **Effort**: Medium | **Priority**: P1

**Security Improvements**:

1. **Dependency Scanning**:
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/gh-action-pip-audit@v1.0.8
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
```

2. **Rate Limiting**:
```python
# src/wemo_mcp_server/rate_limit.py
from collections import defaultdict
import time
from typing import Dict

class RateLimiter:
    """Simple rate limiter for device commands."""
    
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, device_id: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        # Clean old requests
        self.requests[device_id] = [
            t for t in self.requests[device_id]
            if now - t < self.window
        ]
        
        if len(self.requests[device_id]) < self.max_requests:
            self.requests[device_id].append(now)
            return True
        return False

rate_limiter = RateLimiter(max_requests=10, window=60)
```

3. **Input Sanitization** (covered in 1.5)

4. **Security Audit Checklist**:
- ✅ No hardcoded secrets
- ✅ Input validation everywhere
- ✅ Dependencies scanned
- ✅ Rate limiting implemented
- ✅ Network operations secured
- ✅ Error messages don't leak info

**Benefits**:
- Prevent abuse
- Detect vulnerabilities
- Secure by default
- Compliance ready

---

### 6.2 Structured Logging 🟠
**Impact**: Medium | **Effort**: Low | **Priority**: P2

**Problem**: Basic logging; hard to parse and analyze.

**Solution**: Add structured JSON logging with context.

**Implementation**:
```python
# src/wemo_mcp_server/logging.py
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """Structured JSON logger for MCP server."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(self.JSONFormatter())
        self.logger.addHandler(handler)
    
    class JSONFormatter(logging.Formatter):
        """Format logs as JSON."""
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add extra fields if present
            if hasattr(record, "extra"):
                log_data.update(record.extra)
            
            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_data)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(message, extra=kwargs)

# Usage
logger = StructuredLogger("wemo-mcp-server")
logger.info(
    "Device discovered",
    device_name="Office Light",
    device_ip="192.168.1.100",
    device_type="Dimmer"
)
```

**Benefits**:
- Easier log parsing
- Better monitoring
- Context-rich logs
- Analysis-friendly

**Acceptance Criteria**:
- ✅ JSON logging implemented
- ✅ All logs include context
- ✅ Performance impact minimal
- ✅ Human-readable fallback

---

### 6.3 Metrics & Monitoring 🟡
**Impact**: Low | **Effort**: Medium | **Priority**: P3

**Problem**: No visibility into runtime behavior and performance.

**Solution**: Add basic metrics collection.

**Implementation**:
```python
# src/wemo_mcp_server/metrics.py
from dataclasses import dataclass, field
from time import time
from typing import Dict, List

@dataclass
class Metrics:
    """Runtime metrics collector."""
    
    # Counters
    scans_total: int = 0
    devices_discovered: int = 0
    commands_sent: int = 0
    commands_failed: int = 0
    
    # Timing
    scan_durations: List[float] = field(default_factory=list)
    command_durations: List[float] = field(default_factory=list)
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    
    def record_scan(self, duration: float, device_count: int) -> None:
        """Record scan metrics."""
        self.scans_total += 1
        self.devices_discovered += device_count
        self.scan_durations.append(duration)
    
    def record_command(self, duration: float, success: bool) -> None:
        """Record command metrics."""
        self.commands_sent += 1
        if not success:
            self.commands_failed += 1
        self.command_durations.append(duration)
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            "scans": {
                "total": self.scans_total,
                "avg_duration": sum(self.scan_durations) / len(self.scan_durations) if self.scan_durations else 0,
                "total_devices": self.devices_discovered,
            },
            "commands": {
                "total": self.commands_sent,
                "failed": self.commands_failed,
                "success_rate": (self.commands_sent - self.commands_failed) / self.commands_sent if self.commands_sent else 0,
                "avg_duration": sum(self.command_durations) / len(self.command_durations) if self.command_durations else 0,
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) else 0,
            }
        }

metrics = Metrics()

# Add metrics endpoint (optional)
@mcp.tool()
async def get_server_metrics() -> Dict[str, Any]:
    """Get server runtime metrics."""
    return metrics.get_stats()
```

**Benefits**:
- Operational visibility
- Performance tracking
- Capacity planning
- Debugging aid

---

## Phase 7: Advanced Features (Week 15+)

### 7.1 MCP Resources 🟡
**Impact**: Medium | **Effort**: Medium | **Priority**: P2

**Problem**: Devices not exposed as MCP resources.

**Solution**: Implement MCP resource endpoints for device discovery.

**Implementation**:
```python
@mcp.resource("device://{device_id}")
async def get_device_resource(device_id: str) -> Dict[str, Any]:
    """Get device as MCP resource."""
    device = _device_cache.get(device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")
    
    return {
        "uri": f"device://{device_id}",
        "name": device.name,
        "mimeType": "application/json",
        "content": extract_device_info(device)
    }

@mcp.resource("devices://")
async def list_device_resources() -> List[Dict[str, Any]]:
    """List all devices as resources."""
    return [
        {
            "uri": f"device://{name}",
            "name": name,
            "mimeType": "application/json"
        }
        for name in _device_cache.keys()
        if isinstance(name, str) and not name.replace('.', '').isdigit()
    ]
```

**Benefits**:
- Better MCP integration
- Resource discovery
- Standard protocol
- Client compatibility

---

### 7.2 Multi-Subnet Support 🟢
**Impact**: Low | **Effort**: High | **Priority**: P3

**Problem**: Can only scan one subnet at a time.

**Solution**: Add multi-subnet scanning capability.

**Implementation**:
```python
@mcp.tool()
async def scan_multiple_networks(
    subnets: List[str],
    timeout: float = 0.6,
    max_workers: int = 60
) -> Dict[str, Any]:
    """Scan multiple subnets concurrently."""
    tasks = [
        scan_network(subnet, timeout, max_workers)
        for subnet in subnets
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_devices = []
    for result in results:
        if isinstance(result, dict) and "devices" in result:
            all_devices.extend(result["devices"])
    
    return {
        "subnets_scanned": len(subnets),
        "total_devices": len(all_devices),
        "devices": all_devices
    }
```

**Benefits**:
- VLAN support
- Complex networks
- Enterprise use
- Better coverage

---

### 7.3 Device Simulator 🟢
**Impact**: Low | **Effort**: High | **Priority**: P3

**Problem**: Testing requires real hardware.

**Solution**: Create software simulator for development.

**Implementation**:
```python
# tests/simulator.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class MockWeMoDevice:
    """Simulated WeMo device for testing."""
    
    def __init__(self, name: str, device_type: str, port: int):
        self.name = name
        self.type = device_type
        self.port = port
        self.state = 0
        self.brightness = 50
        self.server = None
    
    def start(self):
        """Start HTTP server."""
        handler = self._create_handler()
        self.server = HTTPServer(('', self.port), handler)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """Stop HTTP server."""
        if self.server:
            self.server.shutdown()
    
    def _create_handler(self):
        """Create HTTP request handler."""
        device = self
        
        class DeviceHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/setup.xml':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/xml')
                    self.end_headers()
                    self.wfile.write(device._get_setup_xml().encode())
            
            def do_POST(self):
                # Handle SOAP requests
                pass
        
        return DeviceHandler
    
    def _get_setup_xml(self):
        """Generate setup.xml response."""
        return f'''<?xml version="1.0"?>
        <root>
            <device>
                <friendlyName>{self.name}</friendlyName>
                <deviceType>urn:Belkin:device:{self.type}:1</deviceType>
            </device>
        </root>'''

# Usage in tests
@pytest.fixture
def mock_wemo_network():
    """Create simulated WeMo network."""
    devices = [
        MockWeMoDevice("Office Light", "Dimmer", 49152),
        MockWeMoDevice("Living Room", "Switch", 49153),
    ]
    for device in devices:
        device.start()
    yield devices
    for device in devices:
        device.stop()
```

**Benefits**:
- Test without hardware
- Deterministic tests
- CI friendly
- Faster development

---

## Implementation Roadmap

### Sprint 1-2 (Weeks 1-4): Foundation
**Focus**: Quality & Testing

- Week 1: CI/CD pipeline, code quality automation
- Week 2: Test coverage reporting, input validation
- Week 3: Expanded unit tests (60+ tests)
- Week 4: Error handling, retry logic

**Deliverables**:
- ✅ CI/CD workflow with quality gates
- ✅ 85%+ test coverage
- ✅ Pre-commit hooks configured
- ✅ Input validation with pydantic
- ✅ Robust error handling

**Success Metrics**:
- All PRs must pass CI checks
- Test coverage ≥ 85%
- Zero critical bugs
- Code quality score: A+

---

### Sprint 3-4 (Weeks 5-8): Features & Performance
**Focus**: User Experience

- Week 5: Persistent cache, configuration management
- Week 6: Performance optimization, benchmarking
- Week 7: Event subscriptions (if applicable)
- Week 8: Integration testing, bug fixes

**Deliverables**:
- ✅ Persistent device cache
- ✅ Configuration file support
- ✅ 30% faster scans
- ✅ Performance benchmarks

**Success Metrics**:
- Cache survives restarts
- User-configurable settings
- Scan time < 25s for /24
- No performance regressions

---

### Sprint 5-6 (Weeks 9-12): Architecture & Docs
**Focus**: Maintainability

- Week 9: Code modularization (split server.py)
- Week 10: Refactoring, cleanup
- Week 11: Documentation overhaul
- Week 12: Developer experience improvements

**Deliverables**:
- ✅ Modular code structure
- ✅ Comprehensive documentation
- ✅ Dev tooling (Docker, Makefile, debug configs)
- ✅ Architecture diagrams

**Success Metrics**:
- No file > 200 lines
- All docs updated
- Developer onboarding < 30 min
- Clear architecture

---

### Sprint 7-8 (Weeks 13-14): Security & Observability
**Focus**: Production Readiness

- Week 13: Security hardening, dependency scanning
- Week 14: Structured logging, metrics

**Deliverables**:
- ✅ Security scan in CI
- ✅ Rate limiting implemented
- ✅ Structured JSON logging
- ✅ Runtime metrics

**Success Metrics**:
- Zero high-severity vulnerabilities
- All security best practices followed
- Logs are parseable
- Metrics available

---

### Sprint 9+ (Week 15+): Advanced Features
**Focus**: Innovation

- MCP resources
- Multi-subnet support
- Device simulator
- Additional device type support

**Deliverables**:
- ✅ MCP resources implemented
- ✅ Optional advanced features

**Success Metrics**:
- Feature completeness
- User satisfaction
- Community adoption

---

## Success Criteria

### Technical Metrics
- ✅ Test coverage: 85%+
- ✅ CI/CD: 5+ automated checks
- ✅ Code quality: A+ (ruff, mypy, black)
- ✅ Performance: < 25s scans
- ✅ Security: Zero high-severity issues
- ✅ Documentation: 95% coverage

### Project Health
- ✅ Build: Passing on all commits
- ✅ Dependencies: All up-to-date
- ✅ Issues: < 10 open bugs
- ✅ PRs: < 3 day review time
- ✅ Community: Active discussions

### User Satisfaction
- ✅ Installation: < 2 minutes
- ✅ Onboarding: < 30 minutes
- ✅ Bug reports: < 5 per month
- ✅ Feature requests: Prioritized roadmap
- ✅ Support: < 24h response time

---

## Risk Management

### High Risks
1. **Breaking Changes**: Modularization may break existing integrations
   - Mitigation: Comprehensive tests, gradual rollout, deprecation warnings

2. **Performance Regression**: Optimizations may introduce bugs
   - Mitigation: Benchmarks in CI, canary deployments

3. **Resource Constraints**: Limited development time
   - Mitigation: Prioritize critical items, automate where possible

### Medium Risks
4. **Dependency Vulnerabilities**: New deps may have security issues
   - Mitigation: Automated scanning, minimal dependencies

5. **Test Maintenance**: Large test suite may become burden
   - Mitigation: Good test design, regular cleanup

### Low Risks
6. **Documentation Drift**: Docs may become outdated
   - Mitigation: Docs in CI, review process

---

## Maintenance Plan

### Weekly
- Review and triage new issues
- Merge approved PRs
- Update dependencies
- Review metrics and logs

### Monthly
- Security audit
- Performance review
- Documentation review
- Roadmap adjustment

### Quarterly
- Major version planning
- Community survey
- Architecture review
- Dependency upgrade cycle

---

## Conclusion

This improvement plan transforms the WeMo MCP Server from a production-ready project to a **best-in-class** MCP implementation with:

✅ **World-class quality**: 85%+ test coverage, automated checks  
✅ **Exceptional performance**: Optimized scanning, caching, parallelization  
✅ **Professional architecture**: Modular, maintainable, well-documented  
✅ **Production-grade security**: Hardened, audited, rate-limited  
✅ **Outstanding UX**: Configurable, fast, reliable  

**Estimated Timeline**: 14-16 weeks for complete implementation  
**Effort**: ~200 hours total development time  
**Team Size**: 1-2 developers  
**Risk Level**: Low (incremental improvements)

**Next Steps**: Review and approve this plan, then begin Sprint 1 immediately.

---

**Last Updated**: February 21, 2026  
**Version**: 1.0  
**Status**: Awaiting approval
