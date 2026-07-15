#!/usr/bin/env python3
"""Validate that GA4 event names in JavaScript match the event registry."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "analytics-events.json"
SCRIPT_PATH = ROOT / "assets" / "js" / "analytics-events.js"
DIRECT_EVENT_NAME = re.compile(r"send\(\s*['\"]([a-z0-9_]+)['\"]")
TERNARY_EVENT_NAMES = re.compile(
    r"\?\s*['\"]([a-z0-9_]+)['\"]\s*:\s*['\"]([a-z0-9_]+)['\"]"
)


def extract_implemented_events(script: str) -> list[str]:
    """Extract direct and conditional event names from the analytics script."""
    names = set(DIRECT_EVENT_NAME.findall(script))
    for true_name, false_name in TERNARY_EVENT_NAMES.findall(script):
        names.add(true_name)
        names.add(false_name)
    return sorted(names)


def main() -> int:
    errors: list[str] = []

    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Analytics registry error: {exc}")
        return 1

    try:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Analytics script error: {exc}")
        return 1

    registered_events = registry.get("events", [])
    registered_names = [str(item.get("name", "")).strip() for item in registered_events]
    implemented_names = extract_implemented_events(script)

    duplicates = sorted({name for name in registered_names if registered_names.count(name) > 1 and name})
    if duplicates:
        errors.append(f"Duplicate registry events: {', '.join(duplicates)}")

    missing_names = sorted(set(implemented_names) - set(registered_names))
    if missing_names:
        errors.append(f"Implemented but not registered: {', '.join(missing_names)}")

    unused_names = sorted(set(registered_names) - set(implemented_names))
    if unused_names:
        errors.append(f"Registered but not implemented: {', '.join(unused_names)}")

    for index, item in enumerate(registered_events, start=1):
        name = str(item.get("name", "")).strip()
        purpose = str(item.get("purpose", "")).strip()
        parameters = item.get("parameters")
        conversion = item.get("conversionCandidate")

        if not name or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            errors.append(f"Invalid event name at item {index}: {name or '(empty)'}")
        if not purpose:
            errors.append(f"Missing purpose for event: {name or index}")
        if not isinstance(parameters, list) or not all(isinstance(value, str) and value for value in parameters):
            errors.append(f"Invalid parameters for event: {name or index}")
        if not isinstance(conversion, bool):
            errors.append(f"Invalid conversionCandidate for event: {name or index}")

        prohibited = {"name", "email", "phone", "organization", "message", "free_text"}
        if isinstance(parameters, list) and prohibited.intersection(parameters):
            errors.append(
                f"PII-like parameter registered for event {name}: "
                f"{sorted(prohibited.intersection(parameters))}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Analytics validation passed: {len(registered_names)} events registered and implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
