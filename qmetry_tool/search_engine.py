"""
Search Engine for QMetry CLI Tool

Core logic for searching and retrieving test cases:
- QueryEngine:      Orchestrates search workflow
- FilterBuilder:    Converts friendly params → API filter payload
- ClientSideFilter: Post-retrieval text filtering
- Paginator:        Handles multi-page API results
"""

from typing import Any, Dict, List, Optional

from .field_schema import FieldSchemaCache
from .tc_cache import TCSearchCache


# Standard fields to request by default
DEFAULT_FIELDS = [
    "summary", "description", "precondition", "priority", "status",
    "assignee", "reporter", "estimatedTime", "isAutomated",
    "labels", "components", "fixVersions", "sprint", "folder",
    "created", "updated", "executed",
]


class ClientSideFilter:
    """Filter test cases by text across summary, description, precondition."""

    @staticmethod
    def apply(test_cases: List[Dict], text: str) -> List[Dict]:
        if not text:
            return test_cases
        text_lower = text.lower()
        return [
            tc for tc in test_cases
            if text_lower in (tc.get("summary") or "").lower()
            or text_lower in (tc.get("description") or "").lower()
            or text_lower in (tc.get("precondition") or "").lower()
        ]


class FilterBuilder:
    """Build API filter payload from user-friendly parameters."""

    def __init__(self, schema: FieldSchemaCache, project_id: int):
        self._schema = schema
        self._project_id = project_id

    def build(
        self,
        folder_id: Optional[int] = None,
        key: Optional[str] = None,
        custom_filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build the filter dict for POST /testcases/search.

        Args:
            folder_id: Filter by folder
            key: Filter by TC key (exact match)
            custom_filters: Friendly-name → value pairs for custom field filters

        Returns:
            Filter dict ready for API request body
        """
        f: Dict[str, Any] = {"projectId": self._project_id}

        if folder_id is not None:
            f["folderId"] = folder_id
        if key:
            f["key"] = key

        # Note: The QMetry search API doesn't support custom field filtering
        # in the filter body. Custom field filtering is done client-side.
        return f


class Paginator:
    """Handle paginated API results transparently."""

    def __init__(self, client: Any, page_size: int = 50):
        self._client = client
        self._page_size = page_size

    def search_all(
        self,
        filters: Dict[str, Any],
        fields: List[str],
        max_results: int = 500,
    ) -> Dict[str, Any]:
        """
        Fetch all matching test cases across pages.

        Returns:
            {"total": int, "data": [list of all TCs]}
        """
        all_results: List[Dict] = []
        start_at = 0

        while len(all_results) < max_results:
            page_size = min(self._page_size, max_results - len(all_results))
            result = self._client.search_test_cases(
                filters=filters,
                fields=fields,
                start_at=start_at,
                max_results=page_size,
            )

            if not result.success:
                return {"total": 0, "data": [], "error": result.error}

            data = result.data if isinstance(result.data, dict) else {}
            page_items = data.get("data", [])
            total = data.get("total", 0)

            all_results.extend(page_items)

            # Stop if we've got everything or this was the last page
            if len(page_items) < page_size or len(all_results) >= total:
                break

            start_at += len(page_items)

        return {"total": len(all_results), "data": all_results}


class QueryEngine:
    """
    Orchestrates the search workflow.

    Ties together FilterBuilder, Paginator, ClientSideFilter,
    and FieldSchemaCache to provide a unified search interface.
    """

    def __init__(self, client: Any, schema: FieldSchemaCache, project_id: int):
        self._client = client
        self._schema = schema
        self._project_id = project_id
        self._filter_builder = FilterBuilder(schema, project_id)
        self._paginator = Paginator(client)
        self._cache = TCSearchCache()

    def _build_fields_list(self, include_custom: bool = True) -> List[str]:
        """Build the list of fields to request."""
        fields = list(DEFAULT_FIELDS)
        if include_custom:
            fields.extend(self._schema.get_all_field_ids())
        return fields

    def get_by_key(self, key: str, include_steps: bool = True) -> Dict[str, Any]:
        """
        Retrieve a single test case by key with full detail.

        Returns:
            {"tc": dict, "steps": list | None, "error": str | None}
        """
        fields = self._build_fields_list()
        result = self._client.get_test_case_by_key(key, fields=fields)

        if not result.success:
            return {"tc": None, "steps": None, "error": result.error}

        tc = result.data
        steps = None

        if include_steps:
            tc_id = tc.get("id", "")
            version_no = 1
            version_info = tc.get("version", {})
            if isinstance(version_info, dict):
                version_no = version_info.get("versionNo", 1)

            steps_result = self._client.get_test_steps(tc_id, version_no)
            if steps_result.success and isinstance(steps_result.data, dict):
                steps = steps_result.data.get("data", [])

        return {"tc": tc, "steps": steps, "error": None}

    def search(
        self,
        folder_id: Optional[int] = None,
        text: Optional[str] = None,
        app: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50,
        refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Search test cases with optional filters and text search.

        Args:
            folder_id: Filter by folder
            text: Client-side text search across summary/description/precondition
            app: Filter by App custom field (client-side)
            platform: Filter by Platform custom field (client-side)
            limit: Maximum results to return
            refresh: Force refresh the cache, ignoring TTL

        Returns:
            {"total": int, "data": list, "error": str | None, "cache_hit": bool}
        """
        needs_client_filter = bool(text or app or platform)

        # --- Try cache for broad project scans with client-side filtering ---
        cache_hit = False
        if needs_client_filter and not folder_id:
            if not refresh and self._cache.is_valid():
                cached = self._cache.load()
                if cached is not None:
                    results = cached
                    cache_hit = True

        if not cache_hit:
            filters = self._filter_builder.build(folder_id=folder_id)
            fields = self._build_fields_list()

            # Fetch from API (paginate if needed for client-side filtering)
            fetch_limit = limit if not needs_client_filter else 5000
            raw = self._paginator.search_all(filters, fields, max_results=fetch_limit)

            if raw.get("error"):
                return raw

            results = raw["data"]

            # Save to cache if this was a broad project scan
            if needs_client_filter and not folder_id:
                self._cache.save(results)

        # Apply client-side text filter
        if text:
            results = ClientSideFilter.apply(results, text)

        # Apply client-side custom field filters
        if app:
            results = self._filter_by_custom_field(results, "apps", app)
        if platform:
            results = self._filter_by_custom_field(results, "platform", platform)

        # Trim to requested limit
        results = results[:limit]

        return {
            "total": len(results),
            "data": results,
            "error": None,
            "cache_hit": cache_hit,
        }

    def list_in_folder(
        self,
        folder_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List test cases in a specific folder."""
        filters = self._filter_builder.build(folder_id=folder_id)
        fields = self._build_fields_list(include_custom=False)
        return self._paginator.search_all(filters, fields, max_results=limit)

    @staticmethod
    def _filter_by_custom_field(
        test_cases: List[Dict], field_name_lower: str, value: str
    ) -> List[Dict]:
        """Filter TCs where a custom field contains the given value."""
        value_lower = value.lower()
        matched = []
        for tc in test_cases:
            cf = tc.get("customFields", {})
            for _fid, fdata in cf.items():
                if fdata.get("name", "").lower() == field_name_lower:
                    raw = fdata.get("value", "")
                    if isinstance(raw, list):
                        names = [
                            item.get("name", "").lower()
                            if isinstance(item, dict) else str(item).lower()
                            for item in raw
                        ]
                        if value_lower in names:
                            matched.append(tc)
                            break
                    elif value_lower in str(raw).lower():
                        matched.append(tc)
                        break
        return matched

