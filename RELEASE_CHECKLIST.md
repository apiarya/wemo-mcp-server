# Quick Release Checklist

## One-Time Setup (Do once)

- [ ] Create PyPI account at https://pypi.org/account/register/
- [ ] Enable 2FA on PyPI
- [ ] Configure trusted publishing at https://pypi.org/manage/account/publishing/
  - Project: `wemo-mcp-server`
  - Repo: `apiarya/wemo-mcp-server`
  - Workflow: `pypi-publish.yml`

## For Each Release

### Preparation
- [ ] Update version in `pyproject.toml` (line 7)
- [ ] Update version in `src/wemo_mcp_server/__init__.py` (line 3)
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run tests: `pytest tests/ -v`
- [ ] Test build: `python -m build && twine check dist/*`

### Release
- [ ] Commit: `git commit -m "Release vX.X.X"`
- [ ] Push: `git push origin main`
- [ ] Tag: `git tag vX.X.X` (no longer mcp-v prefix)
- [ ] Push tag: `git push origin vX.X.X`
- [ ] Create GitHub release at https://github.com/apiarya/wemo-mcp-server/releases/new
- [ ] Wait for workflow to complete

### Verification
- [ ] Monitor workflow: https://github.com/apiarya/wemo-mcp-server/actions
- [ ] Wait for workflow completion (~2-3 minutes)
- [ ] Verify on PyPI: https://pypi.org/project/wemo-mcp-server/
- [ ] Verify on MCP Registry: https://registry.modelcontextprotocol.io/?q=apiarya/wemo
- [ ] Test install: `pip install wemo-mcp-server==X.X.X`
- [ ] Test with uvx: `uvx wemo-mcp-server`
- [ ] Test with MCP client (Claude Desktop, VS Code, etc.)

## After First Stable Release (v1.0.0)

- [ ] ✅ **Publishing is automated** - Both PyPI and MCP Registry publish automatically!
- [ ] Share on social media / community forums
- [ ] Monitor issues and user feedback
- [ ] Update documentation if needed

**Note:** MCP Registry publishing is now fully automated via GitHub Actions using OIDC authentication.

## Quick Commands

```bash
# Check current version
grep '^version = ' mcp/pyproject.toml

# Update both version files (replace 1.0.0 with your version)
sed -i '' 's/version = ".*"/version = "1.0.0"/' mcp/pyproject.toml
sed -i '' 's/__version__ = ".*"/__version__ = "1.0.0"/' mcp/src/wemo_mcp_server/__init__.py

# Test build
cd mcp && python -m build && twine check dist/*

# Create and push tag
git tag mcp-v1.0.0 && git push origin mcp-v1.0.0

# Clean up old builds
rm -rf mcp/dist mcp/build mcp/src/*.egg-info
```
