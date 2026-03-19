#!/usr/bin/env python3
"""
Augment Skill: Upload Test Cases to QMetry

Usage: /qmetry-upload <feature-file-path> <target-folder> [--dry-run] [--skip-validation]

Uploads test cases from a feature file to QMetry.

Arguments:
    feature-file-path: Path to .feature file
    target-folder: Target folder in QMetry (e.g., "/Mobile/Authentication")
    --dry-run: Preview without uploading (optional)
    --skip-validation: Skip field validation (optional, not recommended)

Examples:
    /qmetry-upload features/mobile/login.feature "/Mobile/Authentication"
    /qmetry-upload "New Features/CC Sender/ChromecastSender.feature" "/5. Playback/5.19. Chromecast - Sender"
    /qmetry-upload login.feature "/Mobile/Auth" --dry-run
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import create_qmetry_test_case


def main():
    """Upload test cases to QMetry."""
    parser = argparse.ArgumentParser(description="Upload test cases to QMetry")
    parser.add_argument("feature_file", help="Path to .feature file")
    parser.add_argument("target_folder", help="Target folder in QMetry")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview without uploading")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip field validation (not recommended)")
    
    args = parser.parse_args()
    
    # Upload
    result = create_qmetry_test_case(
        feature_file_path=args.feature_file,
        target_folder=args.target_folder,
        dry_run=args.dry_run,
        skip_validation=args.skip_validation
    )
    
    if result["success"]:
        if result.get("dry_run"):
            print(f"📋 Dry Run Preview - No changes made\n")
            print(f"Would upload {result['test_case_count']} test cases to {result['target_folder']}\n")
            print("Test Cases:")
            for tc in result["test_cases"]:
                print(f"  - {tc['name']}")
            print(f"\n💡 Remove --dry-run to proceed with upload")
        else:
            print(f"✅ Successfully uploaded test cases!\n")
            print(f"📊 Results:")
            print(f"   Created: {result['created_count']}")
            print(f"   Updated: {result['updated_count']}")
            print(f"   Failed: {result['failed_count']}")
            print(f"📁 Location: {result['target_folder']}\n")
            
            print("Test Cases:")
            for tc in result["test_cases"]:
                status_icon = "✓" if tc["status"] in ["created", "updated"] else "✗"
                status_text = tc["status"].upper()
                key = tc.get("key", "N/A")
                print(f"  {status_icon} {tc['name']} ({key}) - {status_text}")
                if tc.get("error"):
                    print(f"     Error: {tc['error']}")
            
            if result.get("errors"):
                print(f"\n❌ Errors:")
                for error in result["errors"]:
                    print(f"   - {error}")
    else:
        print(f"❌ Upload failed: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        
        if result.get("invalid_fields"):
            print(f"\n❌ Invalid Fields:")
            for field in result["invalid_fields"]:
                print(f"   - {field['field']} → {field['suggestion']}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()

