# YTTL MCP Server Usage Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd yttl_mcp
   pip install -r requirements.txt
   ```

2. **Test the server:**
   ```bash
   python test_server.py
   ```

3. **Configure Claude Desktop:**
   ```bash
   python configure_claude.py
   ```

4. **Restart Claude Desktop and start using!**

## Available Tools

### 🔍 search_videos
Search through your processed YouTube videos.

**Parameters:**
- `query` (required): Search terms
- `limit` (optional): Max results (1-50, default: 10)
- `include_transcript` (optional): Include transcript in search (default: true)
- `include_summary` (optional): Include summary in search (default: true)

**Example:**
```
Search for videos about "startup advice" with a limit of 5 results
```

### 📹 get_video_content
Get complete content of a specific video.

**Parameters:**
- `video_id` (required): Video ID (e.g., "Y9kuAV_r_VA")
- `include_transcript` (optional): Include full transcript (default: true)

**Example:**
```
Get the full content of video Y9kuAV_r_VA including transcript
```

### 📋 list_videos
Browse recently processed videos.

**Parameters:**
- `limit` (optional): Max videos to return (1-100, default: 20)
- `recent_days` (optional): Only show videos from last N days (0 for all, default: 30)

**Example:**
```
List the 10 most recent videos from the last 7 days
```

### 📄 get_video_summary
Get only the AI-generated summary (faster than full content).

**Parameters:**
- `video_id` (required): Video ID

**Example:**
```
Get just the summary of video Y9kuAV_r_VA
```

### 🔄 compare_videos
Compare multiple videos side by side.

**Parameters:**
- `video_ids` (required): List of 2-5 video IDs

**Example:**
```
Compare videos Y9kuAV_r_VA and ABC123XYZ to find common themes
```

### 📊 get_cache_stats
Get statistics about available videos.

**Example:**
```
Show me statistics about the video cache
```

## Available Resources

Resources provide direct URI-based access to video content:

- `yttl://video/{video_id}` - Complete video content
- `yttl://summary/{video_id}` - Summary only  
- `yttl://transcript/{video_id}` - Transcript only

## Claude Desktop Usage Examples

### Basic Search
```
"Find videos about Peter Thiel's investment philosophy"
```

### Detailed Analysis
```
"Get the full content of video Y9kuAV_r_VA and analyze the main arguments"
```

### Cross-Video Analysis
```
"Compare the last 3 videos about startups and identify common themes"
```

### Content Discovery
```
"Show me the most recent videos and help me pick one to analyze"
```

## Troubleshooting

### No Videos Found
- Make sure YTTL has processed some videos
- Check that .html files exist in the `../out` directory
- Run `python test_server.py` to verify setup

### Claude Desktop Not Connecting
- Verify configuration with `python configure_claude.py`
- Check that the `cwd` path in config is correct
- Restart Claude Desktop after configuration changes
- Check Claude Desktop logs for error messages

### Search Not Working
- Try broader search terms
- Use `list_videos` to see what content is available
- Check that videos have both summaries and transcripts

### Performance Issues
- Large video collections may take time to initialize
- Consider using `recent_days` parameter to limit scope
- Use `get_video_summary` instead of `get_video_content` for faster responses

## Advanced Configuration

### Custom Output Directory
Modify `server.py` to point to a different output directory:

```python
# In server.py, change this line:
output_dir = Path(__file__).parent.parent / "out"

# To your custom path:
output_dir = Path("/path/to/your/videos")
```

### Logging Configuration
Adjust logging level in `server.py`:

```python
# For debug logging:
logging.basicConfig(level=logging.DEBUG, ...)

# For minimal logging:
logging.basicConfig(level=logging.WARNING, ...)
```

### Performance Tuning
Modify `video_parser.py` for better performance:

```python
# Increase concurrent file processing:
semaphore = asyncio.Semaphore(20)  # Default: 10

# Adjust search result limits:
return matches[:limit]  # Customize as needed
```

## Development

### Running Tests
```bash
python test_server.py
```

### Manual Server Testing
```bash
python -m yttl_mcp.server
```

### Adding New Tools
1. Add tool definition to `mcp/tools.py`
2. Implement handler method
3. Update `call_tool` method
4. Test with `test_server.py`

### Adding New Resources
1. Add resource type to `mcp/resources.py`
2. Implement formatting method
3. Update `get_resource` method
4. Test resource access

## Support

If you encounter issues:

1. Run the test suite: `python test_server.py`
2. Check the logs when running the server
3. Verify your Claude Desktop configuration
4. Make sure your YTTL output directory has .html files

The MCP server provides detailed error messages to help diagnose issues.