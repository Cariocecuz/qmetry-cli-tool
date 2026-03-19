"""
Structured Error Handling for Agent Skills

Provides consistent error response format and error types
for agent skills to handle gracefully.
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorType(str, Enum):
    """Standard error types for agent skills."""
    FILE_NOT_FOUND = "file_not_found"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


def create_error_response(
    error_type: ErrorType,
    error_message: str,
    suggestion: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response for agent skills.
    
    Args:
        error_type: Type of error from ErrorType enum
        error_message: Human-readable error message
        suggestion: Optional suggestion for fixing the error
        details: Optional additional error details
    
    Returns:
        Structured error response dictionary
    
    Example:
        return create_error_response(
            error_type=ErrorType.FILE_NOT_FOUND,
            error_message="Feature file not found: login.feature",
            suggestion="Check that the file path is correct",
            details={"file_path": "features/login.feature"}
        )
    """
    response = {
        "success": False,
        "error_type": error_type.value,
        "error_message": error_message
    }
    
    if suggestion:
        response["suggestion"] = suggestion
    
    if details:
        response["details"] = details
    
    return response


def create_validation_error_response(
    invalid_fields: List[Dict[str, str]],
    total_fields: int
) -> Dict[str, Any]:
    """
    Create a validation error response with field-specific details.
    
    Args:
        invalid_fields: List of invalid fields with suggestions
        total_fields: Total number of fields validated
    
    Returns:
        Structured validation error response
    
    Example:
        return create_validation_error_response(
            invalid_fields=[
                {"field": "Platfrom", "suggestion": "Platform"},
                {"field": "Componet", "suggestion": "Component/Feature"}
            ],
            total_fields=5
        )
    """
    return {
        "success": False,
        "error_type": ErrorType.VALIDATION_ERROR.value,
        "error_message": f"{len(invalid_fields)} invalid field(s) found",
        "invalid_fields": invalid_fields,
        "valid_fields": total_fields - len(invalid_fields),
        "total_fields": total_fields,
        "suggestion": "Fix field names or use skip_validation=True (not recommended)"
    }


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response for agent skills.
    
    Args:
        message: Success message
        data: Optional response data
    
    Returns:
        Structured success response dictionary
    
    Example:
        return create_success_response(
            message="Successfully uploaded 5 test cases",
            data={
                "created_count": 5,
                "updated_count": 0,
                "test_cases": [...]
            }
        )
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data:
        response.update(data)
    
    return response


def handle_exception(e: Exception, context: str = "") -> Dict[str, Any]:
    """
    Convert an exception to a structured error response.
    
    Args:
        e: The exception to handle
        context: Optional context about where the error occurred
    
    Returns:
        Structured error response
    
    Example:
        try:
            feature = parse_feature_file(path)
        except Exception as e:
            return handle_exception(e, "parsing feature file")
    """
    error_message = str(e)
    if context:
        error_message = f"{context}: {error_message}"
    
    # Map exception types to ErrorType
    if isinstance(e, FileNotFoundError):
        return create_error_response(
            error_type=ErrorType.FILE_NOT_FOUND,
            error_message=error_message,
            suggestion="Check that the file path is correct"
        )
    elif isinstance(e, ValueError):
        return create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            error_message=error_message,
            suggestion="Check input parameters and values"
        )
    elif isinstance(e, PermissionError):
        return create_error_response(
            error_type=ErrorType.PERMISSION_ERROR,
            error_message=error_message,
            suggestion="Check file permissions or API key permissions"
        )
    else:
        return create_error_response(
            error_type=ErrorType.UNKNOWN_ERROR,
            error_message=error_message
        )

