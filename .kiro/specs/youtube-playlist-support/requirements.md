# YouTube Playlist Support Requirements

## Introduction

This feature will enhance the YTTL tool to support YouTube playlists, allowing users to process entire playlists automatically. The tool will extract individual video URLs from a playlist, process each video separately, and organize the outputs in a dedicated folder named after the playlist.

## Requirements

### Requirement 1: Playlist URL Detection

**User Story:** As a user, I want to provide a YouTube playlist URL to YTTL, so that the tool can automatically detect it's a playlist and process all videos within it.

#### Acceptance Criteria

1. WHEN a user provides a YouTube playlist URL THEN the system SHALL detect it as a playlist
2. WHEN a playlist URL is detected THEN the system SHALL extract the playlist metadata (title, video count)
3. WHEN the playlist URL is invalid or inaccessible THEN the system SHALL display an appropriate error message
4. WHEN the playlist is empty THEN the system SHALL inform the user and exit gracefully

### Requirement 2: Individual Video Processing

**User Story:** As a user processing a playlist, I want each video in the playlist to be processed individually with the same quality and features as single video processing, so that I get consistent results across all videos.

#### Acceptance Criteria

1. WHEN processing a playlist THEN the system SHALL extract individual video URLs from the playlist
2. WHEN processing each video THEN the system SHALL use the same processing pipeline as single video mode
3. WHEN a video in the playlist fails to process THEN the system SHALL log the error and continue with the next video
4. WHEN processing videos THEN the system SHALL maintain all existing features (transcripts, summaries, timestamps, SponsorBlock, etc.)

### Requirement 3: Organized Output Structure

**User Story:** As a user who has processed a playlist, I want all the generated HTML files to be organized in a folder named after the playlist, so that I can easily find and manage the results.

#### Acceptance Criteria

1. WHEN a playlist is processed THEN the system SHALL create a folder named after the playlist title
2. WHEN creating the playlist folder THEN the system SHALL sanitize the folder name to be filesystem-safe
3. WHEN saving individual video summaries THEN the system SHALL place each HTML file in the playlist folder
4. WHEN the playlist folder already exists THEN the system SHALL either use it or create a uniquely named folder

### Requirement 4: Progress Tracking and User Feedback

**User Story:** As a user processing a large playlist, I want to see progress information about which video is being processed and how many remain, so that I can estimate completion time.

#### Acceptance Criteria

1. WHEN processing a playlist THEN the system SHALL display the total number of videos to be processed
2. WHEN processing each video THEN the system SHALL show current video number and title
3. WHEN a video completes processing THEN the system SHALL update the overall progress
4. WHEN processing is complete THEN the system SHALL display a summary of successful and failed videos

### Requirement 5: Error Handling and Resilience

**User Story:** As a user processing a playlist with some problematic videos, I want the tool to continue processing other videos even if some fail, so that I don't lose progress on the entire playlist.

#### Acceptance Criteria

1. WHEN a video in the playlist fails to process THEN the system SHALL log the error with video details
2. WHEN errors occur THEN the system SHALL continue processing remaining videos
3. WHEN processing completes THEN the system SHALL provide a summary of successful and failed videos
4. WHEN all videos fail THEN the system SHALL provide appropriate error information

### Requirement 6: Configuration Consistency

**User Story:** As a user processing a playlist, I want to use the same configuration options (LLM provider, Whisper model, SponsorBlock settings) for all videos in the playlist, so that I get consistent results.

#### Acceptance Criteria

1. WHEN processing a playlist THEN the system SHALL apply the same configuration to all videos
2. WHEN command-line options are provided THEN the system SHALL use them for every video in the playlist
3. WHEN configuration files are used THEN the system SHALL apply them consistently across all videos
4. WHEN processing videos THEN the system SHALL maintain the same quality and feature settings throughout