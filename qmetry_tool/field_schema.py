"""
Field Schema Cache for QMetry CLI Tool

Caches and maps custom field definitions:
- Friendly name → qcf_ ID  (e.g. "Apps" → "qcf_1109995")
- qcf_ ID → friendly name  (for display)
- Option name → option ID   (e.g. "Peacock" → 4748571)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FieldOption:
    """A single option value for a dropdown/multi-select field."""
    id: int
    value: str


@dataclass
class FieldDefinition:
    """A custom field definition from QMetry."""
    id: str           # e.g. "qcf_1109995"
    name: str         # e.g. "Apps"
    field_type: int   # QMetry field type code
    options: List[FieldOption] = field(default_factory=list)


class FieldSchemaCache:
    """
    Caches custom field schema for name↔ID lookups.

    Lazy-loaded on first access. Uses QMetryClient.get_custom_field_schema().
    """

    def __init__(self, client: Any):
        self._client = client
        self._fields: Dict[str, FieldDefinition] = {}  # keyed by qcf_ ID
        self._name_to_id: Dict[str, str] = {}          # lowercase name → qcf_ ID
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load schema from API if not already cached."""
        if self._loaded:
            return

        result = self._client.get_custom_field_schema()
        if not result.success:
            self._loaded = True  # Don't retry on failure
            return

        raw_fields = result.data if isinstance(result.data, list) else []

        for f in raw_fields:
            field_id = f.get("id", "")
            field_name = f.get("name", "")
            field_type = f.get("fieldType", 0)
            if not field_id or not field_name:
                continue

            raw_options = f.get("options") or []
            options = [
                FieldOption(id=opt.get("id", 0), value=opt.get("value", ""))
                for opt in raw_options
                if opt.get("id") and opt.get("value")
            ]

            defn = FieldDefinition(
                id=field_id,
                name=field_name,
                field_type=field_type,
                options=options,
            )
            self._fields[field_id] = defn
            self._name_to_id[field_name.lower()] = field_id

        self._loaded = True

    # --- Public API ---

    def get_all_field_ids(self) -> List[str]:
        """Return all qcf_ IDs for use in API ?fields= param."""
        self._ensure_loaded()
        return list(self._fields.keys())

    def get_field_id(self, friendly_name: str) -> Optional[str]:
        """Map a friendly name to its qcf_ ID (case-insensitive)."""
        self._ensure_loaded()
        return self._name_to_id.get(friendly_name.lower())

    def get_friendly_name(self, field_id: str) -> str:
        """Map a qcf_ ID to its friendly name. Returns the ID if unknown."""
        self._ensure_loaded()
        defn = self._fields.get(field_id)
        return defn.name if defn else field_id

    def get_option_id(self, field_id: str, option_name: str) -> Optional[int]:
        """Get the option ID for a dropdown/multi-select value."""
        self._ensure_loaded()
        defn = self._fields.get(field_id)
        if not defn:
            return None
        name_lower = option_name.lower()
        for opt in defn.options:
            if opt.value.lower() == name_lower:
                return opt.id
        return None

    def get_option_values(self, field_id: str) -> List[str]:
        """Return all valid option values for a field (for validation)."""
        self._ensure_loaded()
        defn = self._fields.get(field_id)
        if not defn:
            return []
        return [opt.value for opt in defn.options]

    def resolve_custom_field_display(
        self, custom_fields: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Convert API customFields response to display-friendly list.

        Input (from API):
            {"qcf_1109995": {"name": "Apps", "value": [{"name": "Peacock", ...}], ...}}

        Output:
            [{"name": "Apps", "value": "Peacock, SkyShowtime"}]
        """
        self._ensure_loaded()
        result = []
        for field_id, field_data in custom_fields.items():
            name = field_data.get("name", self.get_friendly_name(field_id))
            raw_value = field_data.get("value", "")

            # Value can be a list of objects or a plain string
            if isinstance(raw_value, list):
                display = ", ".join(
                    item.get("name", str(item)) if isinstance(item, dict) else str(item)
                    for item in raw_value
                )
            else:
                display = str(raw_value)

            result.append({"name": name, "value": display})

        return sorted(result, key=lambda x: x["name"])

