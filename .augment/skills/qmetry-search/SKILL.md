---
name: qmetry-search
description: Search QMetry test cases by text, app, or platform. Uses a local cache for fast repeat searches.
---

# QMetry Test Case Search

This skill searches test cases across the QMetry project using text and field filters.

## When to Use This Skill

Use this skill when the user:
- Asks to "find test cases about X"
- Says "search for top 10 rail test cases"
- Wants to "show me all iOS test cases"
- Asks "are there existing TCs for login?"
- Says "look up test cases related to browse"

## How to Search

### Using Python Library (Recommended)

```python
from qmetry_agent_skills import search_qmetry_test_cases

# Text search
result = search_qmetry_test_cases(text="top 10 rail")

# Filter by app and platform
result = search_qmetry_test_cases(text="login", app="MyApp", platform="iOS")

# Force refresh from API (bypass 30-min cache)
result = search_qmetry_test_cases(text="browse", refresh=True)

if result["success"]:
    for tc in result["test_cases"]:
        print(f"{tc['key']} - {tc['summary']}")
```

### Using CLI Script

```bash
python3 skills/qmetry-search.py "top 10 rail"
python3 skills/qmetry-search.py "login" --app MyApp --platform iOS
python3 skills/qmetry-search.py "browse" --refresh --limit 20
```

### Using CLI Module

```bash
python3 -m qmetry_tool.cli search --text "top 10 rail"
python3 -m qmetry_tool.cli search --text "login" --app MyApp --refresh
```

## Return Value Structure

```python
{
    "success": bool,
    "test_cases": [
        {"key": "MOB-TC-21153", "summary": "...", "status": "...", "priority": "..."}
    ],
    "total": int,
    "cache_hit": bool
}
```

## Get a Single Test Case

```python
from qmetry_agent_skills import get_qmetry_test_case

result = get_qmetry_test_case(key="MOB-TC-21153")

if result["success"]:
    tc = result["test_case"]
    print(tc["summary"])
    print(tc["description"])
    for step in tc.get("steps", []):
        print(step)
```

## Cache Management

```python
from qmetry_agent_skills import manage_qmetry_cache

# Check cache status
info = manage_qmetry_cache(action="info")

# Clear cache
manage_qmetry_cache(action="clear")
```

```bash
python3 -m qmetry_tool.cli cache info
python3 -m qmetry_tool.cli cache clear
```

## Performance

- **First search**: ~45-90 seconds (fetches all TCs from API, caches locally)
- **Subsequent searches**: < 0.3 seconds (reads from local cache)
- **Cache TTL**: 30 minutes (auto-expires)
- **Force refresh**: Use `refresh=True` or `--refresh` to bypass cache

## Common Issues

- **Slow first search**: Normal — caching all TCs from API. Subsequent searches are instant.
- **Stale results**: Use `--refresh` or `refresh=True` to get fresh data.
- **No results**: Check search text spelling. Try broader terms.

