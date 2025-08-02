"""Tool implementations for YTTL MCP server."""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator

from mcp.types import Tool, TextContent
from .video_parser import VideoParser, VideoData
from .exceptions import YTTLMCPError, InvalidSearchError

logger = logging.getLogger(__name__)

class SearchParams(BaseModel):
    """Parameters for search_videos tool."""
    query: str = Field(description="Search terms to find in video content")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    include_transcript: bool = Field(default=True, description="Include transcript in search")
    include_summary: bool = Field(default=True, description="Include summary in search")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class VideoContentParams(BaseModel):
    """Parameters for get_video_content tool."""
    video_id: str = Field(description="Video ID (filename without .html extension)")
    include_transcript: bool = Field(default=True, description="Include full transcript")
    
    @validator('video_id')
    def video_id_valid(cls, v):
        if not v.strip():
            raise ValueError('Video ID cannot be empty')
        # Remove any path separators for security
        return v.strip().replace('/', '').replace('\\', '')

class ListVideosParams(BaseModel):
    """Parameters for list_videos tool."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum videos to return")
    recent_days: int = Field(default=30, ge=0, description="Only show videos from last N days (0 for all)")

class CompareVideosParams(BaseModel):
    """Parameters for compare_videos tool."""
    video_ids: List[str] = Field(description="List of video IDs to compare", min_items=2, max_items=5)
    
    @validator('video_ids')
    def clean_video_ids(cls, v):
        # Clean and validate video IDs
        cleaned = []
        for vid_id in v:
            if vid_id.strip():
                cleaned.append(vid_id.strip().replace('/', '').replace('\\', ''))
        if len(cleaned) < 2:
            raise ValueError('At least 2 valid video IDs required')
        return cleaned

class YTTLTools:
    """Tool implementations for YTTL MCP server."""
    
    def __init__(self, video_parser: VideoParser):
        self.video_parser = video_parser
    
    async def list_tools(self) -> List[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name="search_videos",
                description="Search through processed YouTube videos by content, title, or transcript. Returns ranked results with context snippets and relevance scores.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search terms to find in video content. Can be phrases or keywords."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-50)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        },
                        "include_transcript": {
                            "type": "boolean",
                            "description": "Include transcript content in search",
                            "default": True
                        },
                        "include_summary": {
                            "type": "boolean",
                            "description": "Include AI-generated summary in search",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_video_content",
                description="Get the complete content of a specific video including title, AI summary, and optionally the full transcript. Use this when you need detailed information about a specific video.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "Video ID (filename without .html extension, e.g., 'Y9kuAV_r_VA')"
                        },
                        "include_transcript": {
                            "type": "boolean",
                            "description": "Include full transcript in response (can be very long)",
                            "default": True
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="list_videos",
                description="List recently processed videos with metadata. Useful for browsing available content and discovering videos to analyze.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (1-100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20
                        },
                        "recent_days": {
                            "type": "integer",
                            "description": "Only show videos processed in the last N days (0 for all videos)",
                            "minimum": 0,
                            "default": 30
                        }
                    }
                }
            ),
            Tool(
                name="get_video_summary",
                description="Get only the AI-generated summary of a video without the full transcript. Faster and more concise than get_video_content for quick overviews.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "Video ID (filename without .html extension)"
                        }
                    },
                    "required": ["video_id"]
                }
            ),
            Tool(
                name="compare_videos",
                description="Compare key themes and content between multiple videos. Provides structured comparison data for analysis across videos.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of video IDs to compare (2-5 videos)",
                            "minItems": 2,
                            "maxItems": 5
                        }
                    },
                    "required": ["video_ids"]
                }
            ),
            Tool(
                name="get_cache_stats",
                description="Get statistics about the video cache and available content. Useful for understanding the scope of available videos.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls with proper validation."""
        try:
            logger.debug(f"Calling tool {name} with arguments: {arguments}")
            
            if name == "search_videos":
                params = SearchParams(**arguments)
                return await self._search_videos(params)
            elif name == "get_video_content":
                params = VideoContentParams(**arguments)
                return await self._get_video_content(params)
            elif name == "list_videos":
                params = ListVideosParams(**arguments)
                return await self._list_videos(params)
            elif name == "get_video_summary":
                video_id = arguments["video_id"].strip().replace('/', '').replace('\\', '')
                return await self._get_video_summary(video_id)
            elif name == "compare_videos":
                params = CompareVideosParams(**arguments)
                return await self._compare_videos(params)
            elif name == "get_cache_stats":
                return await self._get_cache_stats()
            else:
                raise YTTLMCPError(f"Unknown tool: {name}")
        
        except Exception as e:
            logger.error(f"Tool {name} error: {e}")
            if isinstance(e, (YTTLMCPError, InvalidSearchError)):
                raise
            raise YTTLMCPError(f"Tool execution failed: {e}")
    
    async def _search_videos(self, params: SearchParams) -> List[TextContent]:
        """Search videos implementation."""
        try:
            matches = await self.video_parser.search_videos(
                query=params.query,
                limit=params.limit,
                include_transcript=params.include_transcript,
                include_summary=params.include_summary
            )
            
            if not matches:
                return [TextContent(
                    type="text",
                    text=f"No videos found matching '{params.query}'\n\nTry:\n- Using different keywords\n- Checking spelling\n- Using broader search terms\n- Using the list_videos tool to see available content"
                )]
            
            # Format results with better structure
            result = f"# Search Results for '{params.query}'\n\n"
            result += f"Found **{len(matches)}** video(s) matching your search:\n\n"
            
            for i, match in enumerate(matches, 1):
                result += f"## {i}. {match['title']}\n\n"
                result += f"**Video ID:** `{match['video_id']}`\n"
                result += f"**URL:** {match['video_url']}\n"
                result += f"**Relevance Score:** {match.get('relevance_score', 0)}\n\n"
                
                # Show match locations with better formatting
                match_locations = []
                if match.get('title_match'):
                    match_locations.append("**Title**")
                if match.get('summary_matches'):
                    match_locations.append(f"**Summary** ({len(match['summary_matches'])} matches)")
                if match.get('transcript_matches'):
                    match_locations.append(f"**Transcript** ({len(match['transcript_matches'])} matches)")
                
                if match_locations:
                    result += f"**Found in:** {', '.join(match_locations)}\n\n"
                
                # Show best snippet with better formatting
                best_snippet = self._get_best_snippet(match)
                if best_snippet:
                    result += f"**Preview:**\n> {best_snippet}\n\n"
                
                result += "---\n\n"
            
            result += f"\n💡 **Tip:** Use `get_video_content(video_id)` to get the full content of any video above."
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise YTTLMCPError(f"Search failed: {e}")
    
    async def _get_video_content(self, params: VideoContentParams) -> List[TextContent]:
        """Get full video content."""
        video = await self.video_parser.get_video(params.video_id)
        if not video:
            # Provide helpful error message
            available_videos = await self.video_parser.get_recent_videos(limit=5)
            available_ids = [v.video_id for v in available_videos]
            error_msg = f"Video '{params.video_id}' not found."
            if available_ids:
                error_msg += f"\n\nAvailable video IDs include: {', '.join(available_ids)}"
                error_msg += f"\n\nUse the `list_videos` tool to see all available videos."
            else:
                error_msg += "\n\nNo videos found in the output directory. Make sure YTTL has processed some videos first."
            raise YTTLMCPError(error_msg)
        
        content = f"# {video.title}\n\n"
        content += f"**Video URL:** {video.url}\n"
        content += f"**Video ID:** `{video.video_id}`\n"
        content += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n"
        content += f"**File:** `{video.filepath.name}`\n\n"
        
        if video.summary_sections:
            content += "## 📋 AI-Generated Summary\n\n"
            for i, section in enumerate(video.summary_sections, 1):
                if len(video.summary_sections) > 1:
                    content += f"### Section {i}\n\n"
                content += f"{section}\n\n"
        else:
            content += "## 📋 AI-Generated Summary\n\n*No summary available for this video.*\n\n"
        
        if params.include_transcript and video.transcript_segments:
            content += "## 📝 Full Transcript\n\n"
            content += f"*{len(video.transcript_segments)} transcript segments*\n\n"
            
            for segment in video.transcript_segments:
                content += f"{segment}\n\n"
        elif params.include_transcript:
            content += "## 📝 Full Transcript\n\n*No transcript available for this video.*\n\n"
        
        return [TextContent(type="text", text=content)]
    
    async def _list_videos(self, params: ListVideosParams) -> List[TextContent]:
        """List recent videos."""
        videos = await self.video_parser.get_recent_videos(
            limit=params.limit,
            recent_days=params.recent_days
        )
        
        if not videos:
            time_filter = f" from the last {params.recent_days} days" if params.recent_days > 0 else ""
            return [TextContent(
                type="text",
                text=f"No videos found{time_filter}.\n\nMake sure:\n- YTTL has processed some videos\n- The output directory contains .html files\n- Try increasing the `recent_days` parameter or set it to 0 for all videos"
            )]
        
        time_filter = f" (last {params.recent_days} days)" if params.recent_days > 0 else ""
        result = f"# 📹 Available Videos{time_filter}\n\n"
        result += f"Found **{len(videos)}** video(s):\n\n"
        
        for i, video in enumerate(videos, 1):
            result += f"## {i}. {video.title}\n\n"
            result += f"**Video ID:** `{video.video_id}`\n"
            result += f"**URL:** {video.url}\n"
            result += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n"
            
            # Show content stats
            summary_count = len(video.summary_sections)
            transcript_count = len(video.transcript_segments)
            result += f"**Content:** {summary_count} summary section(s), {transcript_count} transcript segment(s)\n\n"
            
            # Show brief summary preview
            if video.summary_sections:
                preview = video.summary_sections[0][:200]
                if len(video.summary_sections[0]) > 200:
                    preview += "..."
                result += f"**Preview:** {preview}\n\n"
            
            result += "---\n\n"
        
        result += f"\n💡 **Tip:** Use `get_video_content(video_id)` or `get_video_summary(video_id)` to get detailed content for any video above."
        
        return [TextContent(type="text", text=result)]
    
    async def _get_video_summary(self, video_id: str) -> List[TextContent]:
        """Get video summary only."""
        video = await self.video_parser.get_video(video_id)
        if not video:
            raise YTTLMCPError(f"Video '{video_id}' not found. Use the `list_videos` tool to see available videos.")
        
        content = f"# {video.title}\n\n"
        content += f"**Video URL:** {video.url}\n"
        content += f"**Video ID:** `{video_id}`\n"
        content += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n\n"
        
        if video.summary_sections:
            content += "## 📋 AI-Generated Summary\n\n"
            for i, section in enumerate(video.summary_sections, 1):
                if len(video.summary_sections) > 1:
                    content += f"### Section {i}\n\n"
                content += f"{section}\n\n"
        else:
            content += "## 📋 AI-Generated Summary\n\n*No summary available for this video.*\n\n"
        
        content += f"\n💡 **Tip:** Use `get_video_content('{video_id}', include_transcript=true)` to also get the full transcript."
        
        return [TextContent(type="text", text=content)]
    
    async def _compare_videos(self, params: CompareVideosParams) -> List[TextContent]:
        """Compare multiple videos."""
        videos = []
        missing_videos = []
        
        for video_id in params.video_ids:
            video = await self.video_parser.get_video(video_id)
            if video:
                videos.append(video)
            else:
                missing_videos.append(video_id)
        
        if missing_videos:
            error_msg = f"Videos not found: {', '.join(missing_videos)}"
            if videos:
                error_msg += f"\n\nFound videos: {', '.join(v.video_id for v in videos)}"
            error_msg += "\n\nUse the `list_videos` tool to see available videos."
            raise YTTLMCPError(error_msg)
        
        if len(videos) < 2:
            raise YTTLMCPError("At least 2 valid videos required for comparison")
        
        result = f"# 🔍 Video Comparison\n\n"
        result += f"Comparing **{len(videos)}** videos:\n\n"
        
        # Create comparison table
        result += "| # | Title | Video ID | Processed |\n"
        result += "|---|-------|----------|----------|\n"
        for i, video in enumerate(videos, 1):
            title_short = video.title[:50] + "..." if len(video.title) > 50 else video.title
            result += f"| {i} | {title_short} | `{video.video_id}` | {video.modified_date.strftime('%Y-%m-%d')} |\n"
        
        result += "\n---\n\n"
        
        # Detailed comparison
        for i, video in enumerate(videos, 1):
            result += f"## Video {i}: {video.title}\n\n"
            result += f"**Video ID:** `{video.video_id}`\n"
            result += f"**URL:** {video.url}\n"
            result += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n\n"
            
            if video.summary_sections:
                result += "### 📋 Key Points\n\n"
                # Use first summary section as key points, truncated for comparison
                summary_preview = video.summary_sections[0]
                if len(summary_preview) > 400:
                    summary_preview = summary_preview[:400] + "..."
                result += f"{summary_preview}\n\n"
            else:
                result += "### 📋 Key Points\n\n*No summary available*\n\n"
            
            # Content statistics
            result += f"**Content Stats:** {len(video.summary_sections)} summary section(s), {len(video.transcript_segments)} transcript segment(s)\n\n"
            
            result += "---\n\n"
        
        result += "## 🎯 Analysis Framework\n\n"
        result += "Use the summaries above to identify:\n\n"
        result += "- **Common Themes:** What topics appear across multiple videos?\n"
        result += "- **Contrasting Views:** Where do the videos disagree or offer different perspectives?\n"
        result += "- **Complementary Info:** How do the videos build on each other?\n"
        result += "- **Unique Insights:** What does each video contribute that others don't?\n"
        result += "- **Key Differences:** How do approaches, conclusions, or focus areas differ?\n\n"
        
        result += f"💡 **Tip:** Use `get_video_content(video_id)` to get full details for any specific video in this comparison."
        
        return [TextContent(type="text", text=result)]
    
    async def _get_cache_stats(self) -> List[TextContent]:
        """Get cache statistics."""
        try:
            stats = await self.video_parser.get_cache_stats()
            
            result = "# 📊 Video Cache Statistics\n\n"
            result += f"**Total Videos:** {stats['total_videos']}\n"
            result += f"**Cache Size:** {stats['cache_size_mb']:.2f} MB\n"
            
            if stats['oldest_video']:
                result += f"**Oldest Video:** {stats['oldest_video'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            if stats['newest_video']:
                result += f"**Newest Video:** {stats['newest_video'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            result += f"\n**Output Directory:** `{self.video_parser.output_dir}`\n"
            result += f"**Cache Status:** {'Initialized' if self.video_parser._initialized else 'Not initialized'}\n\n"
            
            if stats['total_videos'] == 0:
                result += "⚠️ **No videos found.** Make sure YTTL has processed some videos and they are saved as .html files in the output directory.\n"
            else:
                result += f"✅ **Ready to search and analyze {stats['total_videos']} videos!**\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            raise YTTLMCPError(f"Failed to get cache statistics: {e}")
    
    def _get_best_snippet(self, match: Dict) -> str:
        """Get the best snippet from a search match."""
        # Prioritize summary matches, then transcript
        if match.get('summary_matches'):
            snippet = match['summary_matches'][0]
            return snippet[:200] + "..." if len(snippet) > 200 else snippet
        elif match.get('transcript_matches'):
            snippet = match['transcript_matches'][0]
            return snippet[:200] + "..." if len(snippet) > 200 else snippet
        return ""