#!/usr/bin/env python3
"""Compare bundled third-party files with each upstream's latest commit.

Prints a JSON report. With --apply, copies changed upstream files and updates the
lock file, but only for sources whose tracked paths all still exist, whose license
file did not change, and whose adapted material (lock "adapted") did not change.
Adapted material is ported by hand, and the pinned commit must match every hash
recorded for its source.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "maymust"


def git(args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


def clone_latest(repository, workdir):
    checkout = workdir / "repo"
    git(["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout",
         repository, str(checkout)])
    return checkout, git(["rev-parse", "HEAD"], cwd=checkout).decode().strip()


def read_upstream(checkout, path):
    result = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=checkout, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def status(data, expected):
    if data is None:
        return "missing"
    return "same" if sha256(data) == expected else "changed"


def is_license(path):
    return Path(path).name.upper().startswith(("LICENSE", "COPYING"))


def check_source(source, plugin, apply):
    pinned = source["commit"]
    with tempfile.TemporaryDirectory() as workdir:
        checkout, latest = clone_latest(source["repository"], Path(workdir))
        files, updates = [], {}
        for entry in source.get("files", []):
            data = read_upstream(checkout, entry["upstream_path"])
            state = status(data, entry["sha256"])
            if state == "changed":
                updates[entry["path"]] = data
            files.append({"upstream_path": entry["upstream_path"], "path": entry["path"], "status": state})
        adapted = [{"upstream_path": entry["upstream_path"], "used_in": entry["used_in"],
                    "status": status(read_upstream(checkout, entry["upstream_path"]), entry["upstream_sha256"])}
                   for entry in source.get("adapted", [])]

    blocked = None
    if any(item["status"] == "missing" for item in files):
        blocked = "upstream path missing; update upstream_path in the lock by hand"
    elif any(item["status"] == "changed" and is_license(item["upstream_path"]) for item in files):
        blocked = "license file changed; review the new license before updating"
    elif any(item["status"] != "same" for item in adapted):
        blocked = "adapted material changed; port it by hand, then update the commit and hashes"

    applied = bool(apply and updates and not blocked)
    if applied:
        for entry in source["files"]:
            if entry["path"] in updates:
                (plugin / entry["path"]).write_bytes(updates[entry["path"]])
                entry["sha256"] = sha256(updates[entry["path"]])
        source["commit"] = latest

    return {"name": source["name"], "repository": source["repository"], "pinned_commit": pinned,
            "latest_commit": latest, "files": files, "adapted": adapted,
            "blocked": blocked, "applied": applied}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare bundled third-party files with upstream.")
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN)
    parser.add_argument("--apply", action="store_true",
                        help="copy changed files and update the lock where it is safe")
    args = parser.parse_args(argv)

    lock_path = args.plugin_root / "third-party" / "skills.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    reports = [check_source(source, args.plugin_root, args.apply) for source in lock["sources"]]
    if any(report["applied"] for report in reports):
        lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    changed = any(item["status"] != "same"
                  for report in reports for item in report["files"] + report["adapted"])
    print(json.dumps({"changed": changed, "sources": reports}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
