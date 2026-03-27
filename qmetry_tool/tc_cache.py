"""
Test Case Search Cache for QMetry CLI Tool

Caches TC summaries, descriptions, and preconditions locally in JSON
to avoid repeated full-project API scans (~94 calls per search).

Features:
- 30-minute TTL (configurable)
- Force-refresh via --refresh flag
- Stored alongside .qmetry_config.yaml as .qmetry_tc_cache.json
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_handler import find_config_file

TC_CACHE_FILE = ".qmetry_tc_cache.json"
DEFAULT_TTL_SECONDS = 30 * 60  # 30 minutes


class TCSearchCache:
    """Local disk cache for test case search data."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._cache_path = self._resolve_cache_path()

    @staticmethod
    def _resolve_cache_path() -> Path:
        """Cache file lives next to .qmetry_config.yaml."""
        config_file = find_config_file()
        parent = config_file.parent if config_file else Path.cwd()
        return parent / TC_CACHE_FILE

    def is_valid(self) -> bool:
        """Return True if cache exists and hasn't expired."""
        if not self._cache_path.exists():
            return False
        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            created_at = meta.get("created_at", 0)
            return (time.time() - created_at) < self._ttl
        except (json.JSONDecodeError, OSError, KeyError):
            return False

    def load(self) -> Optional[List[Dict[str, Any]]]:
        """Load cached TCs. Returns None if cache is missing or corrupt."""
        if not self._cache_path.exists():
            return None
        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("test_cases", None)
        except (json.JSONDecodeError, OSError):
            return None

    def save(self, test_cases: List[Dict[str, Any]]) -> None:
        """Write TCs to cache with current timestamp."""
        # Keep only search-relevant fields to minimise file size
        slim = []
        for tc in test_cases:
            slim.append({
                "key": tc.get("key", ""),
                "id": tc.get("id", ""),
                "summary": tc.get("summary", ""),
                "description": tc.get("description", ""),
                "precondition": tc.get("precondition", ""),
                "status": tc.get("status"),
                "priority": tc.get("priority"),
                "customFields": tc.get("customFields"),
            })

        payload = {
            "created_at": time.time(),
            "total": len(slim),
            "test_cases": slim,
        }

        with open(self._cache_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, separators=(",", ":"))

    def clear(self) -> bool:
        """Delete the cache file. Returns True if deleted."""
        if self._cache_path.exists():
            self._cache_path.unlink()
            return True
        return False

    def info(self) -> Dict[str, Any]:
        """Return cache metadata (exists, age, TC count, size)."""
        if not self._cache_path.exists():
            return {"exists": False}

        try:
            stat = self._cache_path.stat()
            with open(self._cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            created_at = data.get("created_at", 0)
            age_seconds = time.time() - created_at
            return {
                "exists": True,
                "path": str(self._cache_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "total_tcs": data.get("total", 0),
                "age_seconds": round(age_seconds, 1),
                "age_minutes": round(age_seconds / 60, 1),
                "valid": age_seconds < self._ttl,
                "ttl_minutes": self._ttl / 60,
            }
        except (json.JSONDecodeError, OSError):
            return {"exists": True, "valid": False, "corrupt": True}

