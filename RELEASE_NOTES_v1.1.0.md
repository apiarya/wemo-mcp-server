# v1.1.0 - Repository Migration 🏠

## 🎉 New Home for WeMo MCP Server

The WeMo MCP Server now has its own dedicated repository!

**New Repository:** https://github.com/apiarya/wemo-mcp-server

This move follows MCP ecosystem best practices and significantly improves discoverability for users finding the server through the official MCP Registry.

## What Changed

### Repository & Infrastructure
- ✅ Migrated from `qrussell/wemo-ops-center/mcp` monorepo
- ✅ All documentation and URLs updated to new repository
- ✅ CI/CD pipeline configured for standalone repo
- ✅ MCP Registry metadata updated with new location
- ✅ Simplified versioning (no more `mcp-v*` tags, just `v*`)

### Documentation
- ✅ All image URLs and links updated
- ✅ Installation instructions verified
- ✅ Contributing guidelines updated
- ✅ Issue tracking moved to new repository

### No Breaking Changes
- ✅ Package name remains: `wemo-mcp-server`
- ✅ Installation command unchanged: `pip install wemo-mcp-server`
- ✅ All MCP tools function identically
- ✅ Configuration compatibility maintained

## For Users

**No action needed!** Just install or upgrade as usual:

```bash
# Via pip
pip install --upgrade wemo-mcp-server

# Via uvx (recommended)
uvx wemo-mcp-server@latest
```

## For Contributors

Please submit issues and PRs to the new repository:
- **Issues:** https://github.com/apiarya/wemo-mcp-server/issues
- **Pull Requests:** https://github.com/apiarya/wemo-mcp-server/pulls

## Why This Matters

### MCP Registry Compliance
The MCP Registry requires base repository URLs without path components. The previous URL (`/tree/main/mcp`) caused validation failures.

### Better User Experience
Users discovering the server through the [MCP Registry](https://registry.modelcontextprotocol.io/?q=wemo) now land directly on MCP documentation instead of the desktop app README.

### Industry Standard
This aligns with patterns used by major MCP servers:
- [github/github-mcp-server](https://github.com/github/github-mcp-server)
- [cloudflare/mcp-server-cloudflare](https://github.com/cloudflare/mcp-server-cloudflare)

## Related Projects

The WeMo MCP Server complements the [WeMo Ops Center](https://github.com/qrussell/wemo-ops-center) desktop and server applications for managing WeMo devices.

## Installation

```bash
# PyPI
pip install wemo-mcp-server

# uvx (recommended for MCP)
uvx wemo-mcp-server
```

## Quick Start

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "wemo": {
      "command": "uvx",
      "args": ["wemo-mcp-server"]
    }
  }
}
```

## Full Changelog

See [CHANGELOG.md](https://github.com/apiarya/wemo-mcp-server/blob/main/CHANGELOG.md) for complete version history.

---

**Thanks to @qrussell for the collaboration and support in making this migration happen!** 🙏
