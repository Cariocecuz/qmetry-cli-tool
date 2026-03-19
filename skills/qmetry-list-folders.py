#!/usr/bin/env python3
"""
Augment Skill: List QMetry Folders

Usage: /qmetry-list-folders

Lists all test case folders in the QMetry project.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import list_qmetry_folders


def main():
    """List all QMetry folders."""
    result = list_qmetry_folders()
    
    if result["success"]:
        print(f"✅ Found {result['folder_count']} folders in QMetry\n")
        print_folders(result["folders"], indent=0)
    else:
        print(f"❌ Error: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        sys.exit(1)


def print_folders(folders, indent=0):
    """Recursively print folder hierarchy."""
    for folder in folders:
        print(f"{'  ' * indent}📁 {folder['name']} (id: {folder['id']})")
        print(f"{'  ' * indent}   Path: {folder['path']}")
        if 'children' in folder and folder['children']:
            print_folders(folder['children'], indent + 1)


if __name__ == "__main__":
    main()

