#!/usr/bin/env python3
"""
Augment Skill: Search QMetry Test Cases

Usage: /qmetry-search <text> [--app <app>] [--platform <platform>] [--limit <n>] [--refresh]

Searches test cases by text across summary, description, and precondition.
Uses a local cache (30-min TTL) for fast repeat searches.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qmetry_agent_skills import search_qmetry_test_cases


def main():
    """Search QMetry test cases."""
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print("Usage: /qmetry-search <text> [--app <app>] [--platform <platform>] [--limit <n>] [--refresh]")
        print("\nExamples:")
        print('  /qmetry-search "top 10 rail"')
        print('  /qmetry-search "login" --app MyApp --platform iOS')
        print('  /qmetry-search "browse" --limit 20 --refresh')
        sys.exit(0)

    text = None
    app = None
    platform = None
    limit = 50
    refresh = False

    i = 0
    while i < len(args):
        if args[i] == "--app" and i + 1 < len(args):
            app = args[i + 1]; i += 2
        elif args[i] == "--platform" and i + 1 < len(args):
            platform = args[i + 1]; i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif args[i] == "--refresh":
            refresh = True; i += 1
        elif text is None:
            text = args[i]; i += 1
        else:
            i += 1

    result = search_qmetry_test_cases(
        text=text,
        app=app,
        platform=platform,
        limit=limit,
        refresh=refresh,
    )

    if result["success"]:
        tcs = result.get("test_cases", [])
        cache_note = " (from cache)" if result.get("cache_hit") else ""
        print(f"✅ Found {result['total']} test case(s){cache_note}\n")

        if tcs:
            print(f"{'Key':<18}| {'Summary':<50}| Status")
            print(f"{'-'*18}+{'-'*50}+{'-'*10}")
            for tc in tcs:
                summary = tc["summary"][:47] + "..." if len(tc["summary"]) > 47 else tc["summary"]
                print(f"{tc['key']:<18}| {summary:<50}| {tc.get('status', '—')}")
        else:
            print("No matching test cases found.")
    else:
        print(f"❌ Error: {result['error_message']}")
        if result.get("suggestion"):
            print(f"💡 Suggestion: {result['suggestion']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

