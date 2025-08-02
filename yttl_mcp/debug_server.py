#!/usr/bin/env python3
"""Debug script to test MCP server components individually."""

import asyncio
import logging
import sys
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

async def test_mcp_basic():
    """Test basic MCP server creation."""
    print("🧪 Testing basic MCP server creation...")
    
    try:
        from mcp.server import Server
        server = Server("test")
        print("✅ MCP Server created successfully")
        return True
    except Exception as e:
        print(f"❌ MCP Server creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_stdio_server():
    """Test stdio server creation."""
    print("🧪 Testing stdio server...")
    
    try:
        from mcp.server.stdio import stdio_server
        print("✅ stdio_server imported successfully")
        
        # Test creating the context manager (but don't enter it)
        server_context = stdio_server()
        print("✅ stdio_server context manager created")
        return True
    except Exception as e:
        print(f"❌ stdio_server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_yttl_server_creation():
    """Test YTTL server creation without running."""
    print("🧪 Testing YTTL server creation...")
    
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        output_dir = Path(__file__).parent.parent / "out"
        server = YTTLMCPServer(output_dir=output_dir)
        print("✅ YTTL MCP Server created successfully")
        
        # Test initialization
        await server.video_parser.initialize()
        print("✅ Video parser initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ YTTL server creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_handlers():
    """Test server handler setup."""
    print("🧪 Testing server handlers...")
    
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        output_dir = Path(__file__).parent.parent / "out"
        server = YTTLMCPServer(output_dir=output_dir)
        
        # Initialize
        await server.video_parser.initialize()
        
        # Test that handlers are set up
        print(f"✅ Server has {len(server.server._handlers)} handlers")
        
        return True
    except Exception as e:
        print(f"❌ Server handlers test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all debug tests."""
    print("🔍 YTTL MCP Server Debug Suite")
    print("=" * 50)
    
    tests = [
        ("Basic MCP Server", test_mcp_basic),
        ("stdio_server", test_stdio_server),
        ("YTTL Server Creation", test_yttl_server_creation),
        ("Server Handlers", test_server_handlers),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("📊 Debug Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All debug tests passed! The issue might be in the stdio handling.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())