"""
Output Formatters for QMetry CLI Tool

Formats search/retrieval results for terminal display:
- TableFormatter:  Summary table for search/list results
- DetailFormatter: Full detail view for single TC lookups
- JSONFormatter:   Raw JSON dump
"""

import json
from typing import Any, Dict, List, Optional


def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _safe_get(obj: Any, *keys, default: str = "") -> str:
    """Safely navigate nested dicts."""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
    return str(current) if current is not None else default


def _extract_custom_field_summary(tc: Dict) -> str:
    """Extract key custom fields for table display."""
    cf = tc.get("customFields", {})
    if not cf:
        return ""
    parts = []
    for _fid, fdata in cf.items():
        raw = fdata.get("value", "")
        if isinstance(raw, list):
            vals = [item.get("name", "") if isinstance(item, dict) else str(item) for item in raw]
            parts.append(", ".join(vals))
        elif raw:
            parts.append(str(raw))
    return " | ".join(parts[:3])  # Max 3 fields in table


class TableFormatter:
    """Format search results as a terminal table."""

    @staticmethod
    def format(test_cases: List[Dict], total: int = 0, start_at: int = 0) -> str:
        if not test_cases:
            return "No test cases found."

        # Column definitions: (header, width, extractor)
        columns = [
            ("Key", 16, lambda tc: tc.get("key", "")),
            ("Summary", 45, lambda tc: _truncate(tc.get("summary", ""), 45)),
            ("Status", 10, lambda tc: _safe_get(tc, "status", "name", default="—")),
        ]

        # Build header
        header = " | ".join(h.ljust(w) for h, w, _ in columns)
        sep = "-+-".join("-" * w for _, w, _ in columns)

        lines = [header, sep]
        for tc in test_cases:
            row = " | ".join(ext(tc).ljust(w) for _, w, ext in columns)
            lines.append(row)

        shown = len(test_cases)
        if total:
            lines.append(f"\nShowing {start_at + 1}-{start_at + shown} of {total} test cases")
        else:
            lines.append(f"\n{shown} test case(s)")

        return "\n".join(lines)


class DetailFormatter:
    """Format a single test case with full detail."""

    @staticmethod
    def format(
        tc: Dict,
        steps: Optional[List[Dict]] = None,
        custom_field_display: Optional[List[Dict]] = None,
    ) -> str:
        lines = []
        key = tc.get("key", "")
        summary = tc.get("summary", "")
        lines.append(f"{'─' * 60}")
        lines.append(f"  {key} — {summary}")
        lines.append(f"{'─' * 60}")

        # Standard fields
        field_rows = [
            ("Description", tc.get("description", "") or "—"),
            ("Precondition", tc.get("precondition", "") or "—"),
            ("Status", _safe_get(tc, "status", "name", default="—")),
            ("Priority", _safe_get(tc, "priority", "name", default="—")),
            ("Automated", str(tc.get("isAutomated", False))),
            ("Assignee", tc.get("assignee", "") or "—"),
            ("Reporter", tc.get("reporter", "") or "—"),
            ("Created", _safe_get(tc, "created", "createdOn", default="—")),
            ("Updated", _safe_get(tc, "updated", "updatedOn", default="—")),
            ("Version", _safe_get(tc, "version", "versionNo", default="—")),
        ]
        for label, value in field_rows:
            # Indent multiline values
            value_lines = str(value).split("\n")
            lines.append(f"  {label + ':':<16} {value_lines[0]}")
            for vl in value_lines[1:]:
                lines.append(f"  {'':16} {vl}")

        # Custom fields
        if custom_field_display:
            lines.append(f"\n  {'Custom Fields':}")
            lines.append(f"  {'─' * 40}")
            for cf in custom_field_display:
                lines.append(f"  {cf['name'] + ':':<24} {cf['value']}")

        # Test steps
        if steps:
            lines.append(f"\n  Test Steps ({len(steps)})")
            lines.append(f"  {'─' * 40}")
            for step in steps:
                seq = step.get("seqNo", "?")
                details = step.get("stepDetails", "")
                test_data = step.get("testData", "")
                expected = step.get("expectedResult", "")

                lines.append(f"  Step {seq}:")
                for dl in details.split("\n"):
                    lines.append(f"    {dl}")
                if test_data:
                    lines.append(f"    Test Data: {test_data}")
                if expected:
                    lines.append(f"    Expected:  {expected}")

        lines.append(f"{'─' * 60}")
        return "\n".join(lines)


class JSONFormatter:
    """Format results as pretty-printed JSON."""

    @staticmethod
    def format(data: Any) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)

