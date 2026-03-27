"""
QMetry Agent Skill: Query QMetry Data

Query folders, custom fields, search test cases, and other QMetry metadata.
"""

from typing import Optional, Dict, Any, List

from qmetry_tool.qmetry_api_client import QMetryClient
from qmetry_tool.search_engine import QueryEngine
from qmetry_tool.field_schema import FieldSchemaCache
from qmetry_tool.tc_cache import TCSearchCache

from .core import (
    AgentQMetryConfig,
    create_error_response,
    create_success_response,
    handle_exception,
    ErrorType
)


def list_qmetry_folders(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all test case folders in a QMetry project.
    
    This skill retrieves the complete folder hierarchy from QMetry,
    useful for determining where to upload test cases.
    
    Args:
        api_key: QMetry API key (or use environment variable QMETRY_API_KEY)
        project_id: QMetry project ID (or use environment variable QMETRY_PROJECT)
    
    Returns:
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
    
    Example:
        result = list_qmetry_folders(
            api_key="abc123...",
            project_id="12345"
        )
        
        # Returns:
        # {
        #     "success": True,
        #     "folders": [
        #         {
        #             "id": 1,
        #             "name": "Mobile",
        #             "path": "/Mobile",
        #             "children": [
        #                 {"id": 2, "name": "Authentication", "path": "/Mobile/Authentication", ...}
        #             ]
        #         }
        #     ]
        # }
    
    Agent Usage:
        When user says: "show me the QMetry folders"
        When user says: "list available folders in QMetry"
        When user says: "where can I upload test cases?"
    """
    try:
        # Initialize configuration
        config = AgentQMetryConfig.auto_detect(
            api_key=api_key,
            project=project_id
        )
        
        # Initialize API client
        client = QMetryClient(config.to_base_config())
        
        # Fetch folders
        result = client.list_folders()
        
        if not result.success:
            return create_error_response(
                error_type=ErrorType.API_ERROR,
                error_message=f"Failed to list folders: {result.error}"
            )
        
        # Parse folder data
        folders = result.data
        if isinstance(folders, dict):
            folders = folders.get('data', [])
        elif not isinstance(folders, list):
            folders = []
        
        # Build folder hierarchy with paths
        folder_list = _build_folder_hierarchy(folders)
        
        return create_success_response(
            message=f"Found {len(folder_list)} top-level folders",
            data={
                "folders": folder_list,
                "folder_count": _count_folders(folder_list)
            }
        )
        
    except Exception as e:
        return handle_exception(e, "listing QMetry folders")


def discover_qmetry_custom_fields(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Discover all custom fields and their options in a QMetry project.
    
    This skill retrieves custom field metadata, useful for understanding
    what fields are available and what values they accept.
    
    Args:
        api_key: QMetry API key (or use environment variable QMETRY_API_KEY)
        project_id: QMetry project ID (or use environment variable QMETRY_PROJECT)
    
    Returns:
        {
            "success": bool,
            "fields": {
                "field_name": {
                    "id": str,
                    "type": str,
                    "options": [{"id": int, "value": str}]  # For dropdown/multi-select
                }
            },
            "field_count": int
        }
    
    Example:
        result = discover_qmetry_custom_fields(
            api_key="abc123...",
            project_id="12345"
        )
    
    Agent Usage:
        When user says: "what custom fields are available?"
        When user says: "show me the QMetry fields"
        When user says: "what values can I use for Platform?"
    """
    try:
        # Initialize configuration
        config = AgentQMetryConfig.auto_detect(
            api_key=api_key,
            project=project_id
        )
        
        # Initialize API client
        client = QMetryClient(config.to_base_config())
        
        # Discover fields
        field_map = client.discover_field_ids()
        
        if not field_map:
            return create_error_response(
                error_type=ErrorType.API_ERROR,
                error_message="Failed to discover custom fields"
            )
        
        # Build field details
        fields = {}
        for field_name, field_id in field_map.items():
            fields[field_name] = {
                "id": field_id,
                "options": config.field_options_cache.get(field_name, {})
            }
        
        return create_success_response(
            message=f"Discovered {len(fields)} custom fields",
            data={
                "fields": fields,
                "field_count": len(fields)
            }
        )
        
    except Exception as e:
        return handle_exception(e, "discovering custom fields")


def _init_query_engine(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> tuple:
    """Shared helper to initialize config, client, and QueryEngine."""
    config = AgentQMetryConfig.auto_detect(api_key=api_key, project=project_id)
    client = QMetryClient(config.to_base_config())
    schema = FieldSchemaCache(client)
    engine = QueryEngine(client, schema, int(config.project))
    return config, client, engine


def search_qmetry_test_cases(
    text: Optional[str] = None,
    app: Optional[str] = None,
    platform: Optional[str] = None,
    folder_id: Optional[int] = None,
    limit: int = 50,
    refresh: bool = False,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search test cases across the QMetry project using text and field filters.

    Uses a local cache (30-min TTL) to avoid expensive full-project API scans.
    Pass refresh=True to bypass the cache and fetch fresh data from the API.

    Args:
        text: Free-text search across summary, description, and precondition
        app: Filter by App custom field value (client-side)
        platform: Filter by Platform custom field value (client-side)
        folder_id: Restrict search to a specific folder (server-side)
        limit: Maximum number of results to return (default: 50)
        refresh: Bypass cache and fetch fresh data from API (default: False)
        api_key: QMetry API key (or use environment variable QMETRY_API_KEY)
        project_id: QMetry project ID (or use environment variable QMETRY_PROJECT)

    Returns:
        {
            "success": bool,
            "test_cases": [{"key": str, "summary": str, ...}],
            "total": int,
            "cache_hit": bool
        }

    Agent Usage:
        When user says: "find test cases about login"
        When user says: "search for top 10 rail test cases"
        When user says: "show me iOS test cases for MyApp"
    """
    try:
        _config, _client, engine = _init_query_engine(api_key, project_id)

        result = engine.search(
            folder_id=folder_id,
            text=text,
            app=app,
            platform=platform,
            limit=limit,
            refresh=refresh,
        )

        if result.get("error"):
            return create_error_response(
                error_type=ErrorType.API_ERROR,
                error_message=f"Search failed: {result['error']}"
            )

        test_cases = [
            {
                "key": tc.get("key", ""),
                "summary": tc.get("summary", ""),
                "status": _extract_status(tc),
                "priority": _extract_priority(tc),
            }
            for tc in result.get("data", [])
        ]

        return create_success_response(
            message=f"Found {result['total']} test case(s)",
            data={
                "test_cases": test_cases,
                "total": result["total"],
                "cache_hit": result.get("cache_hit", False),
            }
        )

    except Exception as e:
        return handle_exception(e, "searching test cases")


def get_qmetry_test_case(
    key: str,
    include_steps: bool = True,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve a single test case by its key (e.g. MOB-TC-21153).

    Returns full detail including summary, description, precondition,
    custom fields, and optionally test steps.

    Args:
        key: Test case key (e.g. "MOB-TC-21153")
        include_steps: Whether to fetch test steps (default: True)
        api_key: QMetry API key
        project_id: QMetry project ID

    Returns:
        {
            "success": bool,
            "test_case": {
                "key": str,
                "summary": str,
                "description": str,
                "precondition": str,
                "status": str,
                "priority": str,
                "custom_fields": {...},
                "steps": [{"stepData": str, "expectedResult": str}] | None
            }
        }

    Agent Usage:
        When user says: "get test case MOB-TC-21153"
        When user says: "show me details for MOB-TC-21153"
    """
    try:
        _config, _client, engine = _init_query_engine(api_key, project_id)

        result = engine.get_by_key(key, include_steps=include_steps)

        if result.get("error"):
            return create_error_response(
                error_type=ErrorType.API_ERROR,
                error_message=f"Failed to retrieve {key}: {result['error']}",
                suggestion="Check that the test case key is correct"
            )

        tc = result["tc"]
        steps = result.get("steps")

        tc_data = {
            "key": tc.get("key", ""),
            "summary": tc.get("summary", ""),
            "description": tc.get("description", ""),
            "precondition": tc.get("precondition", ""),
            "status": _extract_status(tc),
            "priority": _extract_priority(tc),
            "custom_fields": _extract_custom_fields(tc),
        }
        if include_steps and steps is not None:
            tc_data["steps"] = steps

        return create_success_response(
            message=f"Retrieved test case {key}",
            data={"test_case": tc_data}
        )

    except Exception as e:
        return handle_exception(e, f"retrieving test case {key}")


def manage_qmetry_cache(
    action: str = "info",
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage the local test case search cache.

    Args:
        action: "info" to get cache status, "clear" to delete cache
        api_key: QMetry API key (unused for cache ops, kept for consistency)
        project_id: QMetry project ID (unused for cache ops)

    Returns:
        {
            "success": bool,
            "cache": {"exists": bool, "total_tcs": int, "age_minutes": float, ...}
        }

    Agent Usage:
        When user says: "show cache status"
        When user says: "clear the TC cache"
    """
    try:
        cache = TCSearchCache()

        if action == "clear":
            deleted = cache.clear()
            msg = "Cache cleared." if deleted else "No cache file to clear."
            return create_success_response(message=msg)

        # Default: info
        info = cache.info()
        return create_success_response(
            message="Cache exists" if info.get("exists") else "No cache file found",
            data={"cache": info}
        )

    except Exception as e:
        return handle_exception(e, "managing TC cache")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_status(tc: Dict) -> str:
    """Extract status name from TC data."""
    status = tc.get("status")
    if isinstance(status, dict):
        return status.get("name", "—")
    return str(status) if status else "—"


def _extract_priority(tc: Dict) -> str:
    """Extract priority name from TC data."""
    priority = tc.get("priority")
    if isinstance(priority, dict):
        return priority.get("name", "—")
    return str(priority) if priority else "—"


def _extract_custom_fields(tc: Dict) -> Dict[str, Any]:
    """Flatten custom fields into {name: value} dict."""
    result = {}
    cf = tc.get("customFields", {})
    for _fid, fdata in cf.items():
        name = fdata.get("name", _fid)
        raw = fdata.get("value", "")
        if isinstance(raw, list):
            result[name] = [
                item.get("name", str(item)) if isinstance(item, dict) else str(item)
                for item in raw
            ]
        else:
            result[name] = raw
    return result


def _build_folder_hierarchy(folders: List[Dict], parent_path: str = "") -> List[Dict]:
    """Build folder hierarchy with full paths."""
    result = []
    for folder in folders:
        name = folder.get('name', 'Unknown')
        folder_id = folder.get('id', '')
        path = f"{parent_path}/{name}" if parent_path else f"/{name}"
        
        folder_data = {
            "id": folder_id,
            "name": name,
            "path": path
        }
        
        children = folder.get('children', [])
        if children:
            folder_data["children"] = _build_folder_hierarchy(children, path)
        
        result.append(folder_data)
    
    return result


def _count_folders(folders: List[Dict]) -> int:
    """Count total folders including nested ones."""
    count = len(folders)
    for folder in folders:
        if 'children' in folder:
            count += _count_folders(folder['children'])
    return count

