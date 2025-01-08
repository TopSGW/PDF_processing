"""Custom exceptions for the letter generator module."""

class ContentError(Exception):
    """Exception raised for content-related errors."""
    pass

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

class FormattingError(Exception):
    """Exception raised for formatting errors."""
    pass

class GenerationError(Exception):
    """Exception raised for letter generation errors."""
    pass