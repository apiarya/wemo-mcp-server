# PyPI Trusted Publishing Configuration

## Status: ✅ Configured

The PyPI package `wemo-mcp-server` is configured for Trusted Publishing with the new repository.

## Current Configuration

**PyPI Project:** wemo-mcp-server  
**Package Owner:** @apiarya  
**Publishing Method:** Trusted Publishing (OIDC)

### Trusted Publisher #1 (Legacy - Can be removed)
- **Repository:** qrussell/wemo-ops-center
- **Workflow:** pypi-publish.yml
- **Environment:** (Any)
- **Status:** ⚠️ Can be removed after migration complete

### Trusted Publisher #2 (Active) ✅
- **Repository:** apiarya/wemo-mcp-server
- **Workflow:** pypi-publish.yml
- **Environment:** (Any)
- **Status:** ✅ Active and ready

## How It Works

1. Create a GitHub release with tag format: `v*.*.*` (e.g., `v1.1.0`)
2. GitHub Actions workflow runs automatically
3. Workflow authenticates to PyPI using OIDC (no secrets needed)
4. Package is built and published to PyPI
5. Release summary is created in GitHub Actions

## Workflow Trigger

The workflow runs when:
- A new release is **published** on GitHub
- Tag matches pattern: `v*` (e.g., `v1.1.0`, `v1.0.2`)
- Manual trigger via `workflow_dispatch` (for testing)

## Verification Steps

Before first release, verify:

### 1. Check PyPI Configuration
- [ ] Visit: https://pypi.org/manage/project/wemo-mcp-server/settings/publishing/
- [ ] Confirm `apiarya/wemo-mcp-server` is listed
- [ ] Confirm workflow name is `pypi-publish.yml`

### 2. Test Workflow Syntax
```bash
cd /Users/swapsapar/workspace/wemo-mcp-server

# Validate workflow file
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pypi-publish.yml'))"

# Check for syntax errors
gh workflow view pypi-publish.yml  # If gh CLI is installed
```

### 3. Dry Run (Optional)
For extra safety, do a test release:
```bash
# Update version to something like 1.0.2-test
# Create and push tag
git tag v1.0.2-test
git push origin v1.0.2-test

# Create a draft release
# Monitor workflow at: https://github.com/apiarya/wemo-mcp-server/actions
```

## First Real Release Checklist

When ready for first release from new repo (v1.1.0):

### Pre-Release
- [ ] Update version in `pyproject.toml` to `1.1.0`
- [ ] Update version in `src/wemo_mcp_server/__init__.py` to `1.1.0`
- [ ] Update version in `server.json` to `1.1.0`
- [ ] Update `CHANGELOG.md` with migration notes
- [ ] Commit all changes
- [ ] Push to main branch

### Release
- [ ] Create tag: `git tag v1.1.0`
- [ ] Push tag: `git push origin v1.1.0`
- [ ] Create GitHub release at: https://github.com/apiarya/wemo-mcp-server/releases/new
  - Title: `v1.1.0 - New Repository Home`
  - Description: See migration.md Phase 7 for template
  - Mark as "latest release"
- [ ] Monitor workflow: https://github.com/apiarya/wemo-mcp-server/actions
- [ ] Verify on PyPI: https://pypi.org/project/wemo-mcp-server/

### Post-Release
- [ ] Test installation: `pip install --upgrade wemo-mcp-server`
- [ ] Verify version: `pip show wemo-mcp-server`
- [ ] Test with MCP client
- [ ] Publish to MCP Registry (Phase 4)

## Troubleshooting

### "Workflow didn't trigger"
- Check tag format: Must be `v*.*.*` (not `mcp-v*.*.*`)
- Check release status: Must be "published" (not "draft")
- Check Actions tab: https://github.com/apiarya/wemo-mcp-server/actions

### "PyPI authentication failed"
- Verify Trusted Publisher is configured on PyPI
- Check repository name matches exactly: `apiarya/wemo-mcp-server`
- Check workflow name matches: `pypi-publish.yml`

### "Version already exists on PyPI"
- PyPI doesn't allow re-uploading same version
- Bump version and try again
- Use test PyPI for testing: https://test.pypi.org

### "Package build failed"
- Check `pyproject.toml` syntax
- Verify all files are committed
- Test locally: `python -m build && twine check dist/*`

## Cleanup After Migration

After successful v1.1.0 release from new repo:
- [ ] Remove old trusted publisher: qrussell/wemo-ops-center
- [ ] Notify qrussell that PyPI publishing has moved
- [ ] Archive old workflow in wemo-ops-center repo

## Security Notes

**Trusted Publishing Benefits:**
- ✅ No long-lived API tokens to manage
- ✅ Short-lived OIDC tokens (expires in minutes)
- ✅ Automatic rotation
- ✅ Linked to specific repository and workflow
- ✅ Reduces risk of token leakage

**Best Practices:**
- Keep workflow file in version control
- Review workflow changes in PRs
- Monitor workflow runs for suspicious activity
- Never commit API tokens (Trusted Publishing doesn't use them)

---

**Configuration Date:** February 21, 2026  
**Configured By:** @apiarya  
**Status:** ✅ Ready for first release
