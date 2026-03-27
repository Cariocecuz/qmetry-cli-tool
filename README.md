# QMetry Feature File Uploader

A Python CLI tool that parses Gherkin feature files and uploads test cases directly to QMetry for Jira (QTM4J) via the Cloud API.

## Features

### 🤖 AI-Powered (NEW)
- ✅ **Augment native skills** - Natural language QMetry integration
- ✅ **Python library** - Programmatic access (`qmetry_agent_skills`)
- ✅ **CLI scripts** - Command-line tools in `skills/` directory
- ✅ **PDF generation** - Generate feature files from requirements PDFs

### 🚀 Core Functionality
- ✅ Parse Gherkin `.feature` files with custom tags
- ✅ Upload test cases directly to QMetry (no CSV export needed)
- ✅ Upload to existing folder paths in QMetry
- ✅ Custom field mapping with automatic ID lookup
- ✅ Smart duplicate handling (updates existing TCs in same folder)
- ✅ Dry run mode to preview uploads
- ✅ Export to CSV format (for manual import)
- ✅ **Cross-workstream compatible** - works with any QMetry custom fields (Mobile, Roku, Web, etc.)
- ✅ **Pre-upload field validation** - catches invalid fields before uploading
- ✅ **Typo detection** - suggests correct field names for typos

## 🤖 NEW: Augment AI Integration

This tool now includes **Augment native skills** for natural language QMetry integration! Use Augment to manage test cases with simple commands.

### Available Skills

- **qmetry-validate** - Validate feature files for syntax and field correctness
- **qmetry-upload** - Upload test cases to QMetry
- **qmetry-generate** - Generate feature files from PDF requirements
- **qmetry-list-folders** - List QMetry folder hierarchy
- **qmetry-discover-fields** - Discover custom fields and options
- **qmetry-search** - Search test cases by text/field filters (cached locally)
- **qmetry-workflow** - Complete end-to-end workflow (PDF → QMetry)

### Using with Augment

Simply ask Augment in natural language:

```
"Validate the login feature file"
"List the QMetry folders"
"Upload test cases to /Mobile/Authentication"
"What custom fields are available?"
"Generate test cases from requirements.pdf"
```

Skills are automatically loaded from `.augment/skills/` when you open this repository in VS Code with Augment.

📖 **See [AGENT_SKILLS_README.md](AGENT_SKILLS_README.md) for complete documentation**

---

## Quick Start

### 1. Install Dependencies

```bash
python3 -m pip install pyyaml certifi pdfplumber
```

> **Note:** `pdfplumber` is optional - only needed if generating feature files from PDFs.

### 2. Create Config File

```bash
python3 -m qmetry_tool.cli config
```

This creates `.qmetry_config.yaml.template`. Copy it to `.qmetry_config.yaml` and fill in your settings:

```yaml
QMETRY_API_KEY: "your-api-key-here"      # From QMetry > Configuration > Open API
QMETRY_PROJECT: "12345"                   # Numeric project ID (from URL: project.id=XXXXX)
QMETRY_DEFAULT_FOLDER: "/Uncategorized"   # Default upload folder
QMETRY_SSL_VERIFY: true                   # Set to false if you have cert issues
```

> ⚠️ **Important:** Add `.qmetry_config.yaml` to `.gitignore` - it contains your API key!

### 3. Upload a Feature File

```bash
# Upload to default folder
python3 -m qmetry_tool.cli upload "path/to/file.feature"

# Upload to specific folder
python3 -m qmetry_tool.cli upload "path/to/file.feature" --folder "/Mobile/PTR"

# Preview without uploading
python3 -m qmetry_tool.cli upload "path/to/file.feature" --dry
```

## Commands

| Command | Shorthand | Description |
|---------|-----------|-------------|
| `gen <pdf>` | `generate` | Generate feature file from PDF (via AI assistant) |
| `validate <file>` | | Check feature file syntax |
| `validate <file> --api` | | Validate fields against QMetry |
| `export <file>` | `exp` | Convert feature file to CSV |
| `upload <file>` | `up` | Upload test cases to QMetry (uses default folder from config) |
| `upload <file> --folder "/Path"` | | Upload to specific folder |
| `upload <file> --dry` | | Preview upload (no changes) |
| `upload <file> --skip-validation` | | Skip field validation (not recommended) |
| `search --text "query"` | | Search test cases by text (uses local cache) |
| `search --text "query" --refresh` | | Search with forced cache refresh from API |
| `search --app MyApp --platform iOS` | | Filter by custom fields |
| `cache info` | | Show local TC cache status (size, age, TTL) |
| `cache clear` | | Delete the local TC cache file |
| `folders` | | List folders in QMetry project |
| `config` | | Create config template |
| `--help` | | Show help |

## Generating Feature Files

> **Note:** The `gen` command is an **AI-assisted workflow** — it's processed by your AI assistant (Augment), not by the QMetry CLI directly. The AI uses existing tools (PDF extraction, Confluence API, file saving) to generate feature files.

### From PDF

```bash
gen requirements.pdf
# or
gen New Features/MyFeature/requirements.pdf
```

The AI will:
1. Extract text from the PDF using `pdfplumber`
2. Generate a Gherkin feature file following project conventions
3. Save to the same folder as the PDF
4. Validate the output

> **Requires:** `python3 -m pip install pdfplumber`

### From Confluence

```bash
gen https://your-confluence.atlassian.net/wiki/spaces/TEAM/pages/123456/Page+Title
# or with explicit folder:
gen https://your-confluence.atlassian.net/wiki/... --folder "New Features/MyFeature"
```

The AI will:
1. Fetch the Confluence page content via API
2. Extract requirements, use cases, and feature flags
3. Generate a Gherkin feature file
4. Save to the specified folder (or prompt for location)
5. Validate the output

### Folder Structure

Store feature files in `New Features/<FeatureName>/`:

```
New Features/
├── PullToRefresh/
│   ├── PullToRefresh.pdf           # PDF source (optional)
│   └── PullToRefresh.feature       # Generated feature file
├── ViewAllButton/
│   └── ViewAllButton.feature       # Generated from Confluence
└── NewFeatureName/
    └── NewFeatureName.feature
```

**Folder naming conventions:**
- Use **short, descriptive names**: `ViewAllButton`, `PullToRefresh`, `UserLogin`
- Avoid ticket numbers in folder names: ❌ `PROJ-1234_View_All_Button`
- Use PascalCase or camelCase: ✅ `ViewAllButton` or `viewAllButton`

### Traceability

Generated files include a source reference comment at the top:

```gherkin
# Source: https://your-confluence.atlassian.net/wiki/spaces/TEAM/pages/123456
# Generated: 2026-03-20

@Feature_Defaults:
@Apps:MyApp
...
```

This links the feature file back to its requirements source for traceability.

### When to Fetch Linked Confluence Pages

| Page Content | Action |
|--------------|--------|
| Has requirements table + use cases | ✅ Generate directly |
| References "Analysis" page with details | 🟡 Ask AI to fetch linked page |
| References Jira tickets for ACs | 🟡 Ask AI to fetch Jira ticket |
| References Figma for visual specs | ⚪ Optional — for visual validation TCs |

**Prompt examples:**
```
"Generate feature file from this Confluence page"
"Also fetch the linked Analysis page for more details"
"Check the Jira ticket PROJ-1234 for acceptance criteria"
```

### What the AI Generates

- `# Source:` comment for traceability (Confluence/PDF URL)
- `@Feature_Defaults:` block with Apps, Platform, Component/Feature
- `# TC-XX` comments before each scenario (for tracking, not uploaded)
- `@Test_Data:` and `@Expected_Result:` blocks
- Coverage for: display, interaction, edge cases, feature flags

### Example Prompt (if not using Augment)

```
Generate a Gherkin feature file from this Confluence page / PDF.
Follow these conventions:
- Add "# Source: <URL>" comment at the top
- @Feature_Defaults: block with Apps, Platform, Component/Feature, Regression_Type
- # TC-XX comments before each scenario
- @Test_Data: and @Expected_Result: blocks after each scenario
- Cover: display, interaction, edge cases, feature flags
```

## Feature File Format

```gherkin
@Feature_Defaults:
@Apps:MyApp
@Platform:iOS,Android
@Component/Feature:Authentication
@TC_requires_use_of_proxy:No
@Regression_Type:New_Features

Feature: User Login
  As a user I want to log in

  Background:
    Given the app is installed
    And user is on login screen

  # TC-01
  @positive
  Scenario: Successful login
    Given user has valid credentials
    When user enters email and password
    And user taps Login
    Then user sees home screen

    @Test_Data:
    - Email: test@example.com
    - Password: Test123

    @Expected_Result:
    User is logged in and sees home screen.

  # TC-02
  @negative @Platform:Android
  Scenario: Login fails with wrong password
    Given user has valid account
    When user enters wrong password
    Then error message is displayed

    @Expected_Result:
    Error message shown. User stays on login screen.
```

### Key Tags

| Tag | Purpose |
|-----|---------|
| `@Feature_Defaults:` | Default values for all scenarios |
| `@FieldName:Value` | Override a field (e.g., `@Platform:iOS`) |
| `@Test_Data:` | Test data block |
| `@Expected_Result:` | Expected result block |
| `@Folder:/Path` | Target folder in QMetry |
| `@positive`, `@negative` | Labels (documentation only) |

## Cross-Workstream Support

The tool auto-detects custom fields from QMetry, so it works with **any team's field configuration**:

```gherkin
# Mobile team
@Apps:MyApp
@Platform:iOS,Android
@Users_Applied:Premium_Tier

# Roku team
@Apps:MyApp
@Device:Roku_Ultra
@Journey:Login_Flow

# Web team
@Apps:MyApp
@Platform:Web
@Browser:Chrome
```

**Features:**
- No hardcoded field list - uses whatever fields exist in your QMetry project
- Handles underscores/spaces flexibly (`TC_requires_use_of_proxy` or `TC requires use of proxy`)
- Typo detection suggests correct field names

## Field Validation

Before uploading, the tool validates all fields against QMetry:

```bash
# Validate fields before upload (automatic)
$ python3 -m qmetry_tool.cli upload MyFeature.feature

Validating fields against QMetry...
  ✓ Apps
  ✗ Platfrom - not found (did you mean 'Platform'?)

✗ Upload aborted. 1 invalid field(s) found.

# Validate fields manually
$ python3 -m qmetry_tool.cli validate MyFeature.feature --api
```

## Finding Your Project ID

1. Open QMetry in your browser
2. Navigate to your project
3. Look at the URL: `...project.id=12345...`
4. Use that number in your config

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `PyYAML is required` | `python3 -m pip install pyyaml` |
| `SSL certificate error` | `python3 -m pip install certifi` |
| `pdfplumber not installed` | `python3 -m pip install pdfplumber` (required for PDF generation) |
| `Config file not found` | Run `python3 -m qmetry_tool.cli config` |
| `API key invalid` | Generate new key from QMetry > Configuration > Open API |
| `HTTP 404` on upload | Check project ID is numeric, not project key |
| `Parent folder ID is not valid` | Create the folder manually in QMetry first, then retry |

## Python Library

The tool also provides a Python library for programmatic access:

```python
from qmetry_agent_skills import (
    validate_qmetry_feature_file,
    create_qmetry_test_case,
    generate_feature_file_from_pdf,
    list_qmetry_folders,
    discover_qmetry_custom_fields
)

# Validate a feature file
result = validate_qmetry_feature_file(
    feature_file_path="login.feature",
    check_api=True
)

# Upload to QMetry
result = create_qmetry_test_case(
    feature_file_path="login.feature",
    target_folder="/Mobile/Authentication"
)

# List folders
result = list_qmetry_folders()

# Discover custom fields
result = discover_qmetry_custom_fields()
```

All functions return structured JSON responses for easy integration.

📖 **See [AGENT_SKILLS_README.md](AGENT_SKILLS_README.md) for complete API documentation**

---

## CLI Scripts

Command-line scripts are available in the `skills/` directory:

```bash
# Validate feature file
python3 skills/qmetry-validate.py "path/to/file.feature"

# Upload to QMetry
python3 skills/qmetry-upload.py "path/to/file.feature" "/Mobile/Auth"

# List folders
python3 skills/qmetry-list-folders.py

# Discover fields
python3 skills/qmetry-discover-fields.py

# Generate from PDF
python3 skills/qmetry-generate.py "requirements.pdf" --platform "iOS,Android"

# Complete workflow
python3 skills/qmetry-workflow.py "requirements.pdf" "/Mobile/Auth" --auto-upload
```

📖 **See [skills/README.md](skills/README.md) for CLI documentation**

---

## Documentation

See the full guide for detailed information:
- **[AGENT_SKILLS_README.md](AGENT_SKILLS_README.md)** - Complete agent skills reference
- **[AGENT_CONVERSATION_EXAMPLES.md](AGENT_CONVERSATION_EXAMPLES.md)** - 9 conversation examples
- **[AUGMENT_INTEGRATION_GUIDE.md](AUGMENT_INTEGRATION_GUIDE.md)** - Integration instructions
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card
- **[skills/README.md](skills/README.md)** - CLI scripts documentation
- **[QMetry CSV Import Guide](_QMetry_Templates/QMetry_CSV_Import_Guide.md)** - Complete reference with all fields, examples, and CSV export details

## Project Structure

```
├── .augment/skills/          # Augment native skills (NEW)
│   ├── qmetry-validate/
│   ├── qmetry-upload/
│   ├── qmetry-generate/
│   ├── qmetry-list-folders/
│   ├── qmetry-discover-fields/
│   ├── qmetry-search/        # Search + cache management
│   └── qmetry-workflow/
├── qmetry_agent_skills/      # Python library (NEW)
│   ├── __init__.py           # Package exports
│   ├── skill_validate.py     # Validation skill
│   ├── skill_upload.py       # Upload skill
│   ├── skill_generate.py     # Generation skill
│   ├── skill_query.py        # Query skills (folders, fields, search)
│   ├── skill_combined.py     # Combined workflows
│   ├── core/                 # Shared utilities
│   │   ├── parser.py         # Enhanced Gherkin parser
│   │   ├── config.py         # Agent-compatible config
│   │   └── errors.py         # Structured error handling
│   └── examples/             # Usage examples
├── skills/                   # CLI scripts (NEW)
│   ├── qmetry-validate.py
│   ├── qmetry-upload.py
│   ├── qmetry-generate.py
│   ├── qmetry-list-folders.py
│   ├── qmetry-discover-fields.py
│   ├── qmetry-search.py      # Search test cases
│   └── qmetry-workflow.py
├── qmetry_tool/              # Original CLI tool
│   ├── __init__.py           # Package marker
│   ├── cli.py                # Command-line interface
│   ├── qmetry_api_client.py  # QMetry API client
│   ├── config_handler.py     # Config and cache management
│   ├── search_engine.py      # Search engine (query, filter, paginate)
│   ├── tc_cache.py           # Local TC search cache (30-min TTL)
│   ├── field_schema.py       # Custom field schema cache
│   ├── gherkin_parser.py     # Feature file parser
│   └── csv_exporter.py       # CSV export functionality
├── _QMetry_Templates/        # Templates and documentation
├── AGENT_SKILLS_README.md    # Agent skills documentation (NEW)
├── AGENT_CONVERSATION_EXAMPLES.md  # Conversation examples (NEW)
├── AUGMENT_INTEGRATION_GUIDE.md    # Integration guide (NEW)
├── QUICK_REFERENCE.md        # Quick reference (NEW)
├── .qmetry_config.yaml       # Your config (git-ignored)
├── .qmetry_cache.yaml        # API cache (auto-generated)
├── .qmetry_tc_cache.json     # TC search cache (auto-generated, git-ignored)
└── README.md                 # This file
```
