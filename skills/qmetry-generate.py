#!/usr/bin/env python3
"""
Augment Skill: Generate Feature File from PDF or Confluence Specification

Usage: /qmetry-generate <source> [--output <path>] [--apps <value>] [--platform <value>]

Generates a Gherkin feature file from a PDF requirements document or a Confluence page URL.

Arguments:
    source: Path to PDF requirements document OR a Confluence page URL
    --output: Output path for .feature file (optional, auto-generated if not provided)
    --apps: Apps field value (optional, default: MyApp)
    --platform: Platform field value (optional, default: iOS,Android)
    --component: Component/Feature field value (optional)

Examples:
    /qmetry-generate requirements/login.pdf
    /qmetry-generate "New Features/PullToRefresh/PullToRefresh.pdf" --platform "iOS,Android"
    /qmetry-generate login.pdf --output features/mobile/auth/login.feature --apps "MyApp"
    /qmetry-generate "https://confluence.example.com/wiki/spaces/PROJ/pages/12345/Feature+Name"

Note: Confluence generation requires the Confluence MCP connection to be configured.
      When a URL is provided, the agent reads the spec and generates test cases from it.
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import generate_feature_file_from_pdf


def _is_confluence_url(source: str) -> bool:
    """Check if the source is a Confluence URL."""
    return source.startswith("http://") or source.startswith("https://")


def main():
    """Generate feature file from PDF or Confluence spec."""
    parser = argparse.ArgumentParser(
        description="Generate feature file from PDF or Confluence specification"
    )
    parser.add_argument(
        "source",
        help="Path to PDF requirements document or Confluence page URL"
    )
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
    
    # Determine source type and generate
    if _is_confluence_url(args.source):
        # Confluence URL — agent handles this via MCP connection
        print(f"🔗 Confluence URL detected: {args.source}")
        print(f"\n📝 To generate test cases from this Confluence page,")
        print(f"   ask the agent directly:")
        print(f'   "Generate test cases from {args.source}"')
        print(f"\n   The agent will read the spec via Confluence and generate")
        print(f"   the .feature file interactively.")
        return 0

    # PDF source
    result = generate_feature_file_from_pdf(
        pdf_path=args.source,
        output_path=args.output,
        defaults=defaults,
        save_to_disk=True
    )

    if result["success"]:
        print(f"✅ Generated feature file!\n")
        print(f"📄 File: {result.get('feature_file_path', 'N/A')}")
        print(f"📝 Feature: {result['feature_name']}")
        print(f"📊 Test Cases: {result['test_case_count']}")
        print(f"📏 Source Length: {result['pdf_text_length']} characters\n")
        
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

