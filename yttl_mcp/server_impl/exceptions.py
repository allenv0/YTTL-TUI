"""Custom exceptions for YTTL MCP server."""

class YTTLMCPError(Exception):
    """Base exception for YTTL MCP server errors."""
    pass

class VideoNotFoundError(YTTLMCPError):
    """Raised when a requested video is not found."""
    pass

class InvalidSearchError(YTTLMCPError):
    """Raised when search parameters are invalid."""
    pass

class ParsingError(YTTLMCPError):
    """Raised when video file parsing fails."""
    pass

class CacheError(YTTLMCPError):
    """Raised when cache operations fail."""
    pass