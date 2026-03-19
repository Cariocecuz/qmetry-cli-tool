#!/usr/bin/env python3
"""
Augment Skill: Validate QMetry Feature File

Usage: /qmetry-validate <feature-file-path> [--no-api-check]

Validates a Gherkin feature file for syntax and field correctness.

Arguments:
    feature-file-path: Path to .feature file
    --no-api-check: Skip API field validation (optional)

Examples:
    /qmetry-validate features/mobile/login.feature
    /qmetry-validate "New Features/CC Sender/ChromecastSender.feature"
    /qmetry-validate login.feature --no-api-check
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import validate_qmetry_feature_file


def main():
    """Validate a QMetry feature file."""
    parser = argparse.ArgumentParser(description="Validate QMetry feature file")
    parser.add_argument("feature_file", help="Path to .feature file")
    parser.add_argument("--no-api-check", action="store_true", 
                       help="Skip API field validation")
    
    args = parser.parse_args()
    
    # Validate
    result = validate_qmetry_feature_file(
        feature_file_path=args.feature_file,
        check_api=not args.no_api_check
    )
    
    if result.get("success") and result.get("valid"):
        print(f"✅ Feature file is valid!\n")
        print(f"📄 Feature: {result.get('feature_name', 'N/A')}")
        print(f"📝 Description: {result.get('feature_description', 'N/A')}")
        print(f"📊 Test Cases: {result.get('test_case_count', 0)}")
        print(f"🔧 Background Steps: {result.get('background_steps_count', 0)}")

        if result.get("warnings"):
            print(f"\n⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"   - {warning}")

    elif result.get("success") and not result.get("valid"):
        print(f"❌ Validation failed!\n")

        if result.get("errors"):
            print("Errors:")
            for error in result["errors"]:
                print(f"  ❌ {error}")

        if result.get("invalid_fields"):
            print(f"\n❌ Invalid Fields ({len(result['invalid_fields'])}):")
            for field in result["invalid_fields"]:
                print(f"   - {field['field']} → Suggestion: {field['suggestion']}")

        if result.get("suggestion"):
            print(f"\n💡 {result['suggestion']}")

        sys.exit(1)

    else:
        print(f"❌ Error: {result.get('error_message', 'Unknown error')}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

