"""
Advanced input validation utilities for enhanced security.
"""

import html
import re
from typing import List, Optional

from pydantic import field_validator


class ValidationPatterns:
    """Common validation patterns for input sanitization."""

    # Pattern for valid names (letters, spaces, hyphens, apostrophes)
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-']+$")

    # Pattern for valid usernames (alphanumeric, underscores, hyphens)
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Pattern for valid phone numbers (international format)
    PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{1,14}$")

    # Pattern for SQL injection detection (basic)
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        re.IGNORECASE,
    )

    # Pattern for XSS detection (basic)
    XSS_PATTERN = re.compile(
        r"(<script|javascript:|onerror=|onload=|<iframe|eval\(|alert\()", re.IGNORECASE
    )

    # Pattern for path traversal detection
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\./|\.\.\\")

    # Pattern for valid URL slug
    SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    # Pattern for currency amount (up to 2 decimal places)
    CURRENCY_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")


class InputValidator:
    """Advanced input validation and sanitization."""

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string input by removing potentially dangerous characters.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not value:
            return value

        # Strip leading/trailing whitespace
        value = value.strip()

        # Limit length if specified
        if max_length:
            value = value[:max_length]

        # HTML escape to prevent XSS
        value = html.escape(value)

        return value

    @staticmethod
    def validate_no_sql_injection(value: str) -> str:
        """
        Check for potential SQL injection patterns.

        Args:
            value: String to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If SQL injection pattern detected
        """
        if ValidationPatterns.SQL_INJECTION_PATTERN.search(value):
            raise ValueError("Input contains potentially dangerous SQL keywords")
        return value

    @staticmethod
    def validate_no_xss(value: str) -> str:
        """
        Check for potential XSS patterns.

        Args:
            value: String to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If XSS pattern detected
        """
        if ValidationPatterns.XSS_PATTERN.search(value):
            raise ValueError("Input contains potentially dangerous script patterns")
        return value

    @staticmethod
    def validate_no_path_traversal(value: str) -> str:
        """
        Check for path traversal attempts.

        Args:
            value: String to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If path traversal pattern detected
        """
        if ValidationPatterns.PATH_TRAVERSAL_PATTERN.search(value):
            raise ValueError("Input contains path traversal patterns")
        return value

    @staticmethod
    def validate_name(value: str) -> str:
        """
        Validate a person's name.

        Args:
            value: Name to validate

        Returns:
            Validated name

        Raises:
            ValueError: If name is invalid
        """
        if not value:
            raise ValueError("Name cannot be empty")

        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters long")

        if len(value) > 100:
            raise ValueError("Name cannot exceed 100 characters")

        if not ValidationPatterns.NAME_PATTERN.match(value):
            raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")

        return value

    @staticmethod
    def validate_phone_number(value: str) -> str:
        """
        Validate a phone number.

        Args:
            value: Phone number to validate

        Returns:
            Validated phone number

        Raises:
            ValueError: If phone number is invalid
        """
        if not value:
            return value

        # Remove common formatting characters
        clean_value = re.sub(r"[\s\-\(\)]", "", value)

        if not ValidationPatterns.PHONE_PATTERN.match(clean_value):
            raise ValueError(
                "Invalid phone number format. Use international format (e.g., +1234567890)"
            )

        return clean_value

    @staticmethod
    def validate_slug(value: str) -> str:
        """
        Validate a URL slug.

        Args:
            value: Slug to validate

        Returns:
            Validated slug

        Raises:
            ValueError: If slug is invalid
        """
        if not value:
            raise ValueError("Slug cannot be empty")

        value = value.strip().lower()

        if not ValidationPatterns.SLUG_PATTERN.match(value):
            raise ValueError("Slug can only contain lowercase letters, numbers, and hyphens")

        if len(value) < 3:
            raise ValueError("Slug must be at least 3 characters long")

        if len(value) > 50:
            raise ValueError("Slug cannot exceed 50 characters")

        return value

    @staticmethod
    def validate_amount(
        value: float, min_amount: float = 0.01, max_amount: float = 1000000.0
    ) -> float:
        """
        Validate a monetary amount.

        Args:
            value: Amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount

        Returns:
            Validated amount

        Raises:
            ValueError: If amount is invalid
        """
        if value < min_amount:
            raise ValueError(f"Amount must be at least {min_amount}")

        if value > max_amount:
            raise ValueError(f"Amount cannot exceed {max_amount}")

        # Ensure only 2 decimal places
        if round(value, 2) != value:
            raise ValueError("Amount can have at most 2 decimal places")

        return value

    @staticmethod
    def validate_list_input(
        value: List[str], min_items: int = 0, max_items: int = 100, max_item_length: int = 100
    ) -> List[str]:
        """
        Validate a list of string inputs.

        Args:
            value: List to validate
            min_items: Minimum number of items
            max_items: Maximum number of items
            max_item_length: Maximum length per item

        Returns:
            Validated list

        Raises:
            ValueError: If list is invalid
        """
        if len(value) < min_items:
            raise ValueError(f"List must contain at least {min_items} items")

        if len(value) > max_items:
            raise ValueError(f"List cannot contain more than {max_items} items")

        # Validate each item
        validated_items = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("All list items must be strings")

            item = item.strip()

            if len(item) > max_item_length:
                raise ValueError(f"List items cannot exceed {max_item_length} characters")

            # Check for dangerous patterns
            InputValidator.validate_no_xss(item)
            InputValidator.validate_no_sql_injection(item)

            validated_items.append(item)

        return validated_items


def create_string_validator(
    min_length: int = 1,
    max_length: int = 255,
    pattern: Optional[re.Pattern] = None,
    sanitize: bool = True,
    check_xss: bool = True,
    check_sql_injection: bool = True,
):
    """
    Factory function to create a Pydantic field validator for strings.

    Args:
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Optional regex pattern to match
        sanitize: Whether to sanitize the string
        check_xss: Whether to check for XSS patterns
        check_sql_injection: Whether to check for SQL injection patterns

    Returns:
        Validator function
    """

    def validator(value: str) -> str:
        if not value:
            return value

        # Sanitize if requested
        if sanitize:
            value = InputValidator.sanitize_string(value, max_length)

        # Length validation
        if len(value) < min_length:
            raise ValueError(f"String must be at least {min_length} characters long")

        if len(value) > max_length:
            raise ValueError(f"String cannot exceed {max_length} characters")

        # Pattern validation
        if pattern and not pattern.match(value):
            raise ValueError("String does not match required format")

        # Security checks
        if check_xss:
            InputValidator.validate_no_xss(value)

        if check_sql_injection:
            InputValidator.validate_no_sql_injection(value)

        return value

    return validator
