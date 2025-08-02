#!/usr/bin/env python3
"""Simple MCP server test to isolate the protocol issue."""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

async def main():
    """Simple MCP server test."""
    logger.info("Starting simple MCP test server")
    
    server = Server("simple-test")
    
    @server.list_tools()
    async def list_tools() -> ListToolsResult:
        """List available tools."""
        return ListToolsResult(tools=[
            Tool(
                name="test_tool",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Test message"
                        }
                    },
                    "required": ["message"]
                }
            )
        ])
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        """Handle tool calls."""
        if name == "test_tool":
            message = arguments.get("message", "Hello")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Test response: {message}")]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    logger.info("Server handlers registered")
    
    try:
        async with stdio_server() as streams:
            logger.info("Starting MCP server...")
            await server.run(streams[0], streams[1], {})
    except Exception as e:
        logger.error(f"Server failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())