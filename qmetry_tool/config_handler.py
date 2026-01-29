"""
Config Handler Module for QMetry CLI Tool

Handles loading and managing .qmetry_config.yaml configuration.
Also manages caching of custom field IDs and folder structures.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class QMetryConfig:
    """QMetry configuration settings."""
    api_key: str = ""
    project: str = ""
    default_folder: str = "/Uncategorized"
    ssl_verify: bool = True  # Set to False to bypass SSL verification
    custom_fields: Dict[str, str] = field(default_factory=dict)
    # Cached data (loaded from .qmetry_cache.yaml)
    folder_cache: Dict[str, int] = field(default_factory=dict)
    field_id_cache: Dict[str, str] = field(default_factory=dict)
    # Cache for custom field options: {field_name: {option_value: option_id}}
    field_options_cache: Dict[str, Dict[str, int]] = field(default_factory=dict)


# Default config file locations
CONFIG_FILE = ".qmetry_config.yaml"
CACHE_FILE = ".qmetry_cache.yaml"


def find_config_file() -> Optional[Path]:
    """Find the config file, searching up the directory tree."""
    current = Path.cwd()
    
    while current != current.parent:
        config_path = current / CONFIG_FILE
        if config_path.exists():
            return config_path
        current = current.parent
    
    # Also check home directory
    home_config = Path.home() / CONFIG_FILE
    if home_config.exists():
        return home_config
    
    return None


def load_config(config_path: Optional[str] = None) -> QMetryConfig:
    """
    Load QMetry configuration from YAML file.
    
    Args:
        config_path: Optional explicit path to config file
    
    Returns:
        QMetryConfig object
    
    Raises:
        FileNotFoundError: If no config file is found
        ValueError: If YAML parsing fails or required fields are missing
    """
    if yaml is None:
        raise ImportError("PyYAML is required. Install with: pip install pyyaml")
    
    # Find config file
    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()
    
    if path is None or not path.exists():
        raise FileNotFoundError(
            f"Config file not found. Create {CONFIG_FILE} with your settings.\n"
            f"See .qmetry_config.yaml.template for an example."
        )
    
    # Load YAML
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    config = QMetryConfig(
        api_key=data.get('QMETRY_API_KEY', ''),
        project=data.get('QMETRY_PROJECT', ''),
        default_folder=data.get('QMETRY_DEFAULT_FOLDER', '/Uncategorized'),
        ssl_verify=data.get('QMETRY_SSL_VERIFY', True),
        custom_fields=data.get('CUSTOM_FIELDS', {}),
    )
    
    # Load cache if exists
    cache_path = path.parent / CACHE_FILE
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = yaml.safe_load(f) or {}
            config.folder_cache = cache_data.get('folders', {})
            config.field_id_cache = cache_data.get('field_ids', {})
            config.field_options_cache = cache_data.get('field_options', {})
        except Exception:
            pass  # Cache is optional, ignore errors

    return config


def save_cache(config: QMetryConfig, config_path: Optional[str] = None) -> None:
    """Save cache data (folder IDs, field IDs) to .qmetry_cache.yaml."""
    if yaml is None:
        return
    
    # Find config file location to store cache alongside it
    if config_path:
        path = Path(config_path).parent
    else:
        found = find_config_file()
        path = found.parent if found else Path.cwd()
    
    cache_path = path / CACHE_FILE
    cache_data = {
        'folders': config.folder_cache,
        'field_ids': config.field_id_cache,
        'field_options': config.field_options_cache,
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        yaml.dump(cache_data, f, default_flow_style=False)


def validate_config(config: QMetryConfig, require_api: bool = False) -> list:
    """
    Validate configuration and return list of issues.
    
    Args:
        config: QMetryConfig to validate
        require_api: If True, API key and project are required
    
    Returns:
        List of validation error messages (empty if valid)
    """
    issues = []
    
    if require_api:
        if not config.api_key:
            issues.append("QMETRY_API_KEY is required for API operations")
        if not config.project:
            issues.append("QMETRY_PROJECT is required")
    
    return issues


def create_config_template(output_path: Optional[str] = None) -> str:
    """Create a template config file."""
    template = '''# QMetry Configuration File
# Copy this to .qmetry_config.yaml and fill in your values
# This file should be gitignored (contains personal API key)

# Your personal QMetry API key
# Generate at: QMetry > Configuration > Open API
QMETRY_API_KEY: "your-api-key-here"

# Your Jira project key (e.g., MOB, ATV, ROKU)
QMETRY_PROJECT: "MOB"

# Default folder for test cases (optional)
QMETRY_DEFAULT_FOLDER: "/Uncategorized"

# Custom field mapping (optional - auto-discovered if not specified)
# Format: FieldName: "qcf_xxxxx"
# CUSTOM_FIELDS:
#   Apps: "qcf_12345"
#   Platform: "qcf_12346"
'''
    
    if output_path is None:
        output_path = ".qmetry_config.yaml.template"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    return output_path

