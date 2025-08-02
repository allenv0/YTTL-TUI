#!/usr/bin/env python3
"""
Configuration helper for Claude Desktop integration.
"""

import json
import os
from pathlib import Path

def get_claude_config_path():
    """Get the Claude Desktop configuration file path."""
    home = Path.home()
    
    # Try different possible locations
    possible_paths = [
        home / ".claude_desktop_config.json",
        home / ".config" / "claude_desktop" / "config.json",
        home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Default to the most common location
    return home / ".claude_desktop_config.json"

def load_claude_config(config_path):
    """Load existing Claude configuration."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not read existing config: {e}")
            return {}
    return {}

def save_claude_config(config_path, config):
    """Save Claude configuration."""
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def main():
    """Configure Claude Desktop for YTTL MCP server."""
    print("🔧 Configuring Claude Desktop for YTTL MCP Server...")
    
    # Get current directory (where the MCP server is located)
    current_dir = Path(__file__).parent.absolute()
    
    # Get Claude config path
    config_path = get_claude_config_path()
    print(f"📁 Claude config path: {config_path}")
    
    # Load existing config
    config = load_claude_config(config_path)
    
    # Ensure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add YTTL MCP server configuration
    yttl_config = {
        "command": "python3",
        "args": ["-m", "yttl_mcp.server"],
        "cwd": str(current_dir),
        "env": {
            "PYTHONPATH": str(current_dir.parent)
        }
    }
    
    # Check if YTTL server already configured
    if "yttl" in config["mcpServers"]:
        print("⚠️  YTTL MCP server already configured in Claude Desktop")
        response = input("Do you want to update the configuration? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Configuration cancelled")
            return
    
    config["mcpServers"]["yttl"] = yttl_config
    
    # Save configuration
    try:
        save_claude_config(config_path, config)
        print("✅ Claude Desktop configuration updated successfully!")
        print(f"📁 Config saved to: {config_path}")
        print("")
        print("📋 Configuration added:")
        print(json.dumps({"mcpServers": {"yttl": yttl_config}}, indent=2))
        print("")
        print("🔄 Please restart Claude Desktop for changes to take effect.")
        print("")
        print("🧪 Test the server with: python3 -m yttl_mcp.server")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        print("")
        print("📋 Manual configuration:")
        print("Add this to your Claude Desktop config file:")
        print(json.dumps({"mcpServers": {"yttl": yttl_config}}, indent=2))

if __name__ == "__main__":
    main()