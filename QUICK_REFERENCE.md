# QMetry Agent Skills - Quick Reference

## Setup (One-Time)

```bash
# Install dependencies
pip install pyyaml certifi pdfplumber

# Set credentials
export QMETRY_API_KEY="your-api-key"
export QMETRY_PROJECT="12345"
```

---

## Skills Cheat Sheet

### 1a. Generate Feature File from PDF
```python
from qmetry_agent_skills import generate_feature_file_from_pdf

result = generate_feature_file_from_pdf(
    pdf_path="requirements/login.pdf",
    defaults={"Apps": "MyApp", "Platform": "iOS,Android"}
)
# Returns: {"success": True, "feature_file_path": "...", "test_case_count": 8}
```

### 1b. Generate Feature File from Confluence URL
When Confluence is connected, provide a page URL and the agent will:
1. Read the spec and any linked/child pages
2. Extract requirements, acceptance criteria, and edge cases
3. Present analysis for review
4. Generate the `.feature` file

**Example prompt:** `"Generate test cases from https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature+Name"`

### 2. Validate Feature File
```python
from qmetry_agent_skills import validate_qmetry_feature_file

result = validate_qmetry_feature_file(
    feature_file_path="features/login.feature",
    check_api=True
)
# Returns: {"valid": True, "invalid_fields": []}
```

### 3. Upload to QMetry
```python
from qmetry_agent_skills import create_qmetry_test_case

result = create_qmetry_test_case(
    feature_file_path="features/login.feature",
    target_folder="/Mobile/Authentication"
)
# Returns: {"success": True, "created_count": 5, "updated_count": 2}
```

### 4. List Folders
```python
from qmetry_agent_skills import list_qmetry_folders

result = list_qmetry_folders()
# Returns: {"success": True, "folders": [...], "folder_count": 10}
```

### 5. Discover Fields
```python
from qmetry_agent_skills import discover_qmetry_custom_fields

result = discover_qmetry_custom_fields()
# Returns: {"success": True, "fields": {...}, "field_count": 15}
```

### 6. Search Test Cases
```python
from qmetry_agent_skills import search_qmetry_test_cases

result = search_qmetry_test_cases(text="top 10 rail", limit=20)
# Returns: {"success": True, "test_cases": [...], "total": 5, "cache_hit": True}

# Filter by app/platform
result = search_qmetry_test_cases(text="login", app="MyApp", platform="iOS")

# Force refresh from API
result = search_qmetry_test_cases(text="browse", refresh=True)
```

### 7. Get Single Test Case
```python
from qmetry_agent_skills import get_qmetry_test_case

result = get_qmetry_test_case(key="MOB-TC-21153")
# Returns: {"success": True, "test_case": {"key": "...", "summary": "...", "steps": [...]}}
```

### 8. Manage Cache
```python
from qmetry_agent_skills import manage_qmetry_cache

manage_qmetry_cache(action="info")   # Cache status
manage_qmetry_cache(action="clear")  # Delete cache
```

### 9. End-to-End Workflow
```python
from qmetry_agent_skills import create_test_cases_from_pdf

# With review
result = create_test_cases_from_pdf(
    pdf_path="requirements/login.pdf",
    target_folder="/Mobile/Auth",
    auto_upload=False  # User reviews first
)

# Auto-upload
result = create_test_cases_from_pdf(
    pdf_path="requirements/login.pdf",
    target_folder="/Mobile/Auth",
    auto_upload=True  # Upload immediately
)
```

---

## Common Patterns

### Pattern 1: Generate → Review → Upload
```python
# Step 1: Generate
gen = generate_feature_file_from_pdf("req.pdf")

# Step 2: User reviews file

# Step 3: Upload
upload = create_qmetry_test_case(
    feature_file_path=gen["feature_file_path"],
    target_folder="/Mobile/Auth"
)
```

### Pattern 1b: Confluence Spec → Review → Upload
```
# Step 1: Provide Confluence URL → Agent analyzes spec and generates .feature file
# Step 2: User reviews file in VS Code
# Step 3: Upload
upload = create_qmetry_test_case("FeatureName.feature", "/2026/FeatureName/Core")
```

### Pattern 2: Validate Before Upload
```python
# Validate first
val = validate_qmetry_feature_file("login.feature", check_api=True)

if val["valid"]:
    # Upload
    upload = create_qmetry_test_case("login.feature", "/Mobile/Auth")
else:
    # Show errors
    print(val["invalid_fields"])
```

### Pattern 3: Dry Run Preview
```python
# Preview without uploading
result = create_qmetry_test_case(
    feature_file_path="login.feature",
    target_folder="/Mobile/Auth",
    dry_run=True
)
# Shows what would be uploaded
```

---

## Error Handling

```python
result = create_qmetry_test_case(...)

if result["success"]:
    print(f"Created {result['created_count']} test cases")
else:
    print(f"Error: {result['error_message']}")
    print(f"Suggestion: {result.get('suggestion', 'N/A')}")
```

---

## Configuration Options

### Option 1: Environment Variables (Recommended)
```bash
export QMETRY_API_KEY="abc123"
export QMETRY_PROJECT="12345"
```

### Option 2: Explicit Parameters
```python
result = create_qmetry_test_case(
    api_key="abc123",
    project_id="12345",
    ...
)
```

### Option 3: Config File
```yaml
# .qmetry_config.yaml
QMETRY_API_KEY: "abc123"
QMETRY_PROJECT: "12345"
```

---

## Agent Conversation Examples

**User:** "Generate test cases from login.pdf"
→ `generate_feature_file_from_pdf("login.pdf")`

**User:** "Upload login test cases to /Mobile/Auth"
→ `create_qmetry_test_case("login.feature", "/Mobile/Auth")`

**User:** "Show me QMetry folders"
→ `list_qmetry_folders()`

**User:** "What fields can I use?"
→ `discover_qmetry_custom_fields()`

**User:** "Find test cases about login"
→ `search_qmetry_test_cases(text="login")`

**User:** "Get test case MOB-TC-21153"
→ `get_qmetry_test_case(key="MOB-TC-21153")`

**User:** "Clear the cache"
→ `manage_qmetry_cache(action="clear")`

**User:** "Process requirements.pdf and upload to /Mobile/Browse"
→ `create_test_cases_from_pdf("requirements.pdf", "/Mobile/Browse", auto_upload=True)`

**User:** "Generate test cases from this Confluence page: [URL]"
→ Agent reads spec via Confluence connection → analyzes → generates `.feature` file

---

## Response Format

All skills return:
```python
{
    "success": bool,
    "message": str,  # If success
    "error_message": str,  # If failure
    "error_type": str,  # If failure
    "suggestion": str,  # If failure
    ...additional data...
}
```

---

## File Locations

```
qmetry-cli-tool/
├── qmetry_agent_skills/          # Agent skills module
│   ├── skill_*.py                # Individual skills
│   ├── core/                     # Utilities
│   └── examples/                 # Usage examples
├── features/                     # Generated feature files
│   ├── mobile/
│   ├── roku/
│   └── web/
├── requirements/                 # Source PDFs
└── AGENT_SKILLS_README.md        # Full documentation
```

---

## Testing

```python
# Run examples
python qmetry_agent_skills/examples/basic_workflow.py

# Test individual skill
from qmetry_agent_skills import list_qmetry_folders
result = list_qmetry_folders()
assert result["success"] == True
```

---

## Troubleshooting

**Problem:** "Config file not found"
**Solution:** Set environment variables or create `.qmetry_config.yaml`

**Problem:** "Invalid field names"
**Solution:** Run `discover_qmetry_custom_fields()` to see available fields

**Problem:** "Folder creation failed"
**Solution:** Create folder manually in QMetry or check API key permissions

**Problem:** "pdfplumber not installed"
**Solution:** `pip install pdfplumber`

---

## Documentation

- **AGENT_SKILLS_README.md** - Complete skill reference
- **AUGMENT_INTEGRATION_GUIDE.md** - Integration instructions
- **AGENT_CONVERSATION_EXAMPLES.md** - Conversation patterns
- **IMPLEMENTATION_SUMMARY.md** - Implementation details

---

## Support

For issues:
1. Check error message and suggestion
2. Review documentation
3. Test with dry-run mode
4. Verify credentials and permissions

