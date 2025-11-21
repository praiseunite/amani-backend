"""Domain-level exceptions for the application.

These are domain errors that adapters should translate database-specific
errors into for cleaner separation of concerns.
"""


class DuplicateEntryError(Exception):
    """Raised when attempting to create a duplicate entry that violates uniqueness constraints.

    This is a domain-level error that adapters should raise when database-level
    IntegrityError or unique constraint violations occur.
    """

    def __init__(self, message: str = "Duplicate entry detected", original_error: Exception = None):
        """Initialize the duplicate entry error.

        Args:
            message: Human-readable error message
            original_error: The original database-specific exception (preserved as __cause__)
        """
        super().__init__(message)
        if original_error:
            self.__cause__ = original_error
