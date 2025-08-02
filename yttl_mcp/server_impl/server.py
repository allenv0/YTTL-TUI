"""Core MCP server implementation for YTTL."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
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
    CallToolResult
)

from .tools import YTTLTools
from .resources import YTTLResources
from .video_parser import VideoParser
from .exceptions import YTTLMCPError

logger = logging.getLogger(__name__)

class YTTLMCPServer:
    """Main YTTL MCP Server class."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.server = Server("yttl")
        self.output_dir = output_dir or Path("out")
        self.video_parser = VideoParser(self.output_dir)
        self.tools = YTTLTools(self.video_parser)
        self.resources = YTTLResources(self.video_parser)
        
        self._setup_handlers()
        logger.info(f"YTTL MCP Server initialized with output directory: {self.output_dir}")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            try:
                logger.debug("Listing available tools")
                tools = await self.tools.list_tools()
                logger.debug(f"Returning {len(tools)} tools")
                return ListToolsResult(tools=tools)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                raise YTTLMCPError(f"Failed to list tools: {e}")
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                logger.info(f"Tool call: {name} with args: {arguments}")
                result = await self.tools.call_tool(name, arguments)
                logger.debug(f"Tool {name} completed successfully")
                return CallToolResult(content=result)
            except YTTLMCPError as e:
                logger.error(f"Tool error: {e}")
                # Return error as content rather than raising
                return CallToolResult(
                    content=[TextContent(type="text", text=f"❌ **Error:** {str(e)}")]
                )
            except Exception as e:
                logger.error(f"Unexpected error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"❌ **Unexpected Error:** Tool {name} failed: {e}")]
                )
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            try:
                logger.debug("Listing available resources")
                resources = await self.resources.list_resources()
                logger.debug(f"Returning {len(resources)} resources")
                return ListResourcesResult(resources=resources)
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                raise YTTLMCPError(f"Failed to list resources: {e}")
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Get a specific resource."""
            try:
                logger.info(f"Resource request: {uri}")
                result = await self.resources.get_resource(uri)
                logger.debug(f"Resource {uri} retrieved successfully")
                return result
            except YTTLMCPError as e:
                logger.error(f"Resource error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting resource {uri}: {e}")
                raise YTTLMCPError(f"Resource {uri} failed: {e}")
    
    async def run(self):
        """Run the MCP server."""
        logger.info(f"Starting YTTL MCP Server")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        
        try:
            # Initialize video parser
            logger.info("Initializing video parser...")
            await self.video_parser.initialize()
            
            # Log initialization stats
            cache_stats = await self.video_parser.get_cache_stats()
            logger.info(f"Initialization complete: {cache_stats['total_videos']} videos loaded")
            
            if cache_stats['total_videos'] == 0:
                logger.warning("No videos found in output directory. Make sure YTTL has processed some videos.")
            
            # Run server
            logger.info("Starting MCP server on stdio...")
            logger.info("Note: This server is designed to be used with Claude Desktop, not run directly")
            try:
                async with stdio_server() as streams:
                    logger.info("MCP server connected and ready")
                    await self.server.run(streams[0], streams[1], {})
            except Exception as e:
                logger.error(f"MCP server run failed: {e}")
                # For Claude Desktop, we want to provide a more helpful error message
                if "TaskGroup" in str(e):
                    logger.error("Server failed to handle MCP protocol properly")
                    logger.error("This might be due to a protocol version mismatch or connection issue")
                    # Don't re-raise for Claude Desktop - let it retry
                    return
                else:
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
                
        except KeyboardInterrupt:
            logger.info("Server shutdown requested by user")
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            raise
        finally:
            logger.info("YTTL MCP Server stopped")