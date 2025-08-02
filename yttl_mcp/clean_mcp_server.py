#!/usr/bin/env python3
"""Clean MCP Server implementation following exact specification."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging to stderr only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

class CleanMCPServer:
    """Clean MCP server implementation."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.videos = []
        self.initialized = False
        
    async def initialize_videos(self):
        """Initialize video data."""
        try:
            if not self.output_dir.exists():
                logger.warning(f"Output directory {self.output_dir} does not exist")
                self.initialized = True
                return
            
            html_files = list(self.output_dir.glob("*.html"))
            for html_file in html_files:
                video_id = html_file.stem
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract title
                    title = f"Video {video_id}"  # default
                    if '<title>' in content and '</title>' in content:
                        title_start = content.find('<title>') + 7
                        title_end = content.find('</title>', title_start)
                        title = content[title_start:title_end].strip()
                    elif '<h1>' in content and '</h1>' in content:
                        title_start = content.find('<h1>') + 4
                        title_end = content.find('</h1>', title_start)
                        title = content[title_start:title_end].strip()
                        # Remove HTML tags from title
                        if '<a' in title:
                            a_start = title.find('>')
                            a_end = title.rfind('<')
                            if a_start != -1 and a_end != -1:
                                title = title[a_start+1:a_end].strip()
                    
                    self.videos.append({
                        'id': video_id,
                        'title': title,
                        'file': str(html_file),
                        'content': content
                    })
                except Exception as e:
                    logger.error(f"Error processing {html_file}: {e}")
                    
            logger.info(f"Initialized with {len(self.videos)} videos")
            self.initialized = True
        except Exception as e:
            logger.error(f"Error initializing videos: {e}")
            self.initialized = True
    
    def send_response(self, response):
        """Send a JSON response to stdout."""
        try:
            json_str = json.dumps(response, separators=(',', ':'))
            print(json_str, flush=True)
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    async def handle_request(self, request_line):
        """Handle a single MCP request."""
        try:
            if not request_line.strip():
                return
                
            request = json.loads(request_line.strip())
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            logger.info(f"Received request: {method} (id: {request_id})")
            
            # Ensure we have a valid request ID for responses
            if request_id is None and method != "notifications/initialized":
                logger.error("Request missing ID")
                return
            
            if method == "initialize":
                # Initialize videos if not done yet
                if not self.initialized:
                    await self.initialize_videos()
                
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
                self.send_response(response)
                
            elif method == "notifications/initialized":
                # Client is ready - no response needed for notifications
                logger.info("Client initialized notification received")
                
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "search_videos",
                                "description": "Search through processed YouTube videos by content, title, or transcript",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Search terms to find in video content"
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Maximum number of results to return",
                                            "default": 10
                                        }
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "list_videos",
                                "description": "List all available processed videos",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "limit": {
                                            "type": "integer",
                                            "description": "Maximum number of videos to return",
                                            "default": 20
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
                self.send_response(response)
                
            elif method == "resources/list":
                resources = []
                for video in self.videos:
                    resources.append({
                        "uri": f"yttl:///video/{video['id']}",
                        "name": f"Video: {video['title']}",
                        "description": f"Complete content for video {video['id']}",
                        "mimeType": "text/html"
                    })
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "resources": resources
                    }
                }
                self.send_response(response)
                
            elif method == "resources/read":
                uri = params.get("uri", "")
                if uri.startswith("yttl:///video/"):
                    video_id = uri.replace("yttl:///video/", "")
                    
                    video_content = None
                    for video in self.videos:
                        if video['id'] == video_id:
                            video_content = video['content']
                            break
                    
                    if video_content:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "contents": [{
                                    "uri": uri,
                                    "text": video_content,
                                    "mimeType": "text/html"
                                }]
                            }
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": f"Video {video_id} not found"
                            }
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown resource URI: {uri}"
                        }
                    }
                self.send_response(response)
                
            elif method == "tools/call":
                # Make sure videos are initialized
                if not self.initialized:
                    await self.initialize_videos()
                    
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "search_videos":
                    query = arguments.get("query", "").lower()
                    limit = arguments.get("limit", 10)
                    
                    # Search through video titles and content
                    matching_videos = []
                    for video in self.videos:
                        if (query in video['title'].lower() or 
                            query in video['id'].lower() or
                            query in video['content'].lower()):
                            matching_videos.append(video)
                    
                    matching_videos = matching_videos[:limit]
                    
                    if matching_videos:
                        result_text = f"# Search Results for '{arguments.get('query', '')}'\n\n"
                        result_text += f"Found **{len(matching_videos)}** video(s):\n\n"
                        
                        for i, video in enumerate(matching_videos, 1):
                            result_text += f"## {i}. {video['title']}\n"
                            result_text += f"**Video ID:** `{video['id']}`\n"
                            result_text += f"**File:** `{Path(video['file']).name}`\n\n"
                    else:
                        result_text = f"No videos found matching '{arguments.get('query', '')}'"
                        
                elif tool_name == "list_videos":
                    limit = arguments.get("limit", 20)
                    videos_to_show = self.videos[:limit]
                    
                    if videos_to_show:
                        result_text = f"# Available Videos\n\n"
                        result_text += f"Found **{len(videos_to_show)}** video(s):\n\n"
                        
                        for i, video in enumerate(videos_to_show, 1):
                            result_text += f"## {i}. {video['title']}\n"
                            result_text += f"**Video ID:** `{video['id']}`\n"
                            result_text += f"**File:** `{Path(video['file']).name}`\n\n"
                    else:
                        result_text = "No videos found. Make sure YTTL has processed some videos first."
                        
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
                self.send_response(response)
                
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
                self.send_response(response)
            
            logger.info(f"Sent response for {method}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            # Don't send error response for parse errors - just log and continue
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            # Only send error response if we have a valid request ID
            if 'request' in locals() and isinstance(request, dict) and request.get("id") is not None:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                self.send_response(error_response)

async def main():
    """Main server loop."""
    logger.info("Starting Clean MCP Server for YTTL")
    
    output_dir = Path(__file__).parent.parent / "out"
    server = CleanMCPServer(output_dir)
    
    try:
        # Read from stdin line by line
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            await server.handle_request(line)
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
