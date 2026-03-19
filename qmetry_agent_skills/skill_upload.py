"""
QMetry Agent Skill: Upload Test Cases

Creates or updates test cases in QMetry from Gherkin feature files.
"""

from typing import Optional, Dict, Any, List
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


def create_qmetry_test_case(
    feature_file_path: Optional[str] = None,
    feature_file_content: Optional[str] = None,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    target_folder: Optional[str] = None,
    default_folder: str = "/Uncategorized",
    dry_run: bool = False,
    skip_validation: bool = False,
    auto_approve: bool = False
) -> Dict[str, Any]:
    """
    Create or update test cases in QMetry from a Gherkin feature file.
    
    This skill:
    1. Parses the feature file (from path or content)
    2. Validates fields against QMetry API (unless skip_validation=True)
    3. Creates or updates test cases in QMetry
    4. Handles duplicate detection (updates existing test cases)
    5. Returns detailed results for each test case
    
    Args:
        feature_file_path: Path to .feature file (mutually exclusive with feature_file_content)
        feature_file_content: Feature file content as string (mutually exclusive with feature_file_path)
        api_key: QMetry API key (or use environment variable QMETRY_API_KEY)
        project_id: QMetry project ID (or use environment variable QMETRY_PROJECT)
        target_folder: Target folder path in QMetry (e.g., "/Mobile/Authentication")
        default_folder: Default folder if not specified (default: "/Uncategorized")
        dry_run: If True, validates but doesn't create test cases
        skip_validation: Skip field validation (not recommended)
        auto_approve: If True, skips confirmation prompt (for agent workflows)
    
    Returns:
        {
            "success": bool,
            "created_count": int,
            "updated_count": int,
            "failed_count": int,
            "test_cases": [
                {
                    "name": str,
                    "key": str,  # QMetry test case key (e.g., "MOB-TC-123")
                    "status": "created" | "updated" | "failed",
                    "error": str  # Only present if status="failed"
                }
            ],
            "target_folder": str,
            "dry_run": bool,
            "errors": [str]
        }
    
    Example:
        # Upload from file
        result = create_qmetry_test_case(
            feature_file_path="features/mobile/login.feature",
            api_key="abc123...",
            project_id="12345",
            target_folder="/Mobile/Authentication"
        )
        
        # Upload from string (in-memory)
        result = create_qmetry_test_case(
            feature_file_content=generated_content,
            target_folder="/Mobile/Browse",
            dry_run=True  # Preview first
        )
    
    Agent Usage:
        When user says: "upload the login test cases to QMetry"
        When user says: "create test cases in /Mobile/Authentication"
        When user says: "push these test cases to QMetry"
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
        
        # Initialize configuration
        config = AgentQMetryConfig.auto_detect(
            api_key=api_key,
            project=project_id,
            default_folder=default_folder
        )
        
        # Parse feature file
        if feature_file_content:
            feature = parse_feature_from_string(
                feature_file_content,
                file_name="generated.feature"
            )
        else:
            feature = parse_feature_file(feature_file_path)
        
        # Determine target folder
        if not target_folder:
            target_folder = feature.defaults.get('Folder', config.default_folder)
        
        # Initialize API client
        client = QMetryClient(config.to_base_config())
        
        # Validate fields against QMetry (unless skipped)
        if not skip_validation:
            validation_result = _validate_fields(client, feature)
            if not validation_result["valid"]:
                return create_validation_error_response(
                    invalid_fields=validation_result["invalid_fields"],
                    total_fields=validation_result["total_fields"]
                )
        
        # Dry run mode - return preview
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "test_case_count": len(feature.test_cases),
                "target_folder": target_folder,
                "test_cases": [{"name": tc.name} for tc in feature.test_cases],
                "message": f"Would create {len(feature.test_cases)} test cases in {target_folder}"
            }
        
        # Get or create folder
        folder_id = client.get_or_create_folder_path(target_folder)
        if folder_id is None:
            return create_error_response(
                error_type=ErrorType.PERMISSION_ERROR,
                error_message=f"Failed to create folder: {target_folder}",
                suggestion="Create folder manually in QMetry or check API key permissions"
            )
        
        # Upload test cases
        results = _upload_test_cases(client, feature, folder_id, config.project)
        
        # Add metadata
        results["target_folder"] = target_folder
        results["dry_run"] = False
        
        return results
        
    except FileNotFoundError as e:
        return handle_exception(e, "uploading test cases")
    except Exception as e:
        return handle_exception(e, "uploading test cases")


def _validate_fields(client: QMetryClient, feature) -> Dict[str, Any]:
    """
    Validate all fields in feature file against QMetry API.

    Returns:
        {
            "valid": bool,
            "invalid_fields": [{"field": str, "suggestion": str}],
            "total_fields": int
        }
    """
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

    return {
        "valid": len(invalid_fields) == 0,
        "invalid_fields": invalid_fields,
        "total_fields": len(all_fields)
    }


def _upload_test_cases(
    client: QMetryClient,
    feature,
    folder_id: int,
    project_id: str
) -> Dict[str, Any]:
    """
    Upload all test cases from feature file to QMetry.

    Returns:
        {
            "success": bool,
            "created_count": int,
            "updated_count": int,
            "failed_count": int,
            "test_cases": [...]
        }
    """
    results = {
        "success": True,
        "created_count": 0,
        "updated_count": 0,
        "failed_count": 0,
        "test_cases": [],
        "errors": []
    }

    for tc in feature.test_cases:
        # Merge defaults with overrides
        merged_fields = {**feature.defaults, **tc.overrides}
        merged_fields.pop('Folder', None)
        merged_fields.pop('Status', None)
        merged_fields.pop('Priority', None)

        # Build test case data
        precondition = '\n'.join(feature.background_steps)
        steps = tc.steps

        # Check for existing test case
        existing = client.find_existing_tc(tc.name, str(folder_id))

        if existing:
            # Update existing test case
            result = client.update_test_case(
                tc_id=existing['id'],
                version_no=existing['versionNo'],
                summary=tc.name,
                description=feature.feature_description,
                precondition=precondition,
                steps=steps,
                test_data=tc.test_data,
                expected_result=tc.expected_result,
                folder_id=str(folder_id),
                custom_fields=merged_fields
            )

            if result.success:
                results["updated_count"] += 1
                results["test_cases"].append({
                    "name": tc.name,
                    "key": existing['key'],
                    "status": "updated"
                })
            else:
                results["failed_count"] += 1
                results["errors"].append(f"{tc.name}: {result.error}")
                results["test_cases"].append({
                    "name": tc.name,
                    "status": "failed",
                    "error": result.error
                })
        else:
            # Create new test case
            result = client.create_test_case(
                summary=tc.name,
                description=feature.feature_description,
                precondition=precondition,
                steps=steps,
                test_data=tc.test_data,
                expected_result=tc.expected_result,
                folder_id=folder_id,
                custom_fields=merged_fields
            )

            if result.success:
                results["created_count"] += 1
                results["test_cases"].append({
                    "name": tc.name,
                    "key": result.data.get('key', 'N/A'),
                    "status": "created"
                })
            else:
                results["failed_count"] += 1
                results["errors"].append(f"{tc.name}: {result.error}")
                results["test_cases"].append({
                    "name": tc.name,
                    "status": "failed",
                    "error": result.error
                })

    results["success"] = results["failed_count"] == 0
    return results

