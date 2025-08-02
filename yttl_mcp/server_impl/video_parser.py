"""Video parsing and caching for YTTL MCP server."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import aiofiles
from bs4 import BeautifulSoup
from pydantic import BaseModel

from .exceptions import ParsingError, CacheError

logger = logging.getLogger(__name__)

class VideoData(BaseModel):
    """Structured video data."""
    video_id: str
    title: str
    url: str
    summary_sections: List[str]
    transcript_segments: List[str]
    filepath: Path
    modified_date: datetime
    
    class Config:
        arbitrary_types_allowed = True

class VideoParser:
    """Handles video file parsing with caching."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self._cache: Dict[str, VideoData] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the parser and build initial cache."""
        async with self._lock:
            if self._initialized:
                return
            
            logger.info(f"Initializing video parser for {self.output_dir}")
            
            if not self.output_dir.exists():
                logger.warning(f"Output directory {self.output_dir} does not exist")
                self._initialized = True
                return
            
            try:
                # Build initial cache
                await self._refresh_cache()
                self._initialized = True
                logger.info(f"Initialized with {len(self._cache)} videos")
            except Exception as e:
                logger.error(f"Failed to initialize video parser: {e}")
                raise CacheError(f"Initialization failed: {e}")
    
    async def _refresh_cache(self):
        """Refresh the video cache."""
        try:
            html_files = list(self.output_dir.glob("*.html"))
            logger.debug(f"Found {len(html_files)} HTML files to process")
            
            if not html_files:
                logger.info("No HTML files found in output directory")
                return
            
            # Process files concurrently with a reasonable limit
            semaphore = asyncio.Semaphore(10)  # Limit concurrent file operations
            
            async def parse_with_semaphore(filepath):
                async with semaphore:
                    return await self._parse_video_file(filepath)
            
            tasks = [parse_with_semaphore(filepath) for filepath in html_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_parses = 0
            for result in results:
                if isinstance(result, VideoData):
                    self._cache[result.video_id] = result
                    self._cache_timestamps[result.video_id] = datetime.now()
                    successful_parses += 1
                elif isinstance(result, Exception):
                    logger.error(f"Error parsing video file: {result}")
            
            logger.info(f"Successfully parsed {successful_parses}/{len(html_files)} video files")
            
        except Exception as e:
            logger.error(f"Cache refresh failed: {e}")
            raise CacheError(f"Failed to refresh cache: {e}")
    
    async def _parse_video_file(self, filepath: Path) -> Optional[VideoData]:
        """Parse a single video file."""
        try:
            logger.debug(f"Parsing video file: {filepath}")
            
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content.strip():
                logger.warning(f"Empty file: {filepath}")
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract basic info
            title_elem = soup.find('h1')
            if not title_elem:
                logger.warning(f"No title found in {filepath}")
                title = f"Unknown Title ({filepath.stem})"
            else:
                title = title_elem.get_text().strip()
                if not title:
                    title = f"Untitled ({filepath.stem})"
            
            # Extract video URL
            video_link = ""
            if title_elem and title_elem.find('a'):
                try:
                    video_link = title_elem.find('a')['href']
                except (KeyError, TypeError):
                    logger.warning(f"Could not extract video URL from {filepath}")
            
            video_id = filepath.stem
            
            # Extract summary sections (excluding transcript)
            summary_sections = []
            sections = soup.find_all('section')
            
            for section in sections:
                h2 = section.find('h2')
                if h2 and 'transcript' in h2.get_text().lower():
                    continue  # Skip transcript section
                
                # Get section text, excluding the h3 timestamp headers
                section_copy = section.__copy__()
                for h3 in section_copy.find_all('h3'):
                    h3.decompose()
                
                section_text = section_copy.get_text().strip()
                if section_text and len(section_text) > 10:  # Filter out very short sections
                    summary_sections.append(section_text)
            
            # Extract transcript segments
            transcript_segments = []
            transcript_parts = soup.find_all('p', class_='transcript-segment')
            
            for segment in transcript_parts:
                segment_text = segment.get_text().strip()
                if segment_text:
                    # Clean up the segment text
                    lines = segment_text.split('\n')
                    clean_lines = [line.strip() for line in lines if line.strip()]
                    if clean_lines:
                        clean_text = ' '.join(clean_lines)
                        transcript_segments.append(clean_text)
            
            # Get file modification time
            try:
                modified_date = datetime.fromtimestamp(filepath.stat().st_mtime)
            except OSError as e:
                logger.warning(f"Could not get modification time for {filepath}: {e}")
                modified_date = datetime.now()
            
            video_data = VideoData(
                video_id=video_id,
                title=title,
                url=video_link,
                summary_sections=summary_sections,
                transcript_segments=transcript_segments,
                filepath=filepath,
                modified_date=modified_date
            )
            
            logger.debug(f"Successfully parsed {filepath}: {len(summary_sections)} summary sections, {len(transcript_segments)} transcript segments")
            return video_data
        
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            raise ParsingError(f"Failed to parse {filepath}: {e}")
    
    async def get_video(self, video_id: str) -> Optional[VideoData]:
        """Get a specific video by ID."""
        if not self._initialized:
            await self.initialize()
        
        # Check if we need to refresh this video
        filepath = self.output_dir / f"{video_id}.html"
        
        if filepath.exists():
            try:
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                cached_time = self._cache_timestamps.get(video_id)
                
                # Re-parse if file is newer than cache or not in cache
                if not cached_time or file_mtime > cached_time or video_id not in self._cache:
                    logger.debug(f"Refreshing video {video_id} from disk")
                    video_data = await self._parse_video_file(filepath)
                    if video_data:
                        self._cache[video_id] = video_data
                        self._cache_timestamps[video_id] = datetime.now()
            except Exception as e:
                logger.error(f"Error refreshing video {video_id}: {e}")
        
        return self._cache.get(video_id)
    
    async def get_recent_videos(self, limit: int = 20, recent_days: int = 30) -> List[VideoData]:
        """Get recently processed videos."""
        if not self._initialized:
            await self.initialize()
        
        videos = list(self._cache.values())
        
        if recent_days > 0:
            cutoff_date = datetime.now() - timedelta(days=recent_days)
            videos = [v for v in videos if v.modified_date >= cutoff_date]
        
        # Sort by modification date (newest first)
        videos.sort(key=lambda x: x.modified_date, reverse=True)
        
        return videos[:limit]
    
    async def search_videos(
        self, 
        query: str, 
        limit: int = 10,
        include_transcript: bool = True,
        include_summary: bool = True
    ) -> List[Dict]:
        """Search videos with enhanced matching."""
        if not self._initialized:
            await self.initialize()
        
        if not query.strip():
            raise InvalidSearchError("Search query cannot be empty")
        
        query_lower = query.lower()
        query_words = query_lower.split()
        matches = []
        
        logger.debug(f"Searching {len(self._cache)} videos for: '{query}'")
        
        for video in self._cache.values():
            match_data = {
                'video_id': video.video_id,
                'title': video.title,
                'video_url': video.url,
                'title_match': False,
                'summary_matches': [],
                'transcript_matches': [],
                'relevance_score': 0
            }
            
            # Check title match (exact phrase and individual words)
            title_lower = video.title.lower()
            if query_lower in title_lower:
                match_data['title_match'] = True
                match_data['relevance_score'] += 20  # High weight for exact phrase in title
            else:
                # Check for individual words in title
                title_word_matches = sum(1 for word in query_words if word in title_lower)
                if title_word_matches > 0:
                    match_data['title_match'] = True
                    match_data['relevance_score'] += title_word_matches * 5
            
            # Check summary matches
            if include_summary:
                for section in video.summary_sections:
                    section_lower = section.lower()
                    if query_lower in section_lower:
                        snippet = self._extract_snippet(section, query, query_lower)
                        match_data['summary_matches'].append(snippet)
                        match_data['relevance_score'] += 10  # Medium weight for summary matches
                    else:
                        # Check for individual words
                        word_matches = sum(1 for word in query_words if word in section_lower)
                        if word_matches > len(query_words) * 0.5:  # At least half the words match
                            snippet = self._extract_snippet(section, query_words[0], query_words[0])
                            match_data['summary_matches'].append(snippet)
                            match_data['relevance_score'] += word_matches * 2
            
            # Check transcript matches (limit to avoid too many results)
            if include_transcript:
                transcript_match_count = 0
                for segment in video.transcript_segments:
                    if transcript_match_count >= 5:  # Limit transcript matches per video
                        break
                    
                    segment_lower = segment.lower()
                    if query_lower in segment_lower:
                        match_data['transcript_matches'].append(segment)
                        match_data['relevance_score'] += 2  # Lower weight for transcript matches
                        transcript_match_count += 1
                    else:
                        # Check for individual words
                        word_matches = sum(1 for word in query_words if word in segment_lower)
                        if word_matches > len(query_words) * 0.7:  # Most words match
                            match_data['transcript_matches'].append(segment)
                            match_data['relevance_score'] += word_matches
                            transcript_match_count += 1
            
            # Only include if we found matches
            if (match_data['title_match'] or 
                match_data['summary_matches'] or 
                match_data['transcript_matches']):
                matches.append(match_data)
        
        # Sort by relevance score (highest first)
        matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.debug(f"Found {len(matches)} matches for '{query}'")
        return matches[:limit]
    
    def _extract_snippet(self, text: str, query: str, query_lower: str) -> str:
        """Extract a snippet around the search term."""
        text_lower = text.lower()
        match_pos = text_lower.find(query_lower)
        
        if match_pos == -1:
            # If exact phrase not found, return beginning of text
            return text[:150] + "..." if len(text) > 150 else text
        
        # Extract context around the match
        snippet_length = 200
        start = max(0, match_pos - snippet_length // 3)
        end = min(len(text), match_pos + len(query) + snippet_length * 2 // 3)
        
        snippet = text[start:end].strip()
        
        # Clean up snippet boundaries
        if start > 0:
            # Try to start at word boundary
            space_pos = snippet.find(' ')
            if space_pos > 0 and space_pos < 20:
                snippet = snippet[space_pos + 1:]
            snippet = "..." + snippet
        
        if end < len(text):
            # Try to end at word boundary
            last_space = snippet.rfind(' ')
            if last_space > len(snippet) - 20:
                snippet = snippet[:last_space]
            snippet = snippet + "..."
        
        return snippet
    
    async def get_cache_stats(self) -> Dict:
        """Get cache statistics for debugging."""
        if not self._initialized:
            await self.initialize()
        
        return {
            'total_videos': len(self._cache),
            'cache_size_mb': sum(
                len(str(video.summary_sections)) + len(str(video.transcript_segments)) 
                for video in self._cache.values()
            ) / (1024 * 1024),
            'oldest_video': min(
                (video.modified_date for video in self._cache.values()), 
                default=None
            ),
            'newest_video': max(
                (video.modified_date for video in self._cache.values()), 
                default=None
            )
        }