# Contributing to WeMo MCP Server

Thank you for your interest in contributing to WeMo MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- A GitHub account

### Finding Something to Work On

- Check [open issues](https://github.com/apiarya/wemo-mcp-server/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Review the [project roadmap](https://github.com/apiarya/wemo-mcp-server/discussions)
- Suggest new features in [discussions](https://github.com/apiarya/wemo-mcp-server/discussions)

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/wemo-mcp-server.git
cd wemo-mcp-server

# Add upstream remote
git remote add upstream https://github.com/apiarya/wemo-mcp-server.git
```

### 2. Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run the server
python -m wemo_mcp_server
```

## Making Changes

### 1. Create a Branch

```bash
# Create a feature branch from main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 2. Make Your Changes

Follow these guidelines:

- **One logical change per commit**: Keep commits focused
- **Write good commit messages**: Clear, descriptive, imperative mood
- **Follow code style**: See [Code Style](#code-style) section
- **Add tests**: All new features must include tests
- **Update documentation**: Keep docs synced with code changes

### 3. Before Committing

**🔒 Security Check** (REQUIRED):
```bash
# Scan for sensitive data
git diff --cached | grep -iE '(api[_-]?key|secret|token|password|credential)'

# Review all changes
git diff --cached
```

**📝 Documentation Check** (REQUIRED):
Review if any of these files need updates:
- [ ] README.md - Features, installation, examples
- [ ] CHANGELOG.md - Document your changes
- [ ] Copilot instructions - If structure/tools change
- [ ] Version files - If releasing (pyproject.toml, __init__.py, server.json)
- [ ] Tool docstrings - If changing MCP tools

### 4. Commit Your Changes

```bash
# Stage your changes
git add -A

# Commit with a descriptive message
git commit -m "Add feature: brief description

- Detailed point 1
- Detailed point 2
- Closes #issue_number"
```

**Commit Message Format:**
```
<type>: <short summary>

<optional detailed description>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=wemo_mcp_server --cov-report=html

# Run specific test file
pytest tests/test_server.py -v

# Run E2E tests (requires real WeMo devices)
python tests/test_e2e.py
```

### Writing Tests

- **Unit tests**: Mock external dependencies
- **Async tests**: Use `pytest-asyncio` for async functions
- **Coverage**: Aim for >80% code coverage
- **Test naming**: Use descriptive names (`test_scan_network_returns_dict`)

Example:
```python
import pytest
from wemo_mcp_server.server import scan_network

@pytest.mark.asyncio
async def test_scan_network_with_invalid_subnet():
    """Test scan_network handles invalid subnet gracefully."""
    result = await scan_network("invalid")
    assert "error" in result
```

## Submitting Changes

### 1. Push to Your Fork

```bash
# Push your branch to your fork
git push origin feature/your-feature-name
```

### 2. Create a Pull Request

1. Go to https://github.com/apiarya/wemo-mcp-server
2. Click "Pull Requests" → "New Pull Request"
3. Click "compare across forks"
4. Select your fork and branch
5. Fill out the PR template:
   - **Title**: Clear, descriptive title
   - **Description**: What, why, and how
   - **Related Issues**: Link any related issues
   - **Checklist**: Complete the checklist
   - **Screenshots**: If UI changes (N/A for this project)

### 3. Code Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Keep your PR up to date with main:
  ```bash
  git fetch upstream
  git rebase upstream/main
  git push --force-with-lease origin feature/your-feature-name
  ```
- Be patient and professional
- PRs are typically reviewed within 48-72 hours

### 4. After Approval

- Maintainer will merge your PR
- Your contribution will be credited in the release notes
- Delete your feature branch after merge

## Code Style

### Python Style

We follow PEP 8 with some project-specific conventions:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/
```

### Key Conventions

1. **Type Hints**: Use throughout
   ```python
   def control_device(device_identifier: str, action: str) -> Dict[str, Any]:
   ```

2. **Async/Await**: All MCP tools must be async
   ```python
   @mcp.tool()
   async def scan_network(subnet: str) -> Dict[str, Any]:
   ```

3. **Logging**: Only log to stderr (never stdout)
   ```python
   logger.info("Scanning network...")  # Goes to stderr
   ```

4. **Error Handling**: Return dicts with "error" key
   ```python
   return {
       "error": "Device not found",
       "suggestion": "Run scan_network first",
       "available_devices": list(device_cache.keys())
   }
   ```

5. **Docstrings**: Google-style docstrings
   ```python
   def my_function(param: str) -> int:
       """Brief description.

       Longer description if needed.

       Args:
           param: Description of param

       Returns:
           Description of return value
       """
   ```

## Documentation

### What Needs Documentation

- New MCP tools → Update README.md and copilot-instructions.md
- API changes → Update tool docstrings
- Configuration changes → Update README.md
- Breaking changes → Update CHANGELOG.md prominently
- Bug fixes → Update CHANGELOG.md

### Documentation Standards

- Keep it clear and concise
- Include examples
- Update table of contents if needed
- Test all code examples
- Use proper Markdown formatting

## Version Management

**🚨 CRITICAL**: When bumping versions, update ALL three files:

1. `pyproject.toml` - Line 7: `version = "X.Y.Z"`
2. `src/wemo_mcp_server/__init__.py` - Line 3: `__version__ = "X.Y.Z"`
3. `server.json` - Line 10: `"version": "X.Y.Z"`

The GitHub Actions workflow verifies these match before publishing.

## Release Process

Releases are handled by maintainers. See `.github/PUBLISHING_AUTOMATION.md` for details.

### For Maintainers

1. Update version in 3 files (see above)
2. Update CHANGELOG.md
3. Commit: `git commit -m "Release vX.Y.Z"`
4. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
5. Create GitHub release → Automated publish to PyPI + MCP Registry

## Getting Help

- **Questions**: Open a [discussion](https://github.com/apiarya/wemo-mcp-server/discussions)
- **Bugs**: Open an [issue](https://github.com/apiarya/wemo-mcp-server/issues)
- **Chat**: Join discussions on existing issues/PRs

## Recognition

Contributors are recognized in:
- Release notes
- CHANGELOG.md
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to WeMo MCP Server! 🎉
