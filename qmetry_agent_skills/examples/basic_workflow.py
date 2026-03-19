"""
Example: Basic QMetry Agent Skill Workflows

This file demonstrates how to use the QMetry agent skills
in various common scenarios.
"""

import os
from qmetry_agent_skills import (
    generate_feature_file_from_pdf,
    validate_qmetry_feature_file,
    create_qmetry_test_case,
    list_qmetry_folders,
    discover_qmetry_custom_fields,
    create_test_cases_from_pdf
)


def example_1_generate_from_pdf():
    """Example 1: Generate feature file from PDF"""
    print("=" * 60)
    print("Example 1: Generate Feature File from PDF")
    print("=" * 60)
    
    result = generate_feature_file_from_pdf(
        pdf_path="requirements/mobile/login_spec.pdf",
        defaults={
            "Apps": "MyApp",
            "Platform": "iOS,Android",
            "Component/Feature": "Authentication",
            "Regression_Type": "New_Features"
        },
        save_to_disk=True
    )
    
    if result["success"]:
        print(f"✓ Generated: {result['feature_file_path']}")
        print(f"  Feature: {result['feature_name']}")
        print(f"  Test Cases: {result['test_case_count']}")
        print(f"\nPreview:\n{result['preview']}")
    else:
        print(f"✗ Error: {result['error_message']}")
    
    return result


def example_2_validate_feature_file():
    """Example 2: Validate feature file"""
    print("\n" + "=" * 60)
    print("Example 2: Validate Feature File")
    print("=" * 60)
    
    result = validate_qmetry_feature_file(
        feature_file_path="features/mobile/authentication/login.feature",
        check_api=True,
        api_key=os.getenv("QMETRY_API_KEY"),
        project_id=os.getenv("QMETRY_PROJECT")
    )
    
    if result["success"]:
        print(f"✓ Valid feature file")
        print(f"  Feature: {result['feature_name']}")
        print(f"  Test Cases: {result['test_case_count']}")
        if result.get("invalid_fields"):
            print(f"  Invalid Fields: {len(result['invalid_fields'])}")
            for field in result["invalid_fields"]:
                print(f"    - {field['field']} (suggestion: {field['suggestion']})")
    else:
        print(f"✗ Validation failed: {result['error_message']}")
    
    return result


def example_3_upload_to_qmetry():
    """Example 3: Upload test cases to QMetry"""
    print("\n" + "=" * 60)
    print("Example 3: Upload Test Cases to QMetry")
    print("=" * 60)
    
    result = create_qmetry_test_case(
        feature_file_path="features/mobile/authentication/login.feature",
        api_key=os.getenv("QMETRY_API_KEY"),
        project_id=os.getenv("QMETRY_PROJECT"),
        target_folder="/Mobile/Authentication",
        dry_run=False  # Set to True to preview without uploading
    )
    
    if result["success"]:
        print(f"✓ Upload successful")
        print(f"  Created: {result['created_count']}")
        print(f"  Updated: {result['updated_count']}")
        print(f"  Failed: {result['failed_count']}")
        print(f"  Folder: {result['target_folder']}")
        print(f"\nTest Cases:")
        for tc in result["test_cases"]:
            status_icon = "✓" if tc["status"] in ["created", "updated"] else "✗"
            print(f"  {status_icon} {tc['name']} ({tc.get('key', 'N/A')})")
    else:
        print(f"✗ Upload failed: {result['error_message']}")
    
    return result


def example_4_list_folders():
    """Example 4: List QMetry folders"""
    print("\n" + "=" * 60)
    print("Example 4: List QMetry Folders")
    print("=" * 60)
    
    result = list_qmetry_folders(
        api_key=os.getenv("QMETRY_API_KEY"),
        project_id=os.getenv("QMETRY_PROJECT")
    )
    
    if result["success"]:
        print(f"✓ Found {result['folder_count']} folders")
        print("\nFolder Structure:")
        _print_folders(result["folders"], indent=0)
    else:
        print(f"✗ Error: {result['error_message']}")
    
    return result


def example_5_end_to_end_workflow():
    """Example 5: End-to-end workflow (PDF → Feature → Upload)"""
    print("\n" + "=" * 60)
    print("Example 5: End-to-End Workflow")
    print("=" * 60)
    
    # Option A: Generate and review (default)
    result = create_test_cases_from_pdf(
        pdf_path="requirements/mobile/login_spec.pdf",
        target_folder="/Mobile/Authentication",
        defaults={
            "Apps": "MyApp",
            "Platform": "iOS,Android",
            "Component/Feature": "Authentication"
        },
        auto_upload=False  # User will review before upload
    )
    
    if result["success"]:
        print(f"✓ Feature file generated")
        print(f"  Path: {result['feature_file_path']}")
        print(f"  Test Cases: {result['test_case_count']}")
        print(f"\n{result['next_step']}")
    else:
        print(f"✗ Error: {result['error_message']}")
    
    return result


def example_6_auto_upload_workflow():
    """Example 6: Auto-upload workflow (skip review)"""
    print("\n" + "=" * 60)
    print("Example 6: Auto-Upload Workflow")
    print("=" * 60)
    
    result = create_test_cases_from_pdf(
        pdf_path="requirements/mobile/login_spec.pdf",
        target_folder="/Mobile/Authentication",
        defaults={
            "Apps": "MyApp",
            "Platform": "iOS,Android",
            "Component/Feature": "Authentication"
        },
        auto_upload=True,  # Upload immediately
        api_key=os.getenv("QMETRY_API_KEY"),
        project_id=os.getenv("QMETRY_PROJECT")
    )
    
    if result["success"]:
        print(f"✓ Complete workflow successful")
        print(f"  Feature: {result['feature_name']}")
        print(f"  Created: {result['created_count']}")
        print(f"  Updated: {result['updated_count']}")
    else:
        print(f"✗ Error: {result['error_message']}")
    
    return result


def _print_folders(folders, indent=0):
    """Helper to print folder hierarchy"""
    for folder in folders:
        print(f"{'  ' * indent}📁 {folder['name']} (id: {folder['id']})")
        if 'children' in folder:
            _print_folders(folder['children'], indent + 1)


if __name__ == "__main__":
    # Run examples
    # Note: Set QMETRY_API_KEY and QMETRY_PROJECT environment variables
    
    # example_1_generate_from_pdf()
    # example_2_validate_feature_file()
    # example_3_upload_to_qmetry()
    # example_4_list_folders()
    # example_5_end_to_end_workflow()
    # example_6_auto_upload_workflow()
    
    print("\nTo run examples, uncomment the desired example function above")
    print("and set QMETRY_API_KEY and QMETRY_PROJECT environment variables")

