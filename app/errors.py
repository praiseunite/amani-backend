"""Domain-level exceptions for the application.

These exceptions represent business logic errors and are independent of
infrastructure concerns (e.g., database-specific errors).
"""


class DuplicateEntryError(Exception):
    """Raised when attempting to create a duplicate entry.
    
    This is a domain-level exception that can be raised by any adapter
    when a unique constraint violation occurs. The application service
    layer can catch this exception to implement idempotent behavior.
    
    The original exception (e.g., IntegrityError from SQLAlchemy) should
    be preserved as the __cause__ for debugging purposes.
    """
    pass
