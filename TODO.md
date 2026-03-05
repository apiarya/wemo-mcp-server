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

### 6. 🖥️ MCP Apps (Interactive Device Dashboard UI)
**Effort:** Medium
**Spec:** [SEP-1865](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1865) · [ext-apps SDK](https://github.com/modelcontextprotocol/ext-apps) · [Python walkthrough](https://mcpui.dev/guide/server/python/walkthrough)
**Supported hosts:** Claude Desktop, VS Code, ChatGPT, Goose — already our target clients!
**Why:** After `scan_network`, Claude can render an **interactive WeMo device dashboard** inline in the chat — toggle switches, brightness sliders, status indicators — no separate web app needed. The UI communicates back to the server via JSON-RPC over `postMessage`.
**How:**
1. Add `mcp-ui-server` dependency (`pip install mcp-ui-server`)
2. Create `show_device_dashboard` tool returning `list[UIResource]` with inline HTML
3. Add `show_device_status_ui` tool for a single device card with controls
4. HTML uses vanilla JS + `postMessage` to call `control_device` back through the host
5. Provide text-only fallback (existing `list_devices` / `get_device_status` unchanged)
**Files to change:**
- `src/wemo_mcp_server/server.py` — 2 new tools + HTML templates
- `pyproject.toml` — add `mcp-ui-server>=0.1.0` dependency

---

## Status

| Idea | Status |
|------|--------|
| Progress Notifications | ⬜ Not started |
| MCP Sampling | ⬜ Not started |
| Remote Transport + OAuth 2.1 | ⬜ Not started |
| Smithery Deployment | ⬜ Not started |
| Claude Skills | ⬜ Not started |
| MCP Apps (Device Dashboard UI) | ⬜ Not started |
