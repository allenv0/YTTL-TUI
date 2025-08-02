#!/usr/bin/env python3
"""YTTL MCP Server - Provides access to processed YouTube video summaries."""

import asyncio
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

async def main():
    """Main entry point for the MCP server."""
    try:
        from yttl_mcp.server_impl.server import YTTLMCPServer
        
        # Default to ../out directory (relative to main YTTL project)
        output_dir = Path(__file__).parent.parent / "out"
        
        server = YTTLMCPServer(output_dir=output_dir)
        await server.run()
    except KeyboardInterrupt:
        logging.info("Server shutdown requested")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())