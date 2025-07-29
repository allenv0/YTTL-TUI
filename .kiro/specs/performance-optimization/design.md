# Performance Optimization Design

## Overview

This design implements two major performance optimizations for YTTL: parallel LLM processing and dynamic audio chunk optimization. The solution uses asyncio for concurrent LLM calls, implements intelligent chunk sizing algorithms, and adds robust error handling with retry mechanisms.

## Architecture

### Current Architecture Issues
- Sequential LLM processing in `summarize_hour()` creates linear time scaling
- Fixed audio chunk sizes don't adapt to hardware or content
- Limited error handling causes complete failures on partial issues
- No performance monitoring or tuning capabilities

### New Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Process Video                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │ Audio Processor │    │     LLM Summary Engine           │ │
│  │                 │    │                                  │ │
│  │ • Dynamic       │    │ • Async Parallel Processing      │ │
│  │   Chunking      │    │ • Concurrent Segment Summaries  │ │
│  │ • Silence       │    │ • Thread-safe Local LLM         │ │
│  │   Detection     │    │ • API Rate Limit Management     │ │
│  │ • Memory        │    │ • Error Recovery & Retry        │ │
│  │   Optimization  │    │                                  │ │
│  └─────────────────┘    └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                Performance Monitor                          │
│  • Timing Statistics  • Concurrency Metrics               │
│  • Memory Usage      • Error Tracking                     │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Parallel LLM Summary Engine

#### AsyncLLMProcessor Class
```python
class AsyncLLMProcessor:
    def __init__(self, llm_provider, max_concurrent=5):
        self.llm_provider = llm_provider
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_segments_parallel(self, segments):
        # Process multiple segments concurrently
        
    async def process_single_segment(self, segment, retry_count=3):
        # Process individual segment with retry logic
```

#### LLM Provider Adaptations
- **API Providers (OpenAI/Groq)**: Use `aiohttp` for async HTTP requests
- **Local LLM**: Implement thread-safe wrapper with queue-based processing
- **ChatGPT/HuggingChat**: Add async session management

### 2. Dynamic Audio Chunk Optimizer

#### ChunkOptimizer Class
```python
class ChunkOptimizer:
    def __init__(self, whisper_provider, hardware_info):
        self.provider = whisper_provider
        self.hardware = hardware_info
    
    def calculate_optimal_chunk_size(self, duration, memory_available):
        # Calculate optimal chunk size based on constraints
        
    def detect_silence_segments(self, audio_path):
        # Identify silent segments to skip
```

#### Hardware Detection
- Memory availability detection
- GPU acceleration capability
- CPU core count for threading decisions

### 3. Enhanced Error Handling System

#### RetryManager Class
```python
class RetryManager:
    def __init__(self, max_retries=3, base_delay=1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        # Exponential backoff retry logic
```

### 4. Performance Monitoring

#### PerformanceTracker Class
```python
class PerformanceTracker:
    def __init__(self):
        self.phase_times = {}
        self.concurrency_stats = {}
        self.error_counts = {}
    
    def track_phase(self, phase_name):
        # Context manager for timing phases
        
    def report_statistics(self):
        # Generate performance report
```

## Data Models

### Configuration Model
```python
@dataclass
class PerformanceConfig:
    max_concurrent_llm: int = 5
    max_concurrent_whisper: int = 2
    chunk_size_strategy: str = "adaptive"  # "adaptive", "fixed", "memory_optimized"
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    silence_threshold: float = -40.0  # dB
    memory_limit_mb: int = 4096
```

### Processing Statistics Model
```python
@dataclass
class ProcessingStats:
    total_time: float
    phase_times: Dict[str, float]
    segments_processed: int
    concurrent_efficiency: float
    memory_peak_mb: int
    errors_encountered: int
    retries_performed: int
```

## Error Handling

### Retry Strategies
1. **Exponential Backoff**: Base delay × 2^attempt_number
2. **Circuit Breaker**: Temporarily disable failing providers
3. **Graceful Degradation**: Continue with successful segments

### Error Categories
- **Network Errors**: Timeout, connection issues
- **API Errors**: Rate limits, authentication
- **Memory Errors**: Out of memory, allocation failures
- **Processing Errors**: Model failures, invalid input

## Testing Strategy

### Unit Tests
- `test_async_llm_processor.py`: Test parallel processing logic
- `test_chunk_optimizer.py`: Test dynamic chunking algorithms
- `test_retry_manager.py`: Test error handling and retry logic
- `test_performance_tracker.py`: Test monitoring functionality

### Integration Tests
- `test_parallel_summarization.py`: End-to-end parallel processing
- `test_audio_optimization.py`: Audio processing with different chunk sizes
- `test_error_recovery.py`: Error scenarios and recovery

### Performance Tests
- `test_performance_benchmarks.py`: Compare sequential vs parallel processing
- `test_memory_usage.py`: Memory consumption under different configurations
- `test_concurrency_limits.py`: Optimal concurrency settings

## Implementation Phases

### Phase 1: Async LLM Processing Foundation
- Implement `AsyncLLMProcessor` base class
- Add async support to API-based LLM providers
- Create thread-safe wrapper for local LLM

### Phase 2: Dynamic Audio Chunking
- Implement `ChunkOptimizer` with basic strategies
- Add hardware detection capabilities
- Integrate silence detection

### Phase 3: Error Handling and Resilience
- Implement `RetryManager` with exponential backoff
- Add circuit breaker pattern
- Enhance error reporting

### Phase 4: Performance Monitoring
- Implement `PerformanceTracker`
- Add configuration management
- Create performance reporting

### Phase 5: Integration and Optimization
- Integrate all components into main processing pipeline
- Performance tuning and optimization
- Documentation and user guides