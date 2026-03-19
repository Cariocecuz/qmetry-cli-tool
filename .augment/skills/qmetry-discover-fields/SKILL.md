---
name: qmetry-discover-fields
description: Discover all custom fields and their available options in QMetry project
---

# QMetry Custom Field Discovery

This skill discovers all custom fields and their options in a QMetry project.

## When to Use This Skill

Use this skill when the user:
- Asks "what custom fields are available?"
- Wants to know "what values can I use for Platform?"
- Says "show me the QMetry fields"
- Needs to know valid field options
- Asks about field names or values

## How to Discover Fields

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import discover_qmetry_custom_fields

result = discover_qmetry_custom_fields()

if result["success"]:
    print(f"✅ Discovered {result['field_count']} custom fields")
    
    for field_name, field_data in result["fields"].items():
        print(f"\n{field_name}:")
        print(f"  ID: {field_data['id']}")
        
        if field_data.get("options"):
            print(f"  Options:")
            for option_value, option_id in field_data["options"].items():
                print(f"    - {option_value}")
else:
    print(f"❌ Error: {result['error_message']}")
```

### Using CLI Script

```bash
python3 skills/qmetry-discover-fields.py
```

## Return Value Structure

```python
{
    "success": bool,
    "fields": {
        "field_name": {
            "id": str,
            "options": {"value": int}  # For dropdown/multi-select fields
        }
    },
    "field_count": int
}
```

## Common Custom Fields

Standard fields in most QMetry projects:

**Apps** (Multi-select)
- Application names

**Platform** (Multi-select)
- iOS
- Android
- Mobile
- Web
- Roku

**Component/Feature** (Text or Dropdown)
- Feature area or component name

**Regression_Type** (Dropdown)
- New_Features
- Smoke
- Sanity
- Full_Regression

**Automatable?** (Dropdown)
- Yes
- No
- Under investigation

## Using Fields in Feature Files

```gherkin
@Feature_Defaults:
@Apps:MyApp
@Platform:iOS,Android
@Component/Feature:Authentication
@Regression_Type:New_Features
@Automatable?:Yes

Feature: User Login
  ...
```

## Example Workflow

1. User asks what fields are available
2. Call `discover_qmetry_custom_fields()`
3. Display field names and options
4. User can use these in feature files

## Common Issues

- **No fields returned**: Check API key permissions
- **Field options empty**: Field may be text type (no predefined options)
- **API error**: Verify credentials and project ID

