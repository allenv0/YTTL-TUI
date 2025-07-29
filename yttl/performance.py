# SPDX-License-Identifier: Apache-2.0

import asyncio
import aiohttp
import time
import logging
import psutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager
import concurrent.futures
import threading
from queue import Queue
import json


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations"""
    max_concurrent_llm: int = 5
    max_concurrent_whisper: int = 2
    chunk_size_strategy: str = "adaptive"  # "adaptive", "fixed", "memory_optimized"
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    silence_threshold: float = -40.0  # dB
    memory_limit_mb: int = 4096
    enable_parallel_processing: bool = True
    api_timeout: float = 60.0
    local_llm_threads: int = 1


@dataclass
class ProcessingStats:
    """Statistics for processing performance"""
    total_time: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    segments_processed: int = 0
    concurrent_efficiency: float = 0.0
    memory_peak_mb: int = 0
    errors_encountered: int = 0
    retries_performed: int = 0
    parallel_speedup: float = 1.0


class PerformanceTracker:
    """Track performance metrics during processing"""
    
    def __init__(self):
        self.phase_times = {}
        self.concurrency_stats = {}
        self.error_counts = {}
        self.start_time = time.time()
        self.memory_peak = 0
        self.current_phase = None
        self.phase_start = None
    
    @asynccontextmanager
    async def track_phase(self, phase_name: str):
        """Context manager for timing phases"""
        self.current_phase = phase_name
        self.phase_start = time.time()
        try:
            yield
        finally:
            if self.phase_start:
                duration = time.time() - self.phase_start
                self.phase_times[phase_name] = duration
                self.phase_start = None
                self.current_phase = None
    
    def track_memory(self):
        """Track current memory usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_peak = max(self.memory_peak, memory_mb)
        return memory_mb
    
    def track_error(self, error_type: str):
        """Track error occurrence"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def track_concurrency(self, phase: str, concurrent_tasks: int, efficiency: float):
        """Track concurrency metrics"""
        self.concurrency_stats[phase] = {
            'concurrent_tasks': concurrent_tasks,
            'efficiency': efficiency
        }
    
    def get_stats(self) -> ProcessingStats:
        """Generate final processing statistics"""
        total_time = time.time() - self.start_time
        
        # Calculate overall efficiency
        concurrent_efficiency = 0.0
        if self.concurrency_stats:
            efficiencies = [stats['efficiency'] for stats in self.concurrency_stats.values()]
            concurrent_efficiency = sum(efficiencies) / len(efficiencies)
        
        return ProcessingStats(
            total_time=total_time,
            phase_times=self.phase_times.copy(),
            segments_processed=sum(stats.get('concurrent_tasks', 0) for stats in self.concurrency_stats.values()),
            concurrent_efficiency=concurrent_efficiency,
            memory_peak_mb=int(self.memory_peak),
            errors_encountered=sum(self.error_counts.values()),
            retries_performed=self.error_counts.get('retry', 0)
        )
    
    def report_statistics(self, verbose: bool = False) -> str:
        """Generate performance report"""
        stats = self.get_stats()
        
        report = []
        report.append(f"Performance Report:")
        report.append(f"  Total Time: {stats.total_time:.2f}s")
        report.append(f"  Memory Peak: {stats.memory_peak_mb}MB")
        report.append(f"  Segments Processed: {stats.segments_processed}")
        
        if stats.concurrent_efficiency > 0:
            report.append(f"  Concurrency Efficiency: {stats.concurrent_efficiency:.1%}")
        
        if stats.errors_encountered > 0:
            report.append(f"  Errors Encountered: {stats.errors_encountered}")
            report.append(f"  Retries Performed: {stats.retries_performed}")
        
        if verbose and self.phase_times:
            report.append("  Phase Breakdown:")
            for phase, duration in self.phase_times.items():
                percentage = (duration / stats.total_time) * 100
                report.append(f"    {phase}: {duration:.2f}s ({percentage:.1f}%)")
        
        return "\n".join(report)


class RetryManager:
    """Handle retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def retry_with_backoff(self, func: Callable, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception


class AsyncLLMProcessor:
    """Process LLM requests with async concurrency control"""
    
    def __init__(self, llm_provider, config: PerformanceConfig, tracker: PerformanceTracker):
        self.llm_provider = llm_provider
        self.config = config
        self.tracker = tracker
        self.semaphore = asyncio.Semaphore(config.max_concurrent_llm)
        self.retry_manager = RetryManager(config.retry_max_attempts, config.retry_base_delay)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        if hasattr(self.llm_provider, 'create_session'):
            self.session = await self.llm_provider.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def process_segments_parallel(self, segments: List[List[str]]) -> List[str]:
        """Process multiple segments concurrently"""
        if not self.config.enable_parallel_processing:
            # Fall back to sequential processing
            return await self._process_segments_sequential(segments)
        
        async with self.tracker.track_phase("parallel_segment_processing"):
            # Create tasks for all segments
            tasks = []
            for i, segment in enumerate(segments):
                if segment:  # Only process non-empty segments
                    task = self._process_single_segment(segment, i)
                    tasks.append(task)
                else:
                    tasks.append(asyncio.create_task(self._return_empty_summary()))
            
            # Execute all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Calculate efficiency metrics
            concurrent_time = end_time - start_time
            sequential_estimate = len([s for s in segments if s]) * 5.0  # Estimate 5s per segment
            efficiency = min(sequential_estimate / concurrent_time, len(tasks)) if concurrent_time > 0 else 1.0
            
            self.tracker.track_concurrency("segment_processing", len(tasks), efficiency)
            
            # Handle any exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(f"Segment {i} failed: {result}")
                    self.tracker.track_error("segment_processing")
                    processed_results.append("")  # Empty summary for failed segments
                else:
                    processed_results.append(result)
            
            return processed_results
    
    async def _process_segments_sequential(self, segments: List[List[str]]) -> List[str]:
        """Fallback sequential processing"""
        results = []
        for segment in segments:
            if segment:
                result = await self._process_single_segment(segment, len(results))
                results.append(result)
            else:
                results.append("")
        return results
    
    async def _process_single_segment(self, segment: List[str], segment_id: int) -> str:
        """Process a single segment with retry logic"""
        async with self.semaphore:  # Limit concurrency
            prompt = f'The following is a transcript of a section of a video.\n{" ".join(segment)}\n Based on the previous transcript, describe what is happening in this section'
            
            try:
                result = await self.retry_manager.retry_with_backoff(
                    self._call_llm_async, prompt
                )
                return result
            except Exception as e:
                logging.error(f"Failed to process segment {segment_id} after retries: {e}")
                self.tracker.track_error("llm_processing")
                return ""  # Return empty summary on failure
    
    async def _return_empty_summary(self) -> str:
        """Return empty summary for empty segments"""
        return ""
    
    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM provider asynchronously"""
        if hasattr(self.llm_provider, 'run_llm_async'):
            return await self.llm_provider.run_llm_async(prompt, session=self.session)
        else:
            # For providers without async support, run in thread pool
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.local_llm_threads) as executor:
                return await loop.run_in_executor(executor, self.llm_provider.run_llm, prompt)
    
    async def generate_consolidated_summary(self, summaries: List[str]) -> str:
        """Generate consolidated summary from individual summaries"""
        if len(summaries) == 1:
            return summaries[0]
        
        # Filter out empty summaries
        non_empty_summaries = [s for s in summaries if s.strip()]
        if not non_empty_summaries:
            return ""
        
        all_sects = '\n'.join(non_empty_summaries)
        prompt = f'The following is a set of summaries of sections of a video.\n{all_sects}\nTake those summaries of individual sections and distill it into a consolidated summary of the entire video.'
        
        try:
            return await self.retry_manager.retry_with_backoff(
                self._call_llm_async, prompt
            )
        except Exception as e:
            logging.error(f"Failed to generate consolidated summary: {e}")
            self.tracker.track_error("consolidated_summary")
            return non_empty_summaries[0] if non_empty_summaries else ""


class LocalLLMWrapper:
    """Thread-safe wrapper for local LLM processing"""
    
    def __init__(self, llm_instance, max_threads: int = 1):
        self.llm = llm_instance
        self.max_threads = max_threads
        self.request_queue = Queue()
        self.response_futures = {}
        self.worker_threads = []
        self.shutdown_event = threading.Event()
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads for processing requests"""
        for i in range(self.max_threads):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.worker_threads.append(worker)
    
    def _worker_loop(self):
        """Worker thread loop for processing LLM requests"""
        while not self.shutdown_event.is_set():
            try:
                request_id, prompt = self.request_queue.get(timeout=1.0)
                
                try:
                    result = self.llm.run_llm(prompt)
                    future = self.response_futures.get(request_id)
                    if future and not future.cancelled():
                        # Use call_soon_threadsafe to set result from worker thread
                        future.get_loop().call_soon_threadsafe(future.set_result, result)
                except Exception as e:
                    future = self.response_futures.get(request_id)
                    if future and not future.cancelled():
                        future.get_loop().call_soon_threadsafe(future.set_exception, e)
                finally:
                    self.request_queue.task_done()
                    if request_id in self.response_futures:
                        del self.response_futures[request_id]
                        
            except:
                continue  # Timeout or other queue exception
    
    async def run_llm_async(self, prompt: str, **kwargs) -> str:
        """Async interface to local LLM"""
        request_id = id(prompt) + int(time.time() * 1000000)
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        self.response_futures[request_id] = future
        self.request_queue.put((request_id, prompt))
        
        try:
            return await future
        except Exception as e:
            # Clean up on error
            if request_id in self.response_futures:
                del self.response_futures[request_id]
            raise e
    
    def shutdown(self):
        """Shutdown worker threads"""
        self.shutdown_event.set()
        for worker in self.worker_threads:
            worker.join(timeout=5.0)


def get_hardware_info() -> Dict[str, Any]:
    """Get hardware information for optimization"""
    return {
        'cpu_count': psutil.cpu_count(),
        'memory_total_mb': psutil.virtual_memory().total / 1024 / 1024,
        'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
        'memory_percent': psutil.virtual_memory().percent
    }


def create_performance_config(hardware_info: Optional[Dict] = None) -> PerformanceConfig:
    """Create optimized performance configuration based on hardware"""
    if hardware_info is None:
        hardware_info = get_hardware_info()
    
    # Adjust concurrency based on available resources
    cpu_count = hardware_info.get('cpu_count', 4)
    memory_mb = hardware_info.get('memory_available_mb', 4096)
    
    # Conservative defaults that scale with hardware
    max_concurrent_llm = min(max(2, cpu_count // 2), 8)
    max_concurrent_whisper = min(max(1, cpu_count // 4), 3)
    
    # Adjust for memory constraints
    if memory_mb < 4096:
        max_concurrent_llm = min(max_concurrent_llm, 2)
        max_concurrent_whisper = 1
    elif memory_mb > 16384:
        max_concurrent_llm = min(max_concurrent_llm + 2, 10)
    
    return PerformanceConfig(
        max_concurrent_llm=max_concurrent_llm,
        max_concurrent_whisper=max_concurrent_whisper,
        memory_limit_mb=int(memory_mb * 0.8),  # Use 80% of available memory
        local_llm_threads=min(max(1, cpu_count // 4), 2)
    )