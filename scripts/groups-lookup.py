#!/usr/bin/env python3
"""
Groups lookup and validation for inbox addressing patterns.

Used by:
- wait-for-brief: find which groups a recipient belongs to
- just groups: list configured groups with validation

Validates that all group members exist in the aliases registry.
"""

import json
import sys
import argparse
from pathlib import Path


def load_agent_sessions(config_path="docs/inbox/agent-sessions.json"):
    """Load and parse agent-sessions.json."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_groups(data, warn=True):
    """
    Validate that all group members exist in aliases.

    Returns: list of (group_name, invalid_member) tuples for invalid members.
    If warn=True, prints warnings to stderr.
    """
    groups = data.get("groups", {})
    aliases = data.get("aliases", {})
    invalid = []

    for group_name, group_data in groups.items():
        # Skip metadata keys starting with _
        if group_name.startswith("_"):
            continue

        if not isinstance(group_data, dict):
            continue

        members = group_data.get("members", [])
        for member in members:
            if member not in aliases:
                invalid.append((group_name, member))
                if warn:
                    print(f"Warning: Group '{group_name}' references non-existent alias '{member}'",
                          file=sys.stderr)

    return invalid


def get_groups_for_recipient(data, recipient):
    """
    Find all groups that contain the given recipient.

    Returns: list of group names (strings).
    """
    groups = data.get("groups", {})
    result = []

    for group_name, group_data in groups.items():
        # Skip metadata keys
        if group_name.startswith("_"):
            continue

        if not isinstance(group_data, dict):
            continue

        members = group_data.get("members", [])
        if recipient in members:
            result.append(group_name)

    return result


def list_groups(data, validate=True):
    """
    Print formatted list of all groups.

    If validate=True, validates group membership first and shows warnings.
    """
    if validate:
        validate_groups(data, warn=True)

    groups = data.get("groups", {})

    # Filter out metadata keys
    group_items = [(k, v) for k, v in groups.items()
                   if not k.startswith("_") and isinstance(v, dict)]

    if not group_items:
        print("No groups configured in agent-sessions.json")
        return

    print("📋 Configured groups (docs/inbox/agent-sessions.json):\n")

    for group_name, group_data in group_items:
        members = group_data.get("members", [])
        desc = group_data.get("description", "No description")

        print(f"  {group_name}:")
        print(f"    Members: {', '.join(members)}")
        print(f"    Description: {desc}")
        print(f"    Addressing: just brief <from> {group_name} <slug>")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Groups lookup and validation for inbox addressing"
    )
    parser.add_argument(
        "--recipient",
        help="Find groups containing this recipient (prints one per line)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured groups with descriptions"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate group membership (returns non-zero if invalid members found)"
    )
    parser.add_argument(
        "--config",
        default="docs/inbox/agent-sessions.json",
        help="Path to agent-sessions.json (default: docs/inbox/agent-sessions.json)"
    )

    args = parser.parse_args()

    data = load_agent_sessions(args.config)

    if args.list:
        list_groups(data, validate=True)
    elif args.recipient:
        # Validate silently first (warnings to stderr if issues)
        validate_groups(data, warn=True)
        groups = get_groups_for_recipient(data, args.recipient)
        for group in groups:
            print(group)
    elif args.validate:
        invalid = validate_groups(data, warn=True)
        sys.exit(1 if invalid else 0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
