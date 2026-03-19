#!/usr/bin/env python3
"""
Augment Skill: Discover QMetry Custom Fields

Usage: /qmetry-discover-fields

Discovers all custom fields and their options in the QMetry project.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import discover_qmetry_custom_fields


def main():
    """Discover QMetry custom fields."""
    result = discover_qmetry_custom_fields()
    
    if result["success"]:
        print(f"✅ Discovered {result['field_count']} custom fields\n")
        print("📋 Available Custom Fields:\n")
        
        for field_name, field_data in sorted(result["fields"].items()):
            print(f"  • {field_name}")
            print(f"    ID: {field_data['id']}")
            
            if field_data.get("options"):
                print(f"    Options:")
                for option_value, option_id in sorted(field_data["options"].items()):
                    print(f"      - {option_value} (id: {option_id})")
            print()
        
        print("\n💡 Usage in @Feature_Defaults: block:")
        print("   @Apps:MyApp")
        print("   @Platform:iOS,Android")
        print("   @Component/Feature:Authentication")
        print("   @Regression_Type:New_Features")
    else:
        print(f"❌ Error: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

