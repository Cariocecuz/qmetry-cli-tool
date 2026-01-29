"""
QMetry API Client Module for QMetry CLI Tool

Handles communication with QMetry for Jira (QTM4J) Cloud API.
- Authentication via API key
- Test case creation
- Folder management
- Custom field discovery
"""

import json
import ssl
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

try:
    import certifi
    HAS_CERTIFI = True
except ImportError:
    HAS_CERTIFI = False


def get_ssl_context(verify: bool = True):
    """Get SSL context based on verification setting."""
    if not verify:
        # Bypass SSL verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    elif HAS_CERTIFI:
        return ssl.create_default_context(cafile=certifi.where())
    else:
        return None

from .config_handler import QMetryConfig, save_cache


# QTM4J Cloud API base URL
API_BASE_URL = "https://qtmcloud.qmetry.com/rest/api/latest"


@dataclass
class APIResponse:
    """Represents an API response."""
    success: bool
    data: Any = None
    error: str = ""
    status_code: int = 0


class QMetryClient:
    """Client for QMetry for Jira (QTM4J) Cloud API."""

    def __init__(self, config: QMetryConfig):
        self.config = config
        self.api_key = config.api_key
        self.project = config.project
        self.ssl_context = get_ssl_context(config.ssl_verify)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> APIResponse:
        """Make an HTTP request to the QMetry API."""
        url = f"{API_BASE_URL}{endpoint}"

        if params:
            url += "?" + urlencode(params)

        headers = {
            "apiKey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = json.dumps(data).encode('utf-8') if data else None

        try:
            req = Request(url, data=body, headers=headers, method=method)
            with urlopen(req, timeout=30, context=self.ssl_context) as response:
                response_body = response.read().decode('utf-8')
                # Handle 204 No Content (empty response body)
                if response.status == 204 or not response_body.strip():
                    return APIResponse(
                        success=True,
                        data=None,
                        status_code=response.status
                    )
                response_data = json.loads(response_body)
                return APIResponse(
                    success=True,
                    data=response_data,
                    status_code=response.status
                )
        except HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            return APIResponse(
                success=False,
                error=f"HTTP {e.code}: {error_body}",
                status_code=e.code
            )
        except URLError as e:
            return APIResponse(success=False, error=f"Network error: {e.reason}")
        except json.JSONDecodeError as e:
            return APIResponse(success=False, error=f"Invalid JSON response: {e}")
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    # --- Folder Management ---
    
    def list_folders(self) -> APIResponse:
        """List all test case folders in the project."""
        return self._make_request(
            "GET",
            f"/projects/{self.project}/testcase-folders"
        )
    
    def search_folder(self, folder_name: str) -> APIResponse:
        """Search for a folder by name."""
        return self._make_request(
            "GET",
            f"/projects/{self.project}/testcase-folders/search",
            params={"folderName": folder_name}
        )
    
    def create_folder(self, name: str, parent_id: Optional[int] = None) -> APIResponse:
        """Create a new folder."""
        data = {"name": name}
        if parent_id:
            data["parentFolderId"] = parent_id
        
        return self._make_request(
            "POST",
            f"/projects/{self.project}/testcase-folders",
            data=data
        )
    
    def get_or_create_folder_path(self, path: str) -> Optional[int]:
        """
        Get folder ID for a path like '/Mobile/PTR', creating folders if needed.
        
        Returns:
            Folder ID or None if failed
        """
        # Check cache first
        if path in self.config.folder_cache:
            return self.config.folder_cache[path]
        
        # Parse path into segments
        segments = [s for s in path.strip('/').split('/') if s]
        if not segments:
            return None
        
        current_parent_id = None
        current_path = ""
        
        for segment in segments:
            current_path += f"/{segment}"
            
            # Check cache for this partial path
            if current_path in self.config.folder_cache:
                current_parent_id = self.config.folder_cache[current_path]
                continue
            
            # Search for folder
            result = self.search_folder(segment)
            
            folder_id = None
            if result.success and result.data:
                # Find matching folder with correct parent
                # Note: API returns 'parentId' in search results, not 'parentFolderId'
                folders = result.data if isinstance(result.data, list) else [result.data]
                for folder in folders:
                    parent_id = folder.get('parentId') or folder.get('parentFolderId')
                    if parent_id == current_parent_id:
                        folder_id = folder.get('id')
                        break
            
            if folder_id is None:
                # Create the folder
                create_result = self.create_folder(segment, current_parent_id)
                if create_result.success and create_result.data:
                    folder_id = create_result.data.get('id')
                else:
                    print(f"\n❌ Failed to create folder: {current_path}")
                    print(f"   API Error: {create_result.error}")
                    print(f"\n   This is likely a permissions issue with your API key.")
                    print(f"   Workaround: Create the folder manually in QMetry, then retry the upload.")
                    print(f"   Path to create: {path}")
                    return None
            
            # Cache and continue
            self.config.folder_cache[current_path] = folder_id
            current_parent_id = folder_id
        
        # Save updated cache
        save_cache(self.config)

        return current_parent_id

    # --- Custom Field Discovery ---

    def get_custom_fields(self) -> APIResponse:
        """Get all custom fields for the project."""
        return self._make_request(
            "GET",
            f"/projects/{self.project}/testcase-custom-fields"
        )

    def discover_field_ids(self) -> Dict[str, str]:
        """
        Discover custom field IDs and their options, and cache them.

        Returns:
            Dictionary mapping field names to field IDs
        """
        result = self.get_custom_fields()

        if not result.success:
            print(f"Failed to get custom fields: {result.error}")
            return {}

        field_map = {}
        fields = result.data if isinstance(result.data, list) else []

        for field in fields:
            field_name = field.get('name', '')
            field_id = field.get('id', '')
            if field_name and field_id:
                field_map[field_name] = field_id
                self.config.field_id_cache[field_name] = field_id

                # Cache options if present (for dropdown/multi-select fields)
                options = field.get('options', [])
                if options:
                    self.config.field_options_cache[field_name] = {
                        opt.get('value', ''): opt.get('id')
                        for opt in options
                        if opt.get('value') and opt.get('id')
                    }

        # Save cache
        save_cache(self.config)

        return field_map

    def get_option_ids(self, field_name: str, values: str) -> list:
        """
        Convert comma-separated option values to their IDs.

        Args:
            field_name: Name of the custom field
            values: Comma-separated option values (e.g., "AppA,AppB")

        Returns:
            String value - either comma-separated option IDs or the original value for text fields
        """
        # Ensure options are cached
        if field_name not in self.config.field_options_cache:
            self.discover_field_ids()

        options_map = self.config.field_options_cache.get(field_name, {})

        # If no options defined, this might be a text field - return the value as-is
        if not options_map:
            return values

        # Split values and look up IDs
        value_list = [v.strip() for v in values.split(',')]
        option_ids = []

        for value in value_list:
            option_id = options_map.get(value)
            if option_id:
                option_ids.append(str(option_id))  # Convert to string
            else:
                print(f"  Warning: Option '{value}' not found for field '{field_name}'")

        # Return comma-separated string of option IDs (API requires string, not array)
        return ','.join(option_ids) if option_ids else values

    def get_field_id(self, field_name: str) -> Optional[str]:
        """Get field ID for a field name, discovering if needed."""
        # Check manual config first
        if field_name in self.config.custom_fields:
            return self.config.custom_fields[field_name]

        # Check cache
        if field_name in self.config.field_id_cache:
            return self.config.field_id_cache[field_name]

        # Discover fields
        if not self.config.field_id_cache:
            self.discover_field_ids()

        return self.config.field_id_cache.get(field_name)

    # --- Test Case Management ---

    def create_test_case(
        self,
        summary: str,
        description: str = "",
        precondition: str = "",
        steps: List[str] = None,
        test_data: str = "",
        expected_result: str = "",
        folder_id: Optional[int] = None,
        labels: List[str] = None,
        priority: str = "Medium",
        status: str = "TO DO",
        custom_fields: Dict[str, str] = None
    ) -> APIResponse:
        """
        Create a new test case in QMetry.

        Args:
            summary: Test case name/summary
            description: Test case description
            precondition: Precondition steps
            steps: List of test steps
            test_data: Test data content
            expected_result: Expected result content
            folder_id: Target folder ID
            labels: List of labels
            priority: Priority level
            status: Test case status
            custom_fields: Dictionary of custom field values

        Returns:
            APIResponse with created test case data
        """
        # Build request body - projectId must be in the body as an INTEGER
        # Note: priority and status are optional - omit them to use defaults
        data = {
            "projectId": int(self.project),
            "summary": summary,
        }

        # Only add optional fields if they have values
        if description:
            data["description"] = description
        if precondition:
            data["precondition"] = precondition

        # Add steps - use "stepDetails" field name (not stepSummary)
        if steps:
            data["steps"] = [
                {
                    "stepDetails": "\n".join(steps),
                    "testData": test_data,
                    "expectedResult": expected_result
                }
            ]

        # Add folder
        if folder_id:
            data["folderId"] = folder_id

        # Note: Labels require integer IDs, not text strings
        # The API expects: "labels": [123, 456] not ["label1", "label2"]
        # For now, we skip sending labels since lookup isn't implemented
        # if labels:
        #     data["labels"] = labels  # Would need label ID lookup

        # Add custom fields
        if custom_fields:
            cf_array = []
            for name, value in custom_fields.items():
                field_id = self.get_field_id(name)
                if field_id:
                    # Convert option values to IDs for dropdown/multi-select fields
                    option_ids = self.get_option_ids(name, value)
                    cf_array.append({"id": field_id, "value": option_ids})
            if cf_array:
                data["customFields"] = cf_array

        return self._make_request(
            "POST",
            "/testcases",
            data=data
        )

    def find_existing_tc(self, summary: str, folder_id: str) -> Optional[Dict[str, Any]]:
        """Find an existing test case with the same summary in the target folder.

        Returns dict with 'id', 'key', and 'versionNo' if found, None otherwise.
        """
        # Search for TCs with matching summary AND folder
        # Request version info in the fields
        result = self._make_request(
            "POST",
            "/testcases/search",
            data={
                "filter": {
                    "projectId": str(self.project),
                    "summary": summary,
                    "folderId": folder_id
                }
            }
        )

        if result.success and result.data:
            # Response format: {"total": N, "data": [{"id": "xxx", "key": "PROJ-TC-123", "version": {"versionNo": 1}, ...}, ...]}
            data = result.data.get('data', []) if isinstance(result.data, dict) else []
            if data and len(data) > 0:
                tc = data[0]
                # Extract version number from nested version object
                version_info = tc.get('version', {})
                version_no = version_info.get('versionNo', 1) if isinstance(version_info, dict) else 1
                return {
                    'id': tc.get('id'),
                    'key': tc.get('key'),
                    'versionNo': version_no
                }

        return None

    def delete_test_steps(self, tc_id: str, version_no: int) -> 'APIResponse':
        """Delete all test steps from a test case version.

        Uses DELETE /testcases/{id}/versions/{no}/teststeps endpoint with deleteAll flag.
        """
        return self._make_request(
            "DELETE",
            f"/testcases/{tc_id}/versions/{version_no}/teststeps",
            data={"deleteAll": True}
        )

    def create_test_steps(
        self,
        tc_id: str,
        version_no: int,
        steps: List[str],
        test_data: str = "",
        expected_result: str = ""
    ) -> 'APIResponse':
        """Create test steps for a test case version.

        Uses POST /testcases/{id}/versions/{no}/teststeps endpoint.
        """
        step_data = [
            {
                "stepDetails": "\n".join(steps),
                "testData": test_data,
                "expectedResult": expected_result
            }
        ]
        return self._make_request(
            "POST",
            f"/testcases/{tc_id}/versions/{version_no}/teststeps",
            data=step_data
        )

    def update_test_case(
        self,
        tc_id: str,
        version_no: int,
        summary: str,
        description: str = "",
        precondition: str = "",
        steps: List[str] = None,
        test_data: str = "",
        expected_result: str = "",
        folder_id: str = "",
        labels: List[str] = None,
        custom_fields: Dict[str, str] = None
    ) -> 'APIResponse':
        """Update an existing test case including steps.

        Uses PUT /testcases/{id}/versions/{no} endpoint for metadata,
        and DELETE + POST /testcases/{id}/versions/{no}/teststeps for steps.
        """
        # First update metadata
        data = {
            "summary": summary
        }

        if description:
            data["description"] = description
        if precondition:
            data["precondition"] = precondition

        # Add custom fields
        if custom_fields:
            cf_array = []
            for name, value in custom_fields.items():
                field_id = self.get_field_id(name)
                if field_id:
                    option_ids = self.get_option_ids(name, value)
                    cf_array.append({"id": field_id, "value": option_ids})
            if cf_array:
                data["customFields"] = cf_array

        result = self._make_request(
            "PUT",
            f"/testcases/{tc_id}/versions/{version_no}",
            data=data
        )

        # If metadata update failed, return the error
        if not result.success:
            return result

        # Now update steps: delete existing and create new
        if steps:
            # Delete existing steps
            self.delete_test_steps(tc_id, version_no)
            # Create new steps
            step_result = self.create_test_steps(
                tc_id, version_no, steps, test_data, expected_result
            )
            # If step creation failed, report it but don't fail the whole update
            if not step_result.success:
                return APIResponse(
                    success=True,
                    data=result.data,
                    status_code=result.status_code,
                    error=f"TC updated but steps failed: {step_result.error}"
                )

        return result

