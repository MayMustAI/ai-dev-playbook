#!/usr/bin/env bash
# MayMust 브랜치 가드 훅 — dev · main 에서 git commit 호출 시 사용자 확인 요청
#
# PreToolUse hook for the Bash tool. All Bash calls pass through; this script
# filters to "git commit" invocations, checks the current branch, and returns an
# "ask" decision when the branch is dev or main.

set -u

# stdin JSON 을 읽음
input=$(cat)

# Python3 로 JSON 파싱 (macOS 기본 탑재)
command=$(printf '%s' "$input" | python3 -c "import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    pass" 2>/dev/null || true)

cwd=$(printf '%s' "$input" | python3 -c "import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get('cwd', ''))
except Exception:
    pass" 2>/dev/null || true)

# command 가 비어있거나 git commit 을 포함하지 않으면 그대로 통과
if [ -z "$command" ] || ! printf '%s' "$command" | grep -qE 'git[[:space:]]+commit([[:space:]]|$)'; then
  exit 0
fi

# 현재 브랜치 확인
if [ -z "$cwd" ]; then
  cwd="$PWD"
fi

current_branch=$(cd "$cwd" 2>/dev/null && git rev-parse --abbrev-ref HEAD 2>/dev/null || true)

# git 저장소가 아니거나 브랜치 탐지 실패 시 통과
if [ -z "$current_branch" ]; then
  exit 0
fi

# 보호 브랜치면 사용자 확인 요청
case "$current_branch" in
  dev|main)
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "⚠️ 현재 '${current_branch}' 브랜치입니다. 팀 컨벤션상 dev · main 에는 직접 커밋하지 않습니다 (feature 브랜치 → PR → squash merge). 의도적인 경우(긴급 hotfix · 릴리즈 메타 등)만 계속하세요."
  }
}
EOF
    exit 0
    ;;
esac

# 그 외 브랜치는 통과
exit 0
