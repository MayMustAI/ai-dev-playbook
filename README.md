# AI Dev Playbook

MayMust 팀의 AI 기반 개발 방식 — **우리는 이렇게 일합니다.**

이 레포는 MayMust 팀 컨벤션용 **Claude Code/Codex 플러그인**과 누구나 설치할 수 있는 범용 **Codex 플러그인**을 함께 배포합니다. 설치, 일하는 흐름, 스킬별 사용법, 문제 해결은 **[매뉴얼](docs/MANUAL.md)**에 정리되어 있습니다.

## 이 레포에 뭐가 있나

| 경로 | 내용 |
| --- | --- |
| `docs/MANUAL.md` | 설치·업데이트·일하는 흐름·스킬 레퍼런스·문제 해결·플레이북 개발 매뉴얼 |
| `.claude-plugin/marketplace.json` | Claude Code 팀 내부 마켓플레이스 정의 |
| `.agents/plugins/marketplace.json` | Codex 마켓플레이스 정의 |
| `plugins/maymust/.claude-plugin/plugin.json` | Claude Code용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/.codex-plugin/plugin.json` | Codex용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/skills/` | 팀 워크플로우 7개 + 분석 스킬 4개(pstack에서 이식) + 발표 점검 1개 + 공통 지침 1개 + 외부 스킬 6개 |
| `plugins/maymust/hooks/` | 세션 시작 공통 지침 주입 및 Claude/Codex별 보호 브랜치 가드 |
| `plugins/maymust/third-party/` | 외부 스킬의 고정 commit·파일 hash·원본 라이선스 |
| `plugins/independent-review/` | 범용 독립 리뷰 플러그인 (`claude-review`, `loop-review`) |
| `plugins/resource-status-sheets/` | DailyUpdates CSV 기반 월별 리소스 현황표 플러그인 |

## MayMust 팀 스킬

| 호출 | 역할 |
| --- | --- |
| [`/maymust:commit`](plugins/maymust/skills/commit/SKILL.md) | 스테이지된 변경을 팀 컨벤션(Conventional Commits · 한글 본문) 으로 커밋. `meaningful` / `wip` 2 모드 |
| [`/maymust:pull-request`](plugins/maymust/skills/pull-request/SKILL.md) | 듀얼 오디언스(사람 30초 스캔 + AI claim 검증) 구조의 PR 생성. 5단계 루프 대화형 확인 |
| [`/maymust:merge`](plugins/maymust/skills/merge/SKILL.md) | 작업 PR은 squash, 장기 브랜치끼리 합치는 통합 PR은 merge commit으로 판정해 머지 + 게이트(작성자·리뷰·mergeable·CI·명사형 제목). `(#PR)` 접미사와 Self-verification/Screenshots 스트립을 강제하고, 머지 후 base 동기화·작업 브랜치 정리(장기 브랜치는 보존) |
| [`/maymust:self-review`](plugins/maymust/skills/self-review/SKILL.md) | 5단계 루프 step 2. PR 본문의 의도(Why/Design decisions) vs 구현(diff) 매칭 렌즈로 구조화 리뷰. 세션 편향 경고 내장 |
| [`/maymust:codex-review`](plugins/maymust/skills/codex-review/SKILL.md) | 새 읽기 전용 Codex 세션의 리뷰·최소 수정·재리뷰 루프. PR 통과 시 실제 리뷰한 head SHA에 연결된 마커 생성 |
| [`/maymust:merge-loop-review-gate`](plugins/maymust/skills/merge-loop-review-gate/SKILL.md) | 머지 전 현재 PR head의 독립 리뷰 통과 마커를 확인. 누락·오래된 마커는 머지 차단. 이미 리뷰된 커밋만 담긴 통합 PR은 사용자 승인으로 면제 |

## 분석 스킬 (pstack에서 이식)

[pstack](https://github.com/cursor/plugins/tree/main/pstack)의 방법론 중 팀 흐름과 충돌하지 않는 부분을 고정 commit 기준으로 옮겨 왔습니다. pstack 자체는 설치하지 않으며, Claude Code와 Codex에서 같은 스킬을 씁니다.

| 호출 | 역할 |
| --- | --- |
| [`/maymust:blast-radius`](plugins/maymust/skills/blast-radius/SKILL.md) | 변경이 diff 밖에서 깨뜨릴 수 있는 것을 찾고, 안전 근거가 되는 사실 하나를 실행으로 증명. 결과는 PR의 Design decisions·Review focus로 연결 |
| [`/maymust:benchmark-checklist`](plugins/maymust/skills/benchmark-checklist/SKILL.md) | 성능 수치를 보고하거나 그 수치로 결정하기 전에 7개 질문(한계 요인·튜닝·물리적 한계·오류·재현성·전체 비중·실제 실행)으로 검증 |
| [`/maymust:how`](plugins/maymust/skills/how/SKILL.md) | 코드·서브시스템 동작을 관점별로 탐색해 설명. 서브에이전트를 여러 개 띄우므로 명시 호출 전용 |
| [`/maymust:why`](plugins/maymust/skills/why/SKILL.md) | 코드가 왜 이렇게 만들어졌는지 git·PR·Linear·Notion·Slack 근거를 출처별로 읽기 전용 조사. 확인된 사실과 추론을 구분. 명시 호출 전용 |

같은 출처에서 self-review·codex 리뷰어의 테스트 판정 기준("동작을 깨면 실패하고 내부만 바꾸면 통과하는가")과 PR 본문 Design decisions의 근거 기록 규칙도 가져왔습니다. pstack의 PR·머지·자율 실행·워크트리 정리 단계는 팀의 PR·리뷰·머지 절차와 충돌하므로 가져오지 않았습니다.

## 발표 자료 점검

| 호출 | 역할 |
| --- | --- |
| [`/maymust:glance-test`](plugins/maymust/skills/glance-test/SKILL.md) | 발표 슬라이드가 3초 안에 핵심 메시지 하나를 전하는지 장별로 점검(글랜스 테스트). 덱을 발표 크기 이미지로 렌더링하고, 내용을 모르는 검토자의 판독을 의도와 대조해 실패 원인과 고칠 방향을 보고. 명시 호출 전용 |

## 공통 작업 지침

`maymust`를 설치하면 세션 시작 훅이 새 세션·재개·초기화·압축 직후마다 [`team-defaults`](plugins/maymust/skills/team-defaults/SKILL.md)의 짧은 공통 지침을 적용합니다. 결과부터 간결하게 답하고(Attention-kind), 요청 범위만 최소로 바꾸고(Karpathy Guidelines), 완료를 주장하기 전에 실제 검증 결과를 확인합니다(verification-before-completion). 측정한 성능 수치는 benchmark-checklist로 점검합니다. 응답 스타일 바꾸기와 자세한 내용은 [매뉴얼 3장](docs/MANUAL.md#3-세션마다-적용되는-공통-지침)을 참고합니다.

외부 원본은 commit SHA에 고정되어 설치 중 최신 `main`을 내려받지 않습니다. Attention Span은 **AGPL-3.0**, 세 다른 소스는 MIT를 선언합니다. pstack 자료는 원본을 그대로 복사하지 않고 팀 흐름에 맞게 수정해 이식했습니다. 원본 라이선스, Karpathy 저장소의 별도 LICENSE 파일 부재, 팀 적용 변경점은 [`THIRD_PARTY_NOTICES.md`](plugins/maymust/THIRD_PARTY_NOTICES.md)에 기록합니다.

## 공개 Codex 스킬

공개 스킬은 사내 경로·저장소 규칙·Google Drive URL을 포함하지 않습니다. 사용자의 현재 저장소 컨벤션과 런타임 입력을 기준으로 동작합니다. 필요 조건과 동작 세부 사항은 [매뉴얼 5장](docs/MANUAL.md#공개-codex-플러그인)에 있습니다.

| 플러그인 / 스킬 | 역할 |
| --- | --- |
| [`independent-review:claude-review`](plugins/independent-review/skills/claude-review/SKILL.md) | 검증된 PR diff를 별도 Claude Code auto-mode 세션에서 읽기 전용으로 리뷰하고, 현재 Codex 세션이 blocker/must-fix를 검증해 최소 수정 |
| [`independent-review:loop-review`](plugins/independent-review/skills/loop-review/SKILL.md) | 새 `codex exec -s read-only` 리뷰어와 수정 루프를 돌려 blocker/must-fix 0까지 수렴 |
| [`resource-status-sheets:resource-status-sheets`](plugins/resource-status-sheets/skills/resource-status-sheets/SKILL.md) | 사용자 제공 DailyUpdates CSV·Google Sheets 템플릿·Drive 폴더로 팀원별 월별 현황표 생성 |

## 설치

변경은 작업 PR로 `dev`에 먼저 머지되고, `dev` → `main` 릴리즈 PR이 머지된 뒤에 팀원에게 배포됩니다. 그래서 설치할 때 **`main` 브랜치를 지정**합니다.

**Claude Code (CLI · Desktop Code 탭)**: 터미널에서 실행하면 Desktop Code 탭에도 적용됩니다.

```bash
claude plugin marketplace add 'MayMustAI/ai-dev-playbook#main'
claude plugin install maymust@maymust-ai-dev-playbook
```

**Codex**: 설치 후 새 세션의 `/hooks`에서 maymust 훅을 검토·신뢰합니다.

```bash
codex plugin marketplace add MayMustAI/ai-dev-playbook --ref main
codex plugin add maymust@maymust-ai-dev-playbook
```

Claude Code CLI·Desktop Code 탭·Codex에서 작동하고, Desktop의 Chat 탭과 Remote 세션에서는 작동하지 않습니다. 요구 사항, 설치 확인, 예전 안내로 설치해 `dev`를 추적하는 경우의 `main` 전환은 [매뉴얼 1장](docs/MANUAL.md#1-설치)을 참고합니다.

## 일하는 흐름 (스킬이 엮이는 방식)

```
1. git switch -c <branch>      ← 작업 브랜치 생성 (base: origin/dev)
   /maymust:how · /maymust:why ← (필요할 때) 코드 동작과 설계 이유 조사
   (작업 진행)
   /maymust:commit [wip]       ← 중간 커밋 (방향을 바꾼 판단은 본문에 이유를)
   /maymust:benchmark-checklist ← (성능 수치를 다룰 때) 측정 검증
   ...
2. /maymust:blast-radius       ← (영향이 넓은 변경) 영향 범위 점검과 안전 근거 증명
3. /maymust:pull-request       ← 설계 판단은 근거와 함께, 검증 상태는 솔직하게 기록하여 PR 생성; 미완료 UI 증거는 draft
4. /maymust:self-review        ← (/clear 후 권장) PR의 의도와 구현 리뷰
5. /maymust:codex-review <PR>  ← 독립 리뷰·수정 루프, 현재 head에 통과 마커 생성
6. (동료 리뷰 — 사람)
7. /maymust:merge              ← 현재 head 리뷰 마커 + 팀 게이트 확인 후 squash(통합 PR은 merge commit) + 정리
8. (릴리즈) dev → main PR      ← /maymust:pull-request(base main) → /maymust:merge(merge commit, dev 보존) → 팀원 업데이트
```

단계별 설명은 [매뉴얼 4장](docs/MANUAL.md#4-일하는-흐름)에 있습니다.

## 업데이트

새 버전은 `main`에 릴리즈된 뒤에 받을 수 있습니다. 릴리즈 후 각 PC에서 다음을 실행하고 새 세션을 시작합니다.

**Claude Code (CLI · Desktop Code 탭)**: `marketplace update`는 마켓플레이스 사본만 갱신하므로 `plugin update`까지 실행해야 설치 버전이 올라갑니다.

```bash
claude plugin marketplace update maymust-ai-dev-playbook
claude plugin update maymust@maymust-ai-dev-playbook
```

**Codex**:

```bash
codex plugin marketplace upgrade maymust-ai-dev-playbook
codex plugin add maymust@maymust-ai-dev-playbook
```

릴리즈 절차는 [매뉴얼 7장](docs/MANUAL.md#7-릴리즈-관리자), 업데이트가 반영되지 않을 때의 점검 순서는 [매뉴얼 8장](docs/MANUAL.md#8-문제-해결)에 있습니다.

## 개발

스킬을 고치거나 추가하는 방법, 로컬 시험, 검증 명령, 외부 자료를 들여오는 규칙은 [매뉴얼 9장](docs/MANUAL.md#9-플레이북-개발)에 있습니다. 변경은 브랜치 → PR → 리뷰 → **squash merge**(자체 스킬을 써서 도그푸딩)로 `dev`에 반영하고, 배포는 `dev` → `main` 릴리즈 PR로 합니다.
