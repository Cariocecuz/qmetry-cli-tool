---
name: qmetry-workflow
description: Complete workflow for generating test cases from PDF requirements and uploading to QMetry
---

# QMetry Complete Workflow

This skill orchestrates the complete workflow: PDF → Feature File → Validation → Upload to QMetry.

## When to Use This Skill

Use this skill when the user:
- Asks to "create test cases from PDF and upload to QMetry"
- Wants end-to-end workflow
- Says "process this PDF and create test cases"
- Mentions both generation and upload
- Wants automated workflow

## How to Use

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import create_test_cases_from_pdf

# With review (default - recommended)
result = create_test_cases_from_pdf(
    pdf_path="requirements/login_spec.pdf",
    target_folder="/Mobile/Authentication",
    defaults={
        "Apps": "MyApp",
        "Platform": "iOS,Android",
        "Component/Feature": "Authentication"
    },
    auto_upload=False  # User reviews before upload
)

if result["success"]:
    print(f"✅ Generated: {result['feature_file_path']}")
    print(f"Test Cases: {result['test_case_count']}")
    print(f"\n{result['next_step']}")
```

### Auto-Upload Mode (Skip Review)

```python
# Auto-upload (skip review)
result = create_test_cases_from_pdf(
    pdf_path="requirements/login_spec.pdf",
    target_folder="/Mobile/Authentication",
    defaults={
        "Apps": "MyApp",
        "Platform": "iOS,Android"
    },
    auto_upload=True  # Upload immediately
)

if result["success"]:
    print(f"✅ Complete workflow successful!")
    print(f"Created: {result['created_count']}")
    print(f"Updated: {result['updated_count']}")
```

### Using CLI Script

```bash
# With review (default)
python3 skills/qmetry-workflow.py "requirements/login.pdf" "/Mobile/Auth"

# Auto-upload (skip review)
python3 skills/qmetry-workflow.py "requirements/login.pdf" "/Mobile/Auth" --auto-upload
```

## Workflow Steps

### Mode 1: With Review (auto_upload=False)

1. **Generate** - Create feature file from PDF
2. **Save** - Save feature file next to PDF
3. **Preview** - Show preview to user
4. **Wait** - User reviews and approves
5. **Upload** - User manually uploads (separate command)

### Mode 2: Auto-Upload (auto_upload=True)

1. **Generate** - Create feature file from PDF
2. **Validate** - Check fields against QMetry API
3. **Upload** - Create/update test cases in QMetry
4. **Report** - Show results

## Return Value Structure

### With Review (auto_upload=False)

```python
{
    "success": bool,
    "feature_file_path": str,
    "feature_file_content": str,
    "feature_name": str,
    "test_case_count": int,
    "preview": str,
    "ready_for_upload": bool,
    "target_folder": str,
    "next_step": str  # Instructions for user
}
```

### Auto-Upload (auto_upload=True)

```python
{
    "success": bool,
    "feature_file_path": str,
    "feature_name": str,
    "created_count": int,
    "updated_count": int,
    "failed_count": int,
    "test_cases": [...],
    "target_folder": str,
    "pdf_path": str
}
```

## Example Workflows

### Workflow 1: Safe (With Review)

```python
# Step 1: Generate and preview
result = create_test_cases_from_pdf(
    pdf_path="requirements/login.pdf",
    target_folder="/Mobile/Auth",
    auto_upload=False
)

# User reviews the generated file

# Step 2: Upload (separate command)
from qmetry_agent_skills import create_qmetry_test_case

upload_result = create_qmetry_test_case(
    feature_file_path=result["feature_file_path"],
    target_folder="/Mobile/Auth"
)
```

### Workflow 2: Quick (Auto-Upload)

```python
# One-step workflow
result = create_test_cases_from_pdf(
    pdf_path="requirements/login.pdf",
    target_folder="/Mobile/Auth",
    auto_upload=True
)
# Done! Test cases created in QMetry
```

## Recommended Approach

**Use auto_upload=False (default)** for:
- New features (review recommended)
- Complex requirements
- First-time generation
- Quality control

**Use auto_upload=True** for:
- Trusted PDFs
- Simple updates
- Batch processing
- Automated workflows

## Common Issues

- **Validation errors**: Fix field names before auto-upload
- **Folder doesn't exist**: Create folder in QMetry first
- **PDF parsing fails**: Check PDF is text-based (not images)

