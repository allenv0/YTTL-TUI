# YouTube Playlist Support Design

## Overview

This design adds YouTube playlist support to YTTL by extending the existing video processing pipeline to handle multiple videos. The solution detects playlist URLs, extracts individual video URLs using yt-dlp's playlist extraction capabilities, and processes each video using the existing single-video pipeline while organizing outputs in playlist-specific folders.

## Architecture

### Current Architecture
```
Single Video URL → Video Processing → HTML Output (out/ directory)
```

### Enhanced Architecture
```
Input URL → URL Type Detection → [Playlist Path] → Video List Extraction → Individual Video Processing → Organized Output
                                ↓                                                      ↓
                         [Single Video Path] ────────────────────────────────────────┘
```

## Components and Interfaces

### 1. URL Type Detection

A new function to determine if the input URL is a playlist:

```python
def is_playlist_url(url: str) -> bool:
    """Detect if URL is a YouTube playlist"""
    return 'playlist?list=' in url or '/playlist/' in url
```

### 2. Playlist Information Extraction

```python
@dataclass
class PlaylistInfo:
    title: str
    video_urls: List[str]
    video_count: int
    playlist_id: str

def extract_playlist_info(playlist_url: str) -> PlaylistInfo:
    """Extract playlist metadata and video URLs using yt-dlp"""
```

### 3. Folder Management

```python
def sanitize_folder_name(name: str) -> str:
    """Convert playlist title to filesystem-safe folder name"""

def create_playlist_folder(playlist_title: str) -> str:
    """Create and return path to playlist output folder"""
```

### 4. Batch Processing Pipeline

```python
def process_playlist(progress_hooks, playlist_url: str, **kwargs) -> PlaylistResult:
    """Process all videos in a playlist"""

@dataclass
class PlaylistResult:
    playlist_title: str
    total_videos: int
    successful_videos: List[str]
    failed_videos: List[Tuple[str, str]]  # (video_id, error_message)
    output_folder: str
```

## Data Flow

### 1. Input Processing
1. User provides URL via command line
2. System detects if URL is playlist or single video
3. Route to appropriate processing pipeline

### 2. Playlist Processing Flow
```
Playlist URL → yt-dlp playlist extraction → Video URL list → Sequential processing
                                                                      ↓
Playlist folder creation ← Progress tracking ← Individual video processing
```

### 3. Output Organization
```
out/
├── [playlist-name]/
│   ├── video1.html
│   ├── video2.html
│   └── video3.html
└── single-video.html (existing single videos)
```

## Implementation Details

### 1. CLI Integration

The existing CLI will be enhanced to handle playlists transparently:

```python
def main():
    # ... existing argument parsing ...
    
    if is_playlist_url(args.video_url):
        result = process_playlist(progress, **kwargs)
        print_playlist_summary(result)
    else:
        result = process_video(progress, **kwargs)
        # ... existing single video handling ...
```

### 2. Progress Tracking Enhancement

Extend the existing ProgressHooks to handle playlist-level progress:

```python
class PlaylistProgressHooks:
    def __init__(self, total_videos: int):
        self.total_videos = total_videos
        self.current_video = 0
        self.video_progress = ProgressHooks()
    
    def start_video(self, video_title: str):
        """Called when starting a new video"""
        
    def complete_video(self, success: bool):
        """Called when a video completes (success or failure)"""
```

### 3. Error Handling Strategy

- **Individual Video Failures**: Log error, continue with next video
- **Playlist Extraction Failures**: Fail fast with clear error message
- **Folder Creation Failures**: Attempt fallback folder names
- **Network Issues**: Retry with exponential backoff

### 4. yt-dlp Integration

Leverage yt-dlp's existing playlist capabilities:

```python
def extract_playlist_info(playlist_url: str) -> PlaylistInfo:
    ydl_opts = {
        'extract_flat': True,  # Don't download, just get metadata
        'quiet': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        
    return PlaylistInfo(
        title=playlist_info['title'],
        video_urls=[entry['url'] for entry in playlist_info['entries']],
        video_count=len(playlist_info['entries']),
        playlist_id=playlist_info['id']
    )
```

## File System Organization

### Folder Naming Strategy
1. Use playlist title as base name
2. Sanitize for filesystem compatibility:
   - Remove/replace invalid characters: `< > : " | ? * /`
   - Limit length to 100 characters
   - Handle Unicode characters appropriately
3. Handle name conflicts with numeric suffixes

### Example Output Structure
```
out/
├── My Favorite Tech Videos/
│   ├── dQw4w9WgXcQ.html
│   ├── abc123def45.html
│   └── xyz789uvw12.html
├── Cooking Tutorials (2)/  # Conflict resolution
│   ├── cook001.html
│   └── cook002.html
└── single-video.html
```

## Performance Considerations

### Sequential vs Parallel Processing
- **Phase 1**: Sequential processing (simpler, more reliable)
- **Future Enhancement**: Parallel processing with configurable concurrency

### Memory Management
- Process videos one at a time to avoid memory issues
- Clean up temporary files between videos
- Monitor memory usage for large playlists

### Network Efficiency
- Reuse yt-dlp instances where possible
- Implement retry logic for network failures
- Respect rate limits and implement backoff

## Error Recovery

### Partial Failure Handling
- Continue processing remaining videos if some fail
- Maintain detailed error log
- Provide summary of successful vs failed videos

### Resume Capability (Future Enhancement)
- Track processed videos
- Allow resuming interrupted playlist processing
- Skip already-processed videos

## User Experience

### Progress Display
```
Processing playlist: "My Favorite Tech Videos" (25 videos)
[████████████████████████████████████████] 15/25 (60%)
Current: "How to Build a Computer" (Video 15/25)
  Downloading captions: 100%
  Generating transcript: 80%
  Generating summaries: 40%

Completed: 14 successful, 1 failed
```

### Final Summary
```
Playlist processing complete!
Playlist: "My Favorite Tech Videos"
Total videos: 25
Successful: 23
Failed: 2
  - Video "Broken Link Example": Download failed
  - Video "Private Video": Access denied
Output folder: out/My Favorite Tech Videos/
```

## Testing Strategy

### Unit Tests
- URL detection logic
- Folder name sanitization
- Playlist info extraction
- Error handling scenarios

### Integration Tests
- End-to-end playlist processing
- Mixed success/failure scenarios
- Large playlist handling
- Network failure recovery

### Manual Testing
- Various playlist types (public, unlisted)
- Different playlist sizes
- Special characters in playlist names
- Network interruption scenarios

## Backward Compatibility

- Single video processing remains unchanged
- Existing CLI options work for both single videos and playlists
- Output structure for single videos unchanged
- Configuration files continue to work as before

## Future Enhancements

### Phase 2 Features
- Parallel video processing
- Resume interrupted processing
- Playlist-level summary generation
- Custom output templates
- Filtering options (date range, duration, etc.)

### Advanced Features
- Playlist update detection
- Incremental processing
- Cross-playlist deduplication
- Batch configuration management