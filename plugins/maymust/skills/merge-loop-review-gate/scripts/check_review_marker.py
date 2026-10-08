#!/usr/bin/env python3
"""Check PR comment review markers against the exact current head SHA."""

import argparse
from datetime import datetime, timezone
import json
import re
import sys


MARKER = re.compile(
    r"^<!-- loop-review:pass head=(?P<head>[0-9a-f]{40}) "
    r"blockers=0 mustfix=0 nits=(?P<nits>[0-9]+) "
    r"round=(?P<round>[1-9][0-9]*) at=(?P<at>\S+) -->$",
    re.MULTILINE,
)


def has_pass_marker(pr: dict, head: str) -> bool:
    if pr.get("headRefOid") != head:
        return False
    for comment in pr.get("comments", []):
        for marker in MARKER.finditer(comment.get("body", "")):
            if marker["head"] != head:
                continue
            try:
                stamp = datetime.fromisoformat(marker["at"].replace("Z", "+00:00"))
            except ValueError:
                continue
            if stamp.tzinfo is not None and stamp.utcoffset() == timezone.utc.utcoffset(stamp):
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.head):
        parser.error("--head must be a full GitHub head SHA")
    try:
        pr = json.load(sys.stdin)
        if not isinstance(pr, dict):
            raise ValueError("expected a PR metadata object")
        passed = has_pass_marker(pr, args.head)
    except (ValueError, TypeError, AttributeError):
        print("Invalid PR metadata; review gate blocked.", file=sys.stderr)
        return 1
    print("Review gate passed." if passed else "No valid review marker for this head; gate blocked.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
