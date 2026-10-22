# AI Dev Playbook

MayMust 팀의 AI 기반 개발 방식 — **우리는 이렇게 일합니다.**

이 레포는 MayMust 팀 컨벤션용 **Claude Code/Codex 플러그인**과 누구나 설치할 수 있는 범용 **Codex 플러그인**을 함께 배포합니다.

## 이 레포에 뭐가 있나

| 경로 | 내용 |
| --- | --- |
| `.claude-plugin/marketplace.json` | Claude Code 팀 내부 마켓플레이스 정의 |
| `.agents/plugins/marketplace.json` | Codex 마켓플레이스 정의 |
| `plugins/maymust/.claude-plugin/plugin.json` | Claude Code용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/.codex-plugin/plugin.json` | Codex용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/skills/` | 팀 워크플로우 7개 + 분석 스킬 4개(pstack에서 이식) + 공통 지침 1개 + 외부 스킬 6개 |
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
| [`/maymust:worklog`](plugins/maymust/skills/worklog/SKILL.md) | 작업당 한 장 worklog. `.worklogs/<date>-<branch>.md` 로 feature 브랜치에 커밋 → squash 시 main 에 자연 축적 |
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

같은 출처에서 self-review·codex 리뷰어의 테스트 판정 기준("동작을 깨면 실패하고 내부만 바꾸면 통과하는가")과 worklog의 근거 기록 규칙도 가져왔습니다. pstack의 PR·머지·자율 실행·워크트리 정리 단계는 팀의 PR·리뷰·머지 절차와 충돌하므로 가져오지 않았습니다.

## 설치 시 공통 작업 지침

`maymust` 0.8.0은 아래 스킬을 함께 배포합니다. SessionStart 훅이
[`team-defaults`](plugins/maymust/skills/team-defaults/SKILL.md)의 짧은 공통 지침과
설치된 원본 스킬 경로를 새 세션·재개·초기화·압축 후 컨텍스트에 전달합니다.
전체 원문은 필요한 단계에서 읽으며, 모든 스킬을 매 턴에 넣지 않습니다.

| 출처 / 스킬 | 기본 적용 |
| --- | --- |
| Superpowers / [`verification-before-completion`](plugins/maymust/skills/verification-before-completion/SKILL.md) | 완료·성공 보고 및 커밋·푸시·PR 전 실제 검증 결과 확인. **Superpowers의 다른 스킬·훅은 포함하지 않음** |
| Attention Span / [`attention-kind`](plugins/maymust/skills/attention-kind/SKILL.md) | 결과부터 간결하게 답하되 판단에 필요한 수치·조건·한계 유지 |
| Karpathy / [`karpathy-guidelines`](plugins/maymust/skills/karpathy-guidelines/SKILL.md) | 구현·리뷰·리팩터링 시 가정 명시, 단순한 구현, 최소 변경, 검증 가능한 목표 |
| pstack(이식) / [`benchmark-checklist`](plugins/maymust/skills/benchmark-checklist/SKILL.md) | 측정한 성능 수치를 보고하거나 그 수치로 결정하기 전 검증 |

Attention Span의 `spartan`·`rundown`은 사용자가 고르는 대체 응답 스타일,
`tldr`은 요청한 자료를 요약하는 선택형 스킬입니다. Claude에서는 제공된 native
output style도 선택할 수 있습니다. 사용자 언어·형식·선택한 스타일을 우선하고,
특정 진단을 가정하지 않으며, 간결함 때문에 승인된 작업을 덜 수행하지 않습니다.

자동 적용에는 **Python 3, 활성화된 플러그인과 SessionStart 훅**이 필요합니다.
Codex에서는 설치만으로 훅이 신뢰되지 않습니다. CLI의 `/hooks`에서 해당 플러그인의
훅을 검토·신뢰한 뒤 새 세션을 시작하세요. 훅 정의가 바뀌면 다시 검토해야 합니다.
훅을 사용할 수 없는 환경에서는 `maymust:team-defaults`를 명시적으로 호출합니다.
Claude 설치 후에는 `/reload-plugins`와 새 세션으로 적용을 확인합니다.

같은 플레이북 버전을 설치하면 같은 스킬 원문과 기본 지침을 받습니다.
이 지침은 모델 행동을 유도하며 실행을 강제로 보장하지 않습니다. CI와 현재 head의
리뷰·머지 게이트는 별도로 유지합니다. 검증 결과는 마지막 관련 변경 이후의 증거를
사용하고, 변화 없는 상태 보고마다 같은 검사를 반복하지 않습니다.

외부 원본은 commit SHA에 고정되어 설치 중 최신 `main`을 내려받지 않습니다.
Attention Span은 **AGPL-3.0**, 세 다른 소스는 MIT를 선언합니다. pstack 자료는
원본을 그대로 복사하지 않고 팀 흐름에 맞게 수정해 이식했으므로, lock 파일에 원본
파일 hash를 기록하고 각 파일 첫 줄에 원본 경로와 commit을 남깁니다. 원본 라이선스,
Karpathy 저장소의 별도 LICENSE 파일 부재, 팀 적용 변경점은
[`THIRD_PARTY_NOTICES.md`](plugins/maymust/THIRD_PARTY_NOTICES.md)에 기록합니다.

## 공개 Codex 스킬

공개 스킬은 사내 경로·저장소 규칙·Google Drive URL을 포함하지 않습니다. 사용자의 현재 저장소 컨벤션과 런타임 입력을 기준으로 동작합니다.

| 플러그인 / 스킬 | 역할 |
| --- | --- |
| [`independent-review:claude-review`](plugins/independent-review/skills/claude-review/SKILL.md) | 검증된 PR diff를 별도 Claude Code auto-mode 세션에서 읽기 전용으로 리뷰하고, 현재 Codex 세션이 blocker/must-fix를 검증해 최소 수정 |
| [`independent-review:loop-review`](plugins/independent-review/skills/loop-review/SKILL.md) | 새 `codex exec -s read-only` 리뷰어와 수정 루프를 돌려 blocker/must-fix 0까지 수렴 |
| [`resource-status-sheets:resource-status-sheets`](plugins/resource-status-sheets/skills/resource-status-sheets/SKILL.md) | 사용자 제공 DailyUpdates CSV·Google Sheets 템플릿·Drive 폴더로 팀원별 월별 현황표 생성 |

`resource-status-sheets`의 행 생성기는 고객사 추론을 기본 비활성화하며, `--customer-hint`가 있을 때만 명백한 고객명을 채웁니다. 템플릿/폴더 URL, 휴일, CSV 헤더, 근무지 매핑도 실행할 때 입력합니다.

반차의 `Note`·`TodaySummary`는 당일, `TomorrowPlan`은 다음 영업일에 적용하며 근무지 이동과 독립적입니다. XLSX 출력 시 빈 근무시간 수식, 줄바꿈과 행 높이를 검증합니다.

## 작동 환경

`maymust` 플러그인은 **터미널 계열 Claude** 와 **Codex 플러그인 환경** 에서 작동합니다. 두 공개 플러그인은 Codex 전용입니다.

| 환경 | 작동 | 호출 |
| --- | --- | --- |
| Claude Code CLI | ✅ | `/maymust:commit` 등 슬래시 명령 |
| Claude Desktop — **Code 탭** | ✅ | 동일 |
| Claude Desktop — **Chat 탭** | ❌ | 지원 안 됨 ("일부 명령어는 Claude Code 터미널에서만 작동" 에러) |
| Claude Desktop — **Remote 세션** | ❌ | 플러그인 자체가 로드되지 않음 |
| Codex | ✅ | `maymust:commit` 등 플러그인 스킬 |

공개 플러그인의 추가 요구사항:

- `independent-review`: Git, GitHub CLI, Codex CLI. `claude-review`에는 인증된 Claude Code CLI도 필요합니다.
- `resource-status-sheets`: Python 3와 사용 가능한 Google Drive/Google Sheets 커넥터가 필요합니다.

> 이유: 스킬이 `Bash` · `Edit` · `Read` 같은 파일시스템·셸 접근 도구를 쓰는데, Chat/Remote 환경은 이를 허용하지 않음.

## Claude/Codex 충돌 방지 설계

- Claude 전용 파일은 기존처럼 `.claude-plugin/` 만 사용합니다.
- Codex 전용 파일은 `.codex-plugin/` 과 `.agents/plugins/` 만 사용합니다.
- `plugins/maymust/skills/` 는 두 런타임이 공유하는 단일 원본입니다.
- 훅 설정은 분리되어 있습니다: Claude는 `hooks/hooks.json`, Codex는 `hooks/codex-hooks.json` 를 읽습니다.

## 설치

변경은 작업 PR로 `dev`에 먼저 머지되고, `dev` → `main` 릴리즈 PR이 머지된 뒤에 팀원에게 배포됩니다([릴리즈](#릴리즈-관리자)). 그래서 설치할 때 **`main` 브랜치를 지정**합니다. 브랜치를 지정하지 않으면 기본 브랜치인 `dev`의 릴리즈 전 변경을 받습니다.

### Claude Code (CLI · Desktop Code 탭)

터미널에서 실행합니다. Desktop Code 탭도 같은 플러그인 저장소(`~/.claude/plugins`)를 쓰므로 함께 적용됩니다.

```bash
claude plugin marketplace add 'MayMustAI/ai-dev-playbook#main'
claude plugin install maymust@maymust-ai-dev-playbook
```

설치한 뒤 새 세션을 시작합니다. Desktop의 Plugins UI(`+` → **Plugins** → **Manage plugins**)로도 추가할 수 있지만, 브랜치가 확실히 지정되도록 위 터미널 명령을 권장합니다.

설치 후 **반드시 Code 탭에서 사용** — Chat 탭에서는 슬래시 명령이 거부됩니다.

### Codex

```bash
codex plugin marketplace add MayMustAI/ai-dev-playbook --ref main
codex plugin add maymust@maymust-ai-dev-playbook
```

그 뒤 필요한 플러그인만 활성화합니다.

- `maymust`: MayMust 팀 컨벤션과 공통 작업 지침 (세션 훅은 별도 검토·신뢰)
- `independent-review`: 범용 독립 코드 리뷰
- `resource-status-sheets`: 범용 월별 리소스 현황표

### 추적 브랜치 확인과 `main` 전환

예전 안내대로 브랜치 없이 추가했다면 `dev`를 추적하고 있을 수 있습니다.

- **Claude**: `claude plugin marketplace list`의 Source가 `MayMustAI/ai-dev-playbook@main`인지 확인합니다. `@main`이 없으면 마켓플레이스를 다시 추가합니다. 마켓플레이스를 제거하면 그 마켓플레이스에서 설치한 플러그인도 함께 제거되므로 재설치까지 진행합니다.

  ```bash
  claude plugin marketplace remove maymust-ai-dev-playbook
  claude plugin marketplace add 'MayMustAI/ai-dev-playbook#main'
  claude plugin install maymust@maymust-ai-dev-playbook
  ```

- **Codex**: `~/.codex/config.toml`의 `[marketplaces.maymust-ai-dev-playbook]`에 `ref = "main"`이 있는지 확인합니다. 없으면 그 줄을 추가한 뒤 [업데이트](#업데이트) 명령을 실행합니다.

### 로컬 개발용 연결 (Codex)

플러그인을 수정하면서 로컬 사본을 직접 연결할 때는 경로를 마켓플레이스로 추가하거나(`codex plugin marketplace add /path/to/ai-dev-playbook`), `~/.codex/config.toml` 에 다음 형태로 추가합니다:

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

## 일하는 흐름 (스킬이 엮이는 방식)

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

## 업데이트

새 버전은 `main`에 릴리즈된 뒤에 받을 수 있습니다. 릴리즈 후 각 PC에서 다음을 실행하고 새 세션을 시작합니다.

**Claude Code (CLI · Desktop Code 탭)**:

```bash
claude plugin marketplace update maymust-ai-dev-playbook
claude plugin update maymust@maymust-ai-dev-playbook
```

`marketplace update`는 마켓플레이스 사본만 갱신합니다. 설치된 플러그인 버전은 `plugin update`까지 실행해야 올라갑니다. 버전은 `claude plugin list`로 확인합니다.

**Codex**:

```bash
codex plugin marketplace upgrade maymust-ai-dev-playbook
codex plugin add maymust@maymust-ai-dev-playbook
```

버전은 `codex plugin list -m maymust-ai-dev-playbook`로 확인합니다. 훅 정의(`hooks/codex-hooks.json`)가 바뀐 버전이면 새 세션의 `/hooks`에서 다시 검토·신뢰합니다.

### 릴리즈 (관리자)

1. 작업 PR이 `dev`에 머지된 상태에서 `/maymust:pull-request`로 base `main`, head `dev`인 릴리즈 PR을 만듭니다. 제목은 `chore(release): maymust <버전> dev 변경을 main 에 병합` 형식입니다.
2. `/maymust:merge`로 머지합니다. 장기 브랜치끼리의 통합 PR이므로 merge commit으로 머지하고 `dev`를 보존합니다. 이미 리뷰된 커밋만 담겼으면 사용자 승인으로 리뷰를 면제합니다.
3. 팀원에게 위 업데이트 명령을 안내합니다.

> `maymust` 버전은 Claude 마켓플레이스와 두 런타임의 plugin.json에서 함께 갱신합니다. 두 런타임 모두 버전별로 설치본을 구분하므로 릴리즈마다 버전을 올립니다. 공개 Codex 플러그인 버전은 각각의 `.codex-plugin/plugin.json`에서 SemVer로 관리합니다.

## 개발 — 스킬 수정 시

레포를 로컬에 클론한 뒤, Claude Code 를 `--plugin-dir` 로 띄우면 설치 없이 실험 가능:

```bash
git clone git@github.com:MayMustAI/ai-dev-playbook.git
cd ai-dev-playbook
claude --plugin-dir plugins/maymust
# Claude 내에서: /maymust:<skill> 호출 확인
# 파일 수정 후: /reload-plugins
```

Codex는 이 레포를 로컬 마켓플레이스로 연결한 뒤 수정 대상 플러그인을 활성화해서 확인합니다. `maymust`의 Claude와 Codex는 같은 `skills/`를 공유하고, 공개 플러그인은 Codex 플러그인 매니페스트만 제공합니다.

검증 명령:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
codex plugin list --marketplace maymust-ai-dev-playbook --available --json
python3 -B -m unittest discover -s plugins/resource-status-sheets/skills/resource-status-sheets/tests -v
python3 -B -m unittest discover -s plugins/maymust/skills/merge-loop-review-gate/tests -v
python3 -B -m unittest discover -s plugins/maymust/hooks/tests -v
claude plugin validate plugins/maymust
```

Attention Span 원본의 `disable-model-invocation`은 Claude용 지원 필드이며 그대로
보존합니다. Codex의 선택형 호출 정책은 각 스킬의 `agents/openai.yaml`에 있습니다.
`quick_validate.py`가 이 Claude 필드를 허용하지 않는 버전이라면 원본을 수정하지
말고 Claude 플러그인 검증과 배포 파일 hash·훅 테스트로 함께 확인합니다.

변경은 브랜치 → PR → 리뷰 → **squash merge** (자체 스킬을 써서 도그푸딩).
