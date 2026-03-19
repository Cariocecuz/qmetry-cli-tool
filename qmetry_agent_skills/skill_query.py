"""
QMetry Agent Skill: Query QMetry Data

Query folders, custom fields, and other QMetry metadata.
"""

from typing import Optional, Dict, Any, List

from qmetry_tool.qmetry_api_client import QMetryClient

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

