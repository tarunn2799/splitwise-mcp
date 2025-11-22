"""Error handling and custom exceptions."""

from dataclasses import dataclass
from typing import Optional, Any, Dict, List
import re


@dataclass
class MCPError:
    """Standardized error response for MCP tools."""
    
    error_type: str  # "authentication", "validation", "not_found", etc.
    message: str
    status_code: int
    details: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        result = {
            "error_type": self.error_type,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation (optional)
            details: Additional error details (optional)
        """
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(self.message)


class RateLimitError(Exception):
    """Exception raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (optional)
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_required(value: Any, field_name: str) -> None:
    """Validate that a required field is provided and not empty.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If value is None or empty string
    """
    if value is None:
        raise ValidationError(
            f"{field_name} is required",
            field=field_name,
            details={"validation": "required"}
        )
    
    if isinstance(value, str) and not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            details={"validation": "not_empty"}
        )


def validate_positive_number(value: Any, field_name: str) -> None:
    """Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If value is not a positive number
    """
    try:
        num = float(value) if isinstance(value, str) else value
        if num <= 0:
            raise ValidationError(
                f"{field_name} must be a positive number",
                field=field_name,
                details={"validation": "positive", "value": value}
            )
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a valid number",
            field=field_name,
            details={"validation": "numeric", "value": value}
        )


def validate_currency_code(currency_code: str) -> None:
    """Validate currency code format.
    
    Args:
        currency_code: Currency code to validate (e.g., "USD", "EUR")
        
    Raises:
        ValidationError: If currency code format is invalid
    """
    if not currency_code or not isinstance(currency_code, str):
        raise ValidationError(
            "currency_code must be a non-empty string",
            field="currency_code",
            details={"validation": "format"}
        )
    
    if not re.match(r'^[A-Z]{3}$', currency_code):
        raise ValidationError(
            "currency_code must be a 3-letter uppercase code (e.g., USD, EUR, GBP)",
            field="currency_code",
            details={"validation": "format", "value": currency_code}
        )


def validate_date_format(date_str: str, field_name: str = "date") -> None:
    """Validate ISO 8601 date format.
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError(
            f"{field_name} must be a non-empty string",
            field=field_name,
            details={"validation": "format"}
        )
    
    # Basic ISO 8601 format check (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$'
    if not re.match(iso_pattern, date_str):
        raise ValidationError(
            f"{field_name} must be in ISO 8601 format (e.g., 2024-01-15 or 2024-01-15T10:30:00Z)",
            field=field_name,
            details={"validation": "format", "value": date_str}
        )


def validate_email(email: str) -> None:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError(
            "email must be a non-empty string",
            field="email",
            details={"validation": "format"}
        )
    
    # Basic email format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(
            "email must be a valid email address",
            field="email",
            details={"validation": "format", "value": email}
        )


def validate_range(value: Any, field_name: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> None:
    """Validate that a value is within a specified range.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        
    Raises:
        ValidationError: If value is outside the specified range
    """
    try:
        num = float(value) if isinstance(value, str) else value
        
        if min_val is not None and num < min_val:
            raise ValidationError(
                f"{field_name} must be at least {min_val}",
                field=field_name,
                details={"validation": "range", "min": min_val, "value": value}
            )
        
        if max_val is not None and num > max_val:
            raise ValidationError(
                f"{field_name} must be at most {max_val}",
                field=field_name,
                details={"validation": "range", "max": max_val, "value": value}
            )
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a valid number",
            field=field_name,
            details={"validation": "numeric", "value": value}
        )


def validate_choice(value: Any, field_name: str, choices: List[Any]) -> None:
    """Validate that a value is one of the allowed choices.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        choices: List of allowed values
        
    Raises:
        ValidationError: If value is not in the allowed choices
    """
    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(str(c) for c in choices)}",
            field=field_name,
            details={"validation": "choice", "choices": choices, "value": value}
        )


def validate_user_split(users: List[Dict[str, Any]]) -> None:
    """Validate user split information for expenses.
    
    Args:
        users: List of user split dictionaries
        
    Raises:
        ValidationError: If user split data is invalid
    """
    if not users or not isinstance(users, list):
        raise ValidationError(
            "users must be a non-empty list",
            field="users",
            details={"validation": "format"}
        )
    
    for i, user in enumerate(users):
        if not isinstance(user, dict):
            raise ValidationError(
                f"users[{i}] must be a dictionary",
                field="users",
                details={"validation": "format", "index": i}
            )
        
        if "user_id" not in user:
            raise ValidationError(
                f"users[{i}] must include user_id",
                field="users",
                details={"validation": "required_field", "index": i, "missing_field": "user_id"}
            )
        
        # Validate paid_share and owed_share if provided
        for share_field in ["paid_share", "owed_share"]:
            if share_field in user:
                try:
                    share_val = float(user[share_field])
                    if share_val < 0:
                        raise ValidationError(
                            f"users[{i}].{share_field} must be non-negative",
                            field="users",
                            details={"validation": "non_negative", "index": i, "field": share_field}
                        )
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"users[{i}].{share_field} must be a valid number",
                        field="users",
                        details={"validation": "numeric", "index": i, "field": share_field}
                    )
