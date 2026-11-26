# OmniContext

A local background daemon that watches **Claude Code** and **Antigravity** simultaneously, indexes everything they do into a single searchable database, and exposes it all as MCP tools — so both AIs always know what the other has been working on.

## Why use it

When you work across Claude Code and Antigravity, each AI only knows what happened inside its own sessions. You end up re-explaining context, copy-pasting findings, or switching tabs constantly.

OmniContext fixes that by running silently in the background and building a shared memory across both tools:

- **No more "what did Claude do earlier?"** — Antigravity can search the full history
- **No more re-explaining the codebase** — both AIs see recently touched files instantly
- **No more context loss on restart** — the database persists across sessions
- **UI design consistency** — both AIs share indexed component patterns and Tailwind tokens

## How it works

OmniContext watches two directories:

```
~/.claude/projects/          ← Claude Code session transcripts
~/.gemini/antigravity/brain/ ← Antigravity session transcripts
```

It parses session logs incrementally (tracking byte offsets so it never re-reads old data), extracts prompts, tool calls, errors, file edits, and solutions, and indexes them into a local SQLite database with FTS5 full-text search.

A lightweight MCP server sits on top, exposing four tools that Claude Code and Antigravity can call directly.

## Features

| Feature | What it does |
|---|---|
| **Passive sync** | Background watcher auto-indexes new activity as you work |
| **Full-text search** | Search across prompts, tool calls, errors, commands, and solutions from both AIs |
| **Recent activity** | See what either AI was doing, filtered by agent or project |
| **File tracking** | See which files were recently touched or created across both agents |
| **UI pattern harvesting** | Indexes Claude's frontend code — Tailwind tokens, gradients, components — so Antigravity can reuse the same design style |
| **Persistent memory** | SQLite database survives restarts; nothing is lost between sessions |
| **MCP server** | Four ready-to-use tools for Claude Code, Claude Desktop, and Antigravity |
| **Windows daemon** | Silent VBScript launcher — starts on boot with zero visible windows |

## MCP Tools

### `get_recent_activity`
See what Claude and Antigravity have been working on recently.
```json
{ "agent": "claude", "limit": 10 }
```
- `agent`: `"claude"`, `"antigravity"`, or omit for both
- Returns: session list with project name, last active time, and summary

### `search_work_context`
Full-text search across all past prompts, errors, fixes, and tool calls.
```json
{ "query": "stripe webhook fix", "limit": 5 }
```
- Searches across both AIs simultaneously
- Returns: ranked results with agent, project, timestamp, and content excerpt

### `get_claude_ui_patterns`
Pull Claude's captured UI components and Tailwind styling so Antigravity can match the same design language.
```json
{ "project": "my-app", "search": "card gradient", "limit": 3 }
```
- Returns: component name, tech stack, style summary, and code snippet

### `get_recent_files`
See which files were most recently touched or created across all projects and agents.
```json
{ "limit": 10 }
```
- Returns: file path, action (edit/create/delete), agent, and timestamp

## Installation

### Requirements
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or pip
- Claude Code CLI
- Antigravity

### Install

```bash
git clone https://github.com/SheikhMustehsan/omni-context
cd omni-context
uv sync
```

Or with pip:
```bash
pip install -e .
```

### First run — index existing sessions

```bash
omni sync
```

This scans all existing Claude and Antigravity sessions and indexes them into the local database. Verify it worked:

```bash
omni status
```

## Setup MCP in Claude Code

```bash
claude mcp add omni-context omni-mcp
```

Or manually add to `~/.claude.json`:
```json
{
  "mcpServers": {
    "omni-context": {
      "command": "omni-mcp"
    }
  }
}
```

## Setup MCP in Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "omni-context": {
      "command": "omni-mcp"
    }
  }
}
```

## Setup MCP in Antigravity

Add to `~/.gemini/antigravity/mcp_config.json`:
```json
{
  "mcpServers": {
    "omni-context": {
      "command": "omni-mcp"
    }
  }
}
```

Or use the bundled setup script:
```bash
python scripts/setup_mcp.py
```

## CLI Commands

| Command | What it does |
|---|---|
| `omni sync` | Manually scan and index all sessions from both agents |
| `omni status` | Show recent sessions across Claude and Antigravity |
| `omni search "query"` | Full-text search across all indexed activity |
| `omni ui` | Browse captured UI components and design patterns |
| `omni watch` | Run the background watcher in the foreground (for debugging) |

### Examples

```bash
# See what both AIs have been doing
omni status

# Find how a bug was fixed last week
omni search "auth middleware error"

# Browse UI components for a project
omni ui --project my-app --limit 10

# Search for a specific component style
omni ui --search "gradient button"
```

## Windows — silent auto-start on boot

To run OmniContext silently in the background on every startup:

**Option 1 — VBScript launcher (no terminal flash)**

Add a shortcut to `scripts/start_daemon.vbs` in your Windows Startup folder:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
```

The VBScript launches the watcher with `WindowStyle = 0` — completely invisible.

**To stop the daemon:**
```powershell
.\scripts\stop_daemon.ps1
```

**Option 2 — run manually in a terminal**
```bash
omni watch
```

## Works with AI Bridge

OmniContext pairs with [AI Bridge](https://github.com/SheikhMustehsan/ai-bridge):

- **OmniContext** tracks *what files and tool calls* both AIs made — shared persistent memory
- **AI Bridge** lets both AIs *talk to each other directly* — ask Claude from Antigravity, ask Antigravity from Claude

Together they give both AIs full situational awareness: shared history (Omni) + live conversation (Bridge).

## License

MIT
