#!/usr/bin/env python3
"""Load the bundled common profile without network access or user-config edits."""

import json
from pathlib import Path
import re


def session_context(plugin_root: Path) -> str:
    profile = plugin_root / "skills" / "team-defaults" / "SKILL.md"
    source = profile.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        raise ValueError("Common profile has no YAML frontmatter")
    body = source.split("---\n", 2)[2].strip()

    # Hooks run in the user's project, so model-facing links need installed paths.
    return re.sub(
        r"\]\((\.\./[^)]+)\)",
        lambda match: f"](<{(profile.parent / match[1]).resolve()}>)",
        body,
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": session_context(root),
        }
    }, ensure_ascii=False))
