# Design Document

## Overview

This design implements robust error handling for the caption download functionality in YTTL. The solution wraps the existing `download_captions` function with comprehensive exception handling while maintaining the current API and fallback behavior to local transcription.

## Architecture

The fix will be implemented as modifications to the existing `download_captions` function in `yttl/yttl.py`. The architecture maintains the current flow:

1. Extract caption URL from video info
2. Attempt to download and parse captions with comprehensive error handling
3. Return None on any failure to trigger fallback to local transcription
4. Provide appropriate logging for debugging and user feedback

## Components and Interfaces

### Modified download_captions Function

```python
def download_captions(video_info, verbose=False):
    """
    Download captions from video with robust error handling.
    
    Args:
        video_info: Video metadata from yt-dlp
        verbose: Enable detailed error logging
        
    Returns:
        List[Segment] or None: Caption segments or None if download fails
    """
```

The function will maintain backward compatibility while adding optional verbose parameter for detailed error reporting.

### Error Handling Strategy

The function will handle these error categories:

1. **Network Errors**: Connection timeouts, DNS failures, network unreachable
2. **HTTP Errors**: 404, 500, 403, and other HTTP status codes
3. **JSON Parsing**: Malformed JSON, empty responses, encoding issues
4. **Data Structure**: Missing keys in JSON response, unexpected data types
5. **General Exceptions**: Catch-all for unexpected errors

### Logging Strategy

- Use Python's logging module for consistent error reporting
- Provide different verbosity levels based on user preference
- Log specific error types with actionable information
- Avoid exposing sensitive information in logs

## Data Models

No changes to existing data models. The function continues to return:
- `List[Segment]` on successful caption download
- `None` on any failure (triggers fallback to local transcription)

The `Segment` namedtuple remains unchanged:
```python
Segment = namedtuple('Segment', ['start', 'end', 'text'])
```

## Error Handling

### Exception Handling Flow

```
download_captions() Error Handling:
├── URL extraction fails → return None
├── requests.Timeout → log timeout, return None
├── requests.ConnectionError → log connection issue, return None  
├── requests.HTTPError → log HTTP error, return None
├── HTTP status != 200 → log status code, return None
├── Empty response → log empty response, return None
├── json.JSONDecodeError → log JSON parse error, return None
├── KeyError (missing 'events') → log missing key, return None
├── UnicodeDecodeError → log encoding error, return None
└── General Exception → log unexpected error, return None
```

### Timeout Configuration

- Set 30-second timeout for caption download requests
- Prevents hanging on slow or unresponsive servers
- Configurable timeout value for future extensibility

### Response Validation

1. Check HTTP status code before processing
2. Validate response content is not empty
3. Verify JSON structure contains expected keys
4. Handle malformed or incomplete JSON gracefully

## Testing Strategy

### Unit Tests

1. **Successful caption download**
   - Mock successful HTTP response with valid JSON
   - Verify segment parsing works correctly
   - Test normal operation unchanged

2. **Network error scenarios**
   - Mock timeout exceptions
   - Mock connection errors
   - Mock DNS resolution failures

3. **HTTP error responses**
   - Test 404, 500, 403 status codes
   - Verify appropriate error handling

4. **JSON parsing errors**
   - Test malformed JSON responses
   - Test empty responses
   - Test responses missing 'events' key

5. **Logging verification**
   - Test verbose vs normal logging modes
   - Verify appropriate log messages for each error type

### Integration Tests

1. **End-to-end failure handling**
   - Test with actual problematic URLs
   - Verify fallback to local transcription works
   - Confirm application completes successfully

2. **Real-world error simulation**
   - Test with expired caption URLs
   - Test with rate-limited responses
   - Test with network connectivity issues

## Implementation Notes

### Backward Compatibility

- Maintain existing function signature with optional verbose parameter
- Preserve current return value contract (List[Segment] or None)
- No changes required to calling code
- Existing behavior preserved for successful downloads

### Performance Considerations

- Minimal overhead from exception handling
- Timeout prevents indefinite hanging
- Early return on obvious failures
- No impact on successful caption downloads

### Security Considerations

- Validate URLs before making requests
- Handle potentially malicious JSON responses safely
- Avoid logging sensitive information
- Prevent information disclosure through error messages

### Logging Configuration

- Use standard Python logging module
- Log at WARNING level for caption download failures
- Include relevant context (URL, error type) without sensitive data
- Support both verbose and normal logging modes