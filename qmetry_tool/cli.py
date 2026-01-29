#!/usr/bin/env python3
"""
QMetry CLI Tool - Main Entry Point

Usage:
    qmetry export <file.feature>            Export to CSV
    qmetry upload <file.feature>            Upload to QMetry via API
    qmetry upload <file.feature> to <folder>  Upload to specific folder
    qmetry folders                          List available folders
    qmetry validate <file.feature>          Validate feature file
    qmetry config                           Create config template
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qmetry_tool.gherkin_parser import parse_feature_file
from qmetry_tool.csv_exporter import export_to_csv
from qmetry_tool.config_handler import (
    load_config, validate_config, create_config_template
)
from qmetry_tool.qmetry_api_client import QMetryClient


def print_usage():
    """Print usage information."""
    print("""
QMetry CLI Tool v1.0.0

Usage:
    python -m qmetry_tool.cli <command> [options]

Commands:
    export <file.feature>                Export feature file to CSV
    upload <file.feature>                Upload test cases to QMetry
    upload <file.feature> to <folder>    Upload to specific folder
    upload <file.feature> --dry          Preview without uploading
    folders                              List available folders
    validate <file.feature>              Validate feature file syntax
    config                               Create config template

Examples:
    python -m qmetry_tool.cli export "Import Testing/PullToRefresh.feature"
    python -m qmetry_tool.cli upload "Import Testing/PullToRefresh.feature"
    python -m qmetry_tool.cli upload "Import Testing/PullToRefresh.feature" to "/Mobile/PTR"
    python -m qmetry_tool.cli folders
    python -m qmetry_tool.cli config
""")


def cmd_export(args):
    """Export feature file to CSV."""
    if not args:
        print("Error: Please specify a feature file")
        return 1
    
    file_path = args[0]
    
    try:
        print(f"Parsing: {file_path}")
        feature = parse_feature_file(file_path)
        print(f"Found {len(feature.test_cases)} test cases")
        
        output_path = export_to_csv(feature)
        print(f"✓ Exported to: {output_path}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_validate(args):
    """Validate feature file syntax."""
    if not args:
        print("Error: Please specify a feature file")
        return 1
    
    file_path = args[0]
    
    try:
        print(f"Validating: {file_path}")
        feature = parse_feature_file(file_path)
        
        print(f"✓ Feature: {feature.feature_name}")
        print(f"  - {len(feature.background_steps)} background steps")
        print(f"  - {len(feature.test_cases)} test cases")
        print(f"  - Defaults: {list(feature.defaults.keys())}")
        
        for i, tc in enumerate(feature.test_cases, 1):
            print(f"\n  Test Case {i}: {tc.name}")
            print(f"    - Labels: {tc.labels}")
            print(f"    - Overrides: {tc.overrides}")
            print(f"    - Steps: {len(tc.steps)}")
            if tc.test_data:
                print(f"    - Test Data: ✓")
            if tc.expected_result:
                print(f"    - Expected Result: ✓")
        
        print("\n✓ Validation passed!")
        return 0
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return 1


def cmd_upload(args):
    """Upload test cases to QMetry."""
    if not args:
        print("Error: Please specify a feature file")
        return 1
    
    file_path = args[0]
    target_folder = None
    dry_run = False
    
    # Parse additional arguments
    i = 1
    while i < len(args):
        if args[i] == "to" and i + 1 < len(args):
            target_folder = args[i + 1]
            i += 2
        elif args[i] == "--folder" and i + 1 < len(args):
            target_folder = args[i + 1]
            i += 2
        elif args[i] == "--dry":
            dry_run = True
            i += 1
        else:
            i += 1
    
    try:
        # Load config
        config = load_config()
        issues = validate_config(config, require_api=True)
        if issues:
            for issue in issues:
                print(f"Config Error: {issue}")
            return 1
        
        # Parse feature file
        print(f"Parsing: {file_path}")
        feature = parse_feature_file(file_path)
        print(f"Found {len(feature.test_cases)} test cases")
        
        # Determine folder
        if not target_folder:
            target_folder = feature.defaults.get('Folder', config.default_folder)
        
        if dry_run:
            print(f"\n[DRY RUN] Would upload to: {config.project}:{target_folder}")
            for tc in feature.test_cases:
                print(f"  - {tc.name}")
            return 0
        
        # Confirmation prompt
        print(f"\nCreating {len(feature.test_cases)} TCs in {config.project}:{target_folder}")
        response = input("Proceed? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 0
        
        # Initialize API client
        client = QMetryClient(config)
        
        # Get or create folder
        folder_id = None
        if target_folder:
            folder_id = client.get_or_create_folder_path(target_folder)
            if folder_id is None:
                # Error message already printed by get_or_create_folder_path
                return 1

        # Push each test case
        created_count = 0
        updated_count = 0
        fail_count = 0

        for tc in feature.test_cases:
            # Build custom fields from merged defaults + overrides
            custom_fields = {**feature.defaults}
            for key, value in tc.overrides.items():
                custom_fields[key] = value

            # Remove non-custom fields
            for key in ['Folder', 'Status', 'Priority']:
                custom_fields.pop(key, None)

            # Check if TC already exists in target folder
            existing_tc = client.find_existing_tc(tc.name, folder_id)

            if existing_tc:
                # Update existing test case
                result = client.update_test_case(
                    tc_id=existing_tc['id'],
                    version_no=existing_tc['versionNo'],
                    summary=tc.name,
                    description=feature.feature_description,
                    precondition='\n'.join(feature.background_steps),
                    steps=tc.steps,
                    test_data=tc.test_data,
                    expected_result=tc.expected_result,
                    folder_id=folder_id,
                    labels=tc.labels,
                    custom_fields=custom_fields
                )

                if result.success:
                    print(f"  ✓ Updated: {tc.name} ({existing_tc['key']})")
                    updated_count += 1
                else:
                    print(f"  ✗ Failed to update: {tc.name} - {result.error}")
                    fail_count += 1
            else:
                # Create new test case
                result = client.create_test_case(
                    summary=tc.name,
                    description=feature.feature_description,
                    precondition='\n'.join(feature.background_steps),
                    steps=tc.steps,
                    test_data=tc.test_data,
                    expected_result=tc.expected_result,
                    folder_id=folder_id,
                    labels=tc.labels,
                    priority=tc.overrides.get('Priority', feature.defaults.get('Priority', 'Medium')),
                    status=tc.overrides.get('Status', feature.defaults.get('Status', 'TO DO')),
                    custom_fields=custom_fields
                )

                if result.success:
                    tc_key = result.data.get('key', 'N/A') if result.data else 'N/A'
                    print(f"  ✓ Created: {tc.name} ({tc_key})")
                    created_count += 1
                else:
                    print(f"  ✗ Failed: {tc.name} - {result.error}")
                    fail_count += 1

        print(f"\nSummary: {created_count} created, {updated_count} updated, {fail_count} failed")
        return 0 if fail_count == 0 else 1

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_folders(args):
    """List available folders in QMetry."""
    try:
        config = load_config()
        issues = validate_config(config, require_api=True)
        if issues:
            for issue in issues:
                print(f"Config Error: {issue}")
            return 1

        client = QMetryClient(config)
        result = client.list_folders()

        if not result.success:
            print(f"Error: {result.error}")
            return 1

        print(f"Folders in {config.project}:\n")
        folders = result.data if isinstance(result.data, list) else []

        def print_folder(folder, indent=0):
            name = folder.get('name', 'Unknown')
            folder_id = folder.get('id', '')
            print(f"{'  ' * indent}📁 {name} (id: {folder_id})")
            for child in folder.get('children', []):
                print_folder(child, indent + 1)

        for folder in folders:
            print_folder(folder)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_config(args):
    """Create config template file."""
    output_path = create_config_template()
    print(f"✓ Created config template: {output_path}")
    print("\nTo use:")
    print("  1. Copy to .qmetry_config.yaml")
    print("  2. Fill in your API key and project")
    print("  3. Add .qmetry_config.yaml to .gitignore")
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        'export': cmd_export,
        'exp': cmd_export,
        'upload': cmd_upload,
        'up': cmd_upload,
        'folders': cmd_folders,
        'validate': cmd_validate,
        'config': cmd_config,
    }

    if command in commands:
        return commands[command](args)
    elif command in ['-h', '--help', 'help']:
        print_usage()
        return 0
    else:
        print(f"Unknown command: {command}")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())

