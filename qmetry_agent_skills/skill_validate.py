"""
QMetry Agent Skill: Validate Feature File

Validates Gherkin feature files for syntax and field correctness.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from qmetry_tool.gherkin_parser import parse_feature_file
from qmetry_tool.qmetry_api_client import QMetryClient

from .core import (
    AgentQMetryConfig,
    parse_feature_from_string,
    create_error_response,
    create_validation_error_response,
    create_success_response,
    handle_exception,
    ErrorType
)


def validate_qmetry_feature_file(
    feature_file_path: Optional[str] = None,
    feature_file_content: Optional[str] = None,
    check_api: bool = True,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate a Gherkin feature file for syntax and field correctness.
    
    This skill validates:
    1. Gherkin syntax (Feature, Scenario, Given/When/Then)
    2. Required blocks (@Feature_Defaults:, @Test_Data:, @Expected_Result:)
    3. Field names against QMetry API (if check_api=True)
    4. Provides typo suggestions for invalid fields
    
    Args:
        feature_file_path: Path to .feature file (mutually exclusive with feature_file_content)
        feature_file_content: Feature file content as string (mutually exclusive with feature_file_path)
        check_api: If True, validates field names against QMetry API
        api_key: QMetry API key (required if check_api=True)
        project_id: QMetry project ID (required if check_api=True)
    
    Returns:
        {
            "success": bool,
            "valid": bool,
            "feature_name": str,
            "feature_description": str,
            "test_case_count": int,
            "background_steps_count": int,
            "defaults": {"field": "value"},
            "invalid_fields": [{"field": str, "suggestion": str}],
            "warnings": [str],
            "errors": [str]
        }
    
    Example:
        # Validate from file
        result = validate_qmetry_feature_file(
            feature_file_path="features/mobile/login.feature",
            check_api=True,
            api_key="abc123...",
            project_id="12345"
        )
        
        # Validate from string
        result = validate_qmetry_feature_file(
            feature_file_content=feature_content,
            check_api=False
        )
    
    Agent Usage:
        When user says: "validate the login feature file"
        When user says: "check if my test cases are correct"
        When user says: "make sure the fields are valid before uploading"
    """
    try:
        # Validate inputs
        if not feature_file_path and not feature_file_content:
            return create_error_response(
                error_type=ErrorType.VALIDATION_ERROR,
                error_message="Must provide either feature_file_path or feature_file_content"
            )
        
        if feature_file_path and feature_file_content:
            return create_error_response(
                error_type=ErrorType.VALIDATION_ERROR,
                error_message="Cannot provide both feature_file_path and feature_file_content"
            )
        
        # Parse feature file
        if feature_file_content:
            feature = parse_feature_from_string(
                feature_file_content,
                file_name="generated.feature"
            )
        else:
            feature = parse_feature_file(feature_file_path)
        
        # Basic validation results
        result = {
            "success": True,
            "valid": True,
            "feature_name": feature.feature_name,
            "feature_description": feature.feature_description,
            "test_case_count": len(feature.test_cases),
            "background_steps_count": len(feature.background_steps),
            "defaults": feature.defaults,
            "invalid_fields": [],
            "warnings": [],
            "errors": []
        }
        
        # Check for missing required elements
        if not feature.feature_name:
            result["errors"].append("Missing Feature: declaration")
            result["valid"] = False
        
        if not feature.test_cases:
            result["warnings"].append("No test cases (Scenarios) found")
        
        if not feature.defaults:
            result["warnings"].append("No @Feature_Defaults: block found")
        
        # Validate fields against QMetry API
        if check_api:
            if not api_key or not project_id:
                return create_error_response(
                    error_type=ErrorType.CONFIG_ERROR,
                    error_message="api_key and project_id required when check_api=True"
                )
            
            # Initialize config and client
            config = AgentQMetryConfig.from_parameters(
                api_key=api_key,
                project=project_id
            )
            client = QMetryClient(config.to_base_config())
            
            # Collect all field names
            all_fields = set(feature.defaults.keys())
            for tc in feature.test_cases:
                all_fields.update(tc.overrides.keys())
            
            # Remove non-custom fields
            all_fields.discard('Folder')
            all_fields.discard('Status')
            all_fields.discard('Priority')
            
            # Validate each field
            invalid_fields = []
            for field in sorted(all_fields):
                field_id = client.get_field_id(field)
                if not field_id:
                    suggestion = client.find_similar_field(field)
                    invalid_fields.append({
                        "field": field,
                        "suggestion": suggestion if suggestion else "No suggestion available"
                    })
            
            result["invalid_fields"] = invalid_fields
            
            if invalid_fields:
                result["valid"] = False
                result["success"] = False
                return create_validation_error_response(
                    invalid_fields=invalid_fields,
                    total_fields=len(all_fields)
                )
        
        # Return success
        if result["errors"]:
            result["valid"] = False
            result["success"] = False
        
        return result
        
    except FileNotFoundError as e:
        return handle_exception(e, "validating feature file")
    except Exception as e:
        return handle_exception(e, "validating feature file")

