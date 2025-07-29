# Design Document

## Overview

This design enhances the existing YouTube video summarization tool to include full transcript display alongside the generated summaries. The solution will modify the data flow to preserve caption segments throughout the processing pipeline and update the HTML template to render the transcript in a user-friendly format with clickable timestamps.

## Architecture

The current architecture processes video captions through several stages:
1. Caption extraction (from YouTube or Whisper transcription)
2. SponsorBlock filtering (optional)
3. Sectionization into time-based chunks
4. LLM summarization
5. HTML template rendering

The enhancement will preserve the original caption segments alongside the existing processing flow, making them available to the HTML template for rendering.

### Data Flow Changes

```
Video URL → Caption Extraction → SponsorBlock Filter → [NEW] Caption Preservation
                                                              ↓
Summary Generation ← Sectionization ← [EXISTING FLOW]        ↓
        ↓                                                     ↓
HTML Template ← [NEW] Enhanced ProcessResult ←───────────────┘
```

## Components and Interfaces

### 1. ProcessResult Enhancement

**Current Structure:**
```python
ProcessResult = namedtuple('ProcessResult', ['video_id', 'summary'])
```

**Enhanced Structure:**
```python
ProcessResult = namedtuple('ProcessResult', ['video_id', 'summary', 'transcript'])
```

The `transcript` field will contain the filtered caption segments with timing information.

### 2. Caption Data Structure

The transcript will use the existing `Segment` namedtuple:
```python
Segment = namedtuple('Segment', ['start', 'end', 'text'])
```

This preserves timing information and text content for each caption segment.

### 3. Template Enhancement

The HTML template will be extended with a new transcript section that:
- Displays a clear "Full Transcript" heading
- Renders each segment with clickable timestamps
- Uses consistent styling with the existing summary sections
- Provides proper spacing and readability

### 4. Timestamp Formatting

A new utility function will format timestamps consistently:
```python
def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
```

## Data Models

### Enhanced ProcessResult
```python
ProcessResult = namedtuple('ProcessResult', [
    'video_id',      # str: Video identifier
    'summary',       # str: HTML summary content
    'transcript'     # List[Segment]: Filtered caption segments
])
```

### Transcript Segment
```python
Segment = namedtuple('Segment', [
    'start',         # int: Start time in seconds
    'end',           # int: End time in seconds  
    'text'           # str: Caption text content
])
```

## Error Handling

### Empty Transcript Handling
- If no captions are available, display a message indicating transcript is unavailable
- Handle cases where all segments are filtered out by SponsorBlock

### Malformed Caption Data
- Skip segments with invalid timing information
- Filter out empty or whitespace-only text segments
- Log warnings for problematic segments when verbose mode is enabled

### Template Rendering Errors
- Gracefully handle missing transcript data
- Provide fallback display when timestamp formatting fails
- Ensure summary section renders even if transcript section fails

## Testing Strategy

### Unit Tests
1. **ProcessResult Enhancement**
   - Test that transcript data is properly preserved through the processing pipeline
   - Verify that existing functionality remains unchanged

2. **Timestamp Formatting**
   - Test edge cases: 0 seconds, exactly 1 hour, over 24 hours
   - Verify consistent formatting across different time ranges

3. **Template Rendering**
   - Test transcript section rendering with various data inputs
   - Verify clickable timestamp generation
   - Test empty transcript handling

### Integration Tests
1. **End-to-End Processing**
   - Process a sample video and verify transcript appears in output
   - Test with SponsorBlock filtering enabled
   - Verify timestamp links work correctly

2. **Caption Source Compatibility**
   - Test with YouTube captions
   - Test with Whisper-generated transcripts
   - Test with local file processing

### Manual Testing
1. **User Experience**
   - Verify transcript readability and formatting
   - Test timestamp link functionality in browsers
   - Confirm visual separation between summary and transcript

2. **Performance Impact**
   - Measure any performance impact from preserving transcript data
   - Verify memory usage remains reasonable for long videos

## Implementation Considerations

### Backward Compatibility
- The enhancement maintains full backward compatibility
- Existing ProcessResult usage will continue to work
- Template changes are additive only

### Performance Impact
- Minimal memory overhead from preserving caption segments
- No additional processing time for transcript generation
- HTML file size increase proportional to transcript length

### Styling Consistency
- Transcript section will use Bootstrap classes consistent with summary sections
- Timestamp links will match existing summary timestamp styling
- Proper responsive design for mobile viewing

### Accessibility
- Transcript provides alternative access to video content
- Proper semantic HTML structure for screen readers
- Keyboard navigation support for timestamp links