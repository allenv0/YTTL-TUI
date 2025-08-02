#!/usr/bin/env python3
"""Update Claude Desktop configuration to use the new server."""

import json
from pathlib import Path

def main():
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update to use the clean server
    config["mcpServers"]["yttl"] = {
        "command": "python3",
        "args": ["/Users/Allen/YTTL-TUI/yttl_mcp/clean_mcp_server.py"],
        "cwd": "/Users/Allen/YTTL-TUI/yttl_mcp",
        "env": {
            "PYTHONPATH": "/Users/Allen/YTTL-TUI"
        }
    }
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Updated Claude Desktop configuration to use clean_mcp_server.py")
    print("🔄 Please restart Claude Desktop for changes to take effect")

if __name__ == "__main__":
    main()
