---
name: qmetry-validate
description: Validate Gherkin feature files for QMetry Test Management, checking syntax and custom field names against the QMetry API
---

# QMetry Feature File Validation

This skill helps validate Gherkin feature files before uploading to QMetry Test Management.

## When to Use This Skill

Use this skill when the user:
- Asks to "validate" a feature file
- Wants to check if a .feature file is correct
- Mentions QMetry and validation
- Wants to verify field names before uploading
- Says "check my test cases"

## How to Validate

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import validate_qmetry_feature_file

result = validate_qmetry_feature_file(
    feature_file_path="path/to/file.feature",
    check_api=True  # Validates field names against QMetry API
)

if result["valid"]:
    print(f"✅ Valid: {result['test_case_count']} test cases")
    print(f"Feature: {result['feature_name']}")
else:
    print("❌ Validation failed:")
    for field in result["invalid_fields"]:
        print(f"  - {field['field']} → Suggestion: {field['suggestion']}")
```

### Using CLI Script

```bash
python3 skills/qmetry-validate.py "path/to/file.feature"

# Skip API validation (syntax only)
python3 skills/qmetry-validate.py "path/to/file.feature" --no-api-check
```

## What Gets Validated

1. **Gherkin Syntax** - Feature, Scenario, Given/When/Then structure
2. **Required Blocks** - @Feature_Defaults:, @Test_Data:, @Expected_Result:
3. **Custom Fields** - Field names validated against QMetry API
4. **Typo Detection** - Suggests corrections for misspelled fields

## Common Field Names

Standard QMetry custom fields:
- **Apps**: Application name (e.g., "MyApp")
- **Platform**: iOS, Android, Mobile, Web, Roku
- **Component/Feature**: Feature area (e.g., "Authentication", "Playback")
- **Regression_Type**: New_Features, Smoke, Sanity, Full_Regression

## Return Value Structure

```python
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
```

## Error Handling

If validation fails, the response includes:
- `valid`: False
- `invalid_fields`: List of incorrect field names with suggestions
- `errors`: Critical syntax errors
- `warnings`: Non-critical issues

## Example Workflow

1. User provides feature file path
2. Call `validate_qmetry_feature_file()`
3. If invalid, show errors with suggestions
4. If valid, confirm and suggest next step (upload)

## Common Issues

- **Typo in field name**: "Platfrom" → Suggestion: "Platform"
- **Missing @Feature_Defaults:**: Add block at top of file
- **No test cases**: File has Feature but no Scenarios
- **Invalid field**: Field doesn't exist in QMetry project

