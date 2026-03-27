"""
QMetry Agent Skills for Augment

This module provides AI agent skills for interacting with QMetry Test Management.
All skills return structured JSON responses suitable for agent workflows.

Available Skills:
- generate_feature_file_from_pdf: Generate Gherkin feature files from PDF requirements
- generate_feature_file_from_confluence: Generate Gherkin feature files from Confluence specs
- validate_qmetry_feature_file: Validate feature file syntax and fields
- create_qmetry_test_case: Upload test cases to QMetry
- list_qmetry_folders: List available folders in QMetry
- discover_qmetry_custom_fields: Discover custom fields and options
- search_qmetry_test_cases: Search test cases by text/field filters (cached)
- get_qmetry_test_case: Retrieve a single test case by key
- manage_qmetry_cache: View or clear the local TC search cache
- create_test_cases_from_pdf: End-to-end workflow (PDF → Feature → Upload)
- create_test_cases_from_confluence: End-to-end workflow (Confluence → Feature → Upload)

Configuration:
    Skills support multiple configuration methods:
    1. Explicit parameters (api_key, project_id)
    2. Environment variables (QMETRY_API_KEY, QMETRY_PROJECT)
    3. Config file (.qmetry_config.yaml)

Example Usage:
    # Generate feature file from PDF
    from qmetry_agent_skills import generate_feature_file_from_pdf
    
    result = generate_feature_file_from_pdf(
        pdf_path="requirements/login_spec.pdf",
        defaults={
            "Apps": "MyApp",
            "Platform": "iOS,Android",
            "Component/Feature": "Authentication"
        }
    )
    
    # Upload to QMetry
    from qmetry_agent_skills import create_qmetry_test_case
    
    result = create_qmetry_test_case(
        feature_file_path=result["feature_file_path"],
        api_key="your-api-key",
        project_id="12345",
        target_folder="/Mobile/Authentication"
    )
"""

from .skill_generate import generate_feature_file_from_pdf, generate_feature_file_from_confluence
from .skill_validate import validate_qmetry_feature_file
from .skill_upload import create_qmetry_test_case
from .skill_query import (
    list_qmetry_folders,
    discover_qmetry_custom_fields,
    search_qmetry_test_cases,
    get_qmetry_test_case,
    manage_qmetry_cache,
)
from .skill_combined import create_test_cases_from_pdf, create_test_cases_from_confluence

from .core import (
    AgentQMetryConfig,
    parse_feature_from_string,
    ErrorType,
    create_error_response,
    create_success_response
)

__version__ = "1.0.0"

__all__ = [
    # Core Skills
    'generate_feature_file_from_pdf',
    'generate_feature_file_from_confluence',
    'validate_qmetry_feature_file',
    'create_qmetry_test_case',
    'list_qmetry_folders',
    'discover_qmetry_custom_fields',
    'search_qmetry_test_cases',
    'get_qmetry_test_case',
    'manage_qmetry_cache',

    # Combined Workflows
    'create_test_cases_from_pdf',
    'create_test_cases_from_confluence',

    # Core Utilities
    'AgentQMetryConfig',
    'parse_feature_from_string',
    'ErrorType',
    'create_error_response',
    'create_success_response'
]

