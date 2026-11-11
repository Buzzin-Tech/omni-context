# OmniContext 🌐

A lightweight, local system observer and memory daemon that tracks everything you work on across **Antigravity** and **Claude Code / Desktop**, indexing your activity, code changes, and UI styling into a unified local database.

---

## Key Features

1. **Passive Continuous Sync**
   - Monitors `~/.claude/projects/` and `~/.gemini/antigravity/brain/` in real time.
   - Zero-overhead incremental parsing (tracks byte offsets, negligible CPU/RAM).
2. **Claude UI Aesthetic Harvester**
   - Automatically detects and indexes Claude's high-aesthetic frontend code, Tailwind tokens, gradients, component layouts, and CSS cards.
   - Antigravity can query Claude's design patterns via MCP or CLI to match Claude's UI quality.
3. **Full-Text Search (FTS5)**
   - Instant search across all prompts, tool calls, errors, commands, and solutions from both tools.
4. **Universal MCP Server**
   - Exposes tools like `get_recent_activity`, `search_work_context`, and `get_claude_ui_patterns` directly to both AI models.

---

## CLI Usage

OmniContext comes with a built-in terminal CLI:

```powershell
# Show active and recent sessions across Claude and Antigravity
omni status

# Search across past conversations, bash commands, errors, and fixes
omni search "stripe webhook"

# View captured Claude UI designs and Tailwind styling patterns
omni ui --limit 5

# Start background file watcher manually in foreground
omni watch

# Force re-sync of all existing sessions
omni sync
```

---

## Background Daemon Controls

The daemon runs silently in the background on Windows:
- **Start Daemon (Silent):** Double-click `scripts/start_daemon.vbs` or run via PowerShell.
- **Stop Daemon:** Run `powershell -ExecutionPolicy Bypass -File scripts/stop_daemon.ps1`.

---

## MCP Setup

- **Claude Code**: Configured automatically in `~/.claude.json`.
- **Claude Desktop**: Configured in `%APPDATA%\Claude\claude_desktop_config.json`.
- **Antigravity**: Registered via skill `omni-context` in `~/.gemini/config/skills/omni-context`.
