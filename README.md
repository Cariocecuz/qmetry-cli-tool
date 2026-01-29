# QMetry Feature File Uploader

A Python CLI tool that parses Gherkin feature files and uploads test cases directly to QMetry for Jira (QTM4J) via the Cloud API.

## Features

- ✅ Parse Gherkin `.feature` files with custom tags
- ✅ Upload test cases directly to QMetry (no CSV export needed)
- ✅ Upload to existing folder paths in QMetry
- ✅ Custom field mapping with automatic ID lookup
- ✅ Smart duplicate handling (updates existing TCs in same folder)
- ✅ Dry run mode to preview uploads
- ✅ Export to CSV format (for manual import)

## Quick Start

### 1. Install Dependencies

```bash
python3 -m pip install pyyaml certifi
```

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
| `validate <file>` | | Check feature file syntax |
| `export <file>` | `exp` | Convert feature file to CSV |
| `upload <file>` | `up` | Upload test cases to QMetry (uses default folder from config) |
| `upload <file> --folder "/Path"` | | Upload to specific folder |
| `upload <file> --dry` | | Preview upload (no changes) |
| `folders` | | List folders in QMetry project |
| `config` | | Create config template |
| `--help` | | Show help |

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
| `Config file not found` | Run `python3 -m qmetry_tool.cli config` |
| `API key invalid` | Generate new key from QMetry > Configuration > Open API |
| `HTTP 404` on upload | Check project ID is numeric, not project key |
| `Parent folder ID is not valid` | Create the folder manually in QMetry first, then retry |

## Documentation

See the full guide for detailed information:
- **[QMetry CSV Import Guide](_QMetry_Templates/QMetry_CSV_Import_Guide.md)** - Complete reference with all fields, examples, and CSV export details

## Project Structure

```
├── qmetry_tool/              # CLI tool source code
│   ├── __init__.py           # Package marker
│   ├── cli.py                # Command-line interface
│   ├── qmetry_api_client.py  # QMetry API client
│   ├── config_handler.py     # Config and cache management
│   ├── gherkin_parser.py     # Feature file parser
│   └── csv_exporter.py       # CSV export functionality
├── _QMetry_Templates/        # Templates and documentation
├── .qmetry_config.yaml       # Your config (git-ignored)
├── .qmetry_cache.yaml        # API cache (auto-generated)
└── README.md                 # This file
```
