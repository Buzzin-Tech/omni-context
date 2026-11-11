"""Rich CLI interface for OmniContext."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from typing import Optional

from omni_context.db import (
    query_recent_sessions, search_events, query_ui_patterns, init_db
)
from omni_context.watcher import sync_all_existing, start_watching

app = typer.Typer(help="OmniContext: Unified cross-agent system observer for Antigravity & Claude.")
console = Console()

@app.command()
def sync():
    """Manually sync and index all sessions from Claude and Antigravity."""
    console.print("[bold blue]Scanning and indexing sessions...[/bold blue]")
    count = sync_all_existing()
    console.print(f"[bold green]✓ Indexed {count} new events across Claude & Antigravity.[/bold green]")

@app.command()
def status(limit: int = 10, agent: Optional[str] = None):
    """Show active and recent sessions across agents."""
    sessions = query_recent_sessions(limit=limit, agent=agent)
    if not sessions:
        console.print("[yellow]No sessions found. Run 'omni sync' first.[/yellow]")
        return

    table = Table(title="Recent Agent Sessions (Claude & Antigravity)", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="bold")
    table.add_column("Project", style="green")
    table.add_column("Last Active", style="magenta")
    table.add_column("Summary / Title", style="white")

    for s in sessions:
        agent_badge = "[bold red]Claude[/bold red]" if s["agent"] == "claude" else "[bold blue]Antigravity[/bold blue]"
        table.add_row(
            agent_badge,
            s["project_name"] or "default",
            s["last_active_at"] or "N/A",
            (s["summary"] or "")[:60]
        )

    console.print(table)

@app.command()
def search(query: str, limit: int = 8):
    """Full-text search across all prompts, thoughts, commands, and solutions."""
    results = search_events(query, limit=limit)
    if not results:
        console.print(f"[yellow]No events matching '{query}'.[/yellow]")
        return

    console.print(f"[bold green]Found {len(results)} matches for '{query}':[/bold green]\n")
    for r in results:
        agent_badge = "[bold red]Claude[/bold red]" if r["agent"] == "claude" else "[bold blue]Antigravity[/bold blue]"
        title = f"{agent_badge} | {r.get('project_name', 'project')} | Type: {r['event_type']} ({r['timestamp']})"
        content = r["content"][:400] + ("..." if len(r["content"]) > 400 else "")
        console.print(Panel(content, title=title, border_style="dim"))

@app.command()
def ui(project: Optional[str] = None, search_term: Optional[str] = None, limit: int = 5):
    """View captured UI designs, components, and Tailwind styling patterns."""
    patterns = query_ui_patterns(project=project, search=search_term, limit=limit)
    if not patterns:
        console.print("[yellow]No UI patterns captured yet.[/yellow]")
        return

    console.print(f"[bold cyan]Captured UI Patterns & Styling ({len(patterns)}):[/bold cyan]\n")
    for p in patterns:
        agent_badge = "[red]Claude[/red]" if p["agent"] == "claude" else "[blue]Antigravity[/blue]"
        title = f"{agent_badge} | {p['project_name']} -> [bold]{p['component_name']}[/bold] ({p['tech_stack']})"
        summary_panel = f"[bold green]Style Summary:[/bold green] {p['style_summary']}\n\n[bold dim]Code Preview:[/bold dim]\n"
        console.print(Panel(summary_panel + p["code_snippet"][:500] + "...", title=title, border_style="cyan"))

@app.command()
def watch():
    """Run continuous background watcher for Claude and Antigravity logs."""
    console.print("[bold green]Starting OmniContext daemon observer...[/bold green]")
    console.print("[dim]Monitoring ~/.claude/projects and ~/.gemini/antigravity/brain[/dim]")
    start_watching()

if __name__ == "__main__":
    app()
