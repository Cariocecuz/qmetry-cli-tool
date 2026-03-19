"""
QMetry Agent Skill: Generate Feature File from PDF

Extracts requirements from PDF and generates Gherkin feature files.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import re

from .core import (
    create_error_response,
    create_success_response,
    handle_exception,
    ErrorType
)


def generate_feature_file_from_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    defaults: Optional[Dict[str, str]] = None,
    save_to_disk: bool = True,
    feature_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a Gherkin feature file from a PDF requirements document.
    
    This skill:
    1. Extracts text from PDF using pdfplumber
    2. Uses LLM to identify test scenarios
    3. Generates properly formatted .feature file
    4. Saves to disk (optional) and returns content
    5. Validates syntax
    
    Args:
        pdf_path: Path to PDF requirements document
        output_path: Where to save .feature file (auto-generated if None)
        defaults: Default field values (Apps, Platform, Component/Feature, etc.)
        save_to_disk: If True, saves file to disk; if False, returns content only
        feature_name: Override feature name (extracted from PDF if None)
    
    Returns:
        {
            "success": bool,
            "feature_file_path": str,  # Where file was saved (if save_to_disk=True)
            "feature_file_content": str,  # Full content
            "feature_name": str,
            "test_case_count": int,
            "preview": str,  # First 500 chars
            "warnings": [str],
            "pdf_text_length": int  # Characters extracted from PDF
        }
    
    Example:
        result = generate_feature_file_from_pdf(
            pdf_path="requirements/login_spec.pdf",
            defaults={
                "Apps": "MyApp",
                "Platform": "iOS,Android",
                "Component/Feature": "Authentication",
                "Regression_Type": "New_Features"
            },
            save_to_disk=True
        )
        
        # Returns:
        # {
        #     "success": True,
        #     "feature_file_path": "features/mobile/authentication/login.feature",
        #     "feature_file_content": "@Feature_Defaults:\n@Apps:MyApp\n...",
        #     "feature_name": "User Login",
        #     "test_case_count": 8,
        #     "preview": "@Feature_Defaults:\n@Apps:MyApp\n..."
        # }
    
    Agent Usage:
        When user says: "generate test cases from login_spec.pdf"
        When user says: "create feature file from this PDF"
        When user says: "extract test scenarios from requirements.pdf"
    
    Note:
        This skill requires pdfplumber to be installed:
        pip install pdfplumber
        
        The actual test case generation logic should use the agent's LLM
        capabilities to analyze the PDF content and generate appropriate
        Gherkin scenarios.
    """
    try:
        # Validate PDF exists
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return create_error_response(
                error_type=ErrorType.FILE_NOT_FOUND,
                error_message=f"PDF file not found: {pdf_path}",
                suggestion="Check that the PDF path is correct"
            )
        
        # Extract text from PDF
        try:
            import pdfplumber
        except ImportError:
            return create_error_response(
                error_type=ErrorType.CONFIG_ERROR,
                error_message="pdfplumber not installed",
                suggestion="Install with: pip install pdfplumber"
            )
        
        pdf_text = _extract_pdf_text(pdf_path)
        
        if not pdf_text:
            return create_error_response(
                error_type=ErrorType.PARSE_ERROR,
                error_message="No text extracted from PDF",
                suggestion="Check that the PDF contains readable text (not just images)"
            )
        
        # Set defaults
        if defaults is None:
            defaults = {}
        
        # Ensure required defaults
        if "Apps" not in defaults:
            defaults["Apps"] = "MyApp"
        if "Platform" not in defaults:
            defaults["Platform"] = "iOS,Android"
        if "Regression_Type" not in defaults:
            defaults["Regression_Type"] = "New_Features"
        if "TC_requires_use_of_proxy" not in defaults:
            defaults["TC_requires_use_of_proxy"] = "No"
        
        # Generate feature file content
        # NOTE: This is where the LLM integration happens
        # The agent should use its LLM to analyze pdf_text and generate scenarios
        feature_content = _generate_feature_content(
            pdf_text=pdf_text,
            defaults=defaults,
            feature_name=feature_name,
            pdf_filename=pdf_file.stem
        )
        
        # Determine output path
        if output_path is None and save_to_disk:
            output_path = _generate_output_path(pdf_path, defaults)
        
        # Save to disk if requested
        if save_to_disk and output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(feature_content, encoding='utf-8')
        
        # Parse to count test cases
        from .core import parse_feature_from_string
        feature = parse_feature_from_string(feature_content)
        
        # Build response
        result = {
            "success": True,
            "feature_file_content": feature_content,
            "feature_name": feature.feature_name,
            "test_case_count": len(feature.test_cases),
            "preview": feature_content[:500] + "..." if len(feature_content) > 500 else feature_content,
            "warnings": [],
            "pdf_text_length": len(pdf_text)
        }
        
        if save_to_disk and output_path:
            result["feature_file_path"] = str(output_path)
        
        # Add warnings
        if not feature.defaults.get("Component/Feature"):
            result["warnings"].append("Component/Feature not specified - please fill in manually")
        
        return result
        
    except Exception as e:
        return handle_exception(e, "generating feature file from PDF")


def _extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

    return "\n\n".join(text_parts)


def _generate_output_path(pdf_path: str, defaults: Dict[str, str]) -> str:
    """
    Generate output path co-located with PDF (matches existing pattern).

    Example:
        PDF: "New Features/PullToRefresh/PullToRefresh.pdf"
        → "New Features/PullToRefresh/PullToRefresh_Generated.feature"
    """
    pdf_file = Path(pdf_path)

    # Use same directory as PDF
    output_dir = pdf_file.parent

    # Use PDF stem as base name
    base_name = pdf_file.stem

    # Remove common suffixes
    base_name = base_name.replace("_spec", "").replace("_requirements", "")
    base_name = base_name.replace(" spec", "").replace(" requirements", "")

    # Add _Generated suffix to distinguish from manually created files
    output_filename = f"{base_name}_Generated.feature"

    return str(output_dir / output_filename)


def _generate_feature_content(
    pdf_text: str,
    defaults: Dict[str, str],
    feature_name: Optional[str],
    pdf_filename: str
) -> str:
    """
    Generate Gherkin feature file content from PDF text.

    NOTE: This is a placeholder implementation. In a real agent skill,
    this function should use the agent's LLM to analyze the PDF text
    and generate appropriate test scenarios.

    For Augment integration, the agent would:
    1. Receive the pdf_text
    2. Use its LLM to identify:
       - Feature name and description
       - Acceptance criteria
       - Edge cases
       - User flows
    3. Generate Gherkin scenarios with proper structure
    4. Return the formatted feature file content
    """
    # Build @Feature_Defaults block
    defaults_block = "@Feature_Defaults:\n"
    for key, value in defaults.items():
        defaults_block += f"@{key}:{value}\n"

    # Extract or use provided feature name
    if not feature_name:
        # Try to extract from PDF text (simple heuristic)
        lines = pdf_text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if len(line.strip()) > 5 and len(line.strip()) < 100:
                feature_name = line.strip()
                break
        if not feature_name:
            feature_name = pdf_filename.replace("_", " ").title()

    # Generate feature file template
    # NOTE: In production, this should be generated by LLM based on PDF content
    template = f"""{defaults_block}
Feature: {feature_name}
  As a user
  I want to use this feature
  So that I can achieve my goals

  Background:
    Given the app is installed and launched
    And the user is logged in

  # TC-01
  @positive
  Scenario: Basic functionality works as expected
    Given the user is on the main screen
    When the user performs the primary action
    Then the expected result is displayed

    @Test_Data:
    - Input: Sample data

    @Expected_Result:
    Expected behavior is observed.

# NOTE: This is a template. The agent should analyze the PDF content
# and generate specific test scenarios based on the requirements.
#
# PDF Content Summary:
# - Length: {len(pdf_text)} characters
# - Filename: {pdf_filename}
#
# To generate proper test cases, the agent should:
# 1. Identify acceptance criteria from the PDF
# 2. Extract edge cases and error scenarios
# 3. Map user flows to Gherkin scenarios
# 4. Add appropriate @Test_Data and @Expected_Result blocks
"""

    return template

