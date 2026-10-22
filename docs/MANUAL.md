# MayMust AI Dev Playbook 매뉴얼

이 문서는 플레이북을 설치하고, 매일의 작업에서 스킬을 쓰고, 문제가 생겼을 때 스스로 해결하는 방법을 정리합니다. 저장소 개요와 스킬 목록은 [README](../README.md)에 있습니다.

- **대상**: 플레이북을 쓰는 팀원, 릴리즈를 맡는 관리자, 스킬을 고치는 개발자
- **기준 버전**: maymust 0.8.1

## 목차

1. [설치](#1-설치)
2. [업데이트](#2-업데이트)
3. [세션마다 적용되는 공통 지침](#3-세션마다-적용되는-공통-지침)
4. [일하는 흐름](#4-일하는-흐름)
5. [스킬 레퍼런스](#5-스킬-레퍼런스)
6. [자동 훅](#6-자동-훅)
7. [릴리즈 (관리자)](#7-릴리즈-관리자)
8. [문제 해결](#8-문제-해결)
9. [플레이북 개발](#9-플레이북-개발)

## 1. 설치

### 배포 채널

변경은 작업 PR로 `dev`에 먼저 머지되고, `dev` → `main` 릴리즈 PR이 머지된 뒤에 팀원에게 배포됩니다. 그래서 설치할 때 **`main` 브랜치를 지정**합니다. 브랜치를 지정하지 않으면 기본 브랜치인 `dev`의 릴리즈 전 변경을 받습니다.

### 작동 환경

| 환경 | 작동 | 호출 |
| --- | --- | --- |
| Claude Code CLI | ✅ | `/maymust:commit` 같은 슬래시 명령 |
| Claude Desktop Code 탭 | ✅ | CLI와 같음 |
| Claude Desktop Chat 탭 | ❌ | 슬래시 명령이 거부됨 |
| Claude Desktop Remote 세션 | ❌ | 플러그인이 로드되지 않음 |
| Codex | ✅ | `$maymust:commit` 같은 플러그인 스킬 |

Chat 탭과 Remote 세션에서 동작하지 않는 이유는, 스킬이 `Bash`·`Edit`·`Read` 같은 파일시스템·셸 도구를 쓰는데 두 환경이 이 도구를 허용하지 않기 때문입니다. 공개 플러그인(`independent-review`, `resource-status-sheets`)은 Codex 전용입니다.

필요한 도구는 다음과 같습니다.

- 세션 시작 훅: Python 3
- 커밋·PR·머지 스킬: `git`, GitHub CLI(`gh`)
- `codex-review`: Codex CLI와 로그인(`codex login status`)
- `why`의 Linear·Notion·Slack 조사: 해당 MCP 연결과 인증
- 공개 플러그인: [5장](#공개-codex-플러그인)의 필요 조건

### Claude Code (CLI · Desktop Code 탭)

```bash
claude plugin marketplace add 'MayMustAI/ai-dev-playbook#main'
claude plugin install maymust@maymust-ai-dev-playbook
```

터미널에서 실행하면 Desktop Code 탭에도 적용됩니다. 두 환경이 같은 플러그인 저장소(`~/.claude/plugins`)를 쓰기 때문입니다. 설치한 뒤 새 세션을 시작합니다. Desktop의 Plugins UI(`+` → **Plugins** → **Manage plugins**)로도 추가할 수 있지만, 브랜치가 확실히 지정되도록 터미널 명령을 권장합니다.

### Codex

```bash
codex plugin marketplace add MayMustAI/ai-dev-playbook --ref main
codex plugin add maymust@maymust-ai-dev-playbook
```

Codex는 설치만으로 훅을 신뢰하지 않습니다. 새 세션의 `/hooks`에서 maymust 훅을 검토·신뢰한 뒤 다시 새 세션을 시작해야 공통 지침이 적용됩니다. 공개 플러그인(`independent-review`, `resource-status-sheets`)이 필요하면 같은 마켓플레이스에서 `codex plugin add <이름>@maymust-ai-dev-playbook`으로 추가합니다.

### 설치 확인

- **Claude**: `claude plugin list`에서 `maymust@maymust-ai-dev-playbook`의 Version과 Status를 확인합니다.
- **Codex**: `codex plugin list -m maymust-ai-dev-playbook`에서 `installed, enabled`와 버전을 확인합니다.

### 추적 브랜치 확인과 `main` 전환

예전 안내대로 브랜치 없이 마켓플레이스를 추가했다면 `dev`를 추적하고 있을 수 있습니다.

- **Claude**: `claude plugin marketplace list`의 Source가 `MayMustAI/ai-dev-playbook@main`이어야 합니다. `@main`이 없으면 마켓플레이스를 다시 추가합니다. 마켓플레이스를 제거하면 거기서 설치한 플러그인도 함께 제거되므로 재설치까지 진행합니다.

  ```bash
  claude plugin marketplace remove maymust-ai-dev-playbook
  claude plugin marketplace add 'MayMustAI/ai-dev-playbook#main'
  claude plugin install maymust@maymust-ai-dev-playbook
  ```

- **Codex**: `~/.codex/config.toml`의 `[marketplaces.maymust-ai-dev-playbook]`에서 `source_type`을 확인합니다.
  - `source_type = "git"`이면 `ref = "main"`이어야 합니다. 없거나 다른 값이면 `ref = "main"`으로 고친 뒤 [업데이트](#2-업데이트) 명령을 실행합니다.
  - `source_type = "local"`이면(예전 안내의 로컬 경로 설치) `ref`가 적용되지 않습니다. 이 상태에서 `ref`를 넣고 갱신하면 "not configured as a Git marketplace" 오류가 납니다. Git 소스로 다시 등록합니다. 로컬 소스는 [플레이북 개발](#9-플레이북-개발)에만 씁니다.

    ```bash
    codex plugin marketplace remove maymust-ai-dev-playbook
    codex plugin marketplace add MayMustAI/ai-dev-playbook --ref main
    codex plugin add maymust@maymust-ai-dev-playbook
    ```

## 2. 업데이트

새 버전은 `main`에 릴리즈된 뒤에 받을 수 있습니다. 릴리즈 후 각 PC에서 다음을 실행하고 새 세션을 시작합니다.

**Claude Code (CLI · Desktop Code 탭)**

```bash
claude plugin marketplace update maymust-ai-dev-playbook
claude plugin update maymust@maymust-ai-dev-playbook
```

`marketplace update`는 마켓플레이스 사본만 갱신합니다. 설치된 플러그인 버전은 `plugin update`까지 실행해야 올라갑니다.

**Codex**

```bash
codex plugin marketplace upgrade maymust-ai-dev-playbook
codex plugin add maymust@maymust-ai-dev-playbook
```

훅 정의(`hooks/codex-hooks.json`)가 바뀐 버전이면 새 세션의 `/hooks`에서 다시 검토·신뢰합니다.

## 3. 세션마다 적용되는 공통 지침

세션 시작 훅이 새 세션, 재개, 초기화, 컨텍스트 압축 직후마다 [team-defaults](../plugins/maymust/skills/team-defaults/SKILL.md)의 짧은 공통 지침을 컨텍스트에 넣습니다. 각 지침의 원문 스킬은 필요한 단계에서만 읽습니다.

| 영역 | 지침 | 원문 스킬 |
| --- | --- | --- |
| 응답 | 결과부터 간결하게 답하되, 판단에 필요한 수치·조건·한계는 유지 | `attention-kind` |
| 구현 | 가정을 밝히고, 가장 단순한 해법으로, 요청 범위만 바꾸고, 검증 가능한 성공 기준을 정함 | `karpathy-guidelines` |
| 완료 | 완료·통과를 주장하거나 커밋·푸시·PR을 만들기 전에 마지막 변경 이후의 실제 검증 결과를 확인 | `verification-before-completion` |
| 성능 수치 | 측정한 수치를 보고하거나 결정에 쓰기 전에 7개 질문으로 점검 | `benchmark-checklist` |

팀에 맞춘 적용 원칙도 함께 들어 있습니다. 사용자의 언어·형식·선택한 스타일을 우선하고, 특정 진단을 가정하지 않으며, 간결함 때문에 승인된 작업을 덜 하지 않습니다. 검증 결과는 마지막 관련 변경 이후의 증거를 쓰고, 바뀐 것이 없으면 상태 보고마다 같은 검사를 반복하지 않습니다.

이 지침은 모델의 행동을 유도할 뿐 강제하지 않습니다. 강제는 CI와 머지 게이트가 맡습니다. 훅을 쓸 수 없는 환경에서는 `/maymust:team-defaults`를 직접 호출합니다.

### 응답 스타일 바꾸기

기본 응답 방식은 Attention-kind입니다. 다른 방식이 필요하면 아래 스킬을 직접 호출합니다. 네 스킬 모두 명시적으로 호출할 때만 동작하고, 서로 섞어 쓰지 않습니다.

| 호출 | 용도 |
| --- | --- |
| `/maymust:attention-kind` | 기본 방식을 명시적으로 다시 적용 |
| `/maymust:spartan` | 군더더기 없이 가장 짧게. 경고와 수치는 유지 |
| `/maymust:rundown` | TL;DR, 상태 체크리스트, 번호 선택지로 된 상태 보고 |
| `/maymust:tldr` | 붙여 넣은 문서·스레드·기록을 요약 (응답 스타일이 아니라 한 번의 변환) |

Claude에서는 같은 이름의 output style(Attention-kind, Spartan, Rundown)도 고를 수 있습니다.

## 4. 일하는 흐름

```
1. /maymust:worklog            ← 작업 시작, worklog 생성
   /maymust:how · /maymust:why ← (필요할 때) 코드 동작과 설계 이유 조사
   (작업 진행)
   /maymust:worklog log "..."  ← 중간 로그 (판단에는 근거를 함께)
   /maymust:commit [wip]       ← 중간 커밋
   /maymust:benchmark-checklist ← (성능 수치를 다룰 때) 측정 검증
   ...
2. /maymust:worklog finish     ← 작업 종료, PR 본문 요약 생성
   /maymust:blast-radius       ← (영향이 넓은 변경) 영향 범위 점검과 안전 근거 증명
3. /maymust:pull-request       ← 검증 상태를 솔직하게 기록하여 PR 생성; 미완료 UI 증거는 draft
4. /maymust:self-review        ← (/clear 후 권장) PR의 의도와 구현 리뷰
5. /maymust:codex-review <PR>  ← 독립 리뷰·수정 루프, 현재 head에 통과 마커 생성
6. (동료 리뷰 — 사람)
7. /maymust:merge              ← 현재 head 리뷰 마커 + 팀 게이트 확인 후 squash(통합 PR은 merge commit) + 정리
8. (릴리즈) dev → main PR      ← /maymust:pull-request(base main) → /maymust:merge(merge commit, dev 보존) → 팀원 업데이트
```

### 4.1 브랜치와 worklog

- `dev`에서 작업 브랜치를 만듭니다. 예: `git switch -c feature/<slug> origin/dev`
- `dev`나 `main`에서 직접 커밋하려 하면 확인 창이 뜹니다. 긴급 hotfix처럼 의도한 경우가 아니면 작업 브랜치를 씁니다.
- `/maymust:worklog`로 작업 기록을 시작합니다. `.worklogs/<날짜>-<브랜치>.md`가 생기고, 작업 PR이 `dev`에 squash 머지될 때 함께 들어갑니다.

### 4.2 조사

- 코드가 어떻게 동작하는지 알아야 하면 `/maymust:how <질문>`을 씁니다.
- 코드가 왜 이렇게 만들어졌는지 알아야 하면 `/maymust:why <질문>`을 씁니다. git·PR과 연결된 Linear·Notion·Slack을 읽기 전용으로 조사합니다.
- 두 스킬은 서브에이전트를 여러 개 띄울 수 있어서 명시적으로 호출할 때만 동작합니다.

### 4.3 구현과 커밋

- 요청 범위 안에서 최소한으로 바꿉니다. 관련 없는 dead code나 주석은 고치지 않고 언급만 합니다.
- 중간 저장은 `/maymust:commit wip`, 리뷰받을 단위는 `/maymust:commit`(meaningful)으로 커밋합니다.
- 방향을 바꾸거나 되돌린 판단은 `/maymust:worklog log "..."`로 근거와 함께 남깁니다.

### 4.4 검증

- 완료를 주장하기 전에 마지막 변경 이후의 테스트·빌드·실행 결과를 직접 확인합니다. 하지 않은 검증은 "미실시"로 적습니다.
- 성능 수치를 보고하거나 그 수치로 결정하려면 `/maymust:benchmark-checklist`를 먼저 거칩니다.

### 4.5 PR

1. `/maymust:worklog finish`로 작업 기록을 완료 처리하고 PR 본문용 요약을 받습니다.
2. 공용 함수, 데이터 형식, 설정, 여러 모듈을 바꾸는 변경이면 `/maymust:blast-radius`로 영향 범위를 점검합니다.
3. `/maymust:pull-request`로 `dev` 대상 PR을 만듭니다. 5단계 루프 체크박스에는 실제로 한 것만 `[x]`로 표시합니다.

### 4.6 리뷰

1. `/maymust:self-review`: 같은 세션의 편향을 줄이려면 `/clear` 후 또는 새 세션에서 실행합니다.
2. `/maymust:codex-review <PR 번호>`: 통과하면 리뷰한 head에 묶인 마커가 PR 코멘트로 남습니다.
3. 동료 리뷰를 받습니다.

### 4.7 머지

`/maymust:merge`가 게이트를 확인하고 최종 제목·본문 미리보기를 보여 줍니다. 승인하면 squash로 머지하고, `dev`를 동기화하고, 작업 브랜치를 정리합니다. 릴리즈는 [7장](#7-릴리즈-관리자)을 따릅니다.

## 5. 스킬 레퍼런스

Claude에서는 `/maymust:<스킬>`, Codex에서는 `$maymust:<스킬>`로 호출합니다.

### 작업 흐름 스킬

#### `commit`

- **언제**: 스테이지된 변경을 팀 규약으로 커밋할 때
- **호출**: `/maymust:commit`(모드 제안), `/maymust:commit meaningful`, `/maymust:commit wip`
- **하는 일**: diff를 읽고 `<type>(<scope>): <한글 설명>` 제목과 한글 본문(왜·어떻게·검증)을 제안한 뒤, 확인을 받아 커밋합니다. meaningful 본문에는 검증 섹션이 필수이고, 하지 않은 검증은 미실시로 적습니다.
- **주의**: `dev`·`main`에서는 경고 후 명시적인 확답이 있어야 진행합니다. `git add .` 자동 실행, `--no-verify`, `Co-Authored-By`, `(#N)` 수동 추가는 금지입니다.

#### `worklog`

- **호출**: `/maymust:worklog`(열기·생성), `new "<작업>"`, `log "<메시지>"`, `finish`
- **파일**: `.worklogs/<YYYY-MM-DD>-<브랜치>.md`. 섹션은 무엇/왜(필수), 진행 로그, 막혔던 것, 결정 노트, 후속입니다.
- **근거 규칙**: 판단을 기록할 때는 근거(커밋 SHA, PR 번호, `file:line`, 실행한 명령과 결과)를 같은 줄에 붙입니다. 틀린 판단은 지우지 않고 새 줄로 정정합니다.
- **finish**: 상태를 `complete`로 바꾸고 PR 본문용 3~5줄 요약을 만듭니다.

#### `pull-request`

- **호출**: `/maymust:pull-request`
- **하는 일**: base(기본 `dev`) 대비 브랜치 전체 변경을 읽고, 규모(소형·중형·대형)에 맞는 본문을 만듭니다. 섹션은 Why, What changed, Design decisions, Review focus, Screenshots, Out of scope / Follow-up, Self-verification, Worklog입니다.
- **5단계 루프**: 직접 테스트, 셀프 리뷰, 다른 LLM 리뷰, 피드백 선별, Playwright. 하지 않은 단계는 `[ ] 미수행: <이유>`로 적습니다.
- **주의**: `main` 대상은 릴리즈 PR만 허용합니다. UI 변경을 스크린샷 없이 ready로 올리지 않습니다. 영향이 넓은 변경은 blast-radius 결과를, 성능 수치는 benchmark-checklist로 검증한 대표 수치 하나를 넣습니다.

#### `self-review`

- **호출**: `/maymust:self-review [PR 번호]`
- **하는 일**: PR 본문의 Why, Design decisions, Out of scope를 의도로 보고 diff와 맞는지 확인합니다. 렌즈는 의도 일치, 엣지 케이스, 잔재, 복잡도, 네이밍, 테스트, 보안·데이터입니다.
- **테스트 판정**: 동작을 깨뜨리면 실패하고, 내부 구현만 바꾸면 통과하는 테스트인지 봅니다.
- **주의**: 작성한 세션에서 바로 실행하면 편향 경고가 붙습니다.

#### `codex-review`

- **호출**: `/maymust:codex-review <PR 번호|URL>`, 옵션 `--once`, `--max <n>`, `--uncommitted`, `--base <ref>`, `--commit <sha>`
- **하는 일**: 새 `codex exec -s read-only` 세션이 리뷰어가 되고, 현재 세션은 검증된 blocker·must-fix만 최소 수정합니다. 기본 최대 5라운드이고, 같은 지적이 반복되면 멈춥니다.
- **통과**: blocker 0, must-fix 0이면 통과입니다. PR 모드에서는 리뷰한 head SHA에 묶인 `loop-review:pass` 마커를 PR 코멘트로 남깁니다. 이후 새 커밋이 생기면 마커는 무효가 됩니다.
- **전제**: Codex 로그인이 필요합니다. 수정을 커밋하는 루프(PR 모드, `--base`, `--commit`, 인자 없이 실행해 브랜치 범위가 선택된 경우)는 깨끗한 작업 트리와 보호 브랜치(`main`, `master`, `dev`, `develop`, 원격 기본 브랜치)가 아닌 작업 브랜치가 필요하고, PR 모드에서는 현재 브랜치와 HEAD가 PR head와 같아야 합니다. 아직 커밋하지 않은 변경은 `--uncommitted`로 리뷰하며(미추적 파일 포함, 수정은 작업 트리에 남김), `--once`는 수정·커밋 없이 한 번만 리뷰합니다.
- **주의**: `--once`와 PR이 아닌 범위의 통과는 머지 증거가 아닙니다. 자동 머지는 하지 않습니다.

#### `merge-loop-review-gate`

- **언제**: "머지해줘" 같은 요청에서 머지 절차보다 먼저 적용됩니다.
- **하는 일**: 현재 PR head의 통과 마커를 확인합니다. 마커가 없으면 codex-review 전체 루프를 진행합니다.
- **통합 PR 면제**: 장기 브랜치끼리 합치는 PR에 새 코드(어느 장기 브랜치에도 없는 커밋)가 없으면 `eligible`로 판정하고, 사용자 승인을 받아 리뷰를 면제합니다. 면제하면 근거를 담은 기록 코멘트를 남깁니다.

#### `merge`

- **호출**: `/maymust:merge [PR 번호]`
- **머지 방식**: 작업 PR은 squash로 머지하고 head 브랜치를 지웁니다. 장기 브랜치끼리의 통합 PR은 merge commit으로 머지하고, head가 장기 브랜치면 보존합니다.
- **게이트**: 리뷰 마커(또는 통합 PR 면제), OPEN·draft 아님, 작성자 일치(경고), 충돌 없음, 리뷰 승인(경고), CI 통과, base 방향, 제목 규칙
- **제목 규칙**: `<type>(<scope>): <명사형 요약> (#<PR 번호>)`. 요약에 한글이 있어야 하고, `추가`·`수정`·`병합` 같은 동작 명사로 끝나야 합니다.
- **본문**: Self-verification과 Screenshots 절을 지우고 나머지를 커밋 본문으로 씁니다.
- **실행**: 미리보기를 보여 주고 승인을 받은 뒤 `--match-head-commit`으로 실행합니다. 이후 base를 동기화하고 로컬 작업 브랜치를 정리합니다.
- **금지**: `--rebase`, 통합 PR의 squash, 장기 브랜치 삭제, 명시적 요청이 없는 `--admin`

### 분석 스킬 (pstack에서 이식)

#### `blast-radius`

- **언제**: PR 전에 변경이 diff 밖에서 무엇을 깨뜨릴 수 있는지 점검할 때, 작은 diff를 믿기 어려울 때
- **호출**: `/maymust:blast-radius [PR 번호|커밋]`
- **핵심**: 호출자 목록이 아니라 변경이 안전하다는 근거가 되는 사실 하나를 찾아 실행으로 증명합니다. 확신 단계는 주장, 위치, 불가능 증명, 실행, 재현 순서로 높아집니다.
- **결과**: 무엇이 바뀌었나, 안전 근거, 위험, 확인했지만 문제없음, 머지 전 확인. 안전 근거와 위험은 PR의 Design decisions와 Review focus로 옮깁니다.
- **주의**: 증명용 스크립트는 저장소 밖에 둡니다. 계속 남길 가치가 있을 때만 테스트로 옮깁니다.

#### `benchmark-checklist`

- **언제**: 속도 향상, 회귀, 처리량, 지연 같은 수치를 보고하거나 그 수치로 결정할 때
- **7개 질문**: 왜 두 배가 아닌가(한계 요인), 튜닝했나, 물리적 한계를 넘었나, 오류가 났나, 재현되나(번갈아 5회 이상, 중앙값과 범위), 중요한가(전체 경로 대비 비중), 작업이 실제로 일어났나
- **보고**: 판정을 먼저 쓰고 단위, 실행 횟수, 범위, 한계 요인을 함께 적습니다. 조건을 채우지 못하면 "판단 불가"로 적습니다.

#### `how`

- **호출**: `/maymust:how <질문>` (명시 호출 전용)
- **하는 일**: 좁은 질문은 설명자 하나가 바로 답하고, 넓은 질문은 2~4개 관점으로 나눠 탐색한 뒤 종합합니다.
- **결과**: 개요, 핵심 개념, 동작 방식(필요하면 mermaid 다이어그램), 코드 위치, 주의할 점

#### `why`

- **호출**: `/maymust:why <질문>` (명시 호출 전용). 출처를 줄이려면 "git이랑 Notion만 봐줘"처럼 지정합니다.
- **출처**: git·GitHub PR(항상), Linear, Notion, Slack(MCP가 연결·인증된 경우). 방어 코드처럼 보이면 장애·회고 기록도 찾습니다.
- **신뢰도 단계**: `[직접]`, `[수렴]`, `[추론]`, `[가설]`, `[미확인]`. 인용 없는 주장은 사실로 쓰지 않습니다.
- **결과**: 질문, 대상 코드, 확인된 사실, 합리적 추론, 경쟁 가설, 모르는 것, 조사한 출처, 신뢰도 요약. 코드를 바꾸려는 질문이면 유지 / 변경 / 피할 것 / 위험 목록이 붙습니다.
- **주의**: 조사는 읽기 전용입니다. 페이지·이슈를 만들거나 메시지를 보내지 않습니다. 결과를 PR이나 공개 문서에 옮길 때는 비공개 정보를 지웁니다.

### 공통 지침 스킬

- `team-defaults`: 세션 시작 훅이 주입하는 공통 지침입니다. 훅이 없는 환경에서 직접 호출합니다.
- `karpathy-guidelines`, `verification-before-completion`: 공통 지침의 원문입니다. 필요한 단계에서 모델이 읽습니다.
- `attention-kind`, `spartan`, `rundown`, `tldr`: [응답 스타일 바꾸기](#응답-스타일-바꾸기)를 참고합니다.

### 공개 Codex 플러그인

| 스킬 | 용도 | 필요 조건 |
| --- | --- | --- |
| `independent-review:claude-review` (`$claude-review`) | Codex 세션에서 별도 Claude Code 백그라운드 세션으로 PR을 읽기 전용 리뷰하고, 검증된 blocker·must-fix만 최소 수정 | `claude`(로그인), `gh`, `git`, `jq` |
| `independent-review:loop-review` (`$loop-review`) | `codex-review`와 같은 codex 리뷰·수정 루프의 범용판 | `codex`(로그인), `gh`, `git` |
| `resource-status-sheets` (`$resource-status-sheets`) | DailyUpdates CSV와 Google Sheets 템플릿으로 팀원별 월별 현황표 생성 | Python 3, Google Drive·Sheets 커넥터 |

공개 플러그인은 사내 경로, 저장소 규칙, Google Drive URL을 포함하지 않고, 사용자의 현재 저장소 컨벤션과 실행 시 입력을 기준으로 동작합니다.

`resource-status-sheets`의 동작 세부 사항은 다음과 같습니다.

- 행 생성기는 고객사 추론을 기본으로 끄고, `--customer-hint`가 있을 때만 명백한 고객명을 채웁니다.
- 템플릿·폴더 URL, 휴일, CSV 헤더, 근무지 매핑은 실행할 때 입력합니다.
- 반차의 `Note`·`TodaySummary`는 당일에, `TomorrowPlan`은 다음 영업일에 적용하며, 근무지 이동과는 독립적입니다.
- XLSX로 내보낼 때는 빈 근무시간 수식, 줄바꿈, 행 높이를 검증합니다.

## 6. 자동 훅

| 훅 | 시점 | 동작 |
| --- | --- | --- |
| SessionStart | 새 세션, 재개, 초기화, 압축 직후 | `team-defaults` 공통 지침을 컨텍스트에 주입 |
| PreToolUse(branch-guard) | 셸 명령 실행 전 | `dev`·`main` 브랜치에서 `git commit`이면 사용자 확인을 요청 |

- Claude는 `hooks/hooks.json`, Codex는 `hooks/codex-hooks.json`을 읽고, 두 설정이 같은 스크립트를 실행합니다.
- Codex에서는 `/hooks`에서 신뢰해야 훅이 동작하고, 훅 정의가 바뀌면 다시 검토해야 합니다.
- **알려진 한계**: branch-guard는 `git -C <경로> commit`, `git -c <설정> commit`처럼 `git`과 `commit` 사이에 옵션이 있는 명령을 잡지 못합니다. 또 `claude -p` 같은 비대화형 실행에서는 확인 요청이 거부로 처리됩니다.

## 7. 릴리즈 (관리자)

1. **버전 갱신**: 작업 PR에서 `.claude-plugin/marketplace.json`, `plugins/maymust/.claude-plugin/plugin.json`, `plugins/maymust/.codex-plugin/plugin.json`의 version을 함께 올립니다. 세 값이 같은지는 테스트가 검사합니다. 두 런타임 모두 버전별로 설치본을 구분하므로, 버전을 올리지 않으면 팀원이 새 버전을 받지 못합니다.
2. **릴리즈 PR**: 작업 PR이 `dev`에 머지된 상태에서 `/maymust:pull-request`로 base `main`, head `dev`인 PR을 만듭니다. 제목은 `chore(release): maymust <버전> dev 변경을 main 에 병합` 형식입니다.
3. **머지**: `/maymust:merge`가 통합 PR로 판정해 merge commit으로 머지하고 `dev`를 보존합니다. `main`에 새로 들어가는 코드가 이미 리뷰된 커밋뿐이면 리뷰 면제(`eligible`)를 승인하고 기록 코멘트를 남깁니다. 머지 전에 저장소의 merge queue와 head 브랜치 자동 삭제 설정이 꺼져 있는지도 확인합니다.
4. **안내**: 팀원에게 [업데이트](#2-업데이트) 명령을 안내합니다.

예: 0.8.0은 작업 PR #8을 `dev`에 squash 머지한 뒤, 릴리즈 PR #9로 `main`에 merge commit 머지해 배포했습니다.

공개 Codex 플러그인(`independent-review`, `resource-status-sheets`)의 버전은 각각의 `.codex-plugin/plugin.json`에서 SemVer로 따로 관리합니다.

## 8. 문제 해결

### 업데이트가 반영되지 않는다

1. 새 버전이 `main`에 릴리즈되었는지 확인합니다. `dev`에만 있는 변경은 받을 수 없습니다.
2. Claude에서 `marketplace update` 다음에 `claude plugin update maymust@maymust-ai-dev-playbook`까지 실행했는지 확인합니다.
3. 새 세션을 시작했는지 확인합니다. 갱신은 새 세션부터 적용됩니다.
4. 추적 브랜치가 `main`인지 확인합니다([1장](#추적-브랜치-확인과-main-전환)).

### Chat 탭에서 슬래시 명령이 거부된다

Chat 탭은 플러그인 스킬을 지원하지 않습니다. Desktop의 Code 탭이나 CLI에서 사용합니다.

### Codex에서 공통 지침이 적용되지 않는다

`/hooks`에서 maymust 훅을 신뢰했는지, Python 3가 설치되어 있는지 확인합니다. 훅을 쓸 수 없으면 `$maymust:team-defaults`를 직접 호출합니다.

### `codex-review`가 시작하지 않는다

- `codex login status`로 로그인 상태를 확인합니다.
- 수정을 커밋하는 루프(PR 모드, `--base`, `--commit`)라면 작업 트리가 깨끗한지 확인합니다. 미추적 파일도 막는 원인이 됩니다. 아직 커밋하지 않은 변경을 리뷰하려면 `--uncommitted`를, 수정 없이 한 번만 리뷰하려면 `--once`를 씁니다.
- 수정을 커밋하는 루프는 `dev`·`main` 같은 보호 브랜치가 아닌 작업 브랜치에서 실행합니다.
- PR 모드에서는 현재 브랜치가 PR head 브랜치이고, 로컬 HEAD가 원격 PR head와 같아야 합니다.

### 머지가 막힌다

- **리뷰 마커 없음 또는 오래됨**: 마커를 남긴 뒤 새 커밋이 생겼다면 `codex-review`를 다시 실행합니다.
- **통합 PR**: 면제 판정이 `eligible`이 아니면(`blocked`) 리뷰 루프를 진행합니다.
- **CI 실패·대기, 충돌**: 원인을 해결한 뒤 다시 시도합니다.
- **제목 규칙**: 요약이 동작 명사로 끝나지 않으면 머지 스킬이 정규화를 제안하거나 확인을 요청합니다.

### 워크트리에서 머지한 뒤 로컬 정리가 실패한다

`dev`가 다른 체크아웃(예: 메인 저장소 폴더)에 이미 체크아웃되어 있으면, 워크트리에서는 `git switch dev`를 할 수 없습니다. 이때는 메인 체크아웃에서 `git pull --ff-only`로 `dev`를 동기화하고, 작업 브랜치는 워크트리를 정리할 때 함께 지웁니다. 저장소 밖에서 `gh pr merge <N> -R MayMustAI/ai-dev-playbook ...`로 머지하면 gh가 로컬 브랜치 전환을 시도하지 않습니다.

### `dev`·`main`에서 커밋하려 하면 확인 창이 뜬다

branch-guard 훅의 의도된 동작입니다. 작업 브랜치를 만들어 커밋합니다.

### `/maymust:why`가 Notion·Slack·Linear를 조사하지 못했다

해당 MCP가 연결·인증되어 있어야 합니다. Claude Code에서는 `/mcp`나 claude.ai 커넥터 설정에서 인증합니다. 조사하지 못한 출처와 이유는 결과의 "조사한 출처"에 표시됩니다.

## 9. 플레이북 개발

### 저장소 구조와 런타임 구분

- Claude 전용 파일은 `.claude-plugin/`만 씁니다.
- Codex 전용 파일은 `.codex-plugin/`과 `.agents/plugins/`만 씁니다.
- `plugins/maymust/skills/`는 두 런타임이 함께 쓰는 단일 원본입니다. 공개 플러그인은 Codex 매니페스트만 제공합니다.
- 훅 설정은 분리되어 있습니다. Claude는 `hooks/hooks.json`, Codex는 `hooks/codex-hooks.json`을 읽습니다.

### 로컬에서 시험하기

저장소를 클론한 뒤 Claude Code를 `--plugin-dir`로 띄우면 설치하지 않고 시험할 수 있습니다.

```bash
git clone git@github.com:MayMustAI/ai-dev-playbook.git
cd ai-dev-playbook
claude --plugin-dir plugins/maymust
```

Claude 안에서 `/maymust:<스킬>`로 호출해 보고, 파일을 고친 뒤에는 `/reload-plugins`로 다시 불러옵니다. 설치된 버전에 없는 새 스킬도 이 방식으로 시험할 수 있습니다.

Codex는 로컬 사본을 마켓플레이스로 연결한 뒤(`codex plugin marketplace add /path/to/ai-dev-playbook`) 수정할 플러그인을 활성화합니다. `~/.codex/config.toml`에 직접 적을 때는 다음 형태를 씁니다. 로컬 소스는 개발용입니다. 팀 배포를 받으려면 [1장](#codex)의 Git 소스로 다시 등록합니다.

```toml
[marketplaces.maymust-ai-dev-playbook]
source_type = "local"
source = "/path/to/ai-dev-playbook"

[plugins."maymust@maymust-ai-dev-playbook"]
enabled = true

[plugins."independent-review@maymust-ai-dev-playbook"]
enabled = true

[plugins."resource-status-sheets@maymust-ai-dev-playbook"]
enabled = true
```

### 검증 명령

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
codex plugin list --marketplace maymust-ai-dev-playbook --available --json
python3 -B -m unittest discover -s plugins/resource-status-sheets/skills/resource-status-sheets/tests -v
python3 -B -m unittest discover -s plugins/maymust/skills/merge-loop-review-gate/tests -v
python3 -B -m unittest discover -s plugins/maymust/hooks/tests -v
python3 -B -m unittest discover -s scripts/tests -v
claude plugin validate plugins/maymust
```

현재 `quick_validate.py`는 Claude 전용 필드인 `disable-model-invocation`을 허용하지 않아서, 이 필드가 있는 스킬(`how`, `why`, Attention Span 스킬)은 `Unexpected key(s)`와 함께 실패(종료 코드 1)합니다. 이런 스킬은 Claude 플러그인 검증과 단위 테스트로 확인합니다. 검증을 통과시키려고 서드파티 원본(예: Attention Span 스킬)의 필드를 지우지 않습니다. Codex의 호출 정책은 각 스킬의 `agents/openai.yaml`에 따로 있습니다.

### 스킬을 추가하거나 고칠 때

- `skills/<이름>/SKILL.md`에 `name`, `description` frontmatter를 둡니다. Codex 표시 정보와 호출 정책은 `agents/openai.yaml`에 둡니다.
- 서브에이전트를 여러 개 띄우는 등 비용이 큰 스킬은 두 런타임 모두 명시 호출 전용으로 둡니다. Claude는 `disable-model-invocation: true`, Codex는 `policy.allow_implicit_invocation: false`입니다.
- Claude와 Codex가 같은 `skills/`를 쓰므로, 서브에이전트처럼 한쪽에만 있는 기능은 "쓸 수 있으면 병렬, 아니면 순서대로"처럼 선택 사항으로 씁니다.
- `team-defaults`의 `../` 링크 수는 테스트에 고정되어 있습니다(현재 7개). 링크를 더하거나 빼면 테스트도 함께 고칩니다.
- `maymust`의 codex 리뷰어 프롬프트와 `independent-review` loop-review의 리뷰어 프롬프트는 같은 파일로 유지합니다. 테스트가 두 파일의 일치를 검사합니다.

### 외부 자료를 들여올 때

| 방식 | 기준 | 기록 |
| --- | --- | --- |
| 원본 그대로 복사 | 내용이 자기 완결적일 때(Superpowers, Attention Span, Karpathy) | `third-party/skills.lock.json`의 `files`에 원본 경로와 sha256. 팀 조정은 `team-defaults`에 분리 |
| 수정해서 이식 | 원본이 다른 스킬·설정·런타임에 의존할 때(pstack) | lock의 `adapted`에 원본 경로와 원본 sha256, 각 파일 첫 줄에 출처 주석 |

두 방식 모두 고정 commit을 쓰고, 원본 라이선스를 `third-party/`에 보존하고, [THIRD_PARTY_NOTICES](../plugins/maymust/THIRD_PARTY_NOTICES.md)를 갱신합니다. 출처 기록은 테스트가 검사합니다.

### 업스트림 갱신 확인

저장소 루트에서 아래 명령을 실행하면, lock에 기록된 출처마다 최신 commit을 받아 파일 해시를 비교하고 결과를 JSON으로 출력합니다.

```bash
python3 scripts/check_upstream.py            # 비교만 합니다
python3 scripts/check_upstream.py --apply    # 안전한 출처만 파일과 lock을 갱신합니다
```

- `changed`가 `false`이면 갱신할 내용이 없습니다. 업스트림에 새 commit이 있어도 가져온 파일이 같으면 고정 commit을 바꾸지 않습니다.
- `--apply`는 추적하는 경로가 모두 남아 있고 라이선스 파일이 바뀌지 않은 출처만 갱신합니다. 경로가 사라졌거나(`missing`) 라이선스가 바뀌었으면 `blocked`에 이유를 적고 그 출처는 건드리지 않습니다. 업스트림에서 옮겨진 경로는 lock의 `upstream_path`를 손으로 고칩니다.
- 수정해서 이식한 자료(`adapted`)는 바뀌었다는 사실만 보고합니다. 바뀐 내용을 읽고 필요한 부분을 손으로 옮깁니다.
- 파일을 갱신했으면 THIRD_PARTY_NOTICES의 표와 버전 문구를 고치고, 세 매니페스트의 버전을 올리고, 단위 테스트를 실행합니다.

### 변경 반영 순서

작업 브랜치 → PR → 리뷰 → `dev`에 squash 머지 → 릴리즈 PR로 `main`에 merge commit 머지. 플레이북 자체의 스킬을 써서 진행합니다.
