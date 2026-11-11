"""Auto-configure OmniContext MCP Server in Claude and Claude Desktop."""
import json
from pathlib import Path

VENV_MCP_EXE = Path(__file__).parent.parent / ".venv" / "Scripts" / "omni-mcp.exe"

def configure_claude_json():
    claude_json_path = Path.home() / ".claude.json"
    if not claude_json_path.exists():
        print(f"Skipping ~/.claude.json (file not found)")
        return

    with open(claude_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        data["mcpServers"] = {}

    data["mcpServers"]["omni_context"] = {
        "command": str(VENV_MCP_EXE)
    }

    with open(claude_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✓ Successfully registered 'omni_context' in ~/.claude.json")

def configure_claude_desktop():
    desktop_config_dir = Path.home() / "AppData" / "Roaming" / "Claude"
    desktop_config_path = desktop_config_dir / "claude_desktop_config.json"
    
    if not desktop_config_dir.exists():
        return

    data = {}
    if desktop_config_path.exists():
        try:
            with open(desktop_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if "mcpServers" not in data:
        data["mcpServers"] = {}

    data["mcpServers"]["omni_context"] = {
        "command": str(VENV_MCP_EXE)
    }

    with open(desktop_config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Successfully registered 'omni_context' in {desktop_config_path}")

if __name__ == "__main__":
    configure_claude_json()
    configure_claude_desktop()
