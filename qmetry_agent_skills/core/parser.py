"""
Enhanced Gherkin Parser for Agent Skills

Extends the base parser to support in-memory parsing from strings,
enabling agent workflows that don't require physical files.
"""

from typing import Optional
from pathlib import Path
from qmetry_tool.gherkin_parser import (
    FeatureFile, TestCase, _extract_tags, _parse_override_tag, RESERVED_TAGS
)


def parse_feature_from_string(
    content: str,
    file_name: str = "generated.feature"
) -> FeatureFile:
    """
    Parse a Gherkin feature file from a string instead of a file.
    
    This enables agent workflows where feature files are generated
    in-memory and don't need to be written to disk before parsing.
    
    Args:
        content: The feature file content as a string
        file_name: Virtual filename for reference (default: "generated.feature")
    
    Returns:
        FeatureFile object with parsed data
    
    Example:
        content = '''
        @Feature_Defaults:
        @Apps:MyApp
        @Platform:iOS
        
        Feature: Login
          As a user I want to log in
        
          Scenario: Successful login
            Given user has credentials
            When user logs in
            Then user sees home screen
        '''
        
        feature = parse_feature_from_string(content, "login.feature")
        print(f"Parsed {len(feature.test_cases)} test cases")
    """
    lines = content.split('\n')
    feature = FeatureFile(file_path=file_name)
    
    # State tracking
    in_defaults_block = False
    in_background = False
    in_scenario = False
    in_test_data = False
    in_expected_result = False
    current_scenario: Optional[TestCase] = None
    pending_tags = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines and comments (except TC-XX comments)
        if not stripped or (stripped.startswith('#') and not stripped.startswith('# TC-')):
            i += 1
            continue
        
        # Parse @Feature_Defaults: block
        if stripped == '@Feature_Defaults:':
            in_defaults_block = True
            i += 1
            continue
        
        # Collect defaults
        if in_defaults_block:
            if stripped.startswith('@') and ':' in stripped:
                key, value = _parse_override_tag(stripped)
                if key and key not in RESERVED_TAGS:
                    feature.defaults[key] = value
                i += 1
                continue
            else:
                in_defaults_block = False
                # Don't increment, reprocess this line
                continue
        
        # Parse Feature: line
        if stripped.startswith('Feature:'):
            feature.feature_name = stripped[8:].strip()
            feature.feature_labels = pending_tags.copy()
            pending_tags.clear()
            i += 1
            # Collect feature description
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
            if stripped.startswith('@Expected_Result:') or (stripped.startswith('@') and not stripped.startswith('-')):
                in_test_data = False
                continue
            data_line = stripped.lstrip('- ')
            if current_scenario.test_data:
                current_scenario.test_data += '\n' + data_line
            else:
                current_scenario.test_data = data_line
            i += 1
            continue
        
        # Collect @Expected_Result content
        if in_expected_result and current_scenario:
            if stripped.startswith('Scenario:') or (stripped.startswith('@') and not stripped.startswith('-')):
                in_expected_result = False
                if stripped.startswith('@') and not stripped.startswith('@Test_Data') and not stripped.startswith('@Expected'):
                    tags = _extract_tags(stripped)
                    pending_tags.extend(tags)
                    i += 1
                continue
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
        
        # Parse tags
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

