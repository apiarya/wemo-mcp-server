# MCP Registry Submission Instructions

## Status: ✅ Published

The WeMo MCP Server has been successfully published to the official MCP Registry from the dedicated repository at `apiarya/wemo-mcp-server`.

## Registry Namespace

**Current Registration:** `io.github.apiarya/wemo` (v1.1.1) - **Active** ✅

**Legacy Registration:** `io.github.qrussell/wemo` (v1.0.1) - Remains for backwards compatibility

## Publication History

- **v1.1.1** - Published February 22, 2026 with new namespace `io.github.apiarya/wemo`
- **v1.1.0** - Initial release from new repository
- **v1.0.1** - Legacy release from `qrussell/wemo-ops-center/mcp` (deprecated)

## For Future Updates

### 1. Install mcp-publisher CLI

```bash
# Option 1: Homebrew (recommended)
brew install mcp-publisher

# Option 2: Direct download
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
mkdir -p ~/.local/bin
mv mcp-publisher ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
```

### 2. Verify installation

```bash
mcp-publisher --version
# Should show version info
```

### 3. Authenticate with GitHub

```bash
mcp-publisher login github
```

This will:
1. Display a URL: https://github.com/login/device
2. Show a code (e.g., ABCD-1234)
3. You visit the URL, enter the code, and authorize
4. Returns to terminal with "Successfully logged in"

### 4. Navigate to the repo

```bash
cd /path/to/wemo-mcp-server
git pull origin main
```

### 5. Publish to MCP Registry

```bash
mcp-publisher publish
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.apiarya/wemo version 1.1.1
```

### 6. Verify publication

```bash
# Search for the server
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=wemo"

# Or visit the registry
open https://registry.modelcontextprotocol.io/
```

## What's already configured

✅ **server.json** - Registry metadata file ready in `server.json`
✅ **PyPI package** - Published at https://pypi.org/project/wemo-mcp-server/
✅ **GitHub releases** - Tags and releases in dedicated repository
✅ **Documentation** - README and release docs updated for new repository

## Troubleshooting

### "You do not have permission to publish this server"
- Make sure you're logged in as the correct GitHub user
- Run `mcp-publisher logout` then `mcp-publisher login github` again

### "Validation failed"
- Check that PyPI package v1.0.0 exists: https://pypi.org/project/wemo-mcp-server/
- Verify server.json matches the schema

### "Registry validation failed"
- The package on PyPI must match the version in server.json (1.0.0)
- The repository URL must be accessible

## After publishing

Once published, the server will be:
- 🔍 Searchable at https://registry.modelcontextprotocol.io/
- 📦 Installable via Claude Desktop, VS Code, Cursor
- 🌐 Discoverable by the MCP community

## Questions?

- MCP Registry docs: https://github.com/modelcontextprotocol/registry
- Registry API: https://registry.modelcontextprotocol.io/docs
- Discord: https://modelcontextprotocol.io/community/communication
