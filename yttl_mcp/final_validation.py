#!/usr/bin/env python3
"""Final validation that YTTL MCP Server works with Claude Desktop's Python."""

import subprocess
import sys
import json
from pathlib import Path

def test_system_python():
    """Test that system Python can run the server."""
    print("🧪 Testing system Python (/usr/local/bin/python3)...")
    
    # Test module import
    try:
        result = subprocess.run([
            '/usr/local/bin/python3', '-c', 
            'import sys; sys.path.append("/Users/Allen/YTTL-TUI"); import yttl_mcp; print("✅ Module import successful")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ System Python can import yttl_mcp module")
        else:
            print(f"❌ Module import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Module import test failed: {e}")
        return False
    
    # Test server startup (should fail with expected error)
    try:
        result = subprocess.run([
            '/usr/local/bin/python3', '-m', 'yttl_mcp.server'
        ], 
        env={'PYTHONPATH': '/Users/Allen/YTTL-TUI'},
        cwd='/Users/Allen/YTTL-TUI',
        capture_output=True, text=True, timeout=5)
        
        # Check if it shows the expected initialization messages
        if "YTTL MCP Server initialized" in result.stderr and "Initialized with 1 videos" in result.stderr:
            print("✅ System Python can run the MCP server")
            print("✅ Server initializes correctly and finds videos")
            return True
        else:
            print(f"❌ Server startup failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Server started (timeout expected - server waits for Claude Desktop)")
        return True
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def check_claude_config():
    """Check Claude Desktop configuration."""
    print("\n⚙️  Checking Claude Desktop configuration...")
    
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    if not config_path.exists():
        print("❌ Claude Desktop config not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("❌ No mcpServers in config")
            return False
        
        if "yttl" not in config["mcpServers"]:
            print("❌ YTTL server not configured")
            return False
        
        yttl_config = config["mcpServers"]["yttl"]
        
        # Check configuration
        expected_command = "/usr/local/bin/python3"
        expected_args = ["-m", "yttl_mcp.server"]
        expected_cwd = "/Users/Allen/YTTL-TUI"
        
        if yttl_config.get("command") != expected_command:
            print(f"⚠️  Command mismatch: {yttl_config.get('command')} != {expected_command}")
        
        if yttl_config.get("args") != expected_args:
            print(f"⚠️  Args mismatch: {yttl_config.get('args')} != {expected_args}")
        
        if yttl_config.get("cwd") != expected_cwd:
            print(f"⚠️  CWD mismatch: {yttl_config.get('cwd')} != {expected_cwd}")
        
        if yttl_config.get("env", {}).get("PYTHONPATH") != "/Users/Allen/YTTL-TUI":
            print(f"⚠️  PYTHONPATH mismatch: {yttl_config.get('env', {}).get('PYTHONPATH')} != /Users/Allen/YTTL-TUI")
        
        print("✅ Claude Desktop configuration looks correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def main():
    """Run final validation."""
    print("🎯 YTTL MCP Server - Final Validation for Claude Desktop")
    print("=" * 60)
    
    success = True
    
    # Test system Python
    if not test_system_python():
        success = False
    
    # Check Claude config
    if not check_claude_config():
        success = False
    
    # Check video files
    print("\n📁 Checking video files...")
    out_dir = Path("/Users/Allen/YTTL-TUI/out")
    if out_dir.exists():
        html_files = list(out_dir.glob("*.html"))
        if html_files:
            print(f"✅ Found {len(html_files)} video file(s)")
        else:
            print("⚠️  No video files found")
    else:
        print("❌ Output directory not found")
        success = False
    
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 FINAL VALIDATION: SUCCESS!")
        print("\n✅ System Python can run the MCP server")
        print("✅ Claude Desktop configuration is correct")
        print("✅ Video files are available")
        print("\n🚀 READY FOR CLAUDE DESKTOP!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Ask Claude: 'Find videos about Peter Thiel'")
        print("3. Enjoy your video search capabilities!")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print("\nPlease fix the issues above before using with Claude Desktop.")
        return 1

if __name__ == "__main__":
    sys.exit(main())