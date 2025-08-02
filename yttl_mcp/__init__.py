"""YTTL MCP Server - Model Context Protocol server for YouTube video summaries."""

__version__ = "1.0.0"
__author__ = "YTTL Team"
__description__ = "MCP server providing access to processed YouTube video summaries"

def mcp_server_main():
    """Entry point for MCP server."""
    import asyncio
    from yttl_mcp.server import main
    asyncio.run(main())