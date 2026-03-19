# Augment Integration Guide for QMetry Agent Skills

This guide explains how to integrate the QMetry agent skills with Augment.

---

## Quick Start

### 1. Setup Environment

```bash
# Navigate to project
cd /Users/fva04/Documents/qmetry-cli-tool

# Install dependencies
pip install pyyaml certifi pdfplumber

# Set environment variables (recommended for agents)
export QMETRY_API_KEY="your-api-key-here"
export QMETRY_PROJECT="12345"
```

### 2. Test Skills

```python
# Test basic skill
from qmetry_agent_skills import list_qmetry_folders

result = list_qmetry_folders()
print(result)
```

---

## Skill Registration for Augment

Augment should register these skills as available tools:

### Skill Definitions

```python
# Skill 1: Generate Feature File
{
    "name": "generate_feature_file_from_pdf",
    "description": "Generate Gherkin feature file from PDF requirements document",
    "parameters": {
        "pdf_path": {"type": "string", "required": True},
        "defaults": {"type": "object", "required": False},
        "save_to_disk": {"type": "boolean", "default": True}
    },
    "returns": {
        "success": "boolean",
        "feature_file_path": "string",
        "feature_file_content": "string",
        "test_case_count": "integer"
    }
}

# Skill 2: Validate Feature File
{
    "name": "validate_qmetry_feature_file",
    "description": "Validate feature file syntax and fields against QMetry",
    "parameters": {
        "feature_file_path": {"type": "string", "required": False},
        "feature_file_content": {"type": "string", "required": False},
        "check_api": {"type": "boolean", "default": True}
    },
    "returns": {
        "success": "boolean",
        "valid": "boolean",
        "invalid_fields": "array"
    }
}

# Skill 3: Upload Test Cases
{
    "name": "create_qmetry_test_case",
    "description": "Upload test cases to QMetry from feature file",
    "parameters": {
        "feature_file_path": {"type": "string", "required": False},
        "feature_file_content": {"type": "string", "required": False},
        "target_folder": {"type": "string", "required": True},
        "dry_run": {"type": "boolean", "default": False}
    },
    "returns": {
        "success": "boolean",
        "created_count": "integer",
        "updated_count": "integer",
        "test_cases": "array"
    }
}

# Skill 4: List Folders
{
    "name": "list_qmetry_folders",
    "description": "List all folders in QMetry project",
    "parameters": {},
    "returns": {
        "success": "boolean",
        "folders": "array",
        "folder_count": "integer"
    }
}

# Skill 5: Discover Fields
{
    "name": "discover_qmetry_custom_fields",
    "description": "Discover custom fields and options in QMetry",
    "parameters": {},
    "returns": {
        "success": "boolean",
        "fields": "object",
        "field_count": "integer"
    }
}

# Skill 6: End-to-End Workflow
{
    "name": "create_test_cases_from_pdf",
    "description": "Complete workflow: PDF → Feature File → QMetry Upload",
    "parameters": {
        "pdf_path": {"type": "string", "required": True},
        "target_folder": {"type": "string", "required": True},
        "defaults": {"type": "object", "required": False},
        "auto_upload": {"type": "boolean", "default": False}
    },
    "returns": {
        "success": "boolean",
        "feature_file_path": "string",
        "created_count": "integer",
        "test_case_count": "integer"
    }
}
```

---

## Agent Decision Tree

When user mentions QMetry-related tasks, Augment should:

```
User Input → Intent Recognition → Skill Selection → Execution → Response

Intent Recognition:
├─ "generate" / "create feature file" / "from PDF"
│  └─> generate_feature_file_from_pdf()
│
├─ "validate" / "check" / "verify"
│  └─> validate_qmetry_feature_file()
│
├─ "upload" / "push" / "create test cases"
│  └─> create_qmetry_test_case()
│
├─ "list folders" / "show folders" / "where to upload"
│  └─> list_qmetry_folders()
│
├─ "what fields" / "available fields" / "custom fields"
│  └─> discover_qmetry_custom_fields()
│
└─ "process PDF and upload" / "end-to-end"
   └─> create_test_cases_from_pdf()
```

---

## Recommended Workflow Patterns

### Pattern 1: Safe Workflow (Default)
```
1. User: "Generate test cases from login.pdf"
2. Agent: generate_feature_file_from_pdf()
3. Agent: Shows preview, asks for review
4. User: Reviews and approves
5. Agent: validate_qmetry_feature_file()
6. Agent: create_qmetry_test_case()
7. Agent: Shows results
```

### Pattern 2: Quick Workflow (Power Users)
```
1. User: "Create test cases from login.pdf and upload to /Mobile/Auth"
2. Agent: create_test_cases_from_pdf(auto_upload=True)
3. Agent: Shows results
```

### Pattern 3: Validation-First Workflow
```
1. User: "Upload login.feature to QMetry"
2. Agent: validate_qmetry_feature_file()
3. If valid: create_qmetry_test_case()
4. If invalid: Show errors, ask user to fix
```

---

## Error Handling

All skills return structured errors. Augment should:

1. **Check `success` field** in response
2. **Display `error_message`** to user
3. **Show `suggestion`** if available
4. **Handle specific error types**:

```python
if not result["success"]:
    error_type = result.get("error_type")
    
    if error_type == "file_not_found":
        # Ask user for correct path
        
    elif error_type == "validation_error":
        # Show invalid fields with suggestions
        
    elif error_type == "api_error":
        # Check credentials, retry
        
    elif error_type == "permission_error":
        # Suggest manual folder creation
```

---

## Configuration Management

### Recommended Approach for Augment:

1. **Use Environment Variables** (most secure)
```python
# Augment sets these from user's secure storage
os.environ["QMETRY_API_KEY"] = user_credentials.qmetry_api_key
os.environ["QMETRY_PROJECT"] = user_credentials.qmetry_project

# Skills auto-detect from environment
result = create_qmetry_test_case(...)
```

2. **Explicit Parameters** (for multi-project scenarios)
```python
result = create_qmetry_test_case(
    api_key=project_a_key,
    project_id=project_a_id,
    ...
)
```

---

## Security Best Practices

1. **Never log API keys**
```python
# ✗ Bad
print(f"Using API key: {api_key}")

# ✓ Good
print("Using configured API key")
```

2. **Store credentials securely**
- Use Augment's credential management
- Never commit API keys to git
- Rotate keys regularly

3. **Validate user inputs**
```python
# Check file paths before passing to skills
if not Path(pdf_path).exists():
    return "PDF file not found"
```

---

## Testing

### Test Each Skill Individually

```python
# Test 1: List folders (no side effects)
result = list_qmetry_folders()
assert result["success"] == True

# Test 2: Validate (no side effects)
result = validate_qmetry_feature_file(
    feature_file_path="test.feature",
    check_api=False  # Skip API for unit tests
)

# Test 3: Dry run upload (no side effects)
result = create_qmetry_test_case(
    feature_file_path="test.feature",
    dry_run=True
)
```

---

## Performance Considerations

1. **Caching**: Skills cache field IDs and folder structures
2. **Rate Limiting**: QMetry API may have rate limits
3. **Batch Operations**: Use combined skills for multiple files
4. **Timeouts**: Long operations may timeout (increase if needed)

---

## Next Steps

1. ✅ Review skill definitions above
2. ✅ Test skills with example data
3. ✅ Integrate with Augment's tool system
4. ✅ Set up credential management
5. ✅ Test end-to-end workflows
6. ✅ Deploy to production

---

## Support

For issues or questions:
- Review `AGENT_SKILLS_README.md` for detailed documentation
- Check `AGENT_CONVERSATION_EXAMPLES.md` for usage patterns
- See `qmetry_agent_skills/examples/` for code examples

