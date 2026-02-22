# v1.1.1 - MCP Registry Namespace Update

## Purpose

This release updates the MCP Registry namespace from `io.github.qrussell/wemo` to `io.github.apiarya/wemo` to properly reflect the repository ownership under apiarya/wemo-mcp-server.

## Changes

### MCP Registry
- ✅ Updated mcp-name to `io.github.apiarya/wemo` in README
- ✅ Updated server.json namespace
- ✅ Version bumped to 1.1.1 for PyPI ownership validation

### Infrastructure
- ✅ Added MCP Registry token files to .gitignore

## No Functional Changes

This is strictly a metadata/registry update:
- ✅ All features from v1.1.0 maintained
- ✅ Same installation command: `pip install wemo-mcp-server`
- ✅ Same usage and configuration
- ✅ All MCP tools function identically

## For Users

No action needed! The package works the same way:

```bash
# Install/upgrade
pip install --upgrade wemo-mcp-server

# Use with uvx (recommended)
uvx wemo-mcp-server
```

## MCP Registry

After this release publishes to PyPI, the server will be registered in the MCP Registry as:
- **New namespace:** `io.github.apiarya/wemo`
- **Repository:** https://github.com/apiarya/wemo-mcp-server
- **Version:** 1.1.1

## Related

- Previous release: [v1.1.0](https://github.com/apiarya/wemo-mcp-server/releases/tag/v1.1.0) - Repository migration
- Original namespace: `io.github.qrussell/wemo` (deprecated, will remain for backwards compatibility)
