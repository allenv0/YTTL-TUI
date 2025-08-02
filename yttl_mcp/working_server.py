#!/usr/bin/env python3
"""Working YTTL MCP Server with proper request handling."""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    Resource,
    ReadResourceResult,
    ListResourcesResult,
    ListToolsResult,
    CallToolResult,
    TextResourceContents,
    AnyUrl
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the MCP server."""
    try:
        # Import our components
        sys.path.append(str(Path(__file__).parent.parent))
        from yttl_mcp.server_impl.video_parser import VideoParser
        from yttl_mcp.server_impl.tools import YTTLTools
        from yttl_mcp.server_impl.resources import YTTLResources
        
        # Initialize components
        output_dir = Path(__file__).parent.parent / "out"
        video_parser = VideoParser(output_dir)
        await video_parser.initialize()
        
        tools = YTTLTools(video_parser)
        resources = YTTLResources(video_parser)
        
        logger.info(f"YTTL MCP Server initialized with {len(video_parser._cache)} videos")
        
        # Create server
        server = Server("yttl")
        
        @server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            try:
                tool_list = await tools.list_tools()
                logger.info(f"Returning {len(tool_list)} tools")
                return ListToolsResult(tools=tool_list)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return ListToolsResult(tools=[])
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            try:
                logger.info(f"Tool call: {name} with args: {arguments}")
                result = await tools.call_tool(name, arguments)
                return CallToolResult(content=result)
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
        
        @server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            try:
                resource_list = await resources.list_resources()
                logger.info(f"Returning {len(resource_list)} resources")
                return ListResourcesResult(resources=resource_list)
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return ListResourcesResult(resources=[])
        
        @server.read_resource()
        async def read_resource(uri) -> ReadResourceResult:
            """Get a specific resource."""
            try:
                logger.info(f"Resource request: {uri}")
                result = await resources.get_resource(uri)
                return result
            except Exception as e:
                logger.error(f"Resource error: {e}")
                return ReadResourceResult(
                    contents=[TextResourceContents(uri=str(uri), text=f"Error: {str(e)}", mimeType="text/plain")]
                )
        
        logger.info("Starting MCP server...")
        
        # Run server with proper error handling
        async with stdio_server() as streams:
            logger.info("MCP server connected and ready")
            await server.run(streams[0], streams[1], {})
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())