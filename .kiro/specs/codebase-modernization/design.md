# Design Document

## Overview

This design outlines the modernization and optimization of the YTTL codebase. The current tool provides YouTube video summarization using various LLM providers and Whisper transcription, but requires significant updates to dependencies, code structure, performance, and maintainability. The modernized version will maintain backward compatibility while introducing modern Python practices, improved performance, and enhanced user experience.

## Architecture

### High-Level Architecture

The modernized system will maintain the core architecture while improving each component:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI/Extension │────│  Core Engine    │────│   LLM Providers │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Audio Processing│
                       │   & Whisper     │
                       └─────────────────┘
                              │
                       ┌─────────────────┐
                       │  Output Engine  │
                       │ & File Manager  │
                       └─────────────────┘
```

### Dependency Updates

**Current vs Target Versions:**
- Python: 3.11+ → 3.12+ (latest LTS)
- llama-cpp-python: 0.2.64 → 0.3.x (latest with GPU optimizations)
- yt-dlp: 2024.4.9 → 2024.12.x (latest)
- huggingface-hub: 0.22.1 → 0.26.x (latest)
- whisper-cpp-python: 0.1 → latest optimized version
- Jinja2: 3.1.3 → 3.1.x (latest)
- requests: 2.31.0 → 2.32.x (latest)

**New Dependencies:**
- pydantic: 2.x for configuration management
- rich: for enhanced CLI output
- asyncio/aiohttp: for async operations
- pytest: for comprehensive testing
- ruff: for fast linting
- black: for code formatting
- mypy: for type checking

## Components and Interfaces

### 1. Configuration Management System

**New Configuration Architecture:**
```python
from pydantic import BaseSettings, Field
from typing import Optional, List
from enum import Enum

class LLMProvider(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    GROQ = "groq"
    CHATGPT = "chatgpt"
    HUGGINGCHAT = "huggingchat"

class WhisperProvider(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"

class AppConfig(BaseSettings):
    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.LOCAL
    local_model_repo: str = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
    local_model_file: str = "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
    
    # Whisper Configuration
    whisper_provider: WhisperProvider = WhisperProvider.LOCAL
    whisper_model: str = "base.en"
    
    # Performance Settings
    max_workers: int = Field(default=4, ge=1, le=16)
    chunk_size: int = Field(default=300, ge=60, le=3600)
    gpu_acceleration: bool = True
    
    # Output Settings
    output_format: str = "html"
    output_directory: str = "out"
    
    class Config:
        env_prefix = "YTTL_"
        case_sensitive = False
```

### 2. Enhanced Audio Processing

**Optimized Audio Pipeline:**
```python
from dataclasses import dataclass
from typing import AsyncIterator, Protocol
import asyncio

@dataclass
class AudioSegment:
    start_time: float
    end_time: float
    audio_data: bytes
    sample_rate: int = 16000

class AudioProcessor(Protocol):
    async def process_chunk(self, chunk: AudioSegment) -> List[TranscriptSegment]:
        ...

class OptimizedWhisperProcessor:
    def __init__(self, model_name: str, gpu_enabled: bool = True):
        self.model_name = model_name
        self.gpu_enabled = gpu_enabled
        self._model = None
    
    async def initialize(self):
        """Lazy initialization of Whisper model"""
        if self._model is None:
            self._model = await self._load_model()
    
    async def process_stream(self, audio_stream: AsyncIterator[AudioSegment]) -> AsyncIterator[TranscriptSegment]:
        """Process audio stream with async batching"""
        batch = []
        async for segment in audio_stream:
            batch.append(segment)
            if len(batch) >= self.batch_size:
                results = await self._process_batch(batch)
                for result in results:
                    yield result
                batch = []
        
        if batch:
            results = await self._process_batch(batch)
            for result in results:
                yield result
```

### 3. Modern LLM Provider System

**Unified LLM Interface:**
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    stream: bool = False

class LLMResponse(BaseModel):
    content: str
    tokens_used: int
    model: str
    finish_reason: str

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Generate streaming response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available"""
        pass

class ModernLocalLLM(BaseLLMProvider):
    def __init__(self, config: LocalLLMConfig):
        self.config = config
        self._llama = None
    
    async def initialize(self):
        """Async initialization with proper resource management"""
        if self._llama is None:
            model_path = await self._download_model()
            self._llama = await asyncio.to_thread(
                self._create_llama_instance, model_path
            )
```

### 4. Enhanced Progress and Error Handling

**Rich Progress System:**
```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.logging import RichHandler
import logging
from contextlib import asynccontextmanager

class ModernProgressTracker:
    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
    
    @asynccontextmanager
    async def track_phase(self, description: str, total: int = 100):
        task_id = self.progress.add_task(description, total=total)
        try:
            yield ProgressUpdater(self.progress, task_id)
        finally:
            self.progress.remove_task(task_id)

class EnhancedErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(RichHandler(rich_tracebacks=True))
    
    async def handle_with_retry(self, operation, max_retries: int = 3):
        """Handle operations with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
```

### 5. Multi-Format Output System

**Flexible Output Engine:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

class OutputFormatter(ABC):
    @abstractmethod
    async def format(self, summary_data: SummaryData) -> str:
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        pass

class HTMLFormatter(OutputFormatter):
    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path or Path(__file__).parent / "templates" / "modern.html"
    
    async def format(self, summary_data: SummaryData) -> str:
        template = await self._load_template()
        return template.render(
            title=summary_data.title,
            summaries=summary_data.summaries,
            metadata=summary_data.metadata,
            timestamp=datetime.now().isoformat()
        )

class MarkdownFormatter(OutputFormatter):
    async def format(self, summary_data: SummaryData) -> str:
        lines = [f"# {summary_data.title}\n"]
        lines.append(f"**Duration:** {summary_data.duration}\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for i, hour_summary in enumerate(summary_data.summaries):
            lines.append(f"## Hour {i+1}: {hour_summary.timestamp}\n")
            lines.append(f"{hour_summary.overall}\n")
            
            for j, section in enumerate(hour_summary.parts):
                if section:
                    lines.append(f"### {hour_summary.timestamp + timedelta(minutes=j*5)}\n")
                    lines.append(f"{section}\n")
        
        return "\n".join(lines)

class OutputManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.formatters = {
            "html": HTMLFormatter(),
            "markdown": MarkdownFormatter(),
            "json": JSONFormatter()
        }
    
    async def save_summary(self, summary_data: SummaryData) -> Path:
        formatter = self.formatters[self.config.output_format]
        content = await formatter.format(summary_data)
        
        output_path = Path(self.config.output_directory) / f"{summary_data.video_id}.{formatter.get_file_extension()}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        return output_path
```

## Data Models

### Enhanced Data Structures

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

@dataclass
class TranscriptSegment:
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None

class VideoMetadata(BaseModel):
    video_id: str
    title: str
    duration: int
    url: str
    extractor: str
    upload_date: Optional[str] = None
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    description: Optional[str] = None

class SectionSummary(BaseModel):
    timestamp: str
    content: str
    confidence_score: Optional[float] = None
    key_topics: List[str] = Field(default_factory=list)

class HourSummary(BaseModel):
    hour_index: int
    timestamp: str
    overall_summary: str
    sections: List[SectionSummary]
    total_sections: int

class SummaryData(BaseModel):
    video_id: str
    title: str
    duration: int
    url: str
    metadata: VideoMetadata
    summaries: List[HourSummary]
    generation_time: datetime
    model_info: Dict[str, Any]
    processing_stats: Dict[str, Any]
```

## Error Handling

### Comprehensive Error Management

```python
from enum import Enum
from typing import Optional, Dict, Any
import traceback

class ErrorCategory(Enum):
    NETWORK = "network"
    MODEL = "model"
    AUDIO = "audio"
    CONFIG = "config"
    SYSTEM = "system"

class YttlError(Exception):
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.category = category
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()

class ErrorHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_counts: Dict[ErrorCategory, int] = {}
    
    async def handle_error(self, error: Exception, context: str) -> bool:
        """Handle error and return whether operation should be retried"""
        if isinstance(error, YttlError):
            self.error_counts[error.category] = self.error_counts.get(error.category, 0) + 1
            
            self.logger.error(
                f"[{error.category.value}] {error.message}",
                extra={
                    "context": context,
                    "details": error.details,
                    "recoverable": error.recoverable
                }
            )
            
            return error.recoverable and self.error_counts[error.category] < 3
        else:
            self.logger.error(f"Unexpected error in {context}: {error}", exc_info=True)
            return False
    
    def get_user_friendly_message(self, error: Exception) -> str:
        """Convert technical errors to user-friendly messages"""
        if isinstance(error, YttlError):
            messages = {
                ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection.",
                ErrorCategory.MODEL: "Model loading failed. Please check your model configuration.",
                ErrorCategory.AUDIO: "Audio processing failed. The video format may not be supported.",
                ErrorCategory.CONFIG: "Configuration error. Please check your settings.",
                ErrorCategory.SYSTEM: "System error occurred. Please try again."
            }
            return messages.get(error.category, str(error))
        return "An unexpected error occurred. Please try again."
```

## Testing Strategy

### Comprehensive Test Suite

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

class TestModernYttl:
    @pytest.fixture
    async def config(self):
        return AppConfig(
            llm_provider=LLMProvider.LOCAL,
            whisper_provider=WhisperProvider.LOCAL,
            output_format="html"
        )
    
    @pytest.fixture
    async def mock_video_source(self):
        mock = AsyncMock()
        mock.extract_info.return_value = VideoMetadata(
            video_id="test123",
            title="Test Video",
            duration=3600,
            url="https://youtube.com/watch?v=test123",
            extractor="youtube"
        )
        return mock
    
    async def test_video_processing_pipeline(self, config, mock_video_source):
        """Test complete video processing pipeline"""
        processor = ModernVideoProcessor(config)
        
        result = await processor.process_video("https://youtube.com/watch?v=test123")
        
        assert result.video_id == "test123"
        assert len(result.summaries) > 0
        assert result.metadata.title == "Test Video"
    
    async def test_error_handling_with_retry(self, config):
        """Test error handling and retry mechanisms"""
        processor = ModernVideoProcessor(config)
        
        # Mock a failing operation that succeeds on retry
        mock_operation = AsyncMock(side_effect=[
            YttlError("Network error", ErrorCategory.NETWORK),
            "success"
        ])
        
        result = await processor.error_handler.handle_with_retry(mock_operation)
        assert result == "success"
        assert mock_operation.call_count == 2
    
    async def test_output_formatters(self, config):
        """Test different output formats"""
        summary_data = SummaryData(
            video_id="test123",
            title="Test Video",
            duration=3600,
            url="https://youtube.com/watch?v=test123",
            metadata=VideoMetadata(...),
            summaries=[...],
            generation_time=datetime.now(),
            model_info={},
            processing_stats={}
        )
        
        html_formatter = HTMLFormatter()
        html_output = await html_formatter.format(summary_data)
        assert "<html>" in html_output
        assert "Test Video" in html_output
        
        md_formatter = MarkdownFormatter()
        md_output = await md_formatter.format(summary_data)
        assert "# Test Video" in md_output
```

## Performance Optimizations

### Key Performance Improvements

1. **Async Processing Pipeline:**
   - Convert synchronous operations to async
   - Implement concurrent processing of audio chunks
   - Use async I/O for file operations and network requests

2. **Memory Management:**
   - Implement streaming for large audio files
   - Use memory-mapped files for model loading
   - Implement proper cleanup and garbage collection

3. **Caching Strategy:**
   - Cache downloaded models with version checking
   - Implement result caching for repeated requests
   - Use efficient serialization for cached data

4. **GPU Acceleration:**
   - Enable GPU support for Whisper processing
   - Optimize CUDA memory usage
   - Implement fallback to CPU when GPU unavailable

5. **Batch Processing:**
   - Process multiple audio segments in batches
   - Implement efficient batching for LLM requests
   - Use vectorized operations where possible

## Browser Extension Modernization

### Manifest V3 Migration

```json
{
  "manifest_version": 3,
  "name": "Modern YTTL",
  "version": "2.0.0",
  "description": "AI-powered video summarization with modern features",
  "permissions": [
    "activeTab",
    "storage",
    "nativeMessaging"
  ],
  "host_permissions": [
    "*://*.youtube.com/*",
    "*://*.twitch.tv/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["*://*.youtube.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_title": "Summarize Video"
  }
}
```

### Enhanced Extension Features

```javascript
// Modern service worker with improved error handling
class ModernExtensionManager {
  constructor() {
    this.nativePort = null;
    this.activeRequests = new Map();
  }
  
  async initializeNativeMessaging() {
    try {
      this.nativePort = chrome.runtime.connectNative("yttl");
      this.nativePort.onMessage.addListener(this.handleNativeMessage.bind(this));
      this.nativePort.onDisconnect.addListener(this.handleNativeDisconnect.bind(this));
    } catch (error) {
      console.error("Failed to initialize native messaging:", error);
      throw new Error("Native application not available");
    }
  }
  
  async summarizeVideo(url, options = {}) {
    const requestId = crypto.randomUUID();
    
    return new Promise((resolve, reject) => {
      this.activeRequests.set(requestId, { resolve, reject });
      
      this.nativePort.postMessage({
        action: "summarize",
        url: url,
        requestId: requestId,
        options: options
      });
      
      // Set timeout for request
      setTimeout(() => {
        if (this.activeRequests.has(requestId)) {
          this.activeRequests.delete(requestId);
          reject(new Error("Request timeout"));
        }
      }, 300000); // 5 minutes timeout
    });
  }
}
```

This design provides a comprehensive modernization plan that addresses all the requirements while maintaining the core functionality of the existing tool. The implementation will be done incrementally to ensure stability and backward compatibility.