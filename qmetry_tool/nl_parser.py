"""
Natural Language Parser for QMetry CLI Tool

Pattern-based entity extraction from natural language search queries.
No LLM dependency - uses regex patterns to identify search entities.

Examples:
    "find Peacock iOS test cases" → app=Peacock, platform=iOS
    "show login TCs requiring proxy" → text=login, proxy=Yes
    "Peacock and SkyShowtime Android TCs" → app=[Peacock, SkyShowtime], platform=Android
"""

import re
from typing import Dict, List, Optional


# Known entity values (case-insensitive matching)
KNOWN_APPS = [
    "Peacock", "SkyShowtime", "Showmax", "NOW-GB", "NOW",
]

KNOWN_PLATFORMS = [
    "iOS", "Android",
]

# Regex patterns for extracting entities
# Order matters: more specific patterns first
PATTERNS = {
    "app": [
        # "for Peacock" / "for Peacock and SkyShowtime"
        re.compile(
            r"(?:for|on)\s+("
            + "|".join(re.escape(a) for a in KNOWN_APPS)
            + r")(?:\s+(?:and|,)\s+("
            + "|".join(re.escape(a) for a in KNOWN_APPS)
            + r"))*",
            re.IGNORECASE,
        ),
        # Bare app name
        re.compile(
            r"\b(" + "|".join(re.escape(a) for a in KNOWN_APPS) + r")\b",
            re.IGNORECASE,
        ),
    ],
    "platform": [
        re.compile(
            r"\b(" + "|".join(re.escape(p) for p in KNOWN_PLATFORMS) + r")\b",
            re.IGNORECASE,
        ),
    ],
    "proxy": [
        re.compile(r"(?:with|requiring|requires?|needs?|using)\s+proxy", re.IGNORECASE),
        re.compile(r"proxy\s*(?:=\s*|:\s*)?(yes|true)", re.IGNORECASE),
    ],
}

# Words to strip when extracting leftover text
STOP_WORDS = {
    "find", "show", "get", "list", "search", "display", "retrieve",
    "all", "the", "me", "my", "test", "cases", "tcs", "tc",
    "in", "on", "for", "with", "and", "that", "are", "have",
    "a", "an", "of",
}


class NLParser:
    """Parse natural language queries into structured search parameters."""

    @staticmethod
    def parse(query: str) -> Dict[str, Optional[str]]:
        """
        Extract search entities from a natural language query.

        Returns:
            Dict with keys: app, platform, proxy, text
            Values are None if not found.
        """
        result: Dict[str, Optional[str]] = {
            "app": None,
            "platform": None,
            "proxy": None,
            "text": None,
        }

        remaining = query

        # Extract apps
        apps_found: List[str] = []
        for pattern in PATTERNS["app"]:
            for match in pattern.finditer(query):
                for group_val in match.groups():
                    if group_val:
                        # Normalize to canonical case
                        canonical = _normalize_app(group_val)
                        if canonical and canonical not in apps_found:
                            apps_found.append(canonical)
                remaining = remaining[:match.start()] + remaining[match.end():]

        if apps_found:
            result["app"] = apps_found[0]  # Primary app for filtering

        # Extract platform
        for pattern in PATTERNS["platform"]:
            match = pattern.search(remaining)
            if match:
                result["platform"] = _normalize_platform(match.group(1))
                remaining = remaining[:match.start()] + remaining[match.end():]
                break

        # Extract proxy
        for pattern in PATTERNS["proxy"]:
            match = pattern.search(remaining)
            if match:
                result["proxy"] = "Yes"
                remaining = remaining[:match.start()] + remaining[match.end():]
                break

        # Remaining text after stripping stop words = text search
        leftover = remaining.strip()
        words = [w for w in leftover.split() if w.lower() not in STOP_WORDS]
        leftover_clean = " ".join(words).strip()
        if leftover_clean:
            result["text"] = leftover_clean

        return result


def _normalize_app(value: str) -> Optional[str]:
    """Normalize an app name to its canonical form."""
    val_lower = value.lower()
    for app in KNOWN_APPS:
        if app.lower() == val_lower:
            return app
    return None


def _normalize_platform(value: str) -> Optional[str]:
    """Normalize a platform name to its canonical form."""
    val_lower = value.lower()
    for plat in KNOWN_PLATFORMS:
        if plat.lower() == val_lower:
            return plat
    return None

