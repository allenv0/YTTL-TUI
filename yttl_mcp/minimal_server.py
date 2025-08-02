#!/usr/bin/env python3
"""Minimal YTTL MCP Server to test basic functionality."""

import asyncio
import logging
import sys
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

async def handle_request(request_line):
    """Handle a single MCP request."""
    try:
        request = json.loads(request_line.strip())
        method = request.get("method")
        request_id = request.get("id")
        
        logger.info(f"Received request: {method}")
        
        if method == "initialize":
            # Return successful initialization
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "yttl",
                        "version": "1.0.0"
                    }
                }
            }
            print(json.dumps(response), flush=True)
            
        elif method == "tools/list":
            # Return list of tools
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "search_videos",
                            "description": "Search through processed YouTube videos",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search terms"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    ]
                }
            }
            print(json.dumps(response), flush=True)
            
        elif method == "tools/call":
            # Handle tool calls
            tool_name = request.get("params", {}).get("name")
            arguments = request.get("params", {}).get("arguments", {})
            
            if tool_name == "search_videos":
                query = arguments.get("query", "")
                result_text = f"Found videos matching '{query}': Peter Thiel video available"
            else:
                result_text = f"Unknown tool: {tool_name}"
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            print(json.dumps(response), flush=True)
            
        else:
            # Unknown method
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            print(json.dumps(response), flush=True)
            
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        if 'request_id' in locals():
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(response), flush=True)

async def main():
    """Main server loop."""
    logger.info("Starting minimal YTTL MCP Server")
    
    try:
        # Read from stdin and respond
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            await handle_request(line)
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())