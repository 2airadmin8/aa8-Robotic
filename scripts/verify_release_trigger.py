#!/usr/bin/env python3
"""Regression gate for the Robotics manual-only production release policy.

No third-party YAML parser is needed. The 'on' block uses the checked-in,
conventional block syntax; alternative spellings fail closed until reviewed.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"


class ReleaseGateError(ValueError):
    """Production release trigger configuration is unsafe or unsupported."""


def triggers_from_yaml(source: str) -> tuple[str, ...]:
    """Read top-level GitHub Actions on: keys; reject unsupported inline styles."""
    lines = source.splitlines()
    on_lines = [i for i, line in enumerate(lines) if re.fullmatch(r"on:\s*", line)]
    if len(on_lines) != 1:
        raise ReleaseGateError(f"Expected one top-level on: block, got {len(on_lines)}")
    start = on_lines[0]
    triggers: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"  ([a-z_]+):(?:\s*#.*)?\s*", line)
        if match:
            triggers.append(match.group(1))
        elif line.startswith("  ") and not line.startswith("    "):
            raise ReleaseGateError(f"Unsupported trigger syntax: {line.strip()}")
    if not triggers:
        raise ReleaseGateError("No production release triggers found")
    return tuple(triggers)


def verify_manual_release(source: str, event_name: str = "") -> None:
    triggers = triggers_from_yaml(source)
    if triggers != ("workflow_dispatch",):
        raise ReleaseGateError(
            f"Production must be workflow_dispatch only, found {triggers!r}"
        )
    if event_name and event_name != "workflow_dispatch":
        raise ReleaseGateError(
            f"Production deployment invoked by forbidden event: {event_name}"
        )


def main() -> int:
    try:
        verify_manual_release(
            WORKFLOW.read_text(encoding="utf-8"),
            os.environ.get("GITHUB_EVENT_NAME", ""),
        )
    except (OSError, ReleaseGateError) as exc:
        print(f"RELEASE GATE FAIL: {exc}", file=sys.stderr)
        return 1
    print("RELEASE GATE PASS: workflow_dispatch only; no push/schedule deployment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
