#!/usr/bin/env python3
"""
Augment Skill: Generate Feature File from PDF

Usage: /qmetry-generate <pdf-path> [--output <path>] [--apps <value>] [--platform <value>]

Generates a Gherkin feature file from a PDF requirements document.

Arguments:
    pdf-path: Path to PDF requirements document
    --output: Output path for .feature file (optional, auto-generated if not provided)
    --apps: Apps field value (optional, default: MyApp)
    --platform: Platform field value (optional, default: iOS,Android)
    --component: Component/Feature field value (optional)

Examples:
    /qmetry-generate requirements/login.pdf
    /qmetry-generate "New Features/PullToRefresh/PullToRefresh.pdf" --platform "iOS,Android"
    /qmetry-generate login.pdf --output features/mobile/auth/login.feature --apps "MyApp"
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import generate_feature_file_from_pdf


def main():
    """Generate feature file from PDF."""
    parser = argparse.ArgumentParser(description="Generate feature file from PDF")
    parser.add_argument("pdf_path", help="Path to PDF requirements document")
    parser.add_argument("--output", help="Output path for .feature file")
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
    
    # Generate
    result = generate_feature_file_from_pdf(
        pdf_path=args.pdf_path,
        output_path=args.output,
        defaults=defaults,
        save_to_disk=True
    )
    
    if result["success"]:
        print(f"✅ Generated feature file from PDF!\n")
        print(f"📄 File: {result.get('feature_file_path', 'N/A')}")
        print(f"📝 Feature: {result['feature_name']}")
        print(f"📊 Test Cases: {result['test_case_count']}")
        print(f"📏 PDF Length: {result['pdf_text_length']} characters\n")
        
        if result.get("warnings"):
            print(f"⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"   - {warning}")
        
        print(f"\n📋 Preview:")
        print(result['preview'])
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Review the generated file")
        print(f"   2. Validate: /qmetry-validate {result.get('feature_file_path', '')}")
        print(f"   3. Upload: /qmetry-upload {result.get('feature_file_path', '')} <target-folder>")
    else:
        print(f"❌ Generation failed: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

