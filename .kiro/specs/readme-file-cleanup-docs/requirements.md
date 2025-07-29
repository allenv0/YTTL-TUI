# Requirements Document

## Introduction

This feature adds documentation to the README about how the application handles video files during and after processing. Users need to understand that video files are automatically cleaned up and don't consume permanent disk space, which addresses common concerns about storage usage.

## Requirements

### Requirement 1

**User Story:** As a user, I want to understand how video files are handled during processing, so that I know whether they consume permanent disk space.

#### Acceptance Criteria

1. WHEN a user reads the README THEN they SHALL understand that video files are automatically cleaned up after processing
2. WHEN a user reads the README THEN they SHALL understand what files are temporarily downloaded during processing
3. WHEN a user reads the README THEN they SHALL understand what files remain after processing is complete

### Requirement 2

**User Story:** As a user, I want to know about disk space usage, so that I can plan my storage accordingly.

#### Acceptance Criteria

1. WHEN a user reads the README THEN they SHALL understand that only HTML summaries and cached models consume permanent storage
2. WHEN a user reads the README THEN they SHALL understand that temporary files are automatically removed
3. WHEN a user reads the README THEN they SHALL understand the difference between temporary and permanent files