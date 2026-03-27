# Agent Conversation Examples

This document shows how Augment would use the QMetry agent skills in real conversations.

---

## Example 1: Generate Test Cases from PDF (with Review)

**User:** "Generate test cases from the login requirements PDF"

**Agent Internal Process:**
1. Identifies PDF path from context or asks user
2. Calls `generate_feature_file_from_pdf()`
3. Returns preview to user

**Agent Response:**
```
✅ Generated feature file from login_spec.pdf

📄 File: features/mobile/authentication/login.feature
📊 Test Cases: 8

Preview:
```gherkin
@Feature_Defaults:
@Apps:MyApp
@Platform:iOS,Android
@Component/Feature:Authentication
@Regression_Type:New_Features

Feature: User Login
  As a user I want to log in to access my account

  Background:
    Given the app is installed
    And user is on login screen

  # TC-01
  @positive
  Scenario: Successful login with valid credentials
    Given user has valid account
    When user enters email and password
    And user taps Login
    Then user sees home screen
    ...
```

⚠️ Please review the generated file and fill in the Component/Feature field if needed.

When ready to upload, say: "upload login test cases to QMetry"
```

**User:** "Upload login test cases to QMetry in /Mobile/Authentication"

**Agent Internal Process:**
1. Calls `validate_qmetry_feature_file()` first
2. If valid, calls `create_qmetry_test_case()`
3. Returns results

**Agent Response:**
```
✅ Successfully uploaded test cases to QMetry!

📊 Results:
- Created: 6 test cases
- Updated: 2 test cases (already existed)
- Failed: 0

📁 Location: MOB-12345:/Mobile/Authentication

Test Cases:
✓ TC-001: Successful login with valid credentials
✓ TC-002: Login fails with invalid password
✓ TC-003: Login fails with invalid email
✓ TC-004: Password reset flow
✓ TC-005: Remember me functionality
✓ TC-006: Social login (Google)
↻ TC-007: Social login (Apple) - Updated
↻ TC-008: Biometric login - Updated
```

---

## Example 2: Quick Auto-Upload Workflow

**User:** "Create test cases from pull_to_refresh_spec.pdf and upload to /Mobile/Browse"

**Agent Internal Process:**
1. Recognizes user wants end-to-end workflow
2. Calls `create_test_cases_from_pdf()` with `auto_upload=True`
3. Returns combined results

**Agent Response:**
```
✅ Generated and uploaded test cases from pull_to_refresh_spec.pdf

📄 Feature File: features/mobile/browse/pull_to_refresh.feature
📊 Test Cases: 14

Upload Results:
- Created: 14 test cases
- Updated: 0
- Failed: 0

📁 QMetry Location: MOB-12345:/Mobile/Browse

All test cases successfully created! ✨
```

---

## Example 3: Validation Error Handling

**User:** "Upload the chromecast feature file to QMetry"

**Agent Internal Process:**
1. Calls `validate_qmetry_feature_file()` first
2. Detects invalid fields
3. Returns validation errors with suggestions

**Agent Response:**
```
⚠️ Validation failed - found invalid field names

Invalid Fields:
- Platfrom → Did you mean "Platform"?
- Componet → Did you mean "Component/Feature"?

Please fix these field names in the feature file, or if you're sure they're correct, say:
"upload chromecast test cases and skip validation"

(Note: Skipping validation is not recommended as it may cause upload failures)
```

**User:** "Fix those typos and try again"

**Agent Internal Process:**
1. Edits the feature file to fix typos
2. Re-validates
3. Uploads

**Agent Response:**
```
✓ Fixed field names:
  - Platfrom → Platform
  - Componet → Component/Feature

✓ Validation passed!

✅ Uploaded 12 test cases to /Mobile/Chromecast
```

---

## Example 4: Exploring QMetry Structure

**User:** "Where should I upload the authentication test cases?"

**Agent Internal Process:**
1. Calls `list_qmetry_folders()`
2. Searches for authentication-related folders
3. Suggests appropriate location

**Agent Response:**
```
📁 Available folders in QMetry:

Mobile
  ├── Authentication
  ├── Browse
  ├── Playback
  └── Settings

Roku
  ├── Authentication
  └── Playback

Web
  └── Authentication

I recommend uploading to:
📍 /Mobile/Authentication

Would you like me to upload there?
```

---

## Example 5: Batch Processing

**User:** "Generate test cases from all PDFs in requirements/mobile/authentication/"

**Agent Internal Process:**
1. Lists PDFs in directory
2. Calls `generate_feature_file_from_pdf()` for each
3. Returns summary

**Agent Response:**
```
✅ Generated 3 feature files from authentication requirements

Files Created:
1. features/mobile/authentication/login.feature (8 test cases)
2. features/mobile/authentication/signup.feature (6 test cases)
3. features/mobile/authentication/password_reset.feature (4 test cases)

Total: 18 test cases across 3 features

⚠️ Next Steps:
Review the generated files, then say:
"upload all authentication test cases to /Mobile/Authentication"
```

**User:** "Upload all authentication test cases to /Mobile/Authentication"

**Agent Internal Process:**
1. Finds all .feature files in authentication directory
2. Calls `create_qmetry_test_case()` for each
3. Returns combined results

**Agent Response:**
```
✅ Uploaded 3 feature files to /Mobile/Authentication

Results:
- login.feature: 8 created, 0 updated
- signup.feature: 6 created, 0 updated
- password_reset.feature: 4 created, 0 updated

Total: 18 test cases created
```

---

## Example 6: Dry Run Preview

**User:** "Show me what would be uploaded from login.feature without actually uploading"

**Agent Internal Process:**
1. Calls `create_qmetry_test_case()` with `dry_run=True`
2. Returns preview

**Agent Response:**
```
📋 Dry Run Preview - No changes will be made

Would upload 8 test cases to /Mobile/Authentication:
1. Successful login with valid credentials
2. Login fails with invalid password
3. Login fails with invalid email
4. Login fails with empty password
5. Password reset flow
6. Remember me functionality
7. Social login (Google)
8. Biometric login

To proceed with upload, say: "upload login test cases to QMetry"
```

---

## Example 7: Field Discovery

**User:** "What custom fields can I use in my feature files?"

**Agent Internal Process:**
1. Calls `discover_qmetry_custom_fields()`
2. Formats results for readability

**Agent Response:**
```
📋 Available Custom Fields in QMetry:

Standard Fields:
- Apps (multi-select)
- Platform (multi-select): iOS, Android, Web, Roku
- Component/Feature (text)
- Regression_Type (dropdown): New_Features, Regression, Smoke
- TC_requires_use_of_proxy (dropdown): Yes, No

Additional Fields:
- Evidence_Type
- Live_Proposition
- Users_Applied
- Automatable?
- HighVisibility
- IsAds?

Use these in your @Feature_Defaults: block like:
@Apps:MyApp
@Platform:iOS,Android
@Regression_Type:New_Features
```

---

## Example 8: Error Recovery

**User:** "Upload test cases to /Mobile/NewFeature"

**Agent Internal Process:**
1. Attempts to create folder
2. Folder creation fails (permission error)
3. Provides helpful error message

**Agent Response:**
```
❌ Failed to create folder: /Mobile/NewFeature

Error: API key lacks folder creation permissions

Suggested Solutions:
1. Create the folder manually in QMetry:
   - Go to QMetry > Test Cases
   - Right-click "Mobile" folder
   - Select "New Folder"
   - Name it "NewFeature"

2. Then retry: "upload test cases to /Mobile/NewFeature"

Alternatively, upload to an existing folder:
- /Mobile/Authentication
- /Mobile/Browse
- /Mobile/Playback
```

---

## Example 9: Multi-Step Workflow with Approval

**User:** "Process the chromecast_sender.pdf requirements"

**Agent Internal Process:**
1. Calls `create_test_cases_from_pdf()` with `auto_upload=False`
2. Returns preview and waits for approval

**Agent Response:**
```
✅ Generated feature file from chromecast_sender.pdf

📄 File: features/mobile/chromecast/chromecast_sender.feature
📊 Test Cases: 25

Preview:
```gherkin
@Feature_Defaults:
@Apps:MyApp
@Platform:iOS
@Component/Feature:Chromecast_Sender
...
```

⚠️ Please review:
1. Check that Component/Feature is correct
2. Verify test scenarios match requirements
3. Confirm Platform (currently set to iOS)

When ready, say: "upload chromecast test cases to /Mobile/Chromecast"
```

**User:** "Change Platform to iOS,Android and upload"

**Agent Internal Process:**
1. Edits feature file to update Platform
2. Validates
3. Uploads

**Agent Response:**
```
✓ Updated Platform: iOS → iOS,Android

✅ Uploaded 25 test cases to /Mobile/Chromecast
```

---

## Example 10: Search for Existing Test Cases

**User:** "Are there any test cases about the top 10 rail?"

**Agent Internal Process:**
1. Calls `search_qmetry_test_cases(text="top 10 rail")`
2. Returns cached results (or fetches from API on first search)

**Agent Response:**
```
✅ Found 5 test case(s) (from cache)

Key              | Summary                                            | Status
-----------------+----------------------------------------------------+--------
MOB-TC-21153     | Verify Top 10 Rail displays correctly               | Draft
MOB-TC-21154     | Verify Top 10 Rail scrolling behavior                | Draft
MOB-TC-21155     | Verify Top 10 Rail deep link navigation              | Draft
MOB-TC-21160     | Verify Top 10 Rail with no content available         | Draft
MOB-TC-21161     | Verify Top 10 Rail refresh on pull-to-refresh        | Draft
```

---

## Example 11: Get Test Case Details

**User:** "Show me details for MOB-TC-21153"

**Agent Internal Process:**
1. Calls `get_qmetry_test_case(key="MOB-TC-21153")`
2. Returns full TC detail including steps

**Agent Response:**
```
📋 MOB-TC-21153: Verify Top 10 Rail displays correctly

Status: Draft
Priority: Medium
Description: Verify that the Top 10 Rail is displayed on the home screen...

Steps:
1. Launch the app → Home screen is displayed
2. Scroll to the Top 10 Rail → Rail is visible with correct title
3. Verify content tiles are displayed → At least 10 tiles shown
```

---

## Example 12: Search with Filters

**User:** "Find iOS test cases for MyApp related to login"

**Agent Internal Process:**
1. Calls `search_qmetry_test_cases(text="login", app="MyApp", platform="iOS")`
2. Filters results by custom fields

**Agent Response:**
```
✅ Found 3 test case(s) matching "login" for MyApp / iOS

Key              | Summary                                            | Status
-----------------+----------------------------------------------------+--------
MOB-TC-20100     | Verify successful login with valid credentials      | Approved
MOB-TC-20101     | Verify login fails with invalid password             | Approved
MOB-TC-20105     | Verify biometric login on iOS                        | Draft
```

---

## Example 13: Cache Management

**User:** "The search results seem stale, can you refresh?"

**Agent Internal Process:**
1. Calls `search_qmetry_test_cases(text="...", refresh=True)`
2. Bypasses cache, fetches fresh data from API

**Agent Response:**
```
🔄 Refreshing cache from QMetry API... (this may take 45-90 seconds)

✅ Cache refreshed! 4,681 test cases loaded.
Found 5 test case(s) matching your search.
```

**User:** "Clear the TC cache"

**Agent Internal Process:**
1. Calls `manage_qmetry_cache(action="clear")`

**Agent Response:**
```
✅ Cache cleared. Next search will fetch fresh data from the API.
```

---

## Example 14: Generate Test Cases from Confluence Specification

**User:** "Generate test cases from https://confluence.example.com/wiki/spaces/PTC/pages/12345/Feature+Name"

**Agent Internal Process:**
1. Reads the Confluence page content via the Confluence connection
2. Follows any linked or child pages for full coverage
3. Extracts testable requirements, acceptance criteria, edge cases, and feature flags
4. Presents analysis and proposed test case list for review
5. Generates `.feature` file after user approval

**Agent Response (Step 1 — Analysis):**
```
📋 Analysis: Feature Name (Web & Mobile)

Source Spec: Confluence Page — Status: COMPLETE

🎯 Feature Summary
[Summary of the feature extracted from the spec]

📌 Extracted Testable Requirements
| Req | Requirement | Scope |
|-----|------------|-------|
| 1   | Requirement description | Web, Mobile |
| 2   | Another requirement | Web, Mobile |

🧪 Proposed Test Cases (17 TCs)
| TC# | Type | Scenario |
|-----|------|----------|
| TC-01 | ✅ Positive | Main flow scenario |
| TC-02 | ❌ Negative | Edge case scenario |
...

❓ Clarifying Questions:
1. Should analytics tracking be in scope?
2. What Component/Feature name should be used?

Please review and I'll generate the feature file.
```

**User:** "Create the feature file as is"

**Agent Response (Step 2 — Generation):**
```
✅ Feature file created: New Features/FeatureName/FeatureName.feature
📊 17 TCs across 8 use cases

Ready for your review in VS Code. When ready to upload, say:
"upload to /2026/FeatureName/Core"
```

> **Note:** This workflow requires the Confluence MCP connection to be configured.

---

## Key Agent Behaviors

1. **Proactive Validation**: Always validates before uploading
2. **Helpful Errors**: Provides suggestions when errors occur
3. **Confirmation for Destructive Actions**: Asks before uploading (unless auto_upload=True)
4. **Context Awareness**: Remembers previous operations in conversation
5. **Flexible Input**: Accepts various phrasings for the same operation
6. **Progress Feedback**: Shows what's happening during long operations
7. **Cache Awareness**: Uses cached results when available, explains when refreshing
8. **Confluence Integration**: Can analyze specs directly from Confluence URLs when the connection is available

