"""
QMetry CLI Tool

A command-line tool for managing Gherkin feature files and pushing test cases to QMetry.

Commands:
    export   - Export feature file to CSV format
    push     - Push test cases to QMetry via API
    folders  - List available folders in QMetry
    validate - Validate feature file syntax
    search   - Search test cases by text/field filters
    cache    - Manage the local TC search cache
    config   - Create config template
"""

from .gherkin_parser import parse_feature_file, FeatureFile, TestCase
from .csv_exporter import export_to_csv, export_multiple_to_csv
from .config_handler import load_config, QMetryConfig, create_config_template
from .qmetry_api_client import QMetryClient
from .search_engine import QueryEngine
from .tc_cache import TCSearchCache
from .field_schema import FieldSchemaCache

__version__ = "1.0.0"

__all__ = [
    'parse_feature_file',
    'FeatureFile',
    'TestCase',
    'export_to_csv',
    'export_multiple_to_csv',
    'load_config',
    'QMetryConfig',
    'create_config_template',
    'QMetryClient',
    'QueryEngine',
    'TCSearchCache',
    'FieldSchemaCache',
]

