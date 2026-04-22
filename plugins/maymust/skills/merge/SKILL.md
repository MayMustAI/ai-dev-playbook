---
description: MayMust 팀 컨벤션으로 Pull Request를 squash-merge. 게이트(작성자 본인 · 리뷰 승인 · mergeable · CI 통과)를 체크하고, PR 본문에서 Self-verification/Screenshots 섹션을 스트립한 깨끗한 squash 메시지로 머지한 뒤 dev 로컬 동기화·feature 브랜치 정리까지 수행. "머지해줘", "merge PR", "/merge" 호출 시 사용.
---

# `/maymust:merge` — 팀 squash-merge 스킬

> 팀은 **squash merge** 로만 통합한다. 이 스킬은 그 규칙을 강제하고, 흔한 머지 실수(rebase/merge-commit, 브랜치 미삭제, dev 동기화 누락)를 방지한다.

## 호출 예

```
/maymust:merge              # 현재 브랜치의 PR 을 찾아 머지
/maymust:merge 42           # 명시적 PR 번호
```

## 게이트 (순서대로)

| # | 체크 | 실패 시 |
| --- | --- | --- |
| 1 | PR 존재 · OPEN · 드래프트 아님 | **하드 블록** — "PR 이 없거나 드래프트입니다" |
| 2 | PR author == `gh auth status` 로그인 사용자 | **경고 + 확인** — 타인 PR 머지 방지 소프트 가드. "계속하시겠어요?" |
| 3 | `mergeable == MERGEABLE` (conflict 없음) | **하드 블록** — "conflict 해소 후 재시도" |
| 4 | `reviewDecision == APPROVED` | **경고 + 확인** — 리뷰 없이 머지할 수 있으나 확인 요함 |
| 5 | 모든 statusChecks == SUCCESS | **하드 블록 (실패 시)** / **경고 (pending 시)** |
| 6 | base == `dev` | `main` 이면 **경고** — "릴리즈 머지가 맞나요?" |

## squash 메시지 생성 — 스트립 규칙

**제목**: PR 제목 그대로 (`/maymust:commit` 규약 준수). PR 번호 `(#N)` 은 GitHub 이 자동 첨부하므로 수동 추가 금지.

**본문**: PR 본문에서 다음 섹션을 **자동 제거**:
- `## Self-verification` ~ 다음 `##` 헤딩 직전까지
- `## Screenshots` ~ 다음 `##` 헤딩 직전까지

**유지되는 섹션** (git log 에 영구 남을 가치 있는 것):
- `## Why`, `## What changed`, `## Design decisions`, `## Review focus`, `## Out of scope / Follow-up`, `## Worklog`, 상단 배지(🚨/⚠️/🔒)

**스트립 이유**: 체크박스·스크린샷은 PR 시점의 휘발성 증거. git log 는 영구 기록이라 "왜/무엇/설계 판단" 만 가치 있음. 5단계 루프 통과 여부는 PR 페이지에서 언제든 확인 가능.

## 워크플로우

1. **PR 식별**
   - 인자 있으면 그 번호, 없으면 현재 브랜치의 PR 자동 탐색
   - `gh pr view <N> --json number,title,body,state,isDraft,author,reviewDecision,mergeable,mergeStateStatus,statusCheckRollup,baseRefName`
2. **게이트 체크** — 위 6개. 소프트 경고는 사용자 확인, 하드 블록은 즉시 종료
3. **squash 메시지 빌드**
   - 제목 = PR 제목
   - 본문 = PR 본문에서 Self-verification + Screenshots 섹션 제거
   - 결과 미리보기 → 사용자 승인
4. **머지 실행**
   ```bash
   gh pr merge <N> --squash --delete-branch \
     --subject "<title>" --body "<stripped body>"
   ```
   - `--delete-branch` 로 원격 feature 브랜치 삭제
5. **로컬 정리**
   ```bash
   git switch dev
   git pull --ff-only
   git branch -d <old-feature-branch> 2>/dev/null || true
   ```
   - 로컬 feature 브랜치 safe-delete (-D 금지)
6. **결과 보고**
   - squash commit 해시, 머지된 PR URL, 현재 브랜치 상태

## 금지 사항

- ❌ `--merge` 또는 `--rebase` 옵션 사용 (팀 컨벤션은 squash 만)
- ❌ `--delete-branch` 누락 (feature 브랜치가 원격에 남음)
- ❌ 머지 후 dev sync 생략
- ❌ `git branch -D` (force delete) — 병합 미반영 데이터 날아갈 수 있음. safe delete 만
- ❌ conflict 있는 PR 을 "강제로" 머지 시도 (수동 해소 요구)
- ❌ statusCheck 실패 상태에서 머지 강행
- ❌ `--admin` 플래그 (관리자 우회 머지) — 사용자가 명시적으로 요청 시에만, 기본 금지

## 예시 출력

```
PR #42 머지 준비 · feat(plugin): /merge 스킬 추가

게이트 체크:
✅ OPEN · non-draft
✅ author 일치 (maymust-jonghyunlee)
✅ APPROVED (리뷰어 2명)
✅ MERGEABLE · conflict 없음
✅ statusChecks: 3/3 SUCCESS
✅ base: dev

스트립된 squash 본문 (프리뷰):
---
## Why
...
## What changed
...
## Worklog
.worklogs/2026-04-22-merge-skill.md
---

머지 진행하시겠습니까? (y/n)

[y]
→ gh pr merge 42 --squash --delete-branch ...
→ git switch dev && git pull
→ git branch -d feature/merge-skill

✅ squash 커밋 7f3ab2c · https://github.com/.../pull/42
   로컬 dev 최신 상태, feature/merge-skill 로컬 삭제됨
```
