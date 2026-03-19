# QMetry Agent Skills for Augment

This document describes the AI agent skills for QMetry Test Management integration.

## Overview

The QMetry Agent Skills module provides a set of functions that enable AI agents (like Augment) to:
- Generate Gherkin feature files from PDF requirements
- Validate feature files for syntax and field correctness
- Upload test cases to QMetry via REST API
- Query QMetry metadata (folders, custom fields)
- Orchestrate end-to-end workflows

All skills return structured JSON responses suitable for agent workflows.

---

## Installation

```bash
# Install dependencies
pip install pyyaml certifi pdfplumber

# Set environment variables (optional)
export QMETRY_API_KEY="your-api-key"
export QMETRY_PROJECT="12345"
```

---

## Available Skills

### 1. `generate_feature_file_from_pdf`

Generate Gherkin feature files from PDF requirements documents.

**Function Signature:**
```python
def generate_feature_file_from_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    defaults: Optional[Dict[str, str]] = None,
    save_to_disk: bool = True,
    feature_name: Optional[str] = None
) -> Dict[str, Any]
```

**Example:**
```python
from qmetry_agent_skills import generate_feature_file_from_pdf

result = generate_feature_file_from_pdf(
    pdf_path="requirements/login_spec.pdf",
    defaults={
        "Apps": "MyApp",
        "Platform": "iOS,Android",
        "Component/Feature": "Authentication"
    }
)

print(result["feature_file_path"])  # features/mobile/authentication/login.feature
print(result["test_case_count"])    # 8
```

**Agent Usage:**
- "Generate test cases from login_spec.pdf"
- "Create feature file from this PDF"
- "Extract test scenarios from requirements.pdf"

---

### 2. `validate_qmetry_feature_file`

Validate feature files for syntax and field correctness against QMetry.

**Function Signature:**
```python
def validate_qmetry_feature_file(
    feature_file_path: Optional[str] = None,
    feature_file_content: Optional[str] = None,
    check_api: bool = True,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]
```

**Example:**
```python
from qmetry_agent_skills import validate_qmetry_feature_file

result = validate_qmetry_feature_file(
    feature_file_path="features/mobile/login.feature",
    check_api=True
)

if result["valid"]:
    print(f"✓ Valid: {result['test_case_count']} test cases")
else:
    for field in result["invalid_fields"]:
        print(f"✗ {field['field']} → {field['suggestion']}")
```

**Agent Usage:**
- "Validate the login feature file"
- "Check if my test cases are correct"
- "Make sure the fields are valid before uploading"

---

### 3. `create_qmetry_test_case`

Upload test cases to QMetry from feature files.

**Function Signature:**
```python
def create_qmetry_test_case(
    feature_file_path: Optional[str] = None,
    feature_file_content: Optional[str] = None,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    target_folder: Optional[str] = None,
    dry_run: bool = False,
    skip_validation: bool = False
) -> Dict[str, Any]
```

**Example:**
```python
from qmetry_agent_skills import create_qmetry_test_case

result = create_qmetry_test_case(
    feature_file_path="features/mobile/login.feature",
    target_folder="/Mobile/Authentication",
    dry_run=False
)

print(f"Created: {result['created_count']}")
print(f"Updated: {result['updated_count']}")
```

**Agent Usage:**
- "Upload the login test cases to QMetry"
- "Create test cases in /Mobile/Authentication"
- "Push these test cases to QMetry"

---

### 4. `list_qmetry_folders`

List all folders in a QMetry project.

**Function Signature:**
```python
def list_qmetry_folders(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]
```

**Example:**
```python
from qmetry_agent_skills import list_qmetry_folders

result = list_qmetry_folders()

for folder in result["folders"]:
    print(f"{folder['path']} (id: {folder['id']})")
```

**Agent Usage:**
- "Show me the QMetry folders"
- "List available folders in QMetry"
- "Where can I upload test cases?"

---

### 5. `discover_qmetry_custom_fields`

Discover custom fields and their options in QMetry.

**Function Signature:**
```python
def discover_qmetry_custom_fields(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]
```

**Agent Usage:**
- "What custom fields are available?"
- "Show me the QMetry fields"
- "What values can I use for Platform?"

---

### 6. `create_test_cases_from_pdf`

End-to-end workflow: PDF → Feature File → QMetry Upload.

**Function Signature:**
```python
def create_test_cases_from_pdf(
    pdf_path: str,
    target_folder: str,
    defaults: Optional[Dict[str, str]] = None,
    auto_upload: bool = False,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]
```

**Example (with review):**
```python
result = create_test_cases_from_pdf(
    pdf_path="requirements/login_spec.pdf",
    target_folder="/Mobile/Authentication",
    auto_upload=False  # User reviews before upload
)

# User reviews, then uploads separately
```

**Example (auto-upload):**
```python
result = create_test_cases_from_pdf(
    pdf_path="requirements/login_spec.pdf",
    target_folder="/Mobile/Authentication",
    auto_upload=True  # Upload immediately
)
```

**Agent Usage:**
- "Create test cases from login_spec.pdf and upload to /Mobile/Authentication"
- "Generate and upload test cases from this PDF"

---

## Configuration

Skills support three configuration methods (in priority order):

1. **Explicit Parameters** (recommended for agents)
```python
result = create_qmetry_test_case(
    api_key="abc123...",
    project_id="12345",
    ...
)
```

2. **Environment Variables**
```bash
export QMETRY_API_KEY="abc123..."
export QMETRY_PROJECT="12345"
```

3. **Config File** (fallback to CLI behavior)
```yaml
# .qmetry_config.yaml
QMETRY_API_KEY: "abc123..."
QMETRY_PROJECT: "12345"
```

---

## Response Format

All skills return structured JSON:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  ...additional data...
}
```

**Error Response:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error_message": "Invalid field names found",
  "suggestion": "Fix field names or use skip_validation=True"
}
```

---

## Agent Workflow Examples

See `qmetry_agent_skills/examples/basic_workflow.py` for complete examples.

---

## Security Considerations

- **Never log or return API keys** in responses
- Use environment variables or secure credential storage
- Validate all user inputs before API calls
- Implement rate limiting for production use

---

## Next Steps

1. Review the example workflows in `examples/basic_workflow.py`
2. Set up environment variables or config file
3. Test skills with dry-run mode first
4. Integrate with your agent framework

