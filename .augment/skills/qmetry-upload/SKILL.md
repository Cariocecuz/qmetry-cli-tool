---
name: qmetry-upload
description: Upload test cases from Gherkin feature files to QMetry Test Management, handling creation and updates of test cases
---

# QMetry Test Case Upload

This skill uploads test cases from Gherkin feature files to QMetry Test Management.

## When to Use This Skill

Use this skill when the user:
- Asks to "upload" test cases to QMetry
- Wants to "create test cases" in QMetry
- Says "push to QMetry"
- Mentions uploading a feature file
- Wants to sync test cases with QMetry

## How to Upload

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import create_qmetry_test_case

result = create_qmetry_test_case(
    feature_file_path="path/to/file.feature",
    target_folder="/Mobile/Authentication",
    dry_run=False  # Set to True to preview without uploading
)

if result["success"]:
    print(f"✅ Upload successful!")
    print(f"Created: {result['created_count']}")
    print(f"Updated: {result['updated_count']}")
    print(f"Failed: {result['failed_count']}")
else:
    print(f"❌ Upload failed: {result['error_message']}")
```

### Using CLI Script

```bash
# Upload to QMetry
python3 skills/qmetry-upload.py "path/to/file.feature" "/Mobile/Authentication"

# Dry run (preview without uploading)
python3 skills/qmetry-upload.py "path/to/file.feature" "/Mobile/Auth" --dry-run

# Skip validation (not recommended)
python3 skills/qmetry-upload.py "path/to/file.feature" "/Mobile/Auth" --skip-validation
```

## What Happens During Upload

1. **Parse Feature File** - Extract test cases and metadata
2. **Validate Fields** - Check field names against QMetry API (unless skipped)
3. **Check for Duplicates** - Find existing test cases by name
4. **Create or Update** - Create new test cases or update existing ones
5. **Return Results** - Detailed results for each test case

## Duplicate Handling

The skill automatically detects duplicates:
- **Existing test case found**: Updates the existing test case
- **No match found**: Creates a new test case
- **Match by**: Test case name and folder

## Return Value Structure

```python
{
    "success": bool,
    "created_count": int,
    "updated_count": int,
    "failed_count": int,
    "test_cases": [
        {
            "name": str,
            "key": str,  # QMetry test case key (e.g., "TC-123")
            "status": "created" | "updated" | "failed",
            "error": str  # Only if status="failed"
        }
    ],
    "target_folder": str,
    "dry_run": bool,
    "errors": [str]
}
```

## Folder Structure

QMetry folders are hierarchical:
- `/Mobile/Authentication`
- `/Mobile/Browse`
- `/Roku/Playback`

Use `qmetry-list-folders` skill to see available folders.

## Example Workflow

1. User specifies feature file and target folder
2. Validate feature file first (recommended)
3. Call `create_qmetry_test_case()`
4. Show results (created/updated counts)
5. Provide QMetry test case keys

## Common Issues

- **Folder doesn't exist**: Create folder manually in QMetry first
- **Permission error**: Check API key has folder creation permissions
- **Validation errors**: Fix field names before uploading
- **API rate limit**: Wait and retry

