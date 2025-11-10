"""
Tests for advanced input validation utilities.
"""
import pytest
from app.core.validation import (
    ValidationPatterns,
    InputValidator,
    create_string_validator
)


class TestValidationPatterns:
    """Test validation patterns."""
    
    def test_name_pattern_valid(self):
        """Test valid names."""
        assert ValidationPatterns.NAME_PATTERN.match("John Doe")
        assert ValidationPatterns.NAME_PATTERN.match("Mary-Jane O'Connor")
        assert ValidationPatterns.NAME_PATTERN.match("Anne Marie")
    
    def test_name_pattern_invalid(self):
        """Test invalid names."""
        assert not ValidationPatterns.NAME_PATTERN.match("John123")
        assert not ValidationPatterns.NAME_PATTERN.match("User@Name")
    
    def test_phone_pattern_valid(self):
        """Test valid phone numbers."""
        assert ValidationPatterns.PHONE_PATTERN.match("+12345678901")
        assert ValidationPatterns.PHONE_PATTERN.match("12345678901")
    
    def test_sql_injection_pattern(self):
        """Test SQL injection detection."""
        assert ValidationPatterns.SQL_INJECTION_PATTERN.search("SELECT * FROM users")
        assert ValidationPatterns.SQL_INJECTION_PATTERN.search("DROP TABLE users")
        assert ValidationPatterns.SQL_INJECTION_PATTERN.search("insert into users")
    
    def test_xss_pattern(self):
        """Test XSS pattern detection."""
        assert ValidationPatterns.XSS_PATTERN.search("<script>alert('xss')</script>")
        assert ValidationPatterns.XSS_PATTERN.search("javascript:alert(1)")
        assert ValidationPatterns.XSS_PATTERN.search("<iframe src='evil'></iframe>")
    
    def test_path_traversal_pattern(self):
        """Test path traversal detection."""
        assert ValidationPatterns.PATH_TRAVERSAL_PATTERN.search("../etc/passwd")
        assert ValidationPatterns.PATH_TRAVERSAL_PATTERN.search("..\\windows\\system32")


class TestInputValidator:
    """Test input validation utilities."""
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        result = InputValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"
        
        result = InputValidator.sanitize_string("<b>Bold</b>")
        assert "&lt;" in result and "&gt;" in result
    
    def test_sanitize_string_max_length(self):
        """Test string sanitization with max length."""
        result = InputValidator.sanitize_string("a" * 100, max_length=10)
        assert len(result) == 10
    
    def test_validate_no_sql_injection_valid(self):
        """Test SQL injection validation with valid input."""
        result = InputValidator.validate_no_sql_injection("normal text")
        assert result == "normal text"
    
    def test_validate_no_sql_injection_invalid(self):
        """Test SQL injection validation with invalid input."""
        with pytest.raises(ValueError, match="SQL keywords"):
            InputValidator.validate_no_sql_injection("SELECT * FROM users")
    
    def test_validate_no_xss_valid(self):
        """Test XSS validation with valid input."""
        result = InputValidator.validate_no_xss("normal text")
        assert result == "normal text"
    
    def test_validate_no_xss_invalid(self):
        """Test XSS validation with invalid input."""
        with pytest.raises(ValueError, match="script patterns"):
            InputValidator.validate_no_xss("<script>alert('xss')</script>")
    
    def test_validate_no_path_traversal_valid(self):
        """Test path traversal validation with valid input."""
        result = InputValidator.validate_no_path_traversal("normal/path")
        assert result == "normal/path"
    
    def test_validate_no_path_traversal_invalid(self):
        """Test path traversal validation with invalid input."""
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.validate_no_path_traversal("../etc/passwd")
    
    def test_validate_name_valid(self):
        """Test name validation with valid input."""
        result = InputValidator.validate_name("John Doe")
        assert result == "John Doe"
    
    def test_validate_name_invalid_empty(self):
        """Test name validation with empty input."""
        with pytest.raises(ValueError, match="cannot be empty"):
            InputValidator.validate_name("")
    
    def test_validate_name_invalid_too_short(self):
        """Test name validation with too short input."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            InputValidator.validate_name("A")
    
    def test_validate_name_invalid_characters(self):
        """Test name validation with invalid characters."""
        with pytest.raises(ValueError, match="letters, spaces, hyphens"):
            InputValidator.validate_name("John123")
    
    def test_validate_phone_number_valid(self):
        """Test phone number validation with valid input."""
        result = InputValidator.validate_phone_number("+1234567890")
        assert result == "+1234567890"
        
        # Test with formatting characters
        result = InputValidator.validate_phone_number("+1 (234) 567-890")
        assert result == "+1234567890"
    
    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid input."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            InputValidator.validate_phone_number("0123456789")  # Starts with 0, invalid
        
        with pytest.raises(ValueError, match="Invalid phone number"):
            InputValidator.validate_phone_number("abc123")  # Contains letters
    
    def test_validate_slug_valid(self):
        """Test slug validation with valid input."""
        result = InputValidator.validate_slug("my-valid-slug")
        assert result == "my-valid-slug"
    
    def test_validate_slug_invalid_characters(self):
        """Test slug validation with invalid characters."""
        with pytest.raises(ValueError, match="lowercase letters, numbers"):
            InputValidator.validate_slug("My_Invalid_Slug")
    
    def test_validate_slug_too_short(self):
        """Test slug validation with too short input."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            InputValidator.validate_slug("ab")
    
    def test_validate_amount_valid(self):
        """Test amount validation with valid input."""
        result = InputValidator.validate_amount(100.50)
        assert result == 100.50
    
    def test_validate_amount_too_small(self):
        """Test amount validation with too small value."""
        with pytest.raises(ValueError, match="at least"):
            InputValidator.validate_amount(0.001)
    
    def test_validate_amount_too_large(self):
        """Test amount validation with too large value."""
        with pytest.raises(ValueError, match="cannot exceed"):
            InputValidator.validate_amount(2000000.00)
    
    def test_validate_amount_too_many_decimals(self):
        """Test amount validation with too many decimal places."""
        with pytest.raises(ValueError, match="2 decimal places"):
            InputValidator.validate_amount(100.123)
    
    def test_validate_list_input_valid(self):
        """Test list input validation with valid input."""
        result = InputValidator.validate_list_input(["item1", "item2", "item3"])
        assert len(result) == 3
    
    def test_validate_list_input_too_few_items(self):
        """Test list input validation with too few items."""
        with pytest.raises(ValueError, match="at least"):
            InputValidator.validate_list_input([], min_items=1)
    
    def test_validate_list_input_too_many_items(self):
        """Test list input validation with too many items."""
        with pytest.raises(ValueError, match="cannot contain more than"):
            InputValidator.validate_list_input(["item"] * 200, max_items=100)
    
    def test_validate_list_input_xss_in_item(self):
        """Test list input validation with XSS in item."""
        with pytest.raises(ValueError, match="script patterns"):
            InputValidator.validate_list_input(["normal", "<script>alert('xss')</script>"])


class TestCreateStringValidator:
    """Test string validator factory function."""
    
    def test_create_string_validator_min_length(self):
        """Test string validator with min length."""
        validator = create_string_validator(min_length=5)
        
        with pytest.raises(ValueError, match="at least 5 characters"):
            validator("abc")
        
        result = validator("abcdef")
        assert result == "abcdef"
    
    def test_create_string_validator_max_length(self):
        """Test string validator with max length."""
        validator = create_string_validator(max_length=10)
        
        # Should truncate
        result = validator("a" * 20)
        assert len(result) <= 10
    
    def test_create_string_validator_pattern(self):
        """Test string validator with pattern."""
        import re
        validator = create_string_validator(pattern=re.compile(r"^\d+$"))
        
        with pytest.raises(ValueError, match="does not match required format"):
            validator("abc123")
        
        result = validator("12345")
        assert result == "12345"
    
    def test_create_string_validator_xss_check(self):
        """Test string validator with XSS check."""
        validator = create_string_validator(check_xss=True)
        
        with pytest.raises(ValueError, match="script patterns"):
            validator("<script>alert('xss')</script>")
    
    def test_create_string_validator_sql_injection_check(self):
        """Test string validator with SQL injection check."""
        validator = create_string_validator(check_sql_injection=True)
        
        with pytest.raises(ValueError, match="SQL keywords"):
            validator("SELECT * FROM users")
