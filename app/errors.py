"""Domain-level error definitions.

These errors represent business/domain exceptions and should be raised
by adapters to decouple the application layer from infrastructure-specific errors.
"""


class DuplicateEntryError(Exception):
    """Raised when attempting to create a duplicate entry that violates uniqueness constraints.
    This domain-level error is raised by adapters when they encounter
    database-specific constraint violations (e.g., SQLAlchemy IntegrityError).
    It allows the application layer to handle duplicates consistently
    without depending on infrastructure-specific exception types.
    """

    pass
