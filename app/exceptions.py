"""
Custom exceptions for the vector database application.
"""


class VectorDBException(Exception):
    """Base exception for all vector database related errors."""
    pass


class NotFoundError(VectorDBException):
    """Raised when a requested resource is not found."""
    pass


class AlreadyExistsError(VectorDBException):
    """Raised when trying to create a resource that already exists."""
    pass


class ValidationError(VectorDBException):
    """Raised when input validation fails."""
    pass


class IndexError(VectorDBException):
    """Raised when index-related operations fail."""
    pass


class EmbeddingError(VectorDBException):
    """Raised when embedding generation fails."""
    pass
