#!/usr/bin/env python3
"""Claude Desktop compatible YTTL MCP Server."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

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

class SimpleYTTLServer:
    """Simplified YTTL MCP Server for Claude Desktop compatibility."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.videos = []
        self.server = Server("yttl")
        self._setup_handlers()
        
    async def initialize(self):
        """Initialize video data."""
        try:
            if not self.output_dir.exists():
                logger.warning(f"Output directory {self.output_dir} does not exist")
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
        except Exception as e:
            logger.error(f"Error initializing videos: {e}")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            tools = [
                Tool(
                    name="search_videos",
                    description="Search through processed YouTube videos by content, title, or transcript",
                    inputSchema={
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
                ),
                Tool(
                    name="list_videos",
                    description="List all available processed videos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of videos to return",
                                "default": 20
                            }
                        }
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "search_videos":
                    query = arguments.get("query", "").lower()
                    limit = arguments.get("limit", 10)
                    
                    # Simple search through video titles and content
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
                        
                elif name == "list_videos":
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
                    result_text = f"Unknown tool: {name}"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
                
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            resources = []
            for video in self.videos:
                resources.append(Resource(
                    uri=AnyUrl(f"yttl:///video/{video['id']}"),
                    name=f"Video: {video['title']}",
                    description=f"Complete content for video {video['id']}",
                    mimeType="text/html"
                ))
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def read_resource(uri: AnyUrl) -> ReadResourceResult:
            """Get a specific resource."""
            try:
                uri_str = str(uri)
                if uri_str.startswith("yttl:///video/"):
                    video_id = uri_str.replace("yttl:///video/", "")
                    
                    for video in self.videos:
                        if video['id'] == video_id:
                            return ReadResourceResult(
                                contents=[TextResourceContents(
                                    uri=uri,
                                    text=video['content'],
                                    mimeType="text/html"
                                )]
                            )
                    
                    raise ValueError(f"Video {video_id} not found")
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                    
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[TextResourceContents(
                        uri=uri,
                        text=f"Error: {str(e)}",
                        mimeType="text/plain"
                    )]
                )

async def main():
    """Main entry point."""
    logger.info("Starting Claude Desktop compatible YTTL MCP Server")
    
    try:
        # Initialize server
        output_dir = Path(__file__).parent.parent / "out"
        server = SimpleYTTLServer(output_dir)
        await server.initialize()
        
        # Run server
        logger.info("Starting MCP server on stdio...")
        async with stdio_server() as streams:
            logger.info("MCP server connected and ready")
            await server.server.run(streams[0], streams[1], {})
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
