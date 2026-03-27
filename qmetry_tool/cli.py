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
    qmetry get <TC-KEY>                     Get test case by key
    qmetry search [--app X] [--platform Y]  Search test cases
    qmetry list <folder-id>                 List test cases in folder
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
from qmetry_tool.field_schema import FieldSchemaCache
from qmetry_tool.search_engine import QueryEngine
from qmetry_tool.output_formatter import TableFormatter, DetailFormatter, JSONFormatter


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
    upload <file.feature> --skip-validation  Skip field validation (not recommended)
    folders                              List available folders
    validate <file.feature>              Validate feature file syntax
    validate <file.feature> --api        Validate fields against QMetry
    config                               Create config template

  Search & Retrieval:
    get <TC-KEY>                         Get test case by key (e.g. MOB-TC-23519)
    get <TC-KEY> --format json           Get test case as JSON
    get <TC-KEY> --no-steps              Skip fetching test steps
    search --app Peacock --platform iOS  Search with structured filters
    search --text "login"                Full-text search (client-side)
    search "natural language query"      Natural language search
    search --format json --limit 100     Control output format and result count
    search --refresh                     Force refresh cache before searching
    list <folder-id>                     List test cases in folder by ID
    cache info                           Show cache status (age, size, TC count)
    cache clear                          Delete the local TC search cache

Examples:
    python -m qmetry_tool.cli export "Import Testing/PullToRefresh.feature"
    python -m qmetry_tool.cli upload "Import Testing/PullToRefresh.feature"
    python -m qmetry_tool.cli upload "Import Testing/PullToRefresh.feature" to "/Mobile/PTR"
    python -m qmetry_tool.cli validate "MyFeature.feature" --api
    python -m qmetry_tool.cli folders
    python -m qmetry_tool.cli config
    python -m qmetry_tool.cli get MOB-TC-23519
    python -m qmetry_tool.cli search --app Peacock --platform iOS
    python -m qmetry_tool.cli search --text "pull to refresh"
    python -m qmetry_tool.cli search "Peacock iOS test cases requiring proxy"
    python -m qmetry_tool.cli list 2232669
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
    """Validate feature file syntax and optionally check fields against QMetry."""
    if not args:
        print("Error: Please specify a feature file")
        return 1

    file_path = args[0]
    check_api = '--api' in args

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

        # If --api flag, validate fields against QMetry
        if check_api:
            print("\nChecking fields against QMetry...")

            try:
                config = load_config()
                issues = validate_config(config, require_api=True)
                if issues:
                    for issue in issues:
                        print(f"  Config Error: {issue}")
                    return 1

                client = QMetryClient(config)

                # Collect all field names from defaults + all TC overrides
                all_fields = set(feature.defaults.keys())
                for tc in feature.test_cases:
                    all_fields.update(tc.overrides.keys())

                # Remove non-custom fields
                all_fields.discard('Folder')
                all_fields.discard('Status')
                all_fields.discard('Priority')

                # Check each field
                invalid_fields = []
                for field in sorted(all_fields):
                    field_id = client.get_field_id(field)
                    if field_id:
                        print(f"  ✓ {field}")
                    else:
                        suggestion = client.find_similar_field(field)
                        if suggestion:
                            print(f"  ✗ {field} - not found (did you mean '{suggestion}'?)")
                        else:
                            print(f"  ✗ {field} - not found in QMetry")
                        invalid_fields.append(field)

                if invalid_fields:
                    print(f"\n✗ Validation failed: {len(invalid_fields)} invalid field(s)")
                    return 1

                print(f"\n✓ All {len(all_fields)} fields valid in QMetry!")

            except Exception as e:
                print(f"\n  Error connecting to QMetry: {e}")
                return 1

        print("\n✓ Validation passed!")
        return 0
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return 1


def _validate_fields_before_upload(client, feature):
    """Validate all fields against QMetry before uploading.

    Returns:
        tuple: (is_valid, invalid_fields_list)
    """
    # Collect all field names from defaults + all TC overrides
    all_fields = set(feature.defaults.keys())
    for tc in feature.test_cases:
        all_fields.update(tc.overrides.keys())

    # Remove non-custom fields
    all_fields.discard('Folder')
    all_fields.discard('Status')
    all_fields.discard('Priority')

    # Check each field
    invalid_fields = []
    print("\nValidating fields against QMetry...")

    for field in sorted(all_fields):
        field_id = client.get_field_id(field)
        if field_id:
            print(f"  ✓ {field}")
        else:
            suggestion = client.find_similar_field(field)
            if suggestion:
                print(f"  ✗ {field} - not found (did you mean '{suggestion}'?)")
            else:
                print(f"  ✗ {field} - not found in QMetry")
            invalid_fields.append(field)

    return (len(invalid_fields) == 0, invalid_fields)


def cmd_upload(args):
    """Upload test cases to QMetry."""
    if not args:
        print("Error: Please specify a feature file")
        return 1

    file_path = args[0]
    target_folder = None
    dry_run = False
    skip_validation = False

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
        elif args[i] == "--skip-validation":
            skip_validation = True
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

        # Initialize API client
        client = QMetryClient(config)

        # Validate fields against QMetry before uploading (fail-fast)
        if not skip_validation:
            is_valid, invalid_fields = _validate_fields_before_upload(client, feature)
            if not is_valid:
                print(f"\n✗ Upload aborted. {len(invalid_fields)} invalid field(s) found.")
                print("  Fix field names and retry.")
                print("  Hint: Use '--skip-validation' to bypass this check (not recommended).")
                print("\nSummary: 0 created (upload cancelled)")
                return 1
            print("✓ All fields valid!")

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
        # API returns {"total": N, "data": [...]} or just a list
        folders = result.data
        if isinstance(folders, dict):
            folders = folders.get('data', [])
        elif not isinstance(folders, list):
            folders = []

        def print_folder(folder, indent=0):
            name = folder.get('name', 'Unknown')
            folder_id = folder.get('id', '')
            print(f"{'  ' * indent}📁 {name} (id: {folder_id})")
            for child in folder.get('children', []):
                print_folder(child, indent + 1)

        for folder in folders:
            print_folder(folder)

        # Cache folder paths for future uploads
        client.discover_all_folders()

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


def _init_search_engine():
    """Initialize QMetryClient, FieldSchemaCache, and QueryEngine."""
    config = load_config()
    issues = validate_config(config, require_api=True)
    if issues:
        for issue in issues:
            print(f"Config Error: {issue}")
        return None, None, None

    client = QMetryClient(config)
    schema = FieldSchemaCache(client)
    engine = QueryEngine(client, schema, int(config.project))
    return client, schema, engine


def cmd_get(args):
    """Get a test case by key with full detail."""
    if not args:
        print("Error: Please specify a test case key (e.g. MOB-TC-23519)")
        return 1

    key = args[0]
    output_format = "detail"
    include_steps = True

    # Parse flags
    for i, arg in enumerate(args[1:], 1):
        if arg == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
        elif arg == "--no-steps":
            include_steps = False
        elif arg == "json":
            # Allow: qmetry get KEY --format json
            pass

    client, schema, engine = _init_search_engine()
    if engine is None:
        return 1

    print(f"Looking up {key}...")
    result = engine.get_by_key(key, include_steps=include_steps)

    if result["error"]:
        print(f"Error: {result['error']}")
        return 1

    tc = result["tc"]
    steps = result["steps"]

    if output_format == "json":
        output = {"testCase": tc}
        if steps is not None:
            output["testSteps"] = steps
        print(JSONFormatter.format(output))
    else:
        custom_display = None
        cf = tc.get("customFields", {})
        if cf:
            custom_display = schema.resolve_custom_field_display(cf)
        print(DetailFormatter.format(tc, steps=steps, custom_field_display=custom_display))

    return 0


def cmd_search(args):
    """Search test cases with structured filters or natural language."""
    # Parse flags
    app = None
    platform = None
    text = None
    folder_id = None
    output_format = "table"
    limit = 50
    refresh = False
    nl_query_parts = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--app" and i + 1 < len(args):
            app = args[i + 1]
            i += 2
        elif arg == "--platform" and i + 1 < len(args):
            platform = args[i + 1]
            i += 2
        elif arg == "--text" and i + 1 < len(args):
            text = args[i + 1]
            i += 2
        elif arg == "--folder" and i + 1 < len(args):
            try:
                folder_id = int(args[i + 1])
            except ValueError:
                print(f"Error: --folder requires a numeric folder ID, got '{args[i + 1]}'")
                return 1
            i += 2
        elif arg == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        elif arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                print(f"Error: --limit requires a number, got '{args[i + 1]}'")
                return 1
            i += 2
        elif arg == "--refresh":
            refresh = True
            i += 1
        elif not arg.startswith("--"):
            nl_query_parts.append(arg)
            i += 1
        else:
            print(f"Unknown option: {arg}")
            i += 1

    # If no structured flags but positional args exist, treat as NL query
    if nl_query_parts and not any([app, platform, text, folder_id]):
        nl_query = " ".join(nl_query_parts)
        # Try NL parsing
        try:
            from qmetry_tool.nl_parser import NLParser
            parsed = NLParser.parse(nl_query)
            app = parsed.get("app")
            platform = parsed.get("platform")
            text = parsed.get("text")
            if parsed.get("proxy"):
                # Will be handled as custom field filter in future
                pass
            print(f"Parsed query: app={app}, platform={platform}, text={text}")
        except ImportError:
            # NL parser not yet available, use as text search
            text = nl_query

    if not any([app, platform, text, folder_id]):
        print("Error: Provide search criteria. Examples:")
        print('  search --app Peacock --platform iOS')
        print('  search --text "login"')
        print('  search "Peacock iOS test cases"')
        return 1

    client, schema, engine = _init_search_engine()
    if engine is None:
        return 1

    if refresh:
        print("Refreshing cache...")
    else:
        print("Searching...")
    result = engine.search(
        folder_id=folder_id,
        text=text,
        app=app,
        platform=platform,
        limit=limit,
        refresh=refresh,
    )

    if result.get("error"):
        print(f"Error: {result['error']}")
        return 1

    data = result["data"]
    total = result["total"]
    cache_hit = result.get("cache_hit", False)

    if cache_hit:
        print("(results from cache — use --refresh to force update)")

    if output_format == "json":
        print(JSONFormatter.format(result))
    else:
        print(TableFormatter.format(data, total=total))

    return 0


def cmd_list(args):
    """List test cases in a folder by folder ID."""
    if not args:
        print("Error: Please specify a folder ID")
        print("  Use 'qmetry folders' to see available folders and their IDs")
        return 1

    try:
        folder_id = int(args[0])
    except ValueError:
        print(f"Error: Folder ID must be a number, got '{args[0]}'")
        return 1

    output_format = "table"
    limit = 50

    for i, arg in enumerate(args[1:], 1):
        if arg == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
        elif arg == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass

    client, schema, engine = _init_search_engine()
    if engine is None:
        return 1

    print(f"Listing test cases in folder {folder_id}...")
    result = engine.list_in_folder(folder_id=folder_id, limit=limit)

    if result.get("error"):
        print(f"Error: {result['error']}")
        return 1

    data = result["data"]
    total = result["total"]

    if output_format == "json":
        print(JSONFormatter.format(result))
    else:
        print(TableFormatter.format(data, total=total))

    return 0


def cmd_cache(args):
    """Manage the local TC search cache."""
    from qmetry_tool.tc_cache import TCSearchCache

    cache = TCSearchCache()
    sub = args[0].lower() if args else "info"

    if sub == "info":
        info = cache.info()
        if not info.get("exists"):
            print("No cache file found. Run a search to populate it.")
        elif info.get("corrupt"):
            print("Cache file is corrupt. Run 'qmetry cache clear' then search again.")
        else:
            valid = "✅ valid" if info["valid"] else "⏰ expired"
            print(f"Cache: {valid}")
            print(f"  Path:  {info['path']}")
            print(f"  TCs:   {info['total_tcs']}")
            print(f"  Size:  {info['size_mb']} MB ({info['size_bytes']:,} bytes)")
            print(f"  Age:   {info['age_minutes']} min (TTL: {info['ttl_minutes']} min)")
        return 0

    elif sub == "clear":
        if cache.clear():
            print("Cache cleared.")
        else:
            print("No cache file to clear.")
        return 0

    else:
        print(f"Unknown cache command: {sub}")
        print("  cache info   — show cache status")
        print("  cache clear  — delete the cache file")
        return 1


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
        'get': cmd_get,
        'search': cmd_search,
        'list': cmd_list,
        'cache': cmd_cache,
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

