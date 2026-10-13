---
name: merge
description: 'MayMust 팀 컨벤션으로 Pull Request를 머지. 작업 PR은 squash, 장기 브랜치(main·dev·release/*)끼리 합치는 통합 PR은 merge commit으로 판정해 실행. 게이트(독립 리뷰 또는 통합 PR 면제 · 작성자 본인 · 리뷰 승인 · mergeable · CI 통과)를 체크하고, 최종 제목의 Conventional Commit prefix·명사형 요약·현재 PR 번호 접미사를 검증하며, PR 본문에서 Self-verification/Screenshots 섹션을 스트립한 뒤 base 로컬 동기화·작업 브랜치 정리까지 수행. "머지해줘", "merge PR", "/merge" 호출 시 사용.'
---

# `/maymust:merge` — 팀 머지 스킬

> 작업 PR은 **squash merge** 로 통합한다. 장기 브랜치끼리 합치는 **통합 PR** 은 공통 조상이 남도록 **merge commit** 으로 통합한다. 이 스킬은 PR마다 머지 방식을 판정해 강제하고, 흔한 머지 실수(작업 PR rebase/merge-commit, 통합 PR squash, 장기 브랜치 삭제, 작업 브랜치 미삭제, base 동기화 누락)를 방지한다.

## 호출 예

```
/maymust:merge              # 현재 브랜치의 PR 을 찾아 머지
/maymust:merge 42           # 명시적 PR 번호
```

## 머지 방식 판정

장기 브랜치는 `main`, `dev`, `release/*` 다. 저장소가 다른 이름을 쓰면 `--long-lived` 로 패턴을 넘긴다.

| PR 종류 | 판정 | 머지 방식 | head 브랜치 |
| --- | --- | --- | --- |
| 작업 PR | 아래 통합 PR 조건에 해당하지 않음 (fork PR 포함) | `--squash` | 원격·로컬 삭제 |
| 통합 PR | base가 장기 브랜치이고, ① head도 장기 브랜치이거나 ② head에 base에 없는 다른 장기 브랜치의 커밋을 병합한 merge commit이 있음 | `--merge` | ①은 **보존**, ②(동기화 브랜치)는 삭제 |

통합 PR을 squash로 합치면 base에 원래 커밋과의 공통 조상이 남지 않는다. 그러면 다음 동기화에서 같은 충돌이 반복되고, 두 장기 브랜치의 차이를 커밋 단위로 추적할 수 없다. ②는 `dev`를 `release/*`에 반영하려고 만든 `chore/sync-...` 같은 브랜치다. 작업 브랜치가 자기 base를 병합해 충돌을 푼 경우는 ②에 해당하지 않으므로 squash를 유지한다.

판정은 [merge-loop-review-gate](../merge-loop-review-gate/SKILL.md)의 스크립트로 한다. 스크립트는 원격의 장기 브랜치와 PR base·head를 fetch한 뒤 판정하며, 조회 도중 PR head가 바뀌면 실패한다:

```bash
python3 <merge-loop-review-gate-dir>/scripts/check_integration_pr.py --pr <N> > <scratch>/integration.json
```

- 출력의 `mode`(`squash`·`merge`), `reason`, `head_long_lived`, `waiver`를 이후 단계에서 사용한다. scratch는 저장소 밖에 둔다.
- 미리보기에 `머지 방식=<squash|merge commit> (근거=<reason>)`을 표시하고 사용자 승인 대상에 포함한다.
- 사용자가 판정과 다른 방식을 명시적으로 요구하면, 판정 근거와 다른 방식을 썼을 때의 영향을 알리고 다시 확인받는다. `--rebase`는 어떤 경우에도 쓰지 않는다.
- 스크립트가 실패하면(조회 오류, Git 2.38 미만 등) 브랜치 이름으로 추측하지 말고 하드 블록한다.
- 통합 PR이면 스크립트가 저장소 설정도 확인한다. base에 merge queue가 있거나(merge commit을 보장할 수 없음), 저장소가 머지된 head 브랜치를 자동 삭제하는데 head가 장기 브랜치이면 실패한다. 이 경우 사유를 보고하고, 설정 변경이나 수동 머지는 사용자가 결정하게 한다.

## 게이트 (순서대로)

| # | 체크 | 실패 시 |
| --- | --- | --- |
| 0 | 현재 PR head의 독립 리뷰 통과 마커. 통합 PR은 면제 조건 충족과 사용자 승인으로 대신할 수 있음 | **하드 블록** — [merge-loop-review-gate](../merge-loop-review-gate/SKILL.md)로 검증; 마커도 면제도 없으면 전체 PR 리뷰 루프 수행 |
| 1 | PR 존재 · OPEN · 드래프트 아님 | **하드 블록** — "PR 이 없거나 드래프트입니다" |
| 2 | PR author == `gh auth status` 로그인 사용자 | **경고 + 확인** — 타인 PR 머지 방지 소프트 가드. "계속하시겠어요?" |
| 3 | `mergeable == MERGEABLE` (conflict 없음) | **하드 블록** — "conflict 해소 후 재시도" |
| 4 | `reviewDecision == APPROVED` | **경고 + 확인** — 리뷰 없이 머지할 수 있으나 확인 요함 |
| 5 | CI check가 모두 완료되고 성공·허용된 SKIPPED/NEUTRAL 상태 | 실패·pending은 **하드 블록**. 검사가 없으면 그 사실을 보고하고 저장소 규칙 확인 |
| 6 | 작업 PR이면 base == `dev`, 통합 PR이면 base·head 조합이 의도한 방향 | 작업 PR의 base가 `main` 이면 **경고** — "릴리즈 머지가 맞나요?". 통합 PR은 미리보기에서 `<head> → <base>` 방향을 확인받는다 |
| 7 | 최종 머지 제목이 명사형 + 현재 PR 번호 규칙 충족 | **하드 블록** — 제목을 정규화한 뒤 다시 검증 |

## 머지 메시지 생성 — 스트립 규칙

squash commit과 merge commit 모두 같은 제목·본문 규칙을 적용한다.

### 제목 하드 규칙

PR 제목을 그대로 복사하지 않는다. 최종 머지 제목 `MERGE_TITLE`을 다음 형식으로 만든다.

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

# 올바른 최종 머지 제목
fix(installer): 체크포인트 기반 설치 재개 구현 (#123)
fix(installer): 클러스터 dnsDomain cluster.local 고정 (#506)
chore(release): release/v0.1 변경을 main 에 병합 (#1080)
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
NUMBER_REF_COUNT=$(printf '%s\n' "$MERGE_TITLE" | rg -o '[#＃]\p{N}+' | wc -l | tr -d ' ')
TITLE_CORE=${MERGE_TITLE%" (#${PR_NUMBER})"}
SUMMARY=${TITLE_CORE#*: }

[ "$SUMMARY" != "$TITLE_CORE" ]
[ -n "$SUMMARY" ]
printf '%s\n' "$SUMMARY" | rg -q '[가-힣]'
printf '%s\n' "$MERGE_TITLE" | rg -q \
  '^(feat|fix|docs|chore|style|refactor|test|perf|build|ci)(\([^)]+\))?!?: '
[ "$NUMBER_REF_COUNT" -eq 1 ]
[ "$MERGE_TITLE" != "$TITLE_CORE" ]
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
   - `gh pr view <N> --json number,title,body,state,isDraft,author,reviewDecision,mergeable,mergeStateStatus,statusCheckRollup,baseRefName,headRefName,headRefOid`
2. **머지 방식 판정** — `check_integration_pr.py`로 `mode`·`reason`·`waiver`를 얻는다. 실패하면 하드 블록
3. **독립 리뷰와 메타데이터 게이트 체크** — 먼저 게이트 0, 이후 1~6번. review marker는 PR comment에서 같은 head SHA로 검증한다. 마커가 없고 `mode=merge`이면 [merge-loop-review-gate](../merge-loop-review-gate/SKILL.md)의 통합 PR 면제 절차를 따른다. 소프트 경고는 기존 사용자 승인 범위를 확인하고, 승인이 없을 때만 확인한다. 하드 블록은 해결 전 머지 금지
4. **머지 메시지 빌드**
   - 제목 = PR의 Conventional Commit prefix + 명사형 요약 + `(#<현재 PR 번호>)`
   - PR 제목에 번호 토큰이 하나 이상 있으면 모두 제거한 뒤 현재 PR 번호를 한 번만 추가
   - 본문 = PR 본문에서 Self-verification + Screenshots 섹션 제거
5. **제목 게이트 체크** — 7번
   - `PREVIEWED_MERGE_TITLE="$MERGE_TITLE"`, `PREVIEWED_BODY="$STRIPPED_BODY"`, `PREVIEWED_HEAD_SHA="$HEAD_SHA"`, `PREVIEWED_MODE="$MODE"`로 승인 대상을 고정
   - 고정한 제목과 본문, `명사형 끝말=<마지막 동작 명사>` 판정, `머지 방식=<squash|merge commit> (근거=<reason>)`, 원격 head 브랜치 삭제 여부를 미리보기 → 사용자 승인
   - 승인 후 제목·본문·머지 방식 또는 PR head가 달라지면 승인 무효. 2번부터 판정·독립 리뷰·CI와 메시지 전체를 다시 검증·미리보기
   - 승인 직후 아래처럼 승인된 스냅샷을 직접 대입하고 이후 재작성 금지
     ```bash
     readonly APPROVED_MERGE_TITLE="$PREVIEWED_MERGE_TITLE"
     readonly APPROVED_BODY="$PREVIEWED_BODY"
     readonly APPROVED_HEAD_SHA="$PREVIEWED_HEAD_SHA"
     readonly APPROVED_MODE="$PREVIEWED_MODE"
     ```
6. **머지 실행**
   - 실행 직전 판정 스크립트와 게이트 0~7을 다시 확인한다. head가 `APPROVED_HEAD_SHA`와 다르거나 `mode`가 `APPROVED_MODE`와 다르면 새 head의 판정·리뷰부터 다시 진행
   - 작업 PR (`APPROVED_MODE=squash`):
     ```bash
     gh pr merge <N> --squash --delete-branch --match-head-commit "$APPROVED_HEAD_SHA" \
       --subject "$APPROVED_MERGE_TITLE" --body "$APPROVED_BODY"
     ```
   - 통합 PR (`APPROVED_MODE=merge`). head가 장기 브랜치(`head_long_lived=true`)이면 `--delete-branch`를 **붙이지 않는다**. 동기화 브랜치이면 붙인다:
     ```bash
     gh pr merge <N> --merge --match-head-commit "$APPROVED_HEAD_SHA" \
       --subject "$APPROVED_MERGE_TITLE" --body "$APPROVED_BODY"
     ```
   - 저장소 설정이 merge commit을 허용하지 않아 실패하면 squash로 대체하지 않고 보고한다
7. **로컬 정리**
   ```bash
   git switch <verified-base-branch>
   git pull --ff-only
   git branch -d <old-work-branch>   # head가 장기 브랜치면 생략
   ```
   - 확인된 base(`dev` 또는 승인된 통합 base)를 동기화한다. 로컬 작업 브랜치는 safe-delete한다. squash 이후 Git이 삭제를 거부하면 남은 브랜치를 보고하고 보존한다. 장기 브랜치는 로컬에서도 지우지 않는다
8. **결과 보고**
   - 머지 방식, squash/merge commit 해시, 머지된 PR URL, 현재 브랜치 상태

## 금지 사항

- ❌ 작업 PR에 `--merge`, 모든 PR에 `--rebase`
- ❌ 통합 PR에 `--squash` (merge commit 머지가 실패했을 때의 대체 수단으로도 금지)
- ❌ head가 장기 브랜치인 PR에 `--delete-branch`, 로컬 장기 브랜치 삭제
- ❌ 작업 PR의 `--delete-branch` 누락 (작업 브랜치가 원격에 남음)
- ❌ 판정 스크립트 없이 브랜치 이름만 보고 머지 방식 결정, 판정과 다른 방식을 사용자 확인 없이 사용
- ❌ 머지 후 base sync 생략
- ❌ `git branch -D` (force delete) — 병합 미반영 데이터 날아갈 수 있음. safe delete 만
- ❌ conflict 있는 PR 을 "강제로" 머지 시도 (수동 해소 요구)
- ❌ statusCheck 실패 상태에서 머지 강행
- ❌ `--admin` 플래그 (관리자 우회 머지) — 사용자가 명시적으로 요청 시에만, 기본 금지
- ❌ PR 제목을 검증 없이 `--subject`로 전달
- ❌ 서술형 머지 제목 또는 현재 PR 번호가 빠진 제목으로 머지
- ❌ 승인 후 제목·본문·머지 방식 변수를 바꾸거나 미리보기와 다른 값을 `gh pr merge`에 전달

## 예시 출력

```
PR #42 머지 준비 · feat(plugin): squash 제목 컨벤션 강제 (#42)

게이트 체크:
✅ 현재 head의 독립 리뷰 통과 마커
✅ OPEN · non-draft
✅ author 일치 (maymust-jonghyunlee)
✅ APPROVED (리뷰어 2명)
✅ MERGEABLE · conflict 없음
✅ statusChecks: 3/3 SUCCESS
✅ base: dev

머지 방식: squash (근거=work-branch) · 원격 feature/merge-skill 삭제
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
→ gh pr merge 42 --squash --delete-branch --match-head-commit <approved-head> --subject "$APPROVED_MERGE_TITLE" ...
→ git switch dev && git pull
→ git branch -d feature/merge-skill

✅ squash 커밋 7f3ab2c · https://github.com/.../pull/42
   로컬 dev 최신 상태, feature/merge-skill 로컬 삭제됨
```

통합 PR (release → main):

```
PR #1080 머지 준비 · chore(release): release/v0.1 변경을 main 에 병합 (#1080)

게이트 체크:
✅ 통합 PR 리뷰 면제 (needs-ack: PR 없이 들어온 커밋 4개 확인·승인, 면제 기록 comment 작성)
✅ OPEN · non-draft · MERGEABLE · statusChecks 통과
✅ 방향: release/v0.1 → main

머지 방식: merge commit (근거=head-long-lived) · release/v0.1 원격·로컬 보존

[y]
→ gh pr merge 1080 --merge --match-head-commit <approved-head> --subject "$APPROVED_MERGE_TITLE" ...
→ git switch main && git pull --ff-only

✅ merge 커밋 9c1d2e4 · https://github.com/.../pull/1080
```
