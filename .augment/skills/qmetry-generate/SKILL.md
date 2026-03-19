---
name: qmetry-generate
description: Generate Gherkin feature files from PDF requirements documents for QMetry Test Management
---

# QMetry Feature File Generation

This skill generates Gherkin feature files from PDF requirements documents.

## When to Use This Skill

Use this skill when the user:
- Asks to "generate test cases from PDF"
- Wants to "create feature file from requirements"
- Says "extract test scenarios from PDF"
- Mentions converting PDF to Gherkin
- Wants to generate test cases from documentation

## How to Generate

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import generate_feature_file_from_pdf

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

if result["success"]:
    print(f"✅ Generated: {result['feature_file_path']}")
    print(f"Feature: {result['feature_name']}")
    print(f"Test Cases: {result['test_case_count']}")
else:
    print(f"❌ Generation failed: {result['error_message']}")
```

### Using CLI Script

```bash
# Generate with defaults
python3 skills/qmetry-generate.py "requirements/login.pdf" \
    --apps "MyApp" \
    --platform "iOS,Android" \
    --component "Authentication"

# Specify output path
python3 skills/qmetry-generate.py "requirements/login.pdf" \
    --output "features/mobile/auth/login.feature"
```

## Output Path Behavior

**Default behavior**: Feature file is saved **next to the PDF**

Example:
```
Input:  "New Features/PullToRefresh/PullToRefresh.pdf"
Output: "New Features/PullToRefresh/PullToRefresh_Generated.feature"
```

The `_Generated` suffix distinguishes auto-generated files from manually created ones.

## Required Defaults

Recommended default fields:
- **Apps**: Application name (e.g., "MyApp")
- **Platform**: Target platforms (e.g., "iOS,Android")
- **Component/Feature**: Feature area (e.g., "Authentication")
- **Regression_Type**: Test type (e.g., "New_Features", "Smoke")

## Return Value Structure

```python
{
    "success": bool,
    "feature_file_path": str,  # Where file was saved
    "feature_file_content": str,  # Full content
    "feature_name": str,
    "test_case_count": int,
    "preview": str,  # First 500 chars
    "warnings": [str],
    "pdf_text_length": int
}
```

## What Gets Generated

1. **@Feature_Defaults:** block with provided defaults
2. **Feature:** declaration with name and description
3. **Background:** section with common preconditions
4. **Scenarios:** test cases extracted from PDF
5. **@Test_Data:** and **@Expected_Result:** blocks for each scenario

## Example Workflow

1. User provides PDF path and defaults
2. Extract text from PDF using pdfplumber
3. Generate Gherkin scenarios (using LLM or templates)
4. Save feature file next to PDF
5. Return preview and file path
6. User reviews generated file
7. User can then validate and upload

## Important Notes

- **Review Required**: Always review generated files before uploading
- **LLM Integration**: The actual scenario generation should use the agent's LLM capabilities
- **Manual Refinement**: Generated files may need manual adjustments
- **Component/Feature**: This field should be filled in manually if not provided

## Common Issues

- **No text extracted**: PDF may be image-based (use OCR)
- **pdfplumber not installed**: Run `pip install pdfplumber`
- **Missing Component/Feature**: Add this field manually after generation

