# Implementation Plan

- [x] 1. Enhance ProcessResult data structure to include transcript data
  - Modify the ProcessResult namedtuple to include a transcript field
  - Update the process_video function to return transcript data alongside summary
  - Ensure backward compatibility with existing ProcessResult usage
  - _Requirements: 1.1, 1.4_

- [x] 2. Modify process_video function to preserve caption segments
  - Update process_video to capture filtered captions after SponsorBlock processing
  - Pass the preserved caption segments to the ProcessResult constructor
  - Ensure captions maintain their original timing and text information
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 3. Create timestamp formatting utility function
  - Implement format_timestamp function to convert seconds to HH:MM:SS format
  - Handle edge cases like 0 seconds, exactly 1 hour, and over 24 hours
  - Write unit tests for timestamp formatting function
  - _Requirements: 3.4_

- [x] 4. Update HTML template to include transcript section
  - Add a new transcript section below the existing summary in template.html
  - Create clear visual separation between summary and transcript sections
  - Use Bootstrap styling consistent with existing summary sections
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5. Implement clickable timestamp links in transcript
  - Render each transcript segment with clickable timestamp links
  - Use the existing time_url function logic for generating video links
  - Format timestamps using the new format_timestamp utility
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 6. Add transcript content filtering and formatting
  - Filter out empty or whitespace-only transcript segments
  - Group transcript segments logically for better readability
  - Preserve natural speech patterns and paragraph breaks where possible
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 7. Handle edge cases and error conditions
  - Add handling for missing or empty transcript data
  - Implement graceful fallback when transcript is unavailable
  - Add error handling for malformed caption segments
  - _Requirements: 1.1, 4.3_

- [x] 8. Write comprehensive tests for transcript functionality
  - Create unit tests for ProcessResult enhancement
  - Add integration tests for end-to-end transcript processing
  - Test with different caption sources (YouTube captions, Whisper transcripts)
  - Verify timestamp link generation and formatting
  - _Requirements: 1.1, 1.2, 3.1, 3.4_

- [ ] 9. Update CLI integration to handle enhanced ProcessResult
  - Ensure CLI module properly handles the new ProcessResult structure
  - Verify that existing functionality remains unchanged
  - Test that HTML output includes transcript section
  - _Requirements: 1.1, 2.1_