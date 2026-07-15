---
name: merge
description: 'MayMust 팀 컨벤션으로 Pull Request를 squash-merge. 게이트(작성자 본인 · 리뷰 승인 · mergeable · CI 통과)를 체크하고, 최종 제목의 Conventional Commit prefix·명사형 요약·현재 PR 번호 접미사를 검증하며, PR 본문에서 Self-verification/Screenshots 섹션을 스트립한 뒤 dev 로컬 동기화·feature 브랜치 정리까지 수행. "머지해줘", "merge PR", "/merge" 호출 시 사용.'
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
| 7 | 최종 squash 제목이 명사형 + 현재 PR 번호 규칙 충족 | **하드 블록** — 제목을 정규화한 뒤 다시 검증 |

## squash 메시지 생성 — 스트립 규칙

### 제목 하드 규칙

PR 제목을 그대로 복사하지 않는다. 최종 squash 제목 `SQUASH_TITLE`을 다음 형식으로 만든다.

```text
<type>(<scope>): <명사형 요약> (#<현재 PR 번호>)
```

- `<type>(<scope>)`는 PR 제목의 Conventional Commit prefix를 유지한다.
- 요약에는 한글을 하나 이상 포함한다. 영문 기술 용어는 섞을 수 있지만 영문 전용 요약은 허용하지 않는다.
- 요약은 `추가`, `구현`, `수정`, `고정`, `제거`, `차단`, `동기화`처럼 작업 결과를 나타내는 **명사형**으로 끝낸다.
- 마지막 어절 자체가 조사·어미 없는 동작 명사여야 한다. `추가해`, `수정할`, `고정하도록`처럼 용언이 활용된 형태는 명사형으로 인정하지 않는다.
- `~한다`, `~합니다`, `~했다`, `~됩니다`, `~되었다` 같은 서술형 종결은 문장부호 유무와 관계없이 허용하지 않는다.
- 요약 끝의 `.`, `!`, `?`, `。` 같은 문장부호도 허용하지 않는다.
- 요약 앞뒤의 불필요한 공백을 제거하고, 접미사 앞에는 ASCII 공백 하나만 둔다.
- PR 제목에 있는 기존 PR 번호 토큰(ASCII·전각 숫자 포함)은 전부 제거하고 **현재 PR 번호**를 정확히 한 번 붙인다.
- `gh pr merge --subject`를 지정하면 GitHub가 번호를 대신 붙여주지 않으므로 `(#<PR 번호>)`를 직접 포함한다.
- 의미를 훼손하지 않고 명사형으로 바꿀 수 없으면 추측하지 말고 사용자에게 최종 제목을 확인받는다.

예시:

```text
# 잘못된 제목
fix(installer): 체크포인트 기반 설치 재개를 구현한다
fix(installer): 클러스터 dnsDomain 을 cluster.local 로 고정한다

# 올바른 최종 squash 제목
fix(installer): 체크포인트 기반 설치 재개 구현 (#123)
fix(installer): 클러스터 dnsDomain cluster.local 고정 (#506)
```

머지 직전 다음을 하드 검증한다.

1. Conventional Commit prefix가 존재한다.
2. 제목이 정확히 ` (#<현재 PR 번호>)`로 끝난다.
3. 제목 전체의 `(#숫자)` 토큰이 현재 PR 번호 하나뿐이다.
4. 번호 접미사를 제외한 요약에 한글이 하나 이상 있고, 마지막 어절이 조사·어미 없는 동작 명사인지 **긍정 판정**한다.
5. 요약이 문장부호 또는 서술형 종결로 끝나지 않는다.
6. 제목 프리뷰에 `명사형 끝말=<마지막 동작 명사>`를 표시하고 사용자 승인을 받는다. 마지막 동작 명사를 특정할 수 없으면 하드 블록한다.

검증 시 최소한 다음과 동등한 검사를 수행한다. 하나라도 실패하면 머지하지 않는다.

```bash
NUMBER_REF_COUNT=$(printf '%s\n' "$SQUASH_TITLE" | rg -o '[#＃]\p{N}+' | wc -l | tr -d ' ')
TITLE_CORE=${SQUASH_TITLE%" (#${PR_NUMBER})"}
SUMMARY=${TITLE_CORE#*: }

[ "$SUMMARY" != "$TITLE_CORE" ]
[ -n "$SUMMARY" ]
printf '%s\n' "$SUMMARY" | rg -q '[가-힣]'
printf '%s\n' "$SQUASH_TITLE" | rg -q \
  '^(feat|fix|docs|chore|style|refactor|test|perf|build|ci)(\([^)]+\))?!?: '
[ "$NUMBER_REF_COUNT" -eq 1 ]
[ "$SQUASH_TITLE" != "$TITLE_CORE" ]
! printf '%s\n' "$SUMMARY" | rg -q '^[[:space:]]|[[:space:]]$'
! printf '%s\n' "$SUMMARY" | rg -q \
  '[가-힣](다|요)$|\p{Po}$'
```

**본문**: PR 본문에서 다음 섹션을 **자동 제거**:
- `## Self-verification` ~ 다음 `##` 헤딩 직전까지
- `## Screenshots` ~ 다음 `##` 헤딩 직전까지

**유지되는 섹션** (git log 에 영구 남을 가치 있는 것):
- `## Why`, `## What changed`, `## Design decisions`, `## Review focus`, `## Out of scope / Follow-up`, `## Worklog`, 상단 배지(🚨/⚠️/🔒)

**스트립 이유**: 체크박스·스크린샷은 PR 시점의 휘발성 증거. git log 는 영구 기록이라 "왜/무엇/설계 판단" 만 가치 있음. 5단계 루프 통과 여부는 PR 페이지에서 언제든 확인 가능.

## 워크플로우

1. **PR 식별**
   - 인자 있으면 그 번호, 없으면 현재 브랜치의 PR 자동 탐색
   - `gh pr view <N> --json number,title,body,state,isDraft,author,reviewDecision,mergeable,mergeStateStatus,statusCheckRollup,baseRefName,headRefOid`
2. **메타데이터 게이트 체크** — 1~6번. 소프트 경고는 사용자 확인, 하드 블록은 즉시 종료
3. **squash 메시지 빌드**
   - 제목 = PR의 Conventional Commit prefix + 명사형 요약 + `(#<현재 PR 번호>)`
   - PR 제목에 번호 토큰이 하나 이상 있으면 모두 제거한 뒤 현재 PR 번호를 한 번만 추가
   - 본문 = PR 본문에서 Self-verification + Screenshots 섹션 제거
4. **제목 게이트 체크** — 7번
   - `PREVIEWED_SQUASH_TITLE="$SQUASH_TITLE"`, `PREVIEWED_BODY="$STRIPPED_BODY"`, `PREVIEWED_HEAD_SHA="$HEAD_SHA"`로 승인 대상을 고정
   - 고정한 제목과 본문, `명사형 끝말=<마지막 동작 명사>` 판정을 미리보기 → 사용자 승인
   - 승인 후 제목·본문 또는 PR head가 달라지면 승인 무효. 3번부터 다시 빌드·검증·미리보기
   - 승인 직후 아래처럼 승인된 스냅샷을 직접 대입하고 이후 재작성 금지
     ```bash
     readonly APPROVED_SQUASH_TITLE="$PREVIEWED_SQUASH_TITLE"
     readonly APPROVED_BODY="$PREVIEWED_BODY"
     readonly APPROVED_HEAD_SHA="$PREVIEWED_HEAD_SHA"
     ```
5. **머지 실행**
   ```bash
   gh pr merge <N> --squash --delete-branch --match-head-commit "$APPROVED_HEAD_SHA" \
     --subject "$APPROVED_SQUASH_TITLE" --body "$APPROVED_BODY"
   ```
   - `--delete-branch` 로 원격 feature 브랜치 삭제
6. **로컬 정리**
   ```bash
   git switch dev
   git pull --ff-only
   git branch -d <old-feature-branch> 2>/dev/null || true
   ```
   - 로컬 feature 브랜치 safe-delete (-D 금지)
7. **결과 보고**
   - squash commit 해시, 머지된 PR URL, 현재 브랜치 상태

## 금지 사항

- ❌ `--merge` 또는 `--rebase` 옵션 사용 (팀 컨벤션은 squash 만)
- ❌ `--delete-branch` 누락 (feature 브랜치가 원격에 남음)
- ❌ 머지 후 dev sync 생략
- ❌ `git branch -D` (force delete) — 병합 미반영 데이터 날아갈 수 있음. safe delete 만
- ❌ conflict 있는 PR 을 "강제로" 머지 시도 (수동 해소 요구)
- ❌ statusCheck 실패 상태에서 머지 강행
- ❌ `--admin` 플래그 (관리자 우회 머지) — 사용자가 명시적으로 요청 시에만, 기본 금지
- ❌ PR 제목을 검증 없이 `--subject`로 전달
- ❌ 서술형 squash 제목 또는 현재 PR 번호가 빠진 제목으로 머지
- ❌ 승인 후 제목·본문 변수를 바꾸거나 미리보기와 다른 값을 `gh pr merge`에 전달

## 예시 출력

```
PR #42 머지 준비 · feat(plugin): squash 제목 컨벤션 강제 (#42)

게이트 체크:
✅ OPEN · non-draft
✅ author 일치 (maymust-jonghyunlee)
✅ APPROVED (리뷰어 2명)
✅ MERGEABLE · conflict 없음
✅ statusChecks: 3/3 SUCCESS
✅ base: dev

스트립된 squash 본문 (프리뷰):
---
제목: feat(plugin): squash 제목 컨벤션 강제 (#42)
명사형 끝말: 강제

## Why
...
## What changed
...
## Worklog
.worklogs/2026-04-22-merge-skill.md
---

머지 진행하시겠습니까? (y/n)

[y]
→ gh pr merge 42 --squash --delete-branch --match-head-commit <approved-head> --subject "$APPROVED_SQUASH_TITLE" ...
→ git switch dev && git pull
→ git branch -d feature/merge-skill

✅ squash 커밋 7f3ab2c · https://github.com/.../pull/42
   로컬 dev 최신 상태, feature/merge-skill 로컬 삭제됨
```
