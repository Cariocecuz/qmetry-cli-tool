"""
Gherkin Parser Module for QMetry CLI Tool

Parses feature files with the custom structure:
- @Feature_Defaults: block
- Background: section
- Scenarios with @Test_Data: and @Expected_Result: blocks
- Inline tag overrides like @Platform:iOS
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class TestCase:
    """Represents a single test case (scenario) from a feature file."""
    name: str
    steps: List[str] = field(default_factory=list)
    test_data: str = ""
    expected_result: str = ""
    labels: List[str] = field(default_factory=list)
    overrides: Dict[str, str] = field(default_factory=dict)


@dataclass
class FeatureFile:
    """Represents a parsed feature file."""
    file_path: str
    feature_name: str = ""
    feature_description: str = ""
    background_steps: List[str] = field(default_factory=list)
    defaults: Dict[str, str] = field(default_factory=dict)
    test_cases: List[TestCase] = field(default_factory=list)
    feature_labels: List[str] = field(default_factory=list)


# Fields that can be overridden via @FieldName:Value syntax
OVERRIDE_FIELDS = {
    'Apps', 'Platform', 'Component/Feature', 'Priority', 'Status',
    'TC_requires_use_of_proxy', 'Regression_Type', 'Automatable?',
    'CT_Update_Target', 'Evidence_Type', 'Live_Proposition',
    'Users_Applied', 'Automated_Proposition', 'HighVisibility',
    'IsAds?', 'NBA_Feature', 'Folder'
}


def parse_feature_file(file_path: str) -> FeatureFile:
    """Parse a Gherkin feature file and return structured data."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {file_path}")
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    feature = FeatureFile(file_path=str(path))
    
    # State tracking
    in_defaults_block = False
    in_background = False
    in_scenario = False
    in_test_data = False
    in_expected_result = False
    current_scenario: Optional[TestCase] = None
    pending_tags: List[str] = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines and comments (except @Feature_Defaults)
        if not stripped or (stripped.startswith('#') and '@Feature_Defaults' not in stripped):
            i += 1
            continue
        
        # Parse @Feature_Defaults: block
        if '@Feature_Defaults:' in stripped:
            in_defaults_block = True
            i += 1
            continue
        
        # End defaults block when we hit Feature: or a tag line for Feature
        if in_defaults_block:
            if stripped.startswith('Feature:') or (stripped.startswith('@') and not stripped.startswith('@Feature_Defaults')):
                # Check if it's an override field or a regular tag
                if stripped.startswith('@') and ':' in stripped:
                    # Could be override like @Apps:MyApp or end of defaults
                    tag_name = stripped.split(':')[0][1:]  # Remove @
                    if tag_name in OVERRIDE_FIELDS or tag_name.replace('_', ' ') in OVERRIDE_FIELDS:
                        # Still in defaults, parse the override
                        key, value = _parse_override_tag(stripped)
                        if key:
                            feature.defaults[key] = value
                        i += 1
                        continue
                in_defaults_block = False
            else:
                # Parse default field (format: FieldName: Value or @FieldName:Value)
                if ':' in stripped:
                    if stripped.startswith('@'):
                        key, value = _parse_override_tag(stripped)
                    else:
                        parts = stripped.split(':', 1)
                        # Convert underscores to spaces in both field names and values
                        key = parts[0].strip().replace('_', ' ')
                        value = parts[1].strip().replace('_', ' ') if len(parts) > 1 else ""
                    if key:
                        feature.defaults[key] = value
                i += 1
                continue
        
        # Parse feature-level tags (before Feature:)
        if stripped.startswith('@') and not in_scenario:
            tags = _extract_tags(stripped)
            # Add ALL tags to pending_tags (both labels and overrides)
            # They will be processed when we hit Feature: or Scenario:
            pending_tags.extend(tags)
            i += 1
            continue
        
        # Parse Feature: line
        if stripped.startswith('Feature:'):
            feature.feature_name = stripped[8:].strip()
            feature.feature_labels = pending_tags.copy()
            pending_tags.clear()
            i += 1
            # Collect feature description (As a/I want/So that)
            desc_lines = []
            while i < len(lines):
                desc_line = lines[i].strip()
                if desc_line.startswith(('As a', 'As an', 'I want', 'So that', 'In order')):
                    desc_lines.append(desc_line)
                    i += 1
                elif not desc_line or desc_line.startswith('#'):
                    i += 1
                else:
                    break
            feature.feature_description = ' '.join(desc_lines)
            continue
        
        # Parse Background: section
        if stripped.startswith('Background:'):
            in_background = True
            in_scenario = False
            i += 1
            continue
        
        # Parse Scenario: line
        if stripped.startswith('Scenario:'):
            # Save previous scenario if exists
            if current_scenario:
                feature.test_cases.append(current_scenario)
            
            in_background = False
            in_scenario = True
            in_test_data = False
            in_expected_result = False
            
            scenario_name = stripped[9:].strip()
            current_scenario = TestCase(name=scenario_name)
            
            # Process pending tags
            for tag in pending_tags:
                if ':' in tag:
                    key, value = _parse_override_tag('@' + tag)
                    if key:
                        current_scenario.overrides[key] = value
                else:
                    current_scenario.labels.append(tag)
            pending_tags.clear()
            i += 1
            continue
        
        # Parse @Test_Data: block
        if stripped.startswith('@Test_Data:'):
            in_test_data = True
            in_expected_result = False
            i += 1
            continue

        # Parse @Expected_Result: block
        if stripped.startswith('@Expected_Result:'):
            in_expected_result = True
            in_test_data = False
            i += 1
            continue

        # Collect @Test_Data content
        if in_test_data and current_scenario:
            # Check if we're starting a new block or scenario
            if stripped.startswith('@Expected_Result:') or stripped.startswith('@') and not stripped.startswith('-'):
                in_test_data = False
                # Don't increment, reprocess this line
                continue
            # Remove leading "- " if present
            data_line = stripped.lstrip('- ')
            if current_scenario.test_data:
                current_scenario.test_data += '\n' + data_line
            else:
                current_scenario.test_data = data_line
            i += 1
            continue

        # Collect @Expected_Result content
        if in_expected_result and current_scenario:
            # Check if we're starting a new scenario or tag block
            if stripped.startswith('Scenario:') or stripped.startswith('@') and not stripped.startswith('-'):
                in_expected_result = False
                # Check if this is a tag for next scenario
                if stripped.startswith('@') and not stripped.startswith('@Test_Data') and not stripped.startswith('@Expected'):
                    tags = _extract_tags(stripped)
                    pending_tags.extend(tags)
                    i += 1
                continue
            # Remove leading "- " if present
            result_line = stripped.lstrip('- ')
            if current_scenario.expected_result:
                current_scenario.expected_result += ' ' + result_line
            else:
                current_scenario.expected_result = result_line
            i += 1
            continue

        # Parse Given/When/Then/And steps
        if stripped.startswith(('Given ', 'When ', 'Then ', 'And ', 'But ')):
            if in_background:
                feature.background_steps.append(stripped)
            elif in_scenario and current_scenario:
                current_scenario.steps.append(stripped)
            i += 1
            continue

        # Parse tags before scenario
        if stripped.startswith('@') and not in_test_data and not in_expected_result:
            tags = _extract_tags(stripped)
            pending_tags.extend(tags)
            i += 1
            continue

        i += 1

    # Don't forget the last scenario
    if current_scenario:
        feature.test_cases.append(current_scenario)

    return feature


def _parse_override_tag(tag: str) -> tuple:
    """Parse an override tag like @Platform:iOS and return (key, value)."""
    # Remove @ prefix if present
    if tag.startswith('@'):
        tag = tag[1:]

    if ':' not in tag:
        return (None, None)

    parts = tag.split(':', 1)
    key = parts[0].strip()
    value = parts[1].strip() if len(parts) > 1 else ""

    # Convert underscores to spaces in both field names and values
    # e.g., TC_requires_use_of_proxy -> TC requires use of proxy
    # e.g., New_Features -> New Features
    key = key.replace('_', ' ')
    value = value.replace('_', ' ')

    return (key, value)


def _extract_tags(line: str) -> List[str]:
    """Extract all @tags from a line."""
    return re.findall(r'@([\w\-/\?:,]+)', line)

