#!/usr/bin/env python3
"""Final test to confirm YTTL MCP Server is working with Claude Desktop."""

import subprocess
import json
import sys
from pathlib import Path

def test_mcp_protocol():
    """Test that the server responds to MCP protocol requests."""
    print("🧪 Testing MCP protocol response...")
    
    # Create a proper MCP initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        # Test the server with a proper MCP request
        result = subprocess.run([
            '/usr/local/bin/python3', '/Users/Allen/YTTL-TUI/yttl_mcp/server.py'
        ],
        input=json.dumps(init_request) + '\n',
        env={'PYTHONPATH': '/Users/Allen/YTTL-TUI'},
        cwd='/Users/Allen/YTTL-TUI',
        capture_output=True,
        text=True,
        timeout=10
        )
        
        # Check if server responds with JSON-RPC
        if '"jsonrpc":"2.0"' in result.stdout:
            print("✅ Server responds to MCP protocol requests")
            return True
        else:
            print(f"❌ Server response: {result.stdout}")
            print(f"❌ Server errors: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Server timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_configuration():
    """Check Claude Desktop configuration."""
    print("\n⚙️  Checking Claude Desktop configuration...")
    
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    if not config_path.exists():
        print("❌ Claude Desktop config not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        yttl_config = config.get("mcpServers", {}).get("yttl", {})
        
        expected = {
            "command": "/usr/local/bin/python3",
            "args": ["/Users/Allen/YTTL-TUI/yttl_mcp/server.py"],
            "cwd": "/Users/Allen/YTTL-TUI",
            "env": {"PYTHONPATH": "/Users/Allen/YTTL-TUI"}
        }
        
        for key, expected_value in expected.items():
            if yttl_config.get(key) != expected_value:
                print(f"⚠️  Config mismatch for {key}:")
                print(f"   Expected: {expected_value}")
                print(f"   Actual: {yttl_config.get(key)}")
                return False
        
        print("✅ Claude Desktop configuration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def main():
    """Run final tests."""
    print("🎯 YTTL MCP Server - Final Protocol Test")
    print("=" * 50)
    
    success = True
    
    # Test MCP protocol
    if not test_mcp_protocol():
        success = False
    
    # Check configuration
    if not check_configuration():
        success = False
    
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 SUCCESS! YTTL MCP Server is working correctly!")
        print("\n✅ Server responds to MCP protocol requests")
        print("✅ Claude Desktop configuration is correct")
        print("\n🚀 READY FOR CLAUDE DESKTOP!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop completely (Quit and reopen)")
        print("2. Ask Claude: 'Find videos about Peter Thiel'")
        print("3. The server should now work properly!")
        return 0
    else:
        print("❌ TESTS FAILED")
        print("\nPlease check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())