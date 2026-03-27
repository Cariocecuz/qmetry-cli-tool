# QMetry Skills - Quick Start Guide

## How to Use Skills in Augment

### Option 1: Ask Augment to Run Skills

The easiest way is to simply ask Augment (me!) to run the skills:

**Examples:**
- "List the QMetry folders"
- "Validate the ChromecastSender.feature file"
- "Upload login.feature to /Mobile/Authentication"
- "Generate test cases from PullToRefresh.pdf"
- "Generate test cases from https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature+Name"

I'll execute the appropriate skill and show you the results.

---

### Option 2: Direct Command Execution

You can also run skills directly from the command line:

```bash
# List folders
python3 skills/qmetry-list-folders.py

# Validate feature file
python3 skills/qmetry-validate.py "New Features/CC Sender/ChromecastSender.feature"

# Upload to QMetry
python3 skills/qmetry-upload.py features/mobile/login.feature "/Mobile/Authentication"

# Generate from PDF
python3 skills/qmetry-generate.py "New Features/PullToRefresh/PullToRefresh.pdf"

# Complete workflow
python3 skills/qmetry-workflow.py requirements/login.pdf "/Mobile/Auth" --auto-upload
```

---

### Option 3: Slash Commands (If Supported)

If Augment supports `/` commands in your environment, you can use:

```
/qmetry-list-folders
/qmetry-validate features/mobile/login.feature
/qmetry-upload login.feature "/Mobile/Auth"
```

---

## Available Skills

| Skill | Purpose | Example |
|-------|---------|---------|
| `qmetry-list-folders` | List QMetry folders | `python3 skills/qmetry-list-folders.py` |
| `qmetry-validate` | Validate feature file | `python3 skills/qmetry-validate.py login.feature` |
| `qmetry-upload` | Upload to QMetry | `python3 skills/qmetry-upload.py login.feature "/Mobile/Auth"` |
| `qmetry-generate` | Generate from PDF or Confluence URL | `python3 skills/qmetry-generate.py requirements.pdf` |
| `qmetry-discover-fields` | List custom fields | `python3 skills/qmetry-discover-fields.py` |
| `qmetry-workflow` | End-to-end workflow | `python3 skills/qmetry-workflow.py req.pdf "/Mobile/Auth"` |

---

## Common Workflows

### Workflow 1: Upload Existing Feature File
```bash
# 1. See available folders
python3 skills/qmetry-list-folders.py

# 2. Validate file
python3 skills/qmetry-validate.py "New Features/CC Sender/ChromecastSender.feature"

# 3. Upload
python3 skills/qmetry-upload.py "New Features/CC Sender/ChromecastSender.feature" "/5. Playback/5.19. Chromecast - Sender"
```

### Workflow 2: Generate and Upload (PDF or Confluence)
```bash
# 1a. Generate from PDF
python3 skills/qmetry-generate.py "New Features/PullToRefresh/PullToRefresh.pdf" --platform "iOS,Android"

# 1b. Or generate from Confluence URL (requires Confluence connection)
#     Ask the agent: "Generate test cases from https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature"

# 2. Review the generated file (manual step)

# 3. Upload
python3 skills/qmetry-upload.py features/mobile/browse/pull_to_refresh.feature "/4. Navigation/4.36. Pull to Refresh"
```

### Workflow 3: One-Command Workflow
```bash
# Generate, validate, and upload in one step
python3 skills/qmetry-workflow.py "New Features/PullToRefresh/PullToRefresh.pdf" "/4. Navigation/4.36. Pull to Refresh" --auto-upload
```

---

## Setup (One-Time)

1. **Set environment variables:**
```bash
export QMETRY_API_KEY="your-api-key"
export QMETRY_PROJECT="your-project-id"
```

2. **Or create config file:**
```yaml
# .qmetry_config.yaml
QMETRY_API_KEY: "your-api-key"
QMETRY_PROJECT: "your-project-id"
```

3. **Test it works:**
```bash
python3 skills/qmetry-list-folders.py
```

---

## Tips

1. **Use quotes for paths with spaces:**
   ```bash
   python3 skills/qmetry-validate.py "New Features/CC Sender/ChromecastSender.feature"
   ```

2. **Use --dry-run to preview:**
   ```bash
   python3 skills/qmetry-upload.py login.feature "/Mobile/Auth" --dry-run
   ```

3. **Get help:**
   ```bash
   python3 skills/qmetry-upload.py --help
   ```

4. **Ask Augment for help:**
   - "How do I upload test cases?"
   - "Show me the QMetry folders"
   - "What skills are available?"

---

## Next Steps

- See `skills/README.md` for detailed documentation
- See `AGENT_SKILLS_README.md` for Python API documentation
- See `AGENT_CONVERSATION_EXAMPLES.md` for conversation examples

