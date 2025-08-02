#!/usr/bin/env python3
"""Validate that YTTL MCP Server is ready for Claude Desktop."""

import asyncio
import json
import sys
from pathlib import Path

async def main():
    """Validate MCP server setup."""
    print("🔍 YTTL MCP Server Validation")
    print("=" * 50)
    
    success = True
    
    # Check dependencies
    print("📦 Checking dependencies...")
    try:
        import mcp
        import pydantic
        import aiofiles
        from bs4 import BeautifulSoup
        print("✅ All dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        success = False
    
    # Check server can be imported
    print("\n🏗️  Checking server import...")
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        print("✅ Server can be imported")
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        success = False
    
    # Check video directory
    print("\n📁 Checking video directory...")
    output_dir = Path(__file__).parent.parent / "out"
    if output_dir.exists():
        html_files = list(output_dir.glob("*.html"))
        if html_files:
            print(f"✅ Found {len(html_files)} video file(s)")
            for f in html_files[:3]:  # Show first 3
                print(f"   - {f.name}")
            if len(html_files) > 3:
                print(f"   ... and {len(html_files) - 3} more")
        else:
            print("⚠️  No HTML files found - process some videos with YTTL first")
    else:
        print("❌ Output directory not found")
        success = False
    
    # Test server functionality
    print("\n🧪 Testing server functionality...")
    try:
        server = YTTLMCPServer(output_dir=output_dir)
        await server.video_parser.initialize()
        
        # Test tools
        tools = await server.tools.list_tools()
        print(f"✅ {len(tools)} tools available")
        
        # Test resources
        resources = await server.resources.list_resources()
        print(f"✅ {len(resources)} resources available")
        
        # Test search if videos exist
        if resources:
            result = await server.tools.call_tool("search_videos", {"query": "test", "limit": 1})
            print("✅ Search functionality working")
        
    except Exception as e:
        print(f"❌ Server functionality test failed: {e}")
        success = False
    
    # Check Claude Desktop config
    print("\n⚙️  Checking Claude Desktop configuration...")
    config_paths = [
        Path.home() / ".claude_desktop_config.json",
        Path.home() / ".config" / "claude_desktop" / "config.json",
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    ]
    
    config_found = False
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                if "mcpServers" in config and "yttl" in config["mcpServers"]:
                    print(f"✅ YTTL MCP server configured in {config_path}")
                    config_found = True
                    break
            except Exception as e:
                print(f"⚠️  Could not read config at {config_path}: {e}")
    
    if not config_found:
        print("⚠️  YTTL MCP server not found in Claude Desktop config")
        print("   Run: python configure_claude.py")
    
    # Final status
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 YTTL MCP Server is ready for Claude Desktop!")
        print("\nNext steps:")
        if not config_found:
            print("1. Run: python configure_claude.py")
            print("2. Restart Claude Desktop")
        else:
            print("1. Restart Claude Desktop (if not done recently)")
        print("2. Ask Claude to search your videos!")
        print("\nExample: 'Find videos about startup advice'")
    else:
        print("❌ Setup issues found. Please fix the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)