---
name: qmetry-list-folders
description: List all test case folders in QMetry project to help determine where to upload test cases
---

# QMetry Folder Listing

This skill lists all test case folders in a QMetry project.

## When to Use This Skill

Use this skill when the user:
- Asks to "list QMetry folders"
- Wants to "see available folders"
- Says "where can I upload test cases?"
- Needs to know the folder structure
- Asks "show me the folders in QMetry"

## How to List Folders

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import list_qmetry_folders

result = list_qmetry_folders()

if result["success"]:
    print(f"✅ Found {result['folder_count']} folders")
    
    for folder in result["folders"]:
        print(f"📁 {folder['name']} (id: {folder['id']})")
        print(f"   Path: {folder['path']}")
        
        if 'children' in folder:
            for child in folder['children']:
                print(f"  📁 {child['name']}")
else:
    print(f"❌ Error: {result['error_message']}")
```

### Using CLI Script

```bash
python3 skills/qmetry-list-folders.py
```

## Return Value Structure

```python
{
    "success": bool,
    "folders": [
        {
            "id": int,
            "name": str,
            "path": str,
            "children": [...]  # Nested folders
        }
    ],
    "folder_count": int
}
```

## Folder Structure Example

```
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
```

## Using Folder Paths

When uploading test cases, use the full path:
- `/Mobile/Authentication`
- `/Mobile/Browse`
- `/Roku/Playback`

## Example Workflow

1. User asks where to upload test cases
2. Call `list_qmetry_folders()`
3. Display folder hierarchy
4. User selects target folder
5. Use folder path in upload command

## Common Issues

- **No folders returned**: Check API key permissions
- **Empty folder list**: Project may not have folders created yet
- **API error**: Verify credentials and project ID

