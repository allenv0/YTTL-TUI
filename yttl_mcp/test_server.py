#!/usr/bin/env python3
"""
Test script for YTTL MCP Server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from yttl_mcp.server_impl.video_parser import VideoParser
from yttl_mcp.server_impl.tools import YTTLTools
from yttl_mcp.server_impl.resources import YTTLResources

async def test_video_parser():
    """Test the video parser functionality."""
    print("🧪 Testing Video Parser...")
    
    # Use ../out directory (relative to main YTTL project)
    output_dir = Path(__file__).parent.parent / "out"
    parser = VideoParser(output_dir)
    
    try:
        await parser.initialize()
        stats = await parser.get_cache_stats()
        
        print(f"✅ Parser initialized successfully")
        print(f"   📊 Total videos: {stats['total_videos']}")
        print(f"   💾 Cache size: {stats['cache_size_mb']:.2f} MB")
        
        if stats['total_videos'] > 0:
            print(f"   📅 Date range: {stats['oldest_video']} to {stats['newest_video']}")
            
            # Test search
            print("\n🔍 Testing search functionality...")
            results = await parser.search_videos("test", limit=3)
            print(f"   Found {len(results)} results for 'test'")
            
            # Test getting a video
            if results:
                video_id = results[0]['video_id']
                print(f"\n📹 Testing video retrieval for: {video_id}")
                video = await parser.get_video(video_id)
                if video:
                    print(f"   ✅ Retrieved video: {video.title}")
                    print(f"   📋 Summary sections: {len(video.summary_sections)}")
                    print(f"   📝 Transcript segments: {len(video.transcript_segments)}")
                else:
                    print(f"   ❌ Failed to retrieve video")
        else:
            print("   ⚠️  No videos found - make sure YTTL has processed some videos")
            
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False
    
    return True

async def test_tools():
    """Test the tools functionality."""
    print("\n🛠️  Testing Tools...")
    
    output_dir = Path(__file__).parent.parent / "out"
    parser = VideoParser(output_dir)
    tools = YTTLTools(parser)
    
    try:
        await parser.initialize()
        
        # Test list_tools
        tool_list = await tools.list_tools()
        print(f"✅ Tools available: {len(tool_list)}")
        for tool in tool_list:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        # Test cache stats
        print("\n📊 Testing cache stats...")
        result = await tools.call_tool("get_cache_stats", {})
        print(f"✅ Cache stats retrieved: {len(result[0].text)} characters")
        
        # Test search if videos available
        stats = await parser.get_cache_stats()
        if stats['total_videos'] > 0:
            print("\n🔍 Testing search tool...")
            result = await tools.call_tool("search_videos", {"query": "test", "limit": 2})
            print(f"✅ Search completed: {len(result[0].text)} characters")
            
            print("\n📋 Testing list videos...")
            result = await tools.call_tool("list_videos", {"limit": 3})
            print(f"✅ List videos completed: {len(result[0].text)} characters")
        
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False
    
    return True

async def test_resources():
    """Test the resources functionality."""
    print("\n📚 Testing Resources...")
    
    output_dir = Path(__file__).parent.parent / "out"
    parser = VideoParser(output_dir)
    resources = YTTLResources(parser)
    
    try:
        await parser.initialize()
        
        # Test list_resources
        print("   Testing list_resources...")
        resource_list = await resources.list_resources()
        print(f"✅ Resources available: {len(resource_list)}")
        
        if resource_list:
            # Test getting a resource
            test_uri = resource_list[0].uri
            print(f"\n📄 Testing resource retrieval: {test_uri}")
            result = await resources.get_resource(test_uri)
            print(f"✅ Resource retrieved: {len(result.contents[0].text)} characters")
        
    except Exception as e:
        print(f"❌ Resources test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("🧪 YTTL MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Video Parser", test_video_parser),
        ("Tools", test_tools),
        ("Resources", test_resources),
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
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! YTTL MCP Server is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())