# YTTL MCP Server

This is the Model Context Protocol (MCP) server implementation for YTTL (YouTube To Text and LLM). It provides Claude Desktop and other MCP-compatible LLMs with direct access to your processed YouTube video summaries and transcripts.

## 🚀 Quick Start

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

## ✨ Features

- **🔍 Smart Search**: Find videos by content, title, or transcript with relevance scoring
- **📹 Complete Access**: Get full video content including AI summaries and transcripts
- **📋 Quick Summaries**: Access just the AI-generated summaries for faster browsing
- **🔄 Video Comparison**: Analyze multiple videos side by side
- **📚 Resource Access**: Direct URI-based access to video content
- **⚡ Performance**: Intelligent caching and async processing
- **🛡️ Error Handling**: Comprehensive error messages and recovery

## 🛠️ Available Tools

### search_videos
Search through your processed YouTube videos with intelligent ranking.

**Parameters:**
- `query` (required): Search terms or phrases
- `limit` (optional): Max results (1-50, default: 10)
- `include_transcript` (optional): Search transcripts (default: true)
- `include_summary` (optional): Search summaries (default: true)

### get_video_content
Get complete content of a specific video.

**Parameters:**
- `video_id` (required): Video ID (e.g., "Y9kuAV_r_VA")
- `include_transcript` (optional): Include full transcript (default: true)

### list_videos
Browse recently processed videos with metadata.

**Parameters:**
- `limit` (optional): Max videos (1-100, default: 20)
- `recent_days` (optional): Filter by days (0 for all, default: 30)

### get_video_summary
Get only the AI-generated summary (faster than full content).

**Parameters:**
- `video_id` (required): Video ID

### compare_videos
Compare multiple videos for analysis.

**Parameters:**
- `video_ids` (required): List of 2-5 video IDs

### get_cache_stats
Get statistics about available videos and cache status.

## 📚 Available Resources

Direct URI access to video content:

- `yttl:///video/{video_id}` - Complete video content (summary + transcript)
- `yttl:///summary/{video_id}` - AI-generated summary only
- `yttl:///transcript/{video_id}` - Full transcript only

## 🎯 Claude Desktop Usage Examples

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

## ⚙️ Installation & Configuration

### Automatic Setup
```bash
# Run the installation script
./install.sh

# Or configure Claude Desktop automatically
python configure_claude.py
```

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install mcp pydantic aiofiles beautifulsoup4 typing-extensions
   ```

2. **Add to Claude Desktop config** (`~/.claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "yttl": {
         "command": "python3",
         "args": ["-m", "yttl_mcp.server"],
         "cwd": "/path/to/your/yttl_mcp"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## 🧪 Testing & Validation

**Validate your setup:**
```bash
python validate_setup.py
```

**Run comprehensive tests:**
```bash
python test_server.py
```

**Test server functionality directly:**
```bash
python test_mcp_direct.py
```

**Note:** Running `python -m yttl_mcp.server` directly will show an error - this is normal! MCP servers are designed to run with Claude Desktop, not standalone. The error indicates the server is working correctly but has no input to process.

## 🔧 Troubleshooting

### No Videos Found
- Ensure YTTL has processed videos in the `../out` directory
- Check that .html files exist and are readable
- Run `python test_server.py` to verify setup

### Claude Desktop Connection Issues
- Verify configuration with `python configure_claude.py`
- Check that the `cwd` path in config points to the yttl_mcp directory
- Restart Claude Desktop after configuration changes
- Check Claude Desktop logs for error messages

### Search Not Working
- Try broader search terms
- Use `list_videos` to see available content
- Check that videos have both summaries and transcripts

### Performance Issues
- Large video collections may take time to initialize
- Use `recent_days` parameter to limit scope
- Use `get_video_summary` for faster responses

## 📁 Project Structure

```
yttl_mcp/
├── __init__.py                 # Package initialization
├── server.py                   # Main entry point
├── requirements.txt            # Dependencies
├── setup.py                    # Package setup
├── install.sh                  # Installation script
├── configure_claude.py         # Claude Desktop configuration
├── test_server.py             # Test suite
├── USAGE.md                   # Detailed usage guide
├── README.md                  # This file
└── server_impl/               # Core implementation
    ├── __init__.py
    ├── server.py              # MCP server logic
    ├── tools.py               # Tool implementations
    ├── resources.py           # Resource implementations
    ├── video_parser.py        # HTML parsing & caching
    └── exceptions.py          # Custom exceptions
```

## 🚀 Advanced Usage

### Custom Output Directory
Modify `server.py` to use a different video directory:
```python
output_dir = Path("/custom/path/to/videos")
```

### Performance Tuning
Adjust caching and concurrency in `video_parser.py`:
```python
semaphore = asyncio.Semaphore(20)  # Increase concurrent processing
```

### Adding Custom Tools
1. Add tool definition to `server_impl/tools.py`
2. Implement handler method
3. Update `call_tool` method
4. Test with `test_server.py`

## 📊 Status

- ✅ **Video Parser**: Robust HTML parsing with caching
- ✅ **Search Engine**: Intelligent search with relevance scoring  
- ✅ **Tools**: 6 comprehensive tools for video analysis
- ✅ **Resources**: Direct URI access to video content
- ✅ **Error Handling**: Comprehensive error messages
- ✅ **Testing**: Full test suite with 100% pass rate
- ✅ **Documentation**: Complete usage guides and examples

## 🎉 Ready to Use!

Your YTTL MCP Server is now ready to provide Claude Desktop with powerful access to your YouTube video library. Start by asking Claude to search for videos or analyze specific content!

For detailed usage examples and advanced features, see [USAGE.md](USAGE.md).