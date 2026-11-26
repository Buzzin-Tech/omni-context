"""Official FastMCP Server for OmniContext (Cross-Agent Memory)."""
from typing import Optional, List, Dict, Any
try:
    from mcp.server.fastmcp import FastMCP as MCPServer
except (ImportError, ModuleNotFoundError):
    from mcp.server import MCPServer

from omni_context.db import (
    query_recent_sessions, search_events, query_ui_patterns, query_recent_file_touches
)

# Initialize MCP Server
mcp = MCPServer("omni-context")

@mcp.tool()
def get_recent_activity(agent: Optional[str] = None, limit: int = 10) -> str:
    """Retrieve recent active sessions and work history across Claude and Antigravity.
    
    Args:
        agent: Filter by 'claude' or 'antigravity' (leave empty for both)
        limit: Number of recent sessions to return (default 10)
    """
    sessions = query_recent_sessions(limit=limit, agent=agent if agent else None)
    if not sessions:
        return "No recent sessions found in OmniContext."

    output = ["### Recent Agent Sessions:"]
    for s in sessions:
        summary_str = f" - {s['summary']}" if s.get("summary") else ""
        output.append(f"- **[{s['agent'].upper()}]** Project: `{s['project_name']}` (Active: {s['last_active_at']}){summary_str}")
    
    return "\n".join(output)

@mcp.tool()
def search_work_context(query: str, limit: int = 5) -> str:
    """Search through past prompts, thoughts, commands, error resolutions, and code changes across both agents.
    
    Args:
        query: Keywords or description (e.g. 'stripe webhook fix', 'auth middleware', 'navbar redesign')
        limit: Max results to return (default 5)
    """
    results = search_events(query, limit=limit)
    if not results:
        return f"No results found matching '{query}' in OmniContext history."

    output = [f"### Context Search Results for '{query}':"]
    for idx, r in enumerate(results, 1):
        output.append(f"\n#### {idx}. [{r['agent'].upper()}] Project: `{r.get('project_name', 'general')}` ({r['timestamp']})")
        output.append(f"**Type:** `{r['event_type']}`")
        output.append(f"**Content:**\n```\n{r['content'][:500]}\n```")

    return "\n".join(output)

@mcp.tool()
def get_claude_ui_patterns(project: Optional[str] = None, search: Optional[str] = None, limit: int = 3) -> str:
    """Retrieve Claude's high-quality UI design patterns, Tailwind styling, and component code.
    Use this whenever you need to build or restyle UI components with modern, beautiful aesthetics.
    
    Args:
        project: Filter by project name (e.g. 'buzzintech')
        search: Filter by UI keywords (e.g. 'card', 'navbar', 'modal', 'gradient', 'button')
        limit: Max component patterns to return (default 3)
    """
    patterns = query_ui_patterns(project=project, search=search, limit=limit)
    if not patterns:
        return "No UI patterns found matching criteria. Claude has not yet authored UI components matching this query."

    output = ["### Claude UI Design Patterns & Styling Standards:"]
    for idx, p in enumerate(patterns, 1):
        output.append(f"\n#### Pattern {idx}: {p['component_name']} (`{p['tech_stack']}` in `{p['project_name']}`)")
        output.append(f"**Style Breakdown:** {p['style_summary']}")
        output.append(f"**Reference Code:**\n```\n{p['code_snippet']}\n```")

    return "\n".join(output)

@mcp.tool()
def get_recent_files(limit: int = 10) -> str:
    """Get the most recently touched, edited, or created files across all projects and agents.
    
    Args:
        limit: Number of file events to retrieve (default 10)
    """
    files = query_recent_file_touches(limit=limit)
    if not files:
        return "No recently touched files logged yet."

    output = ["### Recently Modified Files Across Agents:"]
    for f in files:
        output.append(f"- **[{f['agent'].upper()}]** `{f['action']}`: `{f['file_path']}` ({f['timestamp']})")

    return "\n".join(output)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
