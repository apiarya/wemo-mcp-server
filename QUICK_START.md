# Quick Start - Immediate Action Items

**Generated**: February 21, 2026
**Priority**: Execute these items first (Week 1-2)

## Phase 1: Critical Foundation (This Week)

### Day 1-2: CI/CD Testing Pipeline 🔴 CRITICAL

**Goal**: Automated quality gates on every PR

**Tasks**:
1. Create `.github/workflows/test.yml`
2. Add pytest with coverage
3. Add mypy type checking
4. Add ruff linting
5. Add black formatting check
6. Configure Codecov integration

**Command**:
```bash
# Test locally first
pytest tests/ -v --cov --cov-report=term-missing
mypy src/
ruff check src/ tests/
black --check src/ tests/

# If all pass, commit workflow
git add .github/workflows/test.yml
git commit -m "Add CI/CD testing pipeline"
```

**Expected Outcome**: All future PRs require passing tests

---

### Day 3-4: Pre-commit Hooks 🔴 CRITICAL

**Goal**: Catch issues before commit

**Tasks**:
1. Create `.pre-commit-config.yaml`
2. Install pre-commit
3. Run on all files
4. Commit hooks configuration

**Commands**:
```bash
# Install
pip install pre-commit

# Setup hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Commit
git add .pre-commit-config.yaml
git commit -m "Add pre-commit hooks for code quality"
```

**Expected Outcome**: Automatic formatting and linting on commit

---

### Day 5: Input Validation 🔴 CRITICAL

**Goal**: Prevent invalid inputs, improve security

**Tasks**:
1. Install pydantic and pydantic-settings
2. Create `src/wemo_mcp_server/models.py`
3. Add validation models for all MCP tools
4. Update tools to use models
5. Add tests for validation

**Commands**:
```bash
# Add dependencies
echo "pydantic>=2.0.0" >> pyproject.toml
echo "pydantic-settings>=2.0.0" >> pyproject.toml
pip install -e ".[dev]"

# Create models file (see IMPROVEMENT_PLAN.md section 1.5)
# Then update tools to use validation
```

**Expected Outcome**: All inputs validated, better error messages

---

## Phase 2: Testing Excellence (Next Week)

### Week 2: Expand Test Suite 🟠 HIGH

**Goal**: 85%+ test coverage

**Checklist**:
- [ ] Create `tests/test_scanner.py` (15 tests)
- [ ] Create `tests/test_tools.py` (30 tests)
- [ ] Create `tests/test_cache.py` (10 tests)
- [ ] Create `tests/test_models.py` (5 tests)
- [ ] Run coverage report: `pytest --cov --cov-report=html`
- [ ] Review `htmlcov/index.html` for gaps
- [ ] Fill coverage gaps
- [ ] Commit all tests

**Commands**:
```bash
# Create test files
touch tests/test_scanner.py tests/test_tools.py
touch tests/test_cache.py tests/test_models.py

# Write tests (see IMPROVEMENT_PLAN.md section 2.1)

# Check coverage
pytest tests/ --cov --cov-report=html
open htmlcov/index.html  # macOS
```

**Expected Outcome**: 85%+ coverage, 60+ tests

---

## Quick Win Checklist

Execute these in order for maximum impact:

### Immediate (Today)
- [x] Read IMPROVEMENT_PLAN.md thoroughly
- [ ] Setup development environment
- [ ] Install pre-commit: `pip install pre-commit`
- [ ] Install dev dependencies: `pip install -e ".[dev]"`

### This Week
- [ ] Add CI/CD workflow (.github/workflows/test.yml)
- [ ] Configure pre-commit hooks (.pre-commit-config.yaml)
- [ ] Add input validation (models.py)
- [ ] Run and fix all linting issues
- [ ] Commit everything

### Next Week
- [ ] Write 60+ unit tests
- [ ] Achieve 85%+ coverage
- [ ] Setup Codecov badge
- [ ] Update documentation

### Week 3-4
- [ ] Add persistent cache
- [ ] Add configuration management
- [ ] Optimize performance
- [ ] Add error retry logic

---

## Commands Cheat Sheet

```bash
# Development Setup
pip install -e ".[dev]"
pre-commit install

# Run Tests
pytest tests/ -v
pytest tests/ --cov --cov-report=html

# Code Quality
black src/ tests/
isort src/ tests/
ruff check src/ tests/ --fix
mypy src/

# All Checks (run before commit)
black src/ tests/ && isort src/ tests/ && \
ruff check src/ tests/ && mypy src/ && \
pytest tests/ -v

# Build Package
python -m build

# Run Server
python -m wemo_mcp_server
```

---

## File Creation Order

**Priority 1** (Today):
1. `.github/workflows/test.yml`
2. `.pre-commit-config.yaml`

**Priority 2** (Tomorrow):
3. `src/wemo_mcp_server/models.py`
4. `src/wemo_mcp_server/config.py`

**Priority 3** (This Week):
5. `tests/test_scanner.py`
6. `tests/test_tools.py`
7. `tests/test_cache.py`
8. `tests/test_models.py`

**Priority 4** (Next Week):
9. `src/wemo_mcp_server/cache.py`
10. `src/wemo_mcp_server/retry.py`

---

## Expected Results

### After Week 1:
✅ CI/CD pipeline running on all PRs
✅ Pre-commit hooks preventing bad commits
✅ Input validation on all tools
✅ Linting/formatting automated
✅ Type checking enforced

### After Week 2:
✅ 85%+ test coverage
✅ 60+ unit tests
✅ Coverage badge on README
✅ All critical paths tested
✅ Mock infrastructure in place

### After Week 4:
✅ Persistent device cache
✅ User configuration support
✅ Performance optimizations
✅ Retry logic with backoff
✅ Comprehensive error handling

---

## Need Help?

**Documentation**:
- Full plan: [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)

**Questions**:
- Open an issue: https://github.com/apiarya/wemo-mcp-server/issues
- Discussions: https://github.com/apiarya/wemo-mcp-server/discussions

**Start Here**: Focus on Day 1-2 tasks. Get CI/CD working first—everything else builds on that foundation.
