# Publishing Guide

Complete guide for publishing new versions of WeMo MCP Server to PyPI and MCP Registry.

## Overview

**✅ Publishing is fully automated via GitHub Actions!**

When you create a GitHub release, the workflow automatically:
- ✅ Publishes to PyPI using trusted publishing (OIDC)
- ✅ Publishes to MCP Registry using GitHub OIDC
- ✅ Verifies version consistency
- ✅ Creates detailed release summary

**Time**: ~2-3 minutes from release creation to live on both registries.

## Quick Release Process

For maintainers with push access:

```bash
# 1. Update versions (ALL THREE FILES - must match!)
vim pyproject.toml               # Line 7: version = "X.Y.Z"
vim src/wemo_mcp_server/__init__.py  # Line 3: __version__ = "X.Y.Z"
vim server.json                  # Line 10: "version": "X.Y.Z"

# 2. Update CHANGELOG.md
vim CHANGELOG.md

# 3. Commit and push
git add pyproject.toml src/wemo_mcp_server/__init__.py server.json CHANGELOG.md
git commit -m "Release vX.Y.Z"
git push origin main

# 4. Create and push tag
git tag vX.Y.Z
git push origin vX.Y.Z

# 5. Create GitHub release
# Go to: https://github.com/apiarya/wemo-mcp-server/releases/new
# - Select tag: vX.Y.Z
# - Release title: vX.Y.Z
# - Description: Copy from CHANGELOG.md
# - Click "Publish release"

# ✨ Done! Workflow publishes to PyPI and MCP Registry automatically
```

## Version Management

**🚨 CRITICAL**: All three version files must match exactly:

| File | Location | Format |
|------|----------|--------|
| `pyproject.toml` | Line 7 | `version = "X.Y.Z"` |
| `__init__.py` | Line 3 | `__version__ = "X.Y.Z"` |
| `server.json` | Line 10 | `"version": "X.Y.Z"` |

The GitHub Actions workflow verifies these match before publishing. Mismatches will fail the build.

### Semantic Versioning

Follow [SemVer 2.0.0](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (1.X.0): New features (backwards compatible)
- **PATCH** (1.1.X): Bug fixes (backwards compatible)

Examples:
- `1.1.1` → `1.1.2`: Bug fix
- `1.1.2` → `1.2.0`: New MCP tool added
- `1.2.0` → `2.0.0`: Breaking API change

## Automated Publishing Workflow

### How It Works

File: `.github/workflows/pypi-publish.yml`

**Trigger**: GitHub release with tag `v*.*.*` (e.g., `v1.2.0`)

**Process**:
1. ✅ Checkout code
2. ✅ Verify version matches across files
3. ✅ Build Python package
4. ✅ Publish to PyPI (trusted publishing/OIDC)
5. ✅ Wait 30s for PyPI indexing
6. ✅ Install mcp-publisher CLI
7. ✅ Authenticate with MCP Registry (GitHub OIDC)
8. ✅ Publish to MCP Registry
9. ✅ Create release summary

**Duration**: ~2-3 minutes total

### Security Features

**No secrets or API tokens needed!** Everything uses OIDC:

| Service | Authentication | Token Lifetime |
|---------|----------------|----------------|
| PyPI | Trusted Publishing (OIDC) | Minutes |
| MCP Registry | GitHub OIDC | Minutes |
| GitHub Actions | Built-in GITHUB_TOKEN | Job duration |

**Benefits**:
- 🔒 No long-lived credentials
- ⚡ Automatic token generation
- 🎯 Scoped to specific repo and workflow
- 📊 Full audit trail

### Monitoring

Watch the workflow:
- URL: https://github.com/apiarya/wemo-mcp-server/actions
- Status: Green checkmark = success
- Duration: Typically 2-3 minutes
- Summary: Shows PyPI and MCP Registry links

## Manual Publishing (Fallback)

If automation fails, you can publish manually:

### PyPI

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Verify package
twine check dist/*

# Upload (requires API token)
twine upload dist/*
```

### MCP Registry

```bash
# Install CLI
brew install mcp-publisher
# or
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz
sudo mv mcp-publisher /usr/local/bin/

# Authenticate
mcp-publisher login github

# Publish
mcp-publisher publish server.json

# Verify
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=wemo"
```

## Verification

After release, verify both registries:

### PyPI
```bash
# Check version
pip index versions wemo-mcp-server

# Test installation
pip install wemo-mcp-server==X.Y.Z

# Or with uvx
uvx wemo-mcp-server@X.Y.Z
```

### MCP Registry
- URL: https://registry.modelcontextprotocol.io/?q=apiarya/wemo
- Name: `io.github.apiarya/wemo`
- Check version matches release

### Functional Test
```bash
# Test the server runs
uvx wemo-mcp-server@X.Y.Z

# Expected output: Server starts and awaits MCP protocol messages
```

## Troubleshooting

### Workflow Doesn't Trigger

**Symptoms**: No workflow run after creating release

**Causes**:
- Tag doesn't match `v*.*.*` format
- Release is "draft" (must be "published")
- Workflow file has syntax errors

**Solutions**:
```bash
# Check tag format
git tag -l | grep vX.Y.Z

# Re-push tag
git push origin vX.Y.Z

# Manually trigger workflow
# Go to: https://github.com/apiarya/wemo-mcp-server/actions
# Select "Publish to PyPI and MCP Registry" → "Run workflow"
```

### Version Mismatch Error

**Symptoms**: Workflow fails with "Version mismatch!" error

**Cause**: Version numbers don't match across files

**Solution**:
```bash
# Check versions
grep '^version = ' pyproject.toml
grep '__version__ = ' src/wemo_mcp_server/__init__.py
grep '"version"' server.json

# Fix mismatches, then:
git add pyproject.toml src/wemo_mcp_server/__init__.py server.json
git commit --amend
git push --force origin main
git tag -d vX.Y.Z
git push --delete origin vX.Y.Z
git tag vX.Y.Z
git push origin vX.Y.Z
# Delete and recreate GitHub release
```

### PyPI Publishing Fails

**Symptoms**: Workflow fails at PyPI publish step

**Common Causes**:
- Version already exists on PyPI (can't overwrite)
- Trusted publisher misconfigured
- Package build errors

**Solutions**:
1. **Version exists**: Bump to next version
2. **Trusted publisher**: Verify at https://pypi.org/manage/account/publishing/
3. **Build errors**: Check logs, fix code, re-release

### MCP Registry Publishing Fails

**Symptoms**: PyPI succeeds but MCP Registry fails

**Common Causes**:
- PyPI not indexed yet (30s wait timeout)
- server.json version mismatch
- Package not found on PyPI

**Solutions**:
```bash
# Wait for PyPI indexing (can take 1-2 minutes)
# Then manually publish to registry:
mcp-publisher login github
mcp-publisher publish server.json
```

### Package Not Installable

**Symptoms**: `pip install wemo-mcp-server==X.Y.Z` fails

**Causes**:
- PyPI indexing delay
- Package dependencies issues
- Python version incompatibility

**Solutions**:
- Wait 2-5 minutes for PyPI CDN
- Check package page: https://pypi.org/project/wemo-mcp-server/
- Test with explicit source: `pip install --index-url https://pypi.org/simple wemo-mcp-server==X.Y.Z`

## Release Checklist

Use this checklist for each release:

### Pre-Release
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Code formatted: `black src/ tests/ && isort src/ tests/`
- [ ] Type checks pass: `mypy src/`
- [ ] Lint checks pass: `ruff check src/ tests/`
- [ ] CHANGELOG.md updated with changes
- [ ] Version bumped in ALL 3 files (and they match!)
- [ ] Commit message: `Release vX.Y.Z`
- [ ] Changes pushed to main

### Release
- [ ] Tag created: `git tag vX.Y.Z`
- [ ] Tag pushed: `git push origin vX.Y.Z`
- [ ] GitHub release created
- [ ] Release title: `vX.Y.Z`
- [ ] Release description from CHANGELOG.md
- [ ] Release marked as "latest" (if stable)

### Post-Release
- [ ] Workflow completed successfully
- [ ] PyPI shows new version
- [ ] MCP Registry shows new version
- [ ] Installation tested: `pip install wemo-mcp-server==X.Y.Z`
- [ ] Server runs: `uvx wemo-mcp-server@X.Y.Z`
- [ ] Announcement posted (if major/minor release)

## Configuration

### PyPI Trusted Publisher

**Status**: ✅ Configured

**Settings** (at https://pypi.org/manage/account/publishing/):
- Project: `wemo-mcp-server`
- Owner: `apiarya`
- Repository: `wemo-mcp-server`
- Workflow: `pypi-publish.yml`
- Environment: (Any)

**No changes needed** - already configured and working.

### MCP Registry

**Namespace**: `io.github.apiarya/wemo`
**Authentication**: GitHub OIDC (automatic via workflow)
**No manual configuration needed**

## Version History

| Version | Date | Type | Notes |
|---------|------|------|-------|
| 1.1.1 | 2026-02-21 | Patch | MCP Registry namespace update |
| 1.1.0 | 2026-02-21 | Minor | Repository migration + automation |
| 1.0.1 | 2026-02-16 | Patch | Registry validation fix |
| 1.0.0 | 2026-02-16 | Major | Initial stable release |

See [CHANGELOG.md](../CHANGELOG.md) for complete history.

## Support

**Questions**: [Open a discussion](https://github.com/apiarya/wemo-mcp-server/discussions)
**Issues**: [Report a bug](https://github.com/apiarya/wemo-mcp-server/issues)
**Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated**: February 21, 2026
