class GramDBError(Exception):
    """Base class for all GramDB related errors."""
    pass

class ConnectionError(GramDBError):
    """Raised when there is a network connection issue."""
    pass

class NotFoundError(GramDBError):
    """Raised when a specific table or record is not found."""
    pass

class DuplicateTableError(GramDBError):
    """Raised when a table already exists."""
    pass

class ValidationError(GramDBError):
    """Raised when a validation error occurs."""
    pass

