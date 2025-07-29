# Design Document

## Overview

This design adds a new section to the README that explains file management and cleanup behavior. The documentation will be placed strategically to address user concerns about disk space usage while maintaining the README's existing structure and flow.

## Architecture

### Placement Strategy
The file management documentation will be added as a new section called "File Management" positioned after the "Output Format" section and before "How It Works". This placement ensures users understand what files are created and cleaned up before diving into the technical implementation details.

### Content Structure
The new section will include:
1. **Temporary Files** - What gets downloaded during processing
2. **Automatic Cleanup** - How files are automatically removed
3. **Permanent Files** - What remains after processing
4. **Storage Requirements** - Disk space implications

## Components and Interfaces

### Section Content
The new "File Management" section will contain:

```markdown
## File Management

### Temporary Files
During processing, YTTL temporarily downloads:
- **Audio track**: Extracted from video in m4a format for Whisper transcription
- **Captions**: Downloaded subtitle files (when available)

### Automatic Cleanup
All temporary files are automatically removed after processing:
- **Temporary directory**: Created using Python's `TemporaryDirectory()` 
- **Audio files**: Deleted immediately after transcription
- **Downloaded captions**: Cleaned up with other temporary files
- **No manual cleanup required**: Everything happens automatically

### Permanent Files
Only these files remain on your system:
- **HTML summaries**: Saved in the `out/` directory
- **Model cache**: Downloaded LLM and Whisper models (in `~/.cache/huggingface/`)
- **Configuration files**: Any config files you create

### Storage Impact
- **Temporary usage**: 50MB-500MB during processing (varies by video length)
- **Permanent usage**: Only HTML summaries (~50KB each) and cached models (5-10GB total)
- **No video storage**: Original video files are never permanently stored
```

## Data Models

### Documentation Structure
- **Section title**: "File Management"
- **Subsections**: 4 subsections covering different aspects
- **Content format**: Mix of explanatory text and bullet points
- **Technical details**: Specific implementation details (TemporaryDirectory, file paths)

## Error Handling

### Documentation Accuracy
- Ensure all technical details match the actual implementation
- Reference specific code patterns (TemporaryDirectory usage)
- Provide accurate file size estimates based on typical usage

## Testing Strategy

### Validation Approach
1. **Content accuracy**: Verify all statements match the codebase
2. **Placement validation**: Ensure the section fits well in the README flow
3. **User comprehension**: Check that the information addresses common user concerns
4. **Technical correctness**: Validate file paths, sizes, and cleanup behavior