"""
QMetry Agent Skill: Combined Workflows

End-to-end workflows combining multiple skills.
"""

from typing import Optional, Dict, Any

from .skill_generate import generate_feature_file_from_pdf
from .skill_validate import validate_qmetry_feature_file
from .skill_upload import create_qmetry_test_case

from .core import (
    create_error_response,
    create_success_response,
    handle_exception,
    ErrorType
)


def create_test_cases_from_pdf(
    pdf_path: str,
    target_folder: str,
    defaults: Optional[Dict[str, str]] = None,
    auto_upload: bool = False,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    save_feature_file: bool = True,
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Complete workflow: PDF → Feature File → QMetry Upload.
    
    This skill orchestrates the full workflow:
    1. Generate feature file from PDF
    2. Validate the generated content
    3. Optionally upload to QMetry (if auto_upload=True)
    
    Args:
        pdf_path: Path to PDF requirements document
        target_folder: Target folder in QMetry (e.g., "/Mobile/Authentication")
        defaults: Default field values (Apps, Platform, Component/Feature, etc.)
        auto_upload: If True, uploads immediately; if False, returns preview for review
        api_key: QMetry API key (required if auto_upload=True)
        project_id: QMetry project ID (required if auto_upload=True)
        save_feature_file: If True, saves .feature file to disk
        skip_validation: Skip field validation (not recommended)
    
    Returns:
        If auto_upload=False (default):
        {
            "success": bool,
            "feature_file_path": str,
            "feature_file_content": str,
            "feature_name": str,
            "test_case_count": int,
            "preview": str,
            "ready_for_upload": bool,
            "next_step": str  # Instructions for user
        }
        
        If auto_upload=True:
        {
            "success": bool,
            "feature_file_path": str,
            "created_count": int,
            "updated_count": int,
            "failed_count": int,
            "test_cases": [...],
            "target_folder": str
        }
    
    Example (with review):
        result = create_test_cases_from_pdf(
            pdf_path="requirements/login_spec.pdf",
            target_folder="/Mobile/Authentication",
            defaults={"Apps": "MyApp", "Platform": "iOS,Android"},
            auto_upload=False  # User will review before upload
        )
        # User reviews the generated file
        # Then calls create_qmetry_test_case() to upload
    
    Example (auto-upload):
        result = create_test_cases_from_pdf(
            pdf_path="requirements/login_spec.pdf",
            target_folder="/Mobile/Authentication",
            defaults={"Apps": "MyApp", "Platform": "iOS,Android"},
            auto_upload=True,
            api_key="abc123...",
            project_id="12345"
        )
    
    Agent Usage:
        When user says: "create test cases from login_spec.pdf and upload to /Mobile/Authentication"
        When user says: "generate and upload test cases from this PDF"
        When user says: "process requirements.pdf and create test cases in QMetry"
    """
    try:
        # Step 1: Generate feature file from PDF
        gen_result = generate_feature_file_from_pdf(
            pdf_path=pdf_path,
            defaults=defaults,
            save_to_disk=save_feature_file
        )
        
        if not gen_result["success"]:
            return gen_result
        
        feature_content = gen_result["feature_file_content"]
        feature_path = gen_result.get("feature_file_path")
        
        # Step 2: Validate the generated content
        if not skip_validation and auto_upload:
            val_result = validate_qmetry_feature_file(
                feature_file_content=feature_content,
                check_api=True,
                api_key=api_key,
                project_id=project_id
            )
            
            if not val_result["success"]:
                return {
                    **gen_result,
                    "validation_errors": val_result.get("invalid_fields", []),
                    "success": False,
                    "error_message": "Generated feature file has validation errors"
                }
        
        # Step 3a: If auto_upload=False, return preview for user review
        if not auto_upload:
            return {
                **gen_result,
                "ready_for_upload": True,
                "target_folder": target_folder,
                "next_step": (
                    f"Review the generated file at {feature_path}, then say: "
                    f"'upload {feature_path} to {target_folder}'"
                )
            }
        
        # Step 3b: If auto_upload=True, upload immediately
        upload_result = create_qmetry_test_case(
            feature_file_content=feature_content,
            api_key=api_key,
            project_id=project_id,
            target_folder=target_folder,
            skip_validation=skip_validation,
            auto_approve=True
        )
        
        # Combine results
        return {
            **upload_result,
            "feature_file_path": feature_path,
            "feature_name": gen_result["feature_name"],
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        return handle_exception(e, "creating test cases from PDF")

