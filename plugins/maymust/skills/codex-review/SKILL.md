---
name: codex-review
description: 내가(Claude) 작업한 코드 변경을 codex(OpenAI, 다른 모델·세션 편향 0)에게 maymust:self-review 프레임워크로 리뷰받고, 블로커·머스트픽스가 0 이 될 때까지 리뷰↔수정을 반복하는 루프. 통과 시 머지 게이트 통과로 선언. "코덱스 리뷰", "codex 한테 리뷰 받아줘", "codex 리뷰 루프", "/codex-review" 호출 시 사용.
---

# `/maymust:codex-review` — codex 교차모델 리뷰↔수정 루프

> `maymust:self-review` 의 자매 스킬. self-review 는 **같은 세션 Claude** 가 보므로 `⚠️ 동일 세션 편향` 을 경고만 한다.
> 이 스킬은 리뷰를 **codex(OpenAI 의 다른 모델, 이 세션 맥락 0)** 에게 맡겨 편향을 원천 제거하고, 한 발 더 나아가 **블로커·머스트픽스가 0 이 될 때까지** 리뷰→수정→리뷰를 반복한다.
> 역할: **codex = 비평가, 나(Claude) = 수정자.** 적대적 루프로 머지 가능 상태까지 끌어올린다.

## 호출 예

```
/maymust:codex-review                  # 자동 스코프 + 루프 (기본 최대 5 라운드)
/maymust:codex-review --once           # 루프 없이 1회만 리뷰 (수정 안 함)
/maymust:codex-review --max 8          # 최대 라운드 변경
/maymust:codex-review --uncommitted    # 워킹트리 변경 대상
/maymust:codex-review --base develop   # 다른 베이스
/maymust:codex-review --commit <sha>   # 특정 커밋
/maymust:codex-review 42               # PR #42
```

## 종료 조건 (루프의 목표)
- **PASS** = `blockers == 0 && mustfix == 0` → 머지 게이트 통과 선언. **닛픽은 남아도 OK.**
- 닛픽만 남으면 루프를 돌리지 않는다 (닛픽 강박 금지).

## 사전 조건 (없으면 안내 후 중단)
```bash
command -v codex >/dev/null || { echo "codex CLI 미설치"; exit 1; }
codex login status 2>&1 | grep -qi "logged in" || { echo "codex 미로그인 — '! codex login'"; exit 1; }
```

---

## STEP 0 — 스코프 결정 (루프 진입 전 1회)
인자 우선. **PR URL/번호가 오면(예: `https://github.com/<org>/<repo>/pull/267` 또는 `267`) → PR 모드**:
```bash
PR=$(echo "$ARG" | grep -oE '[0-9]+$')                              # URL 끝/숫자에서 PR 번호
BASE=$(gh pr view "$PR" --json baseRefName -q .baseRefName)         # PR 의 base (Claude=네트워크 OK)
HEAD_BRANCH=$(gh pr view "$PR" --json headRefName -q .headRefName)
git rev-parse --abbrev-ref HEAD | grep -qx "$HEAD_BRANCH" || gh pr checkout "$PR"   # head 브랜치 로컬 체크아웃 보장
SCOPE=pr
```
인자 없으면 자동 판별:
```bash
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); BASE=${BASE:-main}
AHEAD=$(git rev-list --count "origin/$BASE..HEAD" 2>/dev/null || echo 0)
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
```
- `AHEAD > 0` → **`--base $BASE`** (PR 등가 diff. 가장 흔함). ⚠️ 이 모드는 *커밋된* diff 만 본다 → 수정본을 codex 가 보려면 **라운드마다 fix 를 커밋**해야 한다 (STEP 3 참조).
- `AHEAD == 0 && DIRTY > 0` → **`--uncommitted`**. 수정본은 워킹트리에 그대로 두면 다음 라운드가 자연히 본다 (커밋 불필요).
- 둘 다 0 → 리뷰할 변경 없음. 알리고 중단.

**커밋 정책 (사용자에게 1줄 고지 후 진행, 되묻지 않음):**
`--base`/`--commit`/PR 모드는 피처 브랜치를 전제로 하므로 라운드마다 `fix(review): codex R<n> — <요약>` 커밋을 만든다. squash 머지(`maymust:merge`)에서 모두 소멸하므로 안전하다. `main`/보호 브랜치에서 호출됐으면 중단하고 브랜치를 먼저 만들도록 안내.

## STEP 1 — 의도(intent) 수집 (1회)
codex 는 이 세션 맥락이 **전혀 없다.** "무엇을/왜" 를 줘야 "의도 vs 구현" 리뷰가 된다:
1. **PR 존재** → `gh pr view <N|현재브랜치> --json title,body` 에서 `## Why`/`## Design decisions`/`## Out of scope`
2. **PR 없음** → 커밋·worklog:
   ```bash
   git log --format='%s%n%b' "origin/$BASE..HEAD" 2>/dev/null
   cat .worklogs/*$(git branch --show-current)*.md 2>/dev/null
   ```
3. **둘 다 빈약** → `(의도 선언 부족 — 일반 품질 체크만)` 명시
4. **이번 세션에서 방금 한 작업** 을 1~3줄로 직접 요약해 추가 (codex 가 모르는 유일 정보. **추측 금지, 실제 한 것만**)

→ 이 intent 블록은 루프 내내 **고정**. 단, 라운드마다 직전 라운드에서 무엇을 고쳤는지 1줄씩 누적 추가(STEP 4)해 codex 가 변화를 추적하게 한다.

## codex 호출 규약 (중요 — 검증된 방식)
`codex exec review` 의 스코프 플래그(`--base`/`--uncommitted`/`--commit`)는 **커스텀 PROMPT 와 상호 배타**라 maymust 프레임워크를 못 넣는다. 그래서 **plain `codex exec`** 를 쓰되, diff 를 프롬프트에 임베드하지 않고 **codex 가 (비샌드박스 실행에서) repo·PR 을 직접 읽게** 한다 — 프롬프트엔 "무엇이 리뷰 대상인지"(`gh pr diff` 또는 스코프 git 커맨드)만 주고, codex 가 변경을 확인한 뒤 **필요하면 변경 파일의 호출부·관련 파일·기존 동종 패턴까지 직접 읽어** 맥락을 파악한다. 임베드 방식보다 **격리된 diff 가 숨기는 통합 결함(호출부 불일치·기존 패턴 위반·연관 파일 미반영)** 을 더 잘 잡는다.
```bash
codex exec -s danger-full-access -o "$SCRATCH/codex-last.md" - < "$SCRATCH/codex-prompt.md" > "$SCRATCH/codex-log.txt" 2>&1
```
- `-s danger-full-access`: 샌드박스 없음 → **네트워크 + 로컬 git 둘 다** 가능. codex 가 `gh pr diff <N>` 로 PR 을 직접 받고, 로컬 working tree(**현재 브랜치 HEAD**)의 연관 파일도 읽는다. ⚠️ 쓰기도 가능하므로 프롬프트의 "수정 금지" 가 유일 가드. base 모드(로컬 git diff 사용 시)는 라운드마다 fix 를 커밋해야 반영되지만, PR 모드는 codex 가 `gh pr diff` 로 원격 PR 을 보므로 **push 후** 반영된다(STEP 3 (f)).
- `-o <FILE>`: **최종 메시지만** 파일로 — 중간 이벤트 노이즈 없이 깨끗한 리뷰 본문 + STATUS 줄을 여기서 읽는다.
- `codex-prompt.md` = 리뷰 지침(STEP 2 템플릿) + **스코프 git 커맨드/PR 참조 지시**(diff 임베드 아님).

**왜 `-s danger-full-access` 인가 (중요 — 검증됨):** codex 의 `-s read-only` 샌드박스는 **api.github.com 네트워크가 차단**된다(`gh pr diff` → "error connecting to api.github.com"). 그래서 codex 가 PR URL 을 직접 fetch 하거나 GitHub 맥락을 못 본다. **`-s danger-full-access` 로 실행하면 네트워크가 열려** `gh pr diff <N>` 가 실제 diff 를 반환하고(exec 모드에서 승인 대기 없이 동작 — 검증됨), codex 가 PR 을 통째로 받아 연관 파일·GitHub 맥락까지 직접 본다.
- ⚠️ `danger-full-access` = 샌드박스 없음 = codex 가 파일 쓰기·임의 명령 가능. **리뷰어는 읽기만 해야 하므로 프롬프트 첫 줄에 "어떤 파일도 수정하지 말 것"을 강하게 명시**(이게 유일한 가드). codex 가 비평가, 수정은 Claude 만.
- 따라서 사용자는 **PR URL 하나만 던지면 된다**("이 PR 리뷰해줘"). 스킬은 PR 번호를 뽑아 codex 에 "PR #N 을 `gh pr diff` 로 받아 리뷰하라"고 지시한다.
- 보조로 **Claude(이 세션)** 는 session 맥락(codex 가 모르는 의도)을 STEP 1 로 모아 프롬프트에 넣는다.

## STEP 2 — 리뷰 프롬프트 작성 (지침 + 스코프 git 커맨드 지시)
스코프(STEP 0)를 codex 가 **직접 실행할 git 커맨드**로 매핑한다 (diff 를 임베드하지 않는다):
```bash
case "$SCOPE" in
  base)        SCOPE_CMD="git diff $BASE...HEAD"        ;;  # PR 등가. 커밋된 변경만 → 루프에서 라운드마다 커밋 필요
  uncommitted) git add -N . ; SCOPE_CMD="git diff HEAD" ;;  # intent-to-add 로 미추적도 codex 의 git diff 에 보이게. 끝나면 git reset 로 -N 해제
  commit)      SCOPE_CMD="git show $SHA"                ;;
  pr)          SCOPE_CMD="gh pr diff $PR" ;;   # danger-full-access 라 네트워크 OK. 원격 PR head 기준 → 루프에서 fix push 필요
esac
```
지침 템플릿(아래)을 `$SCRATCH/codex-review-instructions.md` 에 쓰고 `{{INTENT}}`,`{{ROUND}}`,`{{FIXLOG}}`,`{{SCOPE_CMD}}` 치환 → 그대로 `codex-prompt.md` 로 (diff 임베드 없음):
```bash
{ echo "당신은 읽기 전용 독립 리뷰어다. 어떤 파일도 수정하지 말 것."; echo
  cat "$SCRATCH/codex-review-instructions.md"
} > "$SCRATCH/codex-prompt.md"
```
> 라운드마다 `{{ROUND}}`/`{{FIXLOG}}` 만 갱신하면 된다 — diff 는 codex 가 매번 최신 HEAD 에서 직접 읽으므로 재임베드 불필요. (base 모드는 STEP 3 (f) 의 라운드별 커밋이 codex 시야에 반영되는 전제.)

````markdown
당신은 작성자가 아닌 **독립 리뷰어**다. 아래 의도와 변경 구현의 일치만 본다.
재설계하지 말고 선언된 의도 대비로만 평가하라. (리뷰 라운드 {{ROUND}})

## 리뷰 대상 (먼저 확인)
먼저 다음으로 리뷰 대상 변경을 확인하라:
```
{{SCOPE_CMD}}
```
그리고 **필요하면** 변경 파일의 호출부·관련 파일·같은 디렉토리의 기존 동종 패턴(유사 role/chart/패키지/테스트)을 로컬 repo 에서 직접 읽어 맥락을 파악하라. **읽기·조회만 하고 어떤 파일도 수정·생성하지 말 것**(너는 비평가다). **평가 대상은 위 변경분**이다; 변경분 바깥의 기존 코드는 맥락 파악에만 쓰고 새로 지적하지 말 것.

## 작성자가 선언한 의도
{{INTENT}}

## 직전 라운드에서 반영한 수정 (있으면)
{{FIXLOG}}

## 리뷰 렌즈
1. 의도 일치(최우선): Why 의 문제를 푸는가? Design decisions 일관? 불변식 깨지는 곳?
2. 엣지: nil/empty/undefined, concurrent·race, 큰입력·타임아웃, 외부의존 실패경로
3. 잔재: TODO/FIXME/XXX/HACK, 디버그로그, 주석처리 코드, 하드코딩 테스트값
4. 복잡도: 함수 50줄↑, 중첩 4단계↑, 동일패턴 3회 반복
5. 네이밍: 무엇 아닌 어떻게, 약어남발, boolean is/has/should
6. 테스트: 변경로직 새 테스트?, 회귀방지?, Out of scope 테스트 follow-up 명시면 OK
7. 보안·데이터: 외부입력 validation, 시크릿 로깅·노출, SQLi·path traversal·XSS

## 금지
- 의도에 없는 추측성 지적 / "전반적 리팩터 필요" 류 추상 피드백(파일:라인 필수)
- 스타일 기호(탭vs스페이스 — 린터 영역) / Out of scope 항목을 블로커로
- 이미 거절된 대안 재제안
- **이미 고쳐진(직전 수정 반영) 항목을 다시 올리기 금지**
- **리뷰 대상 변경분 바깥(기존 코드)의 결함을 이 PR 의 블로커/머스트픽스로 올리기** (맥락용으로만 읽음 — 변경이 건드린 줄/직접 의존만 평가)

## 등급 기준 (엄격히)
- 블로커: 머지하면 의도가 깨지거나 런타임/데이터/보안 사고. 추정 아닌 확신만.
- 머스트픽스: 이번 변경에서 반드시 처리. 안 하면 결함.
- 닛픽: 있으면 좋은 개선. **머지를 막지 않는다.**
의심스러우면 등급을 낮춰라 (블로커→머스트픽스→닛픽). 과잉 블로커 금지.

## 출력 (정확히 이대로, 빈 섹션은 "없습니다.", 한국어)
# Codex review R{{ROUND}} — <대상 요약>
## 🚫 블로커
- `<파일>:<라인>` — <문제> → <제안>
## 🔧 머스트 픽스
- `<파일>:<라인>` — <문제> → <제안>
## 💡 닛픽
- `<파일>:<라인>` — <문제>
## 👍 좋음
- <1~3개>
## 📋 체크리스트 결과
| 렌즈 | 결과 | ... (의도/엣지/잔재/복잡도/네이밍/테스트/보안)

**마지막 줄에 반드시 이 형식만 정확히 출력 (파싱용):**
STATUS: blockers=<정수> mustfix=<정수> nits=<정수>
````

## STEP 3 — 루프 (리뷰 ↔ 수정)
의사코드. `MAX` 기본 5. 직전 발견 시그니처 집합 `prev` 로 진동·정체 감지.

```
round = 0; prev = {}
while round < MAX:
    round += 1

    # (a) 리뷰 — STEP 2 로 codex-prompt.md 재생성({{ROUND}}/{{FIXLOG}} 갱신; diff 는 codex 가 최신 HEAD 에서 직접 읽음) 후:
    codex exec -s danger-full-access -o "$SCRATCH/codex-last.md" - < "$SCRATCH/codex-prompt.md" > "$SCRATCH/codex-log.txt" 2>&1
    사용자에게 codex-last.md 의 리뷰 본문을 그대로 표시 (각색 금지)
    STATUS 줄 파싱 (최종 메시지 파일에서):
      LINE=$(grep -oE 'STATUS: blockers=[0-9]+ mustfix=[0-9]+ nits=[0-9]+' "$SCRATCH/codex-last.md" | tail -1)
      B=$(echo "$LINE" | grep -oE 'blockers=[0-9]+' | cut -d= -f2)
      M=$(echo "$LINE" | grep -oE 'mustfix=[0-9]+'  | cut -d= -f2)
    # STATUS 누락/파싱 실패(codex exit≠0 포함) → codex-last.md+log 보이고 중단 (오판으로 루프 도는 것보다 안전)

    # (b) 종료 판정
    if B == 0 and M == 0:
        → ✅ PASS. STEP 4(머지 게이트)로.

    # (c) 정체/진동 가드
    cur = {블로커·머스트픽스 항목의 (파일:라인 + 핵심어) 시그니처 집합}
    if cur == prev:
        → 같은 지적 반복 = 내 수정이 안 먹혔거나 codex 오판. 중단하고 사용자에게
          해당 항목 + 내 판단(동의/반박) 제시 후 지시 요청. (자동 재시도 금지)
    prev = cur

    # (d) 수정 — 내가(Claude) 직접
    for 항목 in 블로커 + 머스트픽스:
        진짜 결함이면 Edit 로 수정
        codex 오판(이미 처리/Out of scope/문맥오해)이면 수정 안 하고 'FIXLOG' 에
          "반박: <근거>" 로 기록 (다음 라운드 지침에 포함돼 codex 가 재고)
    FIXLOG 갱신 (이번에 고친 것 + 반박한 것 1줄씩)

    # (e) 회귀 가드 — codex 가 검증 커맨드를 줬으면 실행
    리뷰 본문의 "검증 실행:" / 명시된 go test·npm test 등을 실행
    실패하면 먼저 고치고 (이 수정도 FIXLOG 에) 다음 라운드로
    (테스트 미존재·장시간이면 생략하되 그 사실을 보고)

    # (f) 수정 반영 — codex 가 다음 라운드에 보게
    if SCOPE in {--base, --commit}:
        git add -A && git commit -m "fix(review): codex R{round} — <한줄요약>"   # codex 가 로컬 git diff 로 봄 → commit 으로 충분
    elif SCOPE == PR:
        git add -A && git commit -m "fix(review): codex R{round} — <한줄요약>"
        git push                                                                  # codex 가 `gh pr diff` 로 원격 PR 을 보므로 push 필요
    # --uncommitted 모드는 워킹트리 그대로 둠 (codex 의 git diff HEAD 가 즉시 봄)

# 루프 탈출 (MAX 도달)
→ ⚠️ MAX 라운드 내 미수렴. 남은 블로커/머스트픽스 + 각각 내 동의/반박 제시.
  사용자에게 판단 요청. 머지 게이트는 통과 아님.
```

## STEP 4 — 머지 게이트 & 종료
PASS 시:
```
✅ codex 교차모델 루프 통과 — 블로커 0 / 머스트픽스 0 (R<n> 만에 수렴)
   세션 편향 없음. 남은 닛픽 <m>건은 선택 사항.
   머지 게이트 통과 → `/maymust:merge` 로 진행 가능.
```
- **자동 머지하지 않는다.** `maymust:merge` 가 별도 게이트(작성자 본인·리뷰 승인·CI·mergeable)를 본다. 이 스킬은 "코드 품질 게이트 통과" 까지만 선언하고, 머지는 사용자가 `/maymust:merge` 로 트리거.
- `--base` 모드에서 만든 fix 커밋들 요약(N개)을 한 줄로 고지 — squash 시 정리됨을 명시.
- 닛픽 목록은 마지막에 한 번 모아서 제시(처리 여부는 사용자 선택).

## 안전장치 (요약)
- **MAX 라운드**(기본 5): 무한 루프 차단. 초과 시 미수렴으로 보고하고 사용자 판단.
- **정체/진동 가드**: 같은 지적이 수정 후에도 반복되면 즉시 중단 — codex 오판 가능성을 사용자에게.
- **회귀 가드**: 수정 후 codex 가 준 검증 커맨드 실행. 깨지면 머지 게이트 통과 안 함.
- **STATUS 파싱 실패 시 중단**: 카운트를 못 읽으면 루프를 돌리지 않고 원문을 사용자에게.
- **codex 오판은 수정하지 말고 반박**: 무조건 순응 금지. 근거를 FIXLOG 로 남겨 다음 라운드가 재평가하게 함. 내가 맞다고 확신하면 그 항목은 안 고치고 사용자에게 판단 위임.
- **보호 브랜치 호출 차단**: `main`/`master`/보호 브랜치면 커밋 루프 진입 전 중단.
- **codex 는 `-s danger-full-access`(비샌드박스)로 실행** — 네트워크(`gh pr diff`)+연관 파일 읽기를 위해. 쓰기·임의 명령도 가능하므로 프롬프트 첫 줄의 "어떤 파일도 수정·생성 금지"가 유일 가드. codex 가 파일을 건드렸으면(`git status` 로 확인) 무시·되돌리고 사용자에게 보고.

## maymust:self-review 와의 차이
| | self-review | codex-review |
| --- | --- | --- |
| 리뷰어 | 같은 세션 Claude | codex (다른 모델, 맥락 0) |
| 세션 편향 | 경고만(⚠️) | 원천 제거 |
| 모드 | 1회 리뷰 | **블로커·머스트픽스 0 까지 리뷰↔수정 루프** |
| 산출 | 리뷰 텍스트 | 수렴된 코드 + 머지 게이트 통과 선언 |
| 비용 | 0 | codex 호출 N회 + 수정 |

→ 빠른 1차 = self-review, 머지 직전 수렴 = codex-review.
