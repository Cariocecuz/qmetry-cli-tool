# QMetry Augment Skills

Custom Augment skills for QMetry Test Management integration.

## Available Skills

### 1. `/qmetry-list-folders`
List all test case folders in QMetry.

```bash
/qmetry-list-folders
```

**Output:** Hierarchical folder structure with IDs and paths

---

### 2. `/qmetry-validate`
Validate a Gherkin feature file for syntax and field correctness.

```bash
/qmetry-validate <feature-file-path> [--no-api-check]
```

**Examples:**
```bash
/qmetry-validate features/mobile/login.feature
/qmetry-validate "New Features/CC Sender/ChromecastSender.feature"
/qmetry-validate login.feature --no-api-check
```

**Output:** Validation results with field suggestions

---

### 3. `/qmetry-upload`
Upload test cases from a feature file to QMetry.

```bash
/qmetry-upload <feature-file-path> <target-folder> [--dry-run] [--skip-validation]
```

**Examples:**
```bash
/qmetry-upload features/mobile/login.feature "/Mobile/Authentication"
/qmetry-upload "New Features/CC Sender/ChromecastSender.feature" "/5. Playback/5.19. Chromecast - Sender"
/qmetry-upload login.feature "/Mobile/Auth" --dry-run
```

**Output:** Upload results (created/updated/failed counts)

---

### 4. `/qmetry-generate`
Generate a Gherkin feature file from a PDF requirements document or Confluence page URL.

```bash
/qmetry-generate <source> [--output <path>] [--apps <value>] [--platform <value>] [--component <value>]
```

**Examples:**
```bash
# From PDF
/qmetry-generate requirements/login.pdf
/qmetry-generate "New Features/PullToRefresh/PullToRefresh.pdf" --platform "iOS,Android"
/qmetry-generate login.pdf --output features/mobile/auth/login.feature --apps "MyApp"

# From Confluence URL (requires Confluence connection)
/qmetry-generate "https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature+Name"
```

**Output:** Generated feature file path and preview

---

### 5. `/qmetry-discover-fields`
Discover all custom fields and their options in QMetry.

```bash
/qmetry-discover-fields
```

**Output:** List of custom fields with IDs and available options

---

### 6. `/qmetry-workflow`
Complete workflow: PDF/Confluence → Feature File → Validation → Upload.

```bash
/qmetry-workflow <source> <target-folder> [--auto-upload] [--apps <value>] [--platform <value>] [--component <value>]
```

**Examples:**
```bash
# From PDF with review (default)
/qmetry-workflow requirements/login.pdf "/Mobile/Authentication"

# Auto-upload (skip review)
/qmetry-workflow "New Features/PullToRefresh/PullToRefresh.pdf" "/4. Navigation/4.36. Pull to Refresh" --auto-upload

# With custom fields
/qmetry-workflow login.pdf "/Mobile/Auth" --apps "MyApp" --platform "iOS,Android" --component "Authentication"

# From Confluence URL (requires Confluence connection)
/qmetry-workflow "https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature" "/2026/FeatureName/Core"
```

**Output:** 
- Without `--auto-upload`: Feature file preview and next steps
- With `--auto-upload`: Upload results

---

## Setup

### Prerequisites

1. **Install dependencies:**
```bash
pip install pyyaml certifi pdfplumber
```

2. **Set environment variables:**
```bash
export QMETRY_API_KEY="your-api-key"
export QMETRY_PROJECT="your-project-id"
```

Or create `.qmetry_config.yaml`:
```yaml
QMETRY_API_KEY: "your-api-key"
QMETRY_PROJECT: "your-project-id"
```

---

## Usage in Augment

### Method 1: Direct Invocation (If Augment supports `/` commands)

Simply type the skill command in Augment:
```
/qmetry-list-folders
```

### Method 2: Ask Augment to Run the Skill

If direct `/` commands aren't supported, ask Augment:
```
"Run the qmetry-list-folders skill"
"Execute /qmetry-validate on login.feature"
```

Augment will execute the Python script for you.

---

## Common Workflows

### Workflow 1: List Folders → Upload
```bash
# 1. See available folders
/qmetry-list-folders

# 2. Upload to specific folder
/qmetry-upload features/mobile/login.feature "/Mobile/Authentication"
```

### Workflow 2: Generate → Validate → Upload (PDF or Confluence)
```bash
# 1a. Generate from PDF
/qmetry-generate requirements/login.pdf

# 1b. Or generate from Confluence URL
# /qmetry-generate "https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature+Name"

# 2. Validate
/qmetry-validate features/mobile/authentication/login.feature

# 3. Upload
/qmetry-upload features/mobile/authentication/login.feature "/Mobile/Authentication"
```

### Workflow 3: Complete Workflow (One Command)
```bash
# Generate, validate, and upload in one step
/qmetry-workflow requirements/login.pdf "/Mobile/Authentication" --auto-upload
```

---

## Troubleshooting

**Problem:** "Module not found"
**Solution:** Make sure you're in the `qmetry-cli-tool` directory

**Problem:** "Config file not found"
**Solution:** Set environment variables or create `.qmetry_config.yaml`

**Problem:** "Permission denied"
**Solution:** Run `chmod +x skills/*.py`

---

## Direct Python Execution

You can also run skills directly:

```bash
python skills/qmetry-list-folders.py
python skills/qmetry-validate.py features/mobile/login.feature
python skills/qmetry-upload.py login.feature "/Mobile/Auth" --dry-run
```

