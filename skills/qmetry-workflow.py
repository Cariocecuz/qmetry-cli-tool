#!/usr/bin/env python3
"""
Augment Skill: Complete QMetry Workflow

Usage: /qmetry-workflow <pdf-path> <target-folder> [--auto-upload] [--apps <value>] [--platform <value>]

Complete workflow: PDF → Feature File → Validation → Upload to QMetry.

Arguments:
    pdf-path: Path to PDF requirements document
    target-folder: Target folder in QMetry (e.g., "/Mobile/Authentication")
    --auto-upload: Upload immediately without review (optional)
    --apps: Apps field value (optional, default: MyApp)
    --platform: Platform field value (optional, default: iOS,Android)
    --component: Component/Feature field value (optional)

Examples:
    /qmetry-workflow requirements/login.pdf "/Mobile/Authentication"
    /qmetry-workflow "New Features/PullToRefresh/PullToRefresh.pdf" "/4. Navigation/4.36. Pull to Refresh" --auto-upload
    /qmetry-workflow login.pdf "/Mobile/Auth" --apps "MyApp" --platform "iOS,Android"
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import create_test_cases_from_pdf


def main():
    """Execute complete QMetry workflow."""
    parser = argparse.ArgumentParser(description="Complete QMetry workflow")
    parser.add_argument("pdf_path", help="Path to PDF requirements document")
    parser.add_argument("target_folder", help="Target folder in QMetry")
    parser.add_argument("--auto-upload", action="store_true",
                       help="Upload immediately without review")
    parser.add_argument("--apps", default="MyApp", help="Apps field value")
    parser.add_argument("--platform", default="iOS,Android", help="Platform field value")
    parser.add_argument("--component", help="Component/Feature field value")
    
    args = parser.parse_args()
    
    # Build defaults
    defaults = {
        "Apps": args.apps,
        "Platform": args.platform,
        "Regression_Type": "New_Features",
        "TC_requires_use_of_proxy": "No"
    }
    
    if args.component:
        defaults["Component/Feature"] = args.component
    
    # Execute workflow
    result = create_test_cases_from_pdf(
        pdf_path=args.pdf_path,
        target_folder=args.target_folder,
        defaults=defaults,
        auto_upload=args.auto_upload
    )
    
    if result["success"]:
        if args.auto_upload:
            # Auto-upload mode - show upload results
            print(f"✅ Complete workflow successful!\n")
            print(f"📄 Feature: {result['feature_name']}")
            print(f"📁 File: {result.get('feature_file_path', 'N/A')}")
            print(f"\n📊 Upload Results:")
            print(f"   Created: {result['created_count']}")
            print(f"   Updated: {result['updated_count']}")
            print(f"   Failed: {result['failed_count']}")
            print(f"📁 QMetry Location: {result['target_folder']}\n")
            
            if result.get("test_cases"):
                print("Test Cases:")
                for tc in result["test_cases"]:
                    status_icon = "✓" if tc["status"] in ["created", "updated"] else "✗"
                    print(f"  {status_icon} {tc['name']} ({tc.get('key', 'N/A')})")
        else:
            # Review mode - show preview
            print(f"✅ Feature file generated!\n")
            print(f"📄 File: {result.get('feature_file_path', 'N/A')}")
            print(f"📝 Feature: {result['feature_name']}")
            print(f"📊 Test Cases: {result['test_case_count']}\n")
            
            if result.get("warnings"):
                print(f"⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"   - {warning}")
                print()
            
            print(f"📋 Preview:")
            print(result.get('preview', ''))
            
            print(f"\n💡 Next Steps:")
            print(f"   1. Review the generated file: {result.get('feature_file_path', '')}")
            print(f"   2. When ready, upload with:")
            print(f"      /qmetry-upload {result.get('feature_file_path', '')} \"{args.target_folder}\"")
            print(f"\n   Or re-run with --auto-upload to skip review")
    else:
        print(f"❌ Workflow failed: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        
        if result.get("validation_errors"):
            print(f"\n❌ Validation Errors:")
            for field in result["validation_errors"]:
                print(f"   - {field['field']} → {field['suggestion']}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()

