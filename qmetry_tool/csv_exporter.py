"""
CSV Exporter Module for QMetry CLI Tool

Converts parsed Gherkin feature files to QMetry-compatible CSV format.
Outputs 32 columns matching the QMetry import template.
"""

import csv
from pathlib import Path
from typing import List, Optional
from .gherkin_parser import FeatureFile, TestCase


# CSV Header - 32 columns in exact order for QMetry import
CSV_HEADERS = [
    'Issue Key',           # 1 - Empty for new TCs
    'Summary',             # 2 - Scenario name
    'Description',         # 3 - Feature description
    'Precondition',        # 4 - Background steps
    'Status',              # 5 - TO DO
    'Priority',            # 6 - Medium (default)
    'Assignee',            # 7 - Empty
    'Reporter',            # 8 - Empty
    'Estimated Time',      # 9 - Empty
    'Labels',              # 10 - Tags (non-override)
    'Components',          # 11 - Empty
    'Sprint',              # 12 - Empty
    'Fix Versions',        # 13 - Empty
    'Step Summary',        # 14 - Scenario steps
    'Test Data',           # 15 - @Test_Data block
    'Expected Result',     # 16 - @Expected_Result block
    'Folders',             # 17 - Empty or @Folder override
    'Story Linkages',      # 18 - Empty
    'Apps',                # 19 - Custom field
    'Component/Feature',   # 20 - Custom field
    'CT Update Target',    # 21 - Custom field
    'Evidence Type',       # 22 - Custom field
    'Live Proposition',    # 23 - Custom field
    'Platform',            # 24 - Custom field
    'Regression Type',     # 25 - Custom field
    'Users Applied',       # 26 - Custom field
    'Automatable?',        # 27 - Custom field
    'Automated Proposition', # 28 - Custom field
    'HighVisibility',      # 29 - Custom field
    'IsAds?',              # 30 - Custom field
    'NBA Feature',         # 31 - Custom field
    'TC requires use of proxy',  # 32 - Custom field
]


def export_to_csv(feature: FeatureFile, output_path: Optional[str] = None) -> str:
    """
    Export a parsed feature file to QMetry CSV format.
    
    Args:
        feature: Parsed FeatureFile object
        output_path: Optional output path. If None, uses feature filename with _Export.csv
    
    Returns:
        Path to the generated CSV file
    """
    if output_path is None:
        # Generate output path from input file
        input_path = Path(feature.file_path)
        output_path = str(input_path.parent / f"{input_path.stem}_Export.csv")
    
    rows = []
    
    # Build precondition from background steps
    precondition = '\n'.join(feature.background_steps)
    
    # Build description from feature description
    description = feature.feature_description
    
    for test_case in feature.test_cases:
        row = _build_csv_row(feature, test_case, precondition, description)
        rows.append(row)
    
    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)
    
    return output_path


def _build_csv_row(feature: FeatureFile, tc: TestCase, precondition: str, description: str) -> List[str]:
    """Build a single CSV row for a test case."""
    
    # Merge defaults with overrides (overrides win)
    merged = {**feature.defaults}
    for key, value in tc.overrides.items():
        merged[key] = value
    
    # Helper to get field value with underscore/space normalization
    def get_field(name: str, default: str = '') -> str:
        # Try exact match first
        if name in merged:
            return merged[name]
        # Try with underscores (as stored from parser)
        underscore_name = name.replace(' ', '_')
        if underscore_name in merged:
            return merged[underscore_name]
        # Try with spaces
        space_name = name.replace('_', ' ')
        if space_name in merged:
            return merged[space_name]
        return default
    
    # Build labels string (space-separated)
    labels = ' '.join(tc.labels)
    
    # Build steps string
    steps = '\n'.join(tc.steps)
    
    # Build the row (32 columns)
    row = [
        '',                                          # 1 - Issue Key (empty for new)
        tc.name,                                     # 2 - Summary
        description,                                 # 3 - Description
        precondition,                                # 4 - Precondition
        get_field('Status', 'TO DO'),               # 5 - Status
        get_field('Priority', 'Medium'),            # 6 - Priority
        '',                                          # 7 - Assignee
        '',                                          # 8 - Reporter
        '',                                          # 9 - Estimated Time
        labels,                                      # 10 - Labels
        '',                                          # 11 - Components
        '',                                          # 12 - Sprint
        '',                                          # 13 - Fix Versions
        steps,                                       # 14 - Step Summary
        tc.test_data,                                # 15 - Test Data
        tc.expected_result,                          # 16 - Expected Result
        get_field('Folder', ''),                    # 17 - Folders
        '',                                          # 18 - Story Linkages
        get_field('Apps', ''),                      # 19 - Apps
        get_field('Component/Feature', ''),         # 20 - Component/Feature
        get_field('CT Update Target', ''),          # 21 - CT Update Target
        get_field('Evidence Type', ''),             # 22 - Evidence Type
        get_field('Live Proposition', ''),          # 23 - Live Proposition
        get_field('Platform', ''),                  # 24 - Platform
        get_field('Regression Type', ''),           # 25 - Regression Type
        get_field('Users Applied', ''),             # 26 - Users Applied
        get_field('Automatable?', ''),              # 27 - Automatable?
        get_field('Automated Proposition', ''),     # 28 - Automated Proposition
        get_field('HighVisibility', ''),            # 29 - HighVisibility
        get_field('IsAds?', ''),                    # 30 - IsAds?
        get_field('NBA Feature', ''),               # 31 - NBA Feature
        get_field('TC requires use of proxy', ''),  # 32 - TC requires use of proxy
    ]
    
    return row


def export_multiple_to_csv(features: List[FeatureFile], output_path: str) -> str:
    """Export multiple feature files to a single CSV."""
    all_rows = []
    
    for feature in features:
        precondition = '\n'.join(feature.background_steps)
        description = feature.feature_description
        
        for test_case in feature.test_cases:
            row = _build_csv_row(feature, test_case, precondition, description)
            all_rows.append(row)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(all_rows)
    
    return output_path

