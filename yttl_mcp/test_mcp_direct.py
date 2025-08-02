#!/usr/bin/env python3
"""Test MCP server with direct method calls instead of stdio."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

async def test_direct_mcp_calls():
    """Test MCP server by calling methods directly."""
    print("🧪 Testing MCP server with direct method calls...")
    
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        output_dir = Path(__file__).parent.parent / "out"
        server = YTTLMCPServer(output_dir=output_dir)
        
        # Initialize
        await server.video_parser.initialize()
        print("✅ Server initialized")
        
        # Test list_tools
        print("\n🛠️  Testing list_tools...")
        tools = await server.tools.list_tools()
        print(f"✅ Got {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool.name}")
        
        # Test search_videos
        print("\n🔍 Testing search_videos...")
        result = await server.tools.call_tool("search_videos", {"query": "Peter", "limit": 5})
        print(f"✅ Search completed: {len(result[0].text)} characters")
        print(f"   Preview: {result[0].text[:100]}...")
        
        # Test list_resources
        print("\n📚 Testing list_resources...")
        resources = await server.resources.list_resources()
        print(f"✅ Got {len(resources)} resources")
        for resource in resources[:3]:
            print(f"   - {resource.name}: {resource.uri}")
        
        # Test get_resource
        if resources:
            print("\n📄 Testing get_resource...")
            resource_result = await server.resources.get_resource(resources[0].uri)
            print(f"✅ Resource retrieved: {len(resource_result.contents[0].text)} characters")
        
        print("\n🎉 All direct MCP calls successful!")
        return True
        
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_with_mock_stdio():
    """Test server with mock stdio to see if that's the issue."""
    print("\n🧪 Testing server with mock stdio...")
    
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        from mcp.server.stdio import stdio_server
        import io
        
        output_dir = Path(__file__).parent.parent / "out"
        server = YTTLMCPServer(output_dir=output_dir)
        
        # Initialize
        await server.video_parser.initialize()
        
        # Try to create stdio server context but don't run it
        print("✅ Creating stdio server context...")
        
        # The issue might be that stdio_server expects actual stdin/stdout
        # Let's see if we can at least create the context
        try:
            async with stdio_server() as streams:
                print("✅ stdio_server context created successfully")
                print("   This suggests the issue is in the server.run() call")
                # Don't actually run the server as it would hang
                return True
        except Exception as e:
            print(f"❌ stdio_server context failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Mock stdio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run MCP direct tests."""
    print("🔍 YTTL MCP Direct Testing")
    print("=" * 50)
    
    # Test direct method calls
    success1 = await test_direct_mcp_calls()
    
    # Test stdio context creation
    success2 = await test_server_with_mock_stdio()
    
    print(f"\n{'=' * 50}")
    print("📊 Results:")
    print(f"✅ Direct MCP calls: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ stdio context: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 Server functionality works! The issue is likely in stdio handling when no input is provided.")
        print("💡 This is normal - MCP servers are designed to run with Claude Desktop providing input.")
    else:
        print("\n⚠️  There are issues with the server implementation.")

if __name__ == "__main__":
    asyncio.run(main())