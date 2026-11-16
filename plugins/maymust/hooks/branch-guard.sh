#!/usr/bin/env bash
# MayMust 브랜치 가드 훅 — 커밋이 실제로 일어나는 저장소가 dev · main 이면 사용자 확인 요청
#
# PreToolUse hook for Claude Bash and Codex shell tools. All shell calls pass
# through; this script finds each "git commit" in the command and works out the
# folder it runs in: Codex tool_input.workdir (else the hook cwd), followed by
# every "cd <path>" and "git -C <path>" along the way. It returns an "ask"
# decision when any of those folders is on dev or main. Commits pass when the
# folder is in detached HEAD, outside a git repository, or cannot be resolved
# (variable expansion and the like).

set -u

IFS= read -r -d '' script <<'PY' || true
import json
import os
import shlex
import subprocess
import sys

PROTECTED = {"dev", "main"}
CONTROL = set(";&|()\n")
SHELLS = {"bash", "sh", "zsh"}
WRAPPERS = {"command", "env", "exec", "nohup", "time"}
# git 전역 옵션 중 값을 다음 인자로 받는 것 (-C 는 따로 처리)
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}


def resolve(folder, path):
    """folder 에서 path 로 옮겨 간 폴더. 확인할 수 없으면 None."""
    if any(c in path for c in "$`*?["):
        return None
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        if folder is None:
            return None
        path = os.path.join(folder, path)
    return os.path.normpath(path)


def cd(args, folder):
    while args and args[0].startswith("-") and args[0] != "-":
        args = args[1:]
    if not args or args[0].startswith("#"):
        return resolve(folder, "~")
    if args[0] == "-":
        return None
    return resolve(folder, args[0])


def git_commit_folder(args, folder):
    """전역 옵션을 건너뛰어 하위 명령이 commit 이면 커밋할 폴더를, 아니면 False 를 돌려준다."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        option, eq, value = args[i].partition("=")
        i += 1
        if option in GIT_VALUE_OPTIONS and not eq:
            if i >= len(args):
                return False
            value = args[i]
            i += 1
        if option == "-C" and value:
            folder = resolve(folder, value)
        elif option in ("--git-dir", "--work-tree"):
            folder = None
    return folder if i < len(args) and args[i] == "commit" else False


def shell_script(args):
    """bash -c '<script>' 형태면 script 를, 아니면 None 을 돌려준다."""
    for i, arg in enumerate(args):
        if not arg.startswith("-"):
            return None
        if not arg.startswith("--") and "c" in arg[1:]:
            return args[i + 1] if i + 1 < len(args) else None
    return None


def simple_command(words, folder, found):
    """단순 명령 하나에서 커밋 폴더를 모으고, 다음 명령이 실행될 폴더를 돌려준다."""
    i = 0
    while i < len(words):
        if "=" in words[i] and words[i].split("=", 1)[0].isidentifier():
            i += 1
        elif words[i] in WRAPPERS:
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
        else:
            break
    words = words[i:]
    if not words:
        return folder
    name = os.path.basename(words[0])
    if name in ("cd", "pushd"):
        return cd(words[1:], folder)
    if name == "popd":
        return None
    if name == "git":
        target = git_commit_folder(words[1:], folder)
        if target is not False:
            found.append(target)
    elif name in SHELLS:
        script = shell_script(words[1:])
        if script is not None:
            found.extend(commit_folders(script, folder))
    return folder


def commit_folders(command, folder):
    """명령 안의 git commit 마다 그 커밋이 실행될 폴더(확인할 수 없으면 None)를 돌려준다."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    found, words, subshells = [], [], []
    for token in lexer:
        if not token or any(c not in CONTROL for c in token):
            words.append(token)
            continue
        for c in token:
            folder = simple_command(words, folder, found)
            words = []
            if c == "(":
                subshells.append(folder)
            elif c == ")" and subshells:
                folder = subshells.pop()
    simple_command(words, folder, found)
    return found


def branch(folder):
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=folder,
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") or {}
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        if isinstance(command, list):
            command = shlex.join(str(part) for part in command)
        if "commit" not in command:
            return
        cwd = data.get("cwd") or tool_input.get("cwd") or os.getcwd()
        start = os.path.normpath(os.path.join(cwd, tool_input.get("workdir") or ""))
        protected = {}
        for folder in commit_folders(command, start):
            if folder is not None and folder not in protected:
                protected[folder] = branch(folder)
        protected = {folder: name for folder, name in protected.items() if name in PROTECTED}
    except Exception:
        return
    if not protected:
        return
    targets = ", ".join(f"{folder} ('{name}')" for folder, name in protected.items())
    reason = (f"⚠️ 커밋할 저장소가 보호 브랜치입니다: {targets}. "
              "팀 컨벤션상 dev · main 에는 직접 커밋하지 않습니다 (feature 브랜치 → PR → squash merge). "
              "의도적인 경우(긴급 hotfix · 릴리즈 메타 등)만 계속하세요.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask",
                                             "permissionDecisionReason": reason}},
                     ensure_ascii=False, indent=2))


main()
PY

python3 -c "$script" || true
exit 0
