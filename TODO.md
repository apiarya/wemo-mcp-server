# TODO / Future Ideas

Tracked ideas for extending the wemo-mcp-server beyond its current capabilities.
See `.github/copilot-instructions.md` for project context and architecture.

---

## 🔥 Priority Order (recommended)

### 1. 📊 MCP Progress Notifications (Quick Win)
**Effort:** Low
**Why:** `scan_network` takes 23-30s with no feedback — bad UX. Stream real-time progress to the client.
**How:** Use `ctx.report_progress()` in FastMCP inside the scan loop.
**Files to change:** `src/wemo_mcp_server/server.py` → `scan_network` tool and `WeMoScanner` methods.

### 2. 🔄 MCP Sampling (New Primitive)
**Effort:** Low-Medium
**Why:** Closes the loop — server calls back to the LLM through the client. Enables autonomous device monitoring (e.g. "scan and ask the LLM which devices look unusual").
**How:** Use `ctx.sample()` in FastMCP. Requires MCP client support (Claude Desktop v1.1+).
**Files to change:** `src/wemo_mcp_server/server.py` — add a new `analyze_devices` tool that uses sampling.

### 3. 🌐 Remote Transport + OAuth 2.1 (Stretch Goal)
**Effort:** Medium
**Why:** Unlocks:
- "Remote" listing tier on Glama/MCP Registry
- Azure MCP Center eligibility (requires streamable HTTP + OAuth 2.1)
- Glama Connectors listing (`glama.ai/mcp/connectors`)
- Smithery hosted deployment

**How:** FastMCP supports `mcp.run(transport="streamable-http")` natively. Add OAuth 2.1 layer on top.
**Files to change:** `src/wemo_mcp_server/__main__.py`, `src/wemo_mcp_server/server.py`, new `auth.py`.

### 4. 🚀 Smithery Deployment (Easy Distribution)
**Effort:** Very Low
**Why:** Already have `smithery.yaml` — just needs tuning. Smithery hosts servers as remote endpoints, making it one-click installable for users.
**Files to change:** `smithery.yaml`, possibly `Dockerfile`.

### 5. 🎯 Claude Skills
**Effort:** Low
**Why:** Package as a reusable Anthropic Agent Skill for broader Claude discoverability.
**How:** Register at https://www.anthropic.com/news/skills
**Files to change:** Packaging/registration only.

---

## Status

| Idea | Status |
|------|--------|
| Progress Notifications | ⬜ Not started |
| MCP Sampling | ⬜ Not started |
| Remote Transport + OAuth 2.1 | ⬜ Not started |
| Smithery Deployment | ⬜ Not started |
| Claude Skills | ⬜ Not started |
