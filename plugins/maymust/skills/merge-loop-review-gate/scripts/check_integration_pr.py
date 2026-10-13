#!/usr/bin/env python3
"""Decide a PR's merge method and whether an integration PR may skip review."""

import argparse
import fnmatch
import json
import subprocess
import sys


DEFAULT_LONG_LIVED = "main,dev,release/*"
GRAPHQL_BATCH = 80


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


def evaluate_waiver(repo, base_ref, head_ref, merged_pr_shas):
    """Find commits in base..head that no merged PR has already gated."""
    log = git(repo, "log", "--format=%H%x1f%P%x1f%s", f"{base_ref}..{head_ref}").stdout
    conflict_merges, unreviewed = [], []
    count = 0
    for line in log.splitlines():
        sha, parents, subject = line.split("\x1f", 2)
        count += 1
        if sha in merged_pr_shas:
            continue
        parents = parents.split()
        entry = {"sha": sha, "subject": subject}
        if len(parents) > 1:
            if not merge_is_clean(repo, sha, parents):
                conflict_merges.append(entry)
        else:
            unreviewed.append(entry)
    if conflict_merges:
        status = "blocked"
    elif unreviewed:
        status = "needs-ack"
    else:
        status = "eligible"
    return {
        "status": status,
        "commit_count": count,
        "conflict_merges": conflict_merges,
        "unreviewed_commits": unreviewed,
    }


def merged_pr_commits(slug, shas, runner=run):
    """Return the subset of shas that belong to at least one merged PR."""
    owner, name = slug.split("/", 1)
    merged = set()
    for start in range(0, len(shas), GRAPHQL_BATCH):
        chunk = shas[start:start + GRAPHQL_BATCH]
        fields = " ".join(
            f'c{i}: object(oid: "{sha}") {{ ... on Commit {{ '
            f"associatedPullRequests(first: 20) {{ nodes {{ merged }} }} }} }}"
            for i, sha in enumerate(chunk)
        )
        query = (
            "query($owner: String!, $name: String!) { "
            f"repository(owner: $owner, name: $name) {{ {fields} }} }}"
        )
        out = runner(["gh", "api", "graphql", "-f", f"query={query}",
                      "-f", f"owner={owner}", "-f", f"name={name}"])
        repo = json.loads(out.stdout)["data"]["repository"]
        for i, sha in enumerate(chunk):
            commit = repo.get(f"c{i}") or {}
            nodes = (commit.get("associatedPullRequests") or {}).get("nodes") or []
            if any(node.get("merged") for node in nodes):
                merged.add(sha)
    return merged


def fetch_branches(repo, remote, names):
    refspecs = [f"+refs/heads/{n}:refs/remotes/{remote}/{n}" for n in sorted(names)]
    git(repo, "fetch", "--quiet", "--no-tags", remote, *refspecs)


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
    fetch_branches(repo, remote, long_lived | {pr["baseRefName"], pr["headRefName"]})

    base_ref = f"{remote}/{pr['baseRefName']}"
    head_ref = f"{remote}/{pr['headRefName']}"
    if git(repo, "rev-parse", head_ref).stdout.strip() != pr["headRefOid"]:
        raise CheckError("PR head moved while checking; run again")
    others = [f"{remote}/{n}" for n in sorted(long_lived) if n != pr["baseRefName"]]
    mode, reason = classify(repo, base_ref, head_ref, pr["baseRefName"],
                            pr["headRefName"], others, patterns)
    result.update(mode=mode, reason=reason,
                  head_long_lived=is_long_lived(pr["headRefName"], patterns))
    if mode != "merge":
        result["waiver"] = {"status": "not-applicable"}
        return result

    slug = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
               cwd=repo).stdout.strip()
    shas = git(repo, "rev-list", f"{base_ref}..{head_ref}").stdout.split()
    result["waiver"] = evaluate_waiver(repo, base_ref, head_ref, merged_pr_commits(slug, shas))
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
