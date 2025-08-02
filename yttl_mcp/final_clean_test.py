#!/usr/bin/env python3
"""Final test of the clean MCP server."""

import subprocess
import json
import sys
from pathlib import Path

def test_clean_server():
    """Test the clean MCP server with Claude Desktop's exact setup."""
    print("🧪 Testing Clean MCP Server...")
    
    try:
        # Test with the exact same command and environment that Claude Desktop will use
        proc = subprocess.Popen(
            ['python3', '/Users/Allen/YTTL-TUI/yttl_mcp/clean_mcp_server.py'],
            cwd='/Users/Allen/YTTL-TUI/yttl_mcp',
            env={'PYTHONPATH': '/Users/Allen/YTTL-TUI'},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Test sequence of requests (exact Claude Desktop sequence)
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "claude-desktop",
                        "version": "1.0.0"
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "list_videos",
                    "arguments": {"limit": 5}
                }
            }
        ]
        
        # Send all requests
        input_data = '\n'.join(json.dumps(req) for req in requests) + '\n'
        stdout, stderr = proc.communicate(input=input_data, timeout=10)
        
        # Parse responses
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip() and line.startswith('{'):
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        # Validate responses
        success = True
        
        print(f"📊 Received {len(responses)} responses")
        
        # Check initialize response
        if len(responses) >= 1:
            init_resp = responses[0]
            if (init_resp.get('id') == 1 and 
                'result' in init_resp and 
                init_resp['result'].get('protocolVersion') == '2025-06-18'):
                print("✅ Initialize request handled correctly")
            else:
                print(f"❌ Initialize response invalid: {init_resp}")
                success = False
        else:
            print("❌ No initialize response received")
            success = False
        
        # Check tools/list response
        if len(responses) >= 2:
            tools_resp = responses[1]
            if (tools_resp.get('id') == 2 and 
                'result' in tools_resp and 
                'tools' in tools_resp['result']):
                tools = tools_resp['result']['tools']
                if len(tools) >= 2:
                    print(f"✅ Tools list returned {len(tools)} tools")
                    for tool in tools:
                        print(f"   - {tool['name']}: {tool['description'][:50]}...")
                else:
                    print(f"❌ Expected at least 2 tools, got {len(tools)}")
                    success = False
            else:
                print(f"❌ Tools list response invalid: {tools_resp}")
                success = False
        else:
            print("❌ No tools list response received")
            success = False
        
        # Check tool call response
        if len(responses) >= 3:
            call_resp = responses[2]
            if (call_resp.get('id') == 3 and 
                'result' in call_resp and 
                'content' in call_resp['result']):
                content = call_resp['result']['content']
                if len(content) > 0 and 'text' in content[0]:
                    text = content[0]['text']
                    if 'Peter Thiel' in text:
                        print("✅ Tool call returned video content")
                        print(f"   Found video: {text.split('##')[1].split('**')[0].strip() if '##' in text else 'Unknown'}")
                    else:
                        print(f"❌ Tool call content doesn't contain expected video: {text[:100]}...")
                        success = False
                else:
                    print(f"❌ Tool call response has no content: {call_resp}")
                    success = False
            else:
                print(f"❌ Tool call response invalid: {call_resp}")
                success = False
        else:
            print("❌ No tool call response received")
            success = False
        
        # Check for errors in stderr
        if "ERROR" in stderr or "Failed to validate" in stderr or "Traceback" in stderr:
            print(f"❌ Server errors detected: {stderr}")
            success = False
        else:
            print("✅ No validation errors in server logs")
        
        # Check JSON format
        json_valid = True
        for line in stdout.strip().split('\n'):
            if line.strip() and line.startswith('{'):
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in response: {line[:50]}... Error: {e}")
                    json_valid = False
                    success = False
        
        if json_valid:
            print("✅ All JSON responses are valid")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Server test timed out")
        proc.kill()
        return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def check_config():
    """Check Claude Desktop configuration."""
    print("\n⚙️  Checking Claude Desktop configuration...")
    
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    if not config_path.exists():
        print(f"❌ Claude config file not found at {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config or "yttl" not in config["mcpServers"]:
            print("❌ YTTL server not configured in Claude Desktop")
            return False
        
        yttl_config = config["mcpServers"]["yttl"]
        expected_args = ["/Users/Allen/YTTL-TUI/yttl_mcp/clean_mcp_server.py"]
        
        if yttl_config.get("args") == expected_args:
            print("✅ Claude Desktop configured to use clean_mcp_server.py")
            print(f"   Command: {yttl_config.get('command')}")
            print(f"   Working directory: {yttl_config.get('cwd')}")
            print(f"   PYTHONPATH: {yttl_config.get('env', {}).get('PYTHONPATH')}")
            return True
        else:
            print(f"❌ Wrong server configured: {yttl_config.get('args')}")
            return False
            
    except Exception as e:
        print(f"❌ Error reading Claude config: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 YTTL Clean MCP Server Final Test")
    print("=" * 50)
    
    tests = [
        ("Claude Desktop Configuration", check_config),
        ("Clean MCP Server", test_clean_server),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Clean MCP Server is ready for Claude Desktop.")
        print("\n📋 Next steps:")
        print("1. Restart Claude Desktop")
        print("2. Try asking Claude: 'Search for videos about Peter Thiel'")
        print("3. Or: 'List available videos'")
        print("\n✨ The server should now work without any validation errors!")
        print("🔧 The clean implementation bypasses MCP library validation issues")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
