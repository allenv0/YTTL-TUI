# YTTL (YouTube To Text and LLM) - Architecture Overview

## System Overview

## Core Components

### 1. Main Modules

#### 1.1 yttl.py
This is the core module containing the main functionality:

- **Audio Processing**:
  - `LocalWhisper`: Handles local Whisper-based audio transcription
  - `OpenaiWhisper`: Handles cloud-based Whisper transcription via OpenAI API
  - Supports chunked processing of long videos

- **LLM Providers**:
  - `LocalLLM`: Runs LLM models locally using llama.cpp
  - `ChatgptLLM`: Interface for ChatGPT API
  - `HuggingchatLLM`: Interface for HuggingChat models
  - `OpenaiLLM`: Generic OpenAI-compatible API interface (supports Groq)

- **Core Functions**:
  - `process_video`: Main entry point for video processing
  - `generate_captions`: Generates captions from audio
  - `summarize_hour`: Handles summarization of hour-long segments
  - `remove_sponsored`: Integrates with SponsorBlock to filter out sponsored content

#### 1.2 cli.py
Command-line interface for the application:
- Parses command line arguments
- Manages configuration loading
- Handles progress reporting
- Manages output file generation and opening

### 2. Extension (Browser Integration)

Located in the `extension/` directory:
- `manifest.json`: Chrome extension configuration
- `background.js`: Handles extension background processes
- `progress.html/js`: UI for showing summarization progress
- `summary.html`: Displays the generated summary

### 3. Build and Dependencies

- **Build System**:
  - Uses CMake for native extensions
  - Python package management via pyproject.toml

- **Key Dependencies**:
  - `whisper_cpp`: For local Whisper transcription
  - `llama_cpp`: For local LLM inference
  - `yt-dlp`: For YouTube video handling
  - `requests`: For API calls
  - `jinja2`: For HTML template rendering
  - `tqdm`: For progress bars

## Data Flow

1. **Input Processing**:
   - User provides a YouTube URL via CLI or browser extension
   - System extracts video metadata and available captions

2. **Audio Processing Path**:
   - If no captions available, downloads audio
   - Splits audio into manageable chunks
   - Processes each chunk through Whisper (local or cloud)
   - Combines transcript segments

3. **Content Filtering**:
   - Applies SponsorBlock filters if enabled
   - Removes specified segments (sponsors, intros, etc.)

4. **Summarization**:
   - Splits transcript into logical sections
   - Processes each section through selected LLM
   - Combines section summaries into final output

5. **Output Generation**:
   - Renders HTML output with timestamps and summaries
   - Opens in default browser

## Configuration

The system supports configuration through:
1. Command-line arguments
2. Configuration file
3. Environment variables

Key configuration options include:
- LLM provider selection (local, ChatGPT, HuggingChat, OpenAI)
- Whisper model selection
- SponsorBlock filters
- API keys for cloud services
- Verbosity levels

## Extension Architecture

The browser extension provides:
- Context menu integration for YouTube videos
- Background processing of video URLs
- Progress tracking
- Summary display in a new tab

## Build and Deployment

### Local Development
1. Install dependencies: `pip install -e .`
2. Build native extensions: `python setup.py build_ext --inplace`
3. Run: `summarize <youtube-url>`

### Extension Installation
1. Load unpacked extension in Chrome/Edge
2. Right-click on YouTube videos to access summarization

## Performance Considerations

- **Local Processing**:
  - Uses CPU/GPU acceleration where available
  - Chunks audio to manage memory usage
  - Supports batch processing of long videos

- **Cloud Services**:
  - Fallback to cloud APIs when local processing is not feasible
  - Configurable API endpoints for self-hosted services

## Security

- API keys can be provided via environment variables or config files
- Local processing option for sensitive content
- No persistent storage of video content

## Limitations

- Requires significant local resources for large models
- Cloud API usage may incur costs
- Accuracy depends on the quality of source captions and selected models

## Future Enhancements

1. Support for more video platforms
2. Additional summarization styles
3. Batch processing of multiple videos
4. Enhanced configuration options
5. Improved error handling and recovery
