# QMetry CSV Import Guide

> 📋 **Format Quick Reference:**
> ```
> @FieldName:Value     ← Use @ prefix
> @Regression_Type     ← Use underscores or spaces (both work)
> @Apps:MyApp          ← No space after colon
> ```
> The tool handles underscores/spaces flexibly when matching field names.

---

## Quick Commands

Type any of these commands and I will process your request:

### Test Case Creation

| Command | Action |
|---------|--------|
| `generate [file.pdf]` or `gen [file.pdf]` | Generate feature file from PDF requirements |
| `generate [file.pdf] @Apps:MyApp` | Generate with specific defaults |
| `generate [file.pdf] @Apps:MyApp @Platform:iOS` | Generate with multiple defaults |

**Examples:**
```
gen Login_Requirements.pdf
generate Payment_Flow.pdf @Apps:ProductB
gen Onboarding.pdf @Apps:MyApp,ProductB @Platform:iOS,Android
```

**What happens on `generate`:**
1. Read the PDF content (exported from your documentation tool)
2. Identify feature/functionality being described
3. Extract test scenarios from:
   - Acceptance criteria → Positive scenarios
   - Edge cases → Negative scenarios
   - User flows → End-to-end scenarios
4. Generate feature file with:
   - `@Feature_Defaults:` block (**always included** with required fields)
   - `Feature:` name and description from the doc
   - `Background:` for common preconditions
   - `Scenario:` for each test case
   - `@Test_Data:` and `@Expected_Result:` blocks
   - Appropriate tags (@positive, @negative, etc.)
5. Output `.feature` file ready for export to CSV

**`@Feature_Defaults:` fields (always generated):**
```gherkin
@Feature_Defaults:
@Apps:MyApp,ProductB
@Platform:iOS,Android
@Component/Feature:
@TC_requires_use_of_proxy:No
@Regression_Type:New_Features
```

> ⚠️ **IMPORTANT - Generation Format Rules:**
> - Always use `@` prefix: `@FieldName:Value`
> - Underscores and spaces both work: `@Regression_Type` or `@Regression Type`
> - No space after the colon: `@Apps:MyApp` not `@Apps: MyApp`
> - The tool matches field names flexibly (underscores ↔ spaces)
>
> This format must be consistent across all generated feature files.

After generation, you'll be reminded to review and fill in:
- **Component/Feature** (required - left blank for you to specify)
- **Apps** (if not all apps apply to this feature)
- **Platform** (if not both platforms apply)

---

### Export & Validation

| Command | Action |
|---------|--------|
| `export` or `exp` | Convert the currently open feature file to CSV |
| `export [filename]` or `exp [filename]` | Convert the specified feature file to CSV |
| `export all` or `exp all` | Convert all feature files in folder to a single CSV |
| `validate` | Check feature file syntax against this guide |
| `validate [filename]` | Check specified feature file syntax |
| `validate [filename] --api` | Validate fields against QMetry (requires API connection) |

**Examples:**
```
export
export Login.feature
export all
validate
validate Login.feature
validate Login.feature --api
```

**What happens on export:**
1. Read `@Feature_Defaults:` block → Store defaults
2. Read `Background:` → Precondition column
3. For each `Scenario:`:
   - Extract name → Summary
   - Extract steps → Step Summary
   - Extract `@Test_Data:` → Test Data
   - Extract `@Expected_Result:` → Expected Result
   - Apply inline `@FieldName:Value` overrides
   - Apply defaults for remaining fields
4. Output CSV with 32 columns

---

### Upload to QMetry (API)

| Command | Action |
|---------|--------|
| `upload [file.feature]` or `up [file.feature]` | Upload test cases directly to QMetry via API |
| `upload [file.feature] to /Folder/Path` | Upload to a specific folder |
| `upload [file.feature] --dry` | Preview what would be uploaded (no changes) |
| `upload [file.feature] --skip-validation` | Skip pre-upload field validation (not recommended) |
| `folders` | List available folders in your QMetry project |
| `config` | Create config template file |

**Examples:**
```
up Login.feature
upload Login.feature to /Mobile/Authentication
up Login.feature --dry
folders
config
```

**What happens on upload:**
1. Load `.qmetry_config.yaml` for API key and project
2. Parse feature file (same as export)
3. **Validate all field names** against QMetry (fail-fast if any invalid)
4. Determine target folder (inline > @Feature_Defaults > config default)
5. For each test case:
   - Check if TC with same name exists in target folder
   - If exists: **Update** the existing TC with new content
   - If new: **Create** new TC in target folder
   - Auto-discover custom field IDs (cached after first run)
6. Report results (created/updated/failed)

**Pre-upload field validation:**
```
Validating fields against QMetry...
  ✓ Apps
  ✓ Platform
  ✗ Platfrom - not found (did you mean 'Platform'?)

✗ Upload aborted. 1 invalid field(s) found.
```

**Setup required for upload:**
1. Install dependencies: `python3 -m pip install pyyaml certifi`
2. Copy `.qmetry_config.yaml.template` to `.qmetry_config.yaml`
3. Fill in your API key (from QMetry > Configuration > Open API)
4. Fill in your project ID (numeric, found in QMetry URL: `project.id=XXXXX`)
5. Add `.qmetry_config.yaml` to `.gitignore`

**Config file example:**
```yaml
QMETRY_API_KEY: "your-api-key-here"
QMETRY_PROJECT: "12345"  # Numeric project ID, not the key (PROJ)
QMETRY_DEFAULT_FOLDER: "/Uncategorized"
QMETRY_SSL_VERIFY: true  # Set to false if you have certificate issues
```

**Safety features:**
- ✅ **Pre-upload field validation** with typo suggestions
- ✅ Confirmation prompt before uploading
- ✅ Smart duplicate handling (updates existing TCs in same folder, creates new ones elsewhere)
- ✅ Dry run mode (`--dry`) to preview
- ✅ **Cross-workstream compatible** - works with any QMetry custom fields

> ⚠️ **Note on folder creation:** The API may not have permission to create folders. If you get a "Parent folder ID is not valid" error, create the folder manually in QMetry first, then retry the upload.

---

## CSV Column Reference (32 Columns)

| # | Column | Required | Type | Gherkin Source |
|---|--------|----------|------|----------------|
| 1 | Issue Key | No | Default | Empty for new TCs |
| 2 | Summary | Yes | Default | `Scenario:` name |
| 3 | Description | No | Default | `Feature:` description |
| 4 | Precondition | No | Default | `Background:` Given steps |
| 5 | Status | Yes | Default | TO DO |
| 6 | Priority | No | Default | @Priority: |
| 7 | Assignee | No | Default | - |
| 8 | Reporter | No | Default | - |
| 9 | Estimated Time | No | Default | - |
| 10 | Labels | No | Default | @tags (non-override) |
| 11 | Components | No | Default | - |
| 12 | Sprint | No | Default | - |
| 13 | Fix Versions | No | Default | - |
| 14 | Step Summary | Yes | Default | `Scenario:` Given/When/Then steps |
| 15 | Test Data | No | Default | `@Test_Data:` block |
| 16 | Expected Result | Yes | Default | `@Expected_Result:` block |
| 17 | Folders | No | Default | - |
| 18 | Story Linkages | No | Default | - |
| 19 | Apps | Yes | Custom | @Apps: |
| 20 | Component/Feature | Yes | Custom | @Component/Feature: |
| 21 | CT Update Target | No | Custom | @CT_Update_Target: |
| 22 | Evidence Type | No | Custom | @Evidence_Type: |
| 23 | Live Proposition | No | Custom | @Live_Proposition: |
| 24 | Platform | Yes | Custom | @Platform: |
| 25 | Regression Type | No | Custom | @Regression_Type: |
| 26 | Users Applied | No | Custom | @Users_Applied: |
| 27 | Automatable? | No | Custom | @Automatable: |
| 28 | Automated Proposition | No | Custom | @Automated_Proposition: |
| 29 | HighVisibility | No | Custom | @HighVisibility: |
| 30 | IsAds? | No | Custom | @IsAds: |
| 31 | NBA Feature | No | Custom | @NBA_Feature: |
| 32 | TC requires use of proxy | No | Custom | @TC_requires_use_of_proxy: |

---

## CSV Header (Copy-Paste Ready)

```
Issue Key,Summary,Description,Precondition,Status,Priority,Assignee,Reporter,Estimated Time,Labels,Components,Sprint,Fix Versions,Step Summary,Test Data,Expected Result,Folders,Story Linkages,Apps,Component/Feature,CT Update Target,Evidence Type,Live Proposition,Platform,Regression Type,Users Applied,Automatable?,Automated Proposition,HighVisibility,IsAds?,NBA Feature,TC requires use of proxy
```

---

## Feature File Structure

### @Feature_Defaults Block
Define shared values for ALL scenarios in the file:

```gherkin
@Feature_Defaults:
@Apps:MyApp,ProductB
@Platform:iOS,Android
@Component/Feature:Authentication
@TC_requires_use_of_proxy:No
@Regression_Type:New_Features
@Status:TO_DO
@Priority:Medium
```

### Inline Overrides
Override defaults on individual scenarios using `@FieldName:Value`:

```gherkin
@negative @Platform:Android @Apps:MyApp @Priority:High
Scenario: Login fails with invalid password
```

**Rules:**
- Use `@FieldName:Value` format (with `@` prefix)
- No space after colon: `@Platform:iOS` ✓
- Multiple values use comma: `@Platform:iOS,Android` ✓
- **Underscores and spaces both work** - the tool matches field names flexibly:
  - `@Regression_Type` or `@Regression Type` → both match "Regression Type"
  - `@TC_requires_use_of_proxy` → matches "TC requires use of proxy"
  - Works with any field name format in QMetry
- Regular tags (no colon) go to Labels column
- Same format works in BOTH `@Feature_Defaults:` block and inline overrides
- **Number test cases with `# TC-XX` comments before tags** (not in scenario name):
  ```gherkin
  # TC-01
  @positive
  Scenario: User logs in successfully
  ```
  This makes it easier to reference specific TCs for edits (e.g., "update TC-03 and TC-07")

---

## Gherkin to QMetry Mapping

| Gherkin Element | QMetry Field | Notes |
|-----------------|--------------|-------|
| `Feature:` name | - | Not imported directly |
| `Feature:` As a/I want/So that | Description | Combine into paragraph |
| `Background:` Given steps | Precondition | Only Given steps (setup) |
| `Scenario:` name | Summary | Test case name |
| `Scenario:` Given/When/Then | Step Summary | All scenario steps |
| `@tags` (no colon) | Labels | Space-separated |
| `@FieldName:Value` | Override field | See column list |
| `@Test_Data:` block | Test Data | Free-form text |
| `@Expected_Result:` block | Expected Result | Free-form text |

---

## Complete Feature File Example

```gherkin
# ============================================================
@Feature_Defaults:
@Apps:MyApp
@Platform:iOS,Android
@Component/Feature:Authentication
@TC_requires_use_of_proxy:No
@Regression_Type:New_Features
@Status:TO_DO
@Priority:Medium

# ============================================================
@smoke @regression
Feature: User Login Functionality
  As a registered user
  I want to log into the application
  So that I can access my account features

  Background:
    Given the app is installed and launched
    And the user is on the login screen

  # Uses ALL defaults
  @positive
  Scenario: Successful login with valid credentials
    Given the user has a valid account
    When the user enters valid email "test@example.com"
    And the user enters valid password "Password123"
    And the user taps the Login button
    Then the user should be logged in successfully
    And the home screen should be displayed

    @Test_Data:
    - Email: test@example.com
    - Password: Password123
    - Account status: Active

    @Expected_Result:
    User successfully logs in and sees home screen.

  # Overrides Platform and Apps
  @negative @Platform:Android,iOS @Apps:ProductB
  Scenario: Login fails with invalid password
    Given the user has a valid account
    When the user enters valid email "test@example.com"
    And the user enters invalid password "WrongPass"
    And the user taps the Login button
    Then an error message should be displayed

    @Test_Data:
    - Email: test@example.com
    - Password: WrongPass (invalid)

    @Expected_Result:
    Error message "Invalid credentials" displayed.
    User remains on login screen.
```

---

## CSV Row Template

```
,{SUMMARY},{DESCRIPTION},"{PRECONDITION}",{STATUS},{PRIORITY},,,,,,,,"{ STEPS}",{TEST_DATA},{EXPECTED_RESULT},,,{APPS},{COMPONENT/FEATURE},{CT_UPDATE_TARGET},{EVIDENCE_TYPE},{LIVE_PROPOSITION},"{PLATFORM}",{REGRESSION_TYPE},{USERS_APPLIED},{AUTOMATABLE},{AUTOMATED_PROPOSITION},{HIGHVISIBILITY},{ISADS},{NBA_FEATURE},{PROXY}
```

---

## Example CSV Row (from feature file above)

**Scenario 1 - Successful login (uses defaults):**
```
,Successful login with valid credentials,As a registered user I want to log into the application so that I can access my account features,"Given the app is installed and launched
And the user is on the login screen",TO DO,Medium,,,,,,,,"Given the user has a valid account
When the user enters valid email ""test@example.com""
And the user enters valid password ""Password123""
And the user taps the Login button
Then the user should be logged in successfully
And the home screen should be displayed","Email: test@example.com
Password: Password123
Account status: Active",User successfully logs in and sees home screen.,,,MyApp,Authentication,,,,"iOS,Android",New Features,,,,,,,
```

**Scenario 2 - Login fails (with overrides):**
```
,Login fails with invalid password,As a registered user I want to log into the application so that I can access my account features,"Given the app is installed and launched
And the user is on the login screen",TO DO,Medium,,,,,,,,"Given the user has a valid account
When the user enters valid email ""test@example.com""
And the user enters invalid password ""WrongPass""
And the user taps the Login button
Then an error message should be displayed","Email: test@example.com
Password: WrongPass (invalid)","Error message ""Invalid credentials"" displayed. User remains on login screen.",,,ProductB,Authentication,,,,"Android,iOS",New Features,,,,,,,
```

---

## Override Resolution

```
1. Start with @Feature_Defaults values
2. Scan scenario tags for @FieldName:Value
3. Override matching fields
4. Regular @tags → Labels column
5. Generate CSV row with resolved values
```

| Tag | Type | Action |
|-----|------|--------|
| `@positive` | Label | Add to Labels |
| `@smoke` | Label | Add to Labels |
| `@Platform:iOS` | Override | Set Platform = iOS |
| `@Apps:MyApp` | Override | Set Apps = MyApp |
| `@Priority:High` | Override | Set Priority = High |

---

## CSV Formatting Rules

1. **Delimiter:** Comma `,`
2. **Multiline text:** Wrap in double quotes `"line1\nline2"`
3. **Quotes inside text:** Escape with double quotes `""value""`
4. **Commas in values:** Wrap in quotes `"iOS,Android"`
5. **Empty values:** Consecutive commas `,,`

---

## Conversion Checklist

- [ ] Parse `@Feature_Defaults:` → Store defaults
- [ ] Copy CSV header (32 columns)
- [ ] For each Scenario:
  - [ ] Extract `Background:` Given steps → Precondition
  - [ ] Extract scenario name → Summary
  - [ ] Extract feature description → Description
  - [ ] Extract non-override tags → Labels
  - [ ] Extract scenario Given/When/Then → Step Summary
  - [ ] Extract `@Test_Data:` block → Test Data
  - [ ] Extract `@Expected_Result:` block → Expected Result
  - [ ] Apply `@FieldName:Value` overrides
  - [ ] Fill remaining fields from defaults
- [ ] Save as `.csv`
- [ ] Verify 32 columns per row

---

## Platform Values

| Override Tag | CSV Value |
|--------------|-----------|
| `@Platform:iOS` | iOS |
| `@Platform:Android` | Android |
| `@Platform:Web` | Web |
| `@Platform:iOS,Android` | "iOS,Android" |

---

## Automatable? Values

| Override Tag | CSV Value |
|--------------|-----------|
| `@Automatable:Yes-iOS` | Yes - iOS |
| `@Automatable:Yes-Android` | Yes - Android |
| `@Automatable:No-iOS` | No - iOS |
| `@Automatable:No-Android` | No - Android |
| `@Automatable:Under_Investigation` | Under Investigation |

---

## Quick Validation

```bash
# Count columns in header
head -1 yourfile.csv | awk -F',' '{print "Header columns:", NF}'

# Count columns in first data row
sed -n '2p' yourfile.csv | awk -F',' '{print "Data columns:", NF}'
```

Both should output `32`.

---

## CLI Tool Usage (Terminal Commands)

The QMetry CLI tool can be run directly from any terminal (Terminal, iTerm, VS Code terminal, etc.) without requiring Augment or any AI assistant.

### Setup (One-time)

```bash
# 1. Install Python dependencies
python3 -m pip install pyyaml certifi

# 2. Create config file (run from project root)
python3 -m qmetry_tool.cli config

# 3. Edit .qmetry_config.yaml with your settings:
#    - QMETRY_API_KEY: Your personal API key from QMetry > Configuration > Open API
#    - QMETRY_PROJECT: Your numeric project ID (e.g., 12345)
#    - QMETRY_DEFAULT_FOLDER: Default folder for uploads (e.g., /Uncategorized)
```

### Available Commands

```bash
# Validate feature file syntax
python3 -m qmetry_tool.cli validate "path/to/file.feature"

# Validate fields against QMetry (requires API connection)
python3 -m qmetry_tool.cli validate "path/to/file.feature" --api

# Export feature file to CSV
python3 -m qmetry_tool.cli export "path/to/file.feature"

# Upload to QMetry (uses default folder from config or @Folder tag)
python3 -m qmetry_tool.cli upload "path/to/file.feature"
python3 -m qmetry_tool.cli up "path/to/file.feature"  # shorthand

# Upload to a specific folder (two syntax options)
python3 -m qmetry_tool.cli up "path/to/file.feature" --folder "/Parent/Child"
python3 -m qmetry_tool.cli up "path/to/file.feature" to "/Parent/Child"

# Preview upload without making changes (dry run)
python3 -m qmetry_tool.cli up "path/to/file.feature" --dry

# Skip field validation (not recommended)
python3 -m qmetry_tool.cli up "path/to/file.feature" --skip-validation

# List folders in QMetry project
python3 -m qmetry_tool.cli folders

# Show help
python3 -m qmetry_tool.cli --help
```

### Examples

```bash
# Validate a feature file
python3 -m qmetry_tool.cli validate "TestCases/Login.feature"

# Validate fields against QMetry
python3 -m qmetry_tool.cli validate "TestCases/Login.feature" --api

# Upload to default folder
python3 -m qmetry_tool.cli up "TestCases/Login.feature"

# Upload to specific folder
python3 -m qmetry_tool.cli up "TestCases/Login.feature" --folder "/TestFolder/Feature"

# Dry run to see what would be uploaded
python3 -m qmetry_tool.cli up "TestCases/Login.feature" --dry
```

### Output

| Command | Output |
|---------|--------|
| `validate` | Displays parsed test cases and any syntax issues |
| `validate --api` | Also checks field names against QMetry (with typo suggestions) |
| `export` | Creates `{filename}_Export.csv` in same directory |
| `upload` | Validates fields, then creates or updates test cases in QMetry |

### Folder Resolution Order

When uploading, the target folder is determined in this order:
1. `--folder` or `to` argument (if specified)
2. `@Folder:` tag in `@Feature_Defaults:` block
3. `QMETRY_DEFAULT_FOLDER` from `.qmetry_config.yaml`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `PyYAML is required` | Run `python3 -m pip install pyyaml` |
| `SSL certificate error` | Run `python3 -m pip install certifi` or set `QMETRY_SSL_VERIFY: false` in config |
| `Config file not found` | Run `python3 -m qmetry_tool.cli config` to create template |
| `API key invalid` | Generate new key from QMetry > Configuration > Open API |
| `Field not found` | Check field name spelling - tool will suggest correct name if typo |
| `Upload aborted` | One or more invalid fields; fix names and retry, or use `--skip-validation` |