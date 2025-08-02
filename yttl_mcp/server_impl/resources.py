"""Resource implementations for YTTL MCP server."""

import logging
from typing import List
from mcp.types import Resource, ReadResourceResult, TextContent, TextResourceContents, AnyUrl
from .video_parser import VideoParser
from .exceptions import YTTLMCPError

logger = logging.getLogger(__name__)

class YTTLResources:
    """Resource implementations for YTTL MCP server."""
    
    def __init__(self, video_parser: VideoParser):
        self.video_parser = video_parser
    
    async def list_resources(self) -> List[Resource]:
        """List available resources."""
        if not self.video_parser._initialized:
            await self.video_parser.initialize()
        
        resources = []
        
        logger.debug(f"Listing resources for {len(self.video_parser._cache)} videos")
        
        for video_id, video_data in self.video_parser._cache.items():
            # Truncate long titles for resource names
            title_display = video_data.title
            if len(title_display) > 60:
                title_display = title_display[:57] + "..."
            
            resources.extend([
                Resource(
                    uri=AnyUrl(f"yttl:///video/{video_id}"),
                    name=f"📹 {title_display}",
                    description=f"Complete content (summary + transcript) for video {video_id}",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri=AnyUrl(f"yttl:///summary/{video_id}"),
                    name=f"📋 Summary: {title_display}",
                    description=f"AI-generated summary only for video {video_id}",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri=AnyUrl(f"yttl:///transcript/{video_id}"),
                    name=f"📝 Transcript: {title_display}",
                    description=f"Full transcript only for video {video_id}",
                    mimeType="text/plain"
                )
            ])
        
        # Sort resources by video modification date (newest first)
        def get_video_date(resource):
            # Extract video_id from URI path
            uri_str = str(resource.uri)
            video_id = uri_str.split('/')[-1]
            video_data = self.video_parser._cache.get(video_id)
            return video_data.modified_date if video_data else None
        
        resources.sort(key=get_video_date, reverse=True)
        
        logger.debug(f"Generated {len(resources)} resources")
        return resources
    
    async def get_resource(self, uri) -> ReadResourceResult:
        """Get a specific resource."""
        # Handle both string and URL object types
        if hasattr(uri, 'scheme') and hasattr(uri, 'path'):
            # It's a URL object
            uri_str = str(uri)
            scheme = uri.scheme
            path = uri.path
        else:
            # It's a string
            uri_str = str(uri)
            if "://" in uri_str:
                scheme, rest = uri_str.split("://", 1)
                path = "/" + rest.split("/", 1)[1] if "/" in rest else ""
            else:
                raise YTTLMCPError(f"Invalid URI format: {uri_str}")
        
        logger.debug(f"Getting resource: {uri_str} (scheme: {scheme}, path: {path})")
        
        if scheme != "yttl":
            raise YTTLMCPError(f"Invalid URI scheme. Expected 'yttl', got: {scheme}")
        
        try:
            # Parse path like "/video/Y9kuAV_r_VA" -> ["video", "Y9kuAV_r_VA"]
            # Remove leading slash and split
            path_clean = path.lstrip("/")
            if not path_clean:
                raise YTTLMCPError("Empty path in URI")
            
            path_parts = path_clean.split("/")
        except Exception as e:
            raise YTTLMCPError(f"Failed to parse URI path: {uri_str} - {e}")
        
        if len(path_parts) != 2:
            raise YTTLMCPError(f"Invalid URI format. Expected 'yttl://type/video_id', got: {uri_str} (parsed parts: {path_parts})")
        
        resource_type, video_id = path_parts
        
        # Validate resource type
        if resource_type not in ["video", "summary", "transcript"]:
            raise YTTLMCPError(f"Unknown resource type: {resource_type}. Valid types: video, summary, transcript")
        
        # Clean video ID for security
        video_id = video_id.strip().replace('/', '').replace('\\', '')
        if not video_id:
            raise YTTLMCPError("Video ID cannot be empty")
        
        video = await self.video_parser.get_video(video_id)
        if not video:
            # Provide helpful error with available videos
            available_videos = await self.video_parser.get_recent_videos(limit=5)
            available_ids = [v.video_id for v in available_videos]
            error_msg = f"Video '{video_id}' not found."
            if available_ids:
                error_msg += f" Available videos include: {', '.join(available_ids)}"
            raise YTTLMCPError(error_msg)
        
        try:
            if resource_type == "video":
                content = self._format_full_video(video)
            elif resource_type == "summary":
                content = self._format_summary(video)
            elif resource_type == "transcript":
                content = self._format_transcript(video)
            
            return ReadResourceResult(
                contents=[TextResourceContents(uri=uri_str, text=content, mimeType="text/markdown")]
            )
            
        except Exception as e:
            logger.error(f"Error formatting resource {uri}: {e}")
            raise YTTLMCPError(f"Failed to format resource: {e}")
    
    def _format_full_video(self, video) -> str:
        """Format complete video content."""
        content = f"# {video.title}\n\n"
        content += f"**Video URL:** {video.url}\n"
        content += f"**Video ID:** `{video.video_id}`\n"
        content += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n"
        content += f"**File:** `{video.filepath.name}`\n\n"
        
        # Content statistics
        summary_count = len(video.summary_sections)
        transcript_count = len(video.transcript_segments)
        content += f"**Content Overview:** {summary_count} summary section(s), {transcript_count} transcript segment(s)\n\n"
        
        content += "---\n\n"
        
        if video.summary_sections:
            content += "## 📋 AI-Generated Summary\n\n"
            for i, section in enumerate(video.summary_sections, 1):
                if len(video.summary_sections) > 1:
                    content += f"### Summary Section {i}\n\n"
                content += f"{section}\n\n"
        else:
            content += "## 📋 AI-Generated Summary\n\n*No summary available for this video.*\n\n"
        
        if video.transcript_segments:
            content += "## 📝 Full Transcript\n\n"
            content += f"*{len(video.transcript_segments)} transcript segments*\n\n"
            
            for i, segment in enumerate(video.transcript_segments, 1):
                # Add segment numbers for long transcripts
                if len(video.transcript_segments) > 10:
                    content += f"**Segment {i}:**\n"
                content += f"{segment}\n\n"
        else:
            content += "## 📝 Full Transcript\n\n*No transcript available for this video.*\n\n"
        
        return content
    
    def _format_summary(self, video) -> str:
        """Format video summary only."""
        content = f"# {video.title}\n\n"
        content += f"**Video URL:** {video.url}\n"
        content += f"**Video ID:** `{video.video_id}`\n"
        content += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n\n"
        
        if video.summary_sections:
            content += "## 📋 AI-Generated Summary\n\n"
            for i, section in enumerate(video.summary_sections, 1):
                if len(video.summary_sections) > 1:
                    content += f"### Summary Section {i}\n\n"
                content += f"{section}\n\n"
            
            # Add helpful note
            if video.transcript_segments:
                content += f"\n---\n\n💡 **Note:** This video also has a full transcript with {len(video.transcript_segments)} segments. "
                content += f"Use `yttl://transcript/{video.video_id}` to access it.\n"
        else:
            content += "## 📋 AI-Generated Summary\n\n"
            content += "*No summary available for this video.*\n\n"
            
            if video.transcript_segments:
                content += f"However, this video has a full transcript with {len(video.transcript_segments)} segments. "
                content += f"Use `yttl://transcript/{video.video_id}` to access it.\n"
        
        return content
    
    def _format_transcript(self, video) -> str:
        """Format video transcript only."""
        content = f"# Transcript: {video.title}\n\n"
        content += f"**Video URL:** {video.url}\n"
        content += f"**Video ID:** `{video.video_id}`\n"
        content += f"**Processed:** {video.modified_date.strftime('%Y-%m-%d at %H:%M:%S')}\n\n"
        
        if not video.transcript_segments:
            content += "## 📝 Transcript\n\n"
            content += "*No transcript available for this video.*\n\n"
            
            if video.summary_sections:
                content += f"However, this video has an AI-generated summary. "
                content += f"Use `yttl://summary/{video.video_id}` to access it.\n"
            
            return content
        
        content += f"## 📝 Full Transcript\n\n"
        content += f"*{len(video.transcript_segments)} transcript segments*\n\n"
        content += "---\n\n"
        
        for i, segment in enumerate(video.transcript_segments, 1):
            # Add segment markers for very long transcripts
            if len(video.transcript_segments) > 20:
                content += f"**[Segment {i}]**\n"
            
            content += f"{segment}\n\n"
        
        content += "---\n\n"
        
        if video.summary_sections:
            content += f"💡 **Tip:** This video also has an AI-generated summary. "
            content += f"Use `yttl://summary/{video.video_id}` for a concise overview.\n"
        
        return content