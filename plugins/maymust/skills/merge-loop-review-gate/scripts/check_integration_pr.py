#!/usr/bin/env python3
"""Decide a PR's merge method and whether an integration PR may skip review."""

import argparse
import fnmatch
import json
import subprocess
import sys


DEFAULT_LONG_LIVED = "main,dev,release/*"


class CheckError(RuntimeError):
    pass


def run(args, cwd=None, ok=(0,)):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode not in ok:
        raise CheckError(f"{' '.join(args[:3])} failed: {result.stderr.strip()}")
    return result


def git(repo, *args, ok=(0,)):
    return run(["git", "-C", repo, *args], ok=ok)


def is_long_lived(name, patterns):
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def is_ancestor(repo, commit, ref):
    return git(repo, "merge-base", "--is-ancestor", commit, ref, ok=(0, 1)).returncode == 0


def classify(repo, base_ref, head_ref, base_name, head_name, other_long_refs, patterns):
    """Return (mode, reason). mode is "merge" for integration PRs, else "squash"."""
    if not is_long_lived(base_name, patterns):
        return "squash", "base-not-long-lived"
    if is_long_lived(head_name, patterns):
        return "merge", "head-long-lived"
    merges = git(repo, "rev-list", "--merges", "--parents", f"{base_ref}..{head_ref}").stdout
    for line in merges.splitlines():
        sha, _first, *merged = line.split()
        for parent in merged:
            if is_ancestor(repo, parent, base_ref):
                continue
            for ref in other_long_refs:
                if is_ancestor(repo, parent, ref):
                    return "merge", f"sync-merge {sha[:12]} from {ref}"
    return "squash", "work-branch"


def merge_is_clean(repo, sha, parents):
    """True when the merge tree equals Git's automatic merge of its two parents."""
    if len(parents) != 2:
        return False
    result = git(repo, "merge-tree", "--write-tree", "--no-messages", *parents, ok=(0, 1))
    if result.returncode != 0:
        return False
    tree = git(repo, "rev-parse", f"{sha}^{{tree}}").stdout.strip()
    return result.stdout.split()[0] == tree


def evaluate_waiver(repo, base_ref, head_ref, long_refs):
    """Block when the PR brings commits no long-lived branch holds yet.

    Commits already on a long-lived branch passed that branch's PR gate. A new
    commit is allowed only as a merge identical to Git's automatic merge.
    """
    excluded = [f"^{ref}" for ref in [base_ref, *long_refs]]
    log = git(repo, "log", "--format=%H%x1f%P%x1f%s", head_ref, *excluded).stdout
    blocking = []
    for line in log.splitlines():
        sha, parents, subject = line.split("\x1f", 2)
        parents = parents.split()
        if len(parents) > 1 and merge_is_clean(repo, sha, parents):
            continue
        kind = "merge-differs-from-auto-merge" if len(parents) > 1 else "new-commit"
        blocking.append({"sha": sha, "subject": subject, "kind": kind})
    return {"status": "blocked" if blocking else "eligible", "blocking_commits": blocking}


def check(pr_number, repo, remote, patterns):
    pr = json.loads(run(
        ["gh", "pr", "view", str(pr_number), "--json",
         "number,baseRefName,headRefName,headRefOid,isCrossRepository"], cwd=repo).stdout)
    result = {
        "pr": pr["number"],
        "base": pr["baseRefName"],
        "head": pr["headRefName"],
        "head_sha": pr["headRefOid"],
        "head_long_lived": False,
    }
    if pr["isCrossRepository"]:
        return {**result, "mode": "squash", "reason": "cross-repository",
                "waiver": {"status": "not-applicable"}}

    remote_heads = git(repo, "ls-remote", "--heads", remote).stdout
    names = {line.split("refs/heads/", 1)[1] for line in remote_heads.splitlines()}
    long_lived = {n for n in names if is_long_lived(n, patterns)}
    fetch = long_lived | {pr["baseRefName"], pr["headRefName"]}
    git(repo, "fetch", "--quiet", "--no-tags", remote,
        *[f"+refs/heads/{n}:refs/remotes/{remote}/{n}" for n in sorted(fetch)])

    base_ref = f"{remote}/{pr['baseRefName']}"
    head_ref = f"{remote}/{pr['headRefName']}"
    if git(repo, "rev-parse", head_ref).stdout.strip() != pr["headRefOid"]:
        raise CheckError("PR head moved while checking; run again")
    long_refs = [f"{remote}/{n}" for n in sorted(long_lived)]
    others = [ref for ref in long_refs if ref != base_ref]
    mode, reason = classify(repo, base_ref, head_ref, pr["baseRefName"],
                            pr["headRefName"], others, patterns)
    result.update(mode=mode, reason=reason,
                  head_long_lived=is_long_lived(pr["headRefName"], patterns))
    if mode == "merge":
        result["waiver"] = evaluate_waiver(repo, base_ref, head_ref, long_refs)
    else:
        result["waiver"] = {"status": "not-applicable"}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--repo-dir", default=".")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--long-lived", default=DEFAULT_LONG_LIVED,
                        help="comma-separated branch patterns (default: %(default)s)")
    args = parser.parse_args()
    patterns = [p.strip() for p in args.long_lived.split(",") if p.strip()]
    try:
        result = check(args.pr, args.repo_dir, args.remote, patterns)
    except (CheckError, KeyError, ValueError, TypeError, AttributeError) as error:
        print(f"Integration check failed; merge blocked: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
