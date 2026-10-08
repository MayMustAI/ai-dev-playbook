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
| `plugins/maymust/skills/` | 팀 워크플로우 7개 + 공통 지침 1개 + 외부 스킬 6개 |
| `plugins/maymust/hooks/` | 세션 시작 공통 지침 주입 및 Claude/Codex별 보호 브랜치 가드 |
| `plugins/maymust/third-party/` | 외부 스킬의 고정 commit·파일 hash·원본 라이선스 |
| `plugins/independent-review/` | 범용 독립 리뷰 플러그인 (`claude-review`, `loop-review`) |
| `plugins/resource-status-sheets/` | DailyUpdates CSV 기반 월별 리소스 현황표 플러그인 |

## MayMust 팀 스킬

| 호출 | 역할 |
| --- | --- |
| [`/maymust:commit`](plugins/maymust/skills/commit/SKILL.md) | 스테이지된 변경을 팀 컨벤션(Conventional Commits · 한글 본문) 으로 커밋. `meaningful` / `wip` 2 모드 |
| [`/maymust:pull-request`](plugins/maymust/skills/pull-request/SKILL.md) | 듀얼 오디언스(사람 30초 스캔 + AI claim 검증) 구조의 PR 생성. 5단계 루프 대화형 확인 |
| [`/maymust:merge`](plugins/maymust/skills/merge/SKILL.md) | squash-merge + 게이트(작성자·리뷰·mergeable·CI·명사형 제목). `(#PR)` 접미사와 Self-verification/Screenshots 스트립을 강제하고, 머지 후 dev 동기화·feature 브랜치 정리 |
| [`/maymust:worklog`](plugins/maymust/skills/worklog/SKILL.md) | 작업당 한 장 worklog. `.worklogs/<date>-<branch>.md` 로 feature 브랜치에 커밋 → squash 시 main 에 자연 축적 |
| [`/maymust:self-review`](plugins/maymust/skills/self-review/SKILL.md) | 5단계 루프 step 2. PR 본문의 의도(Why/Design decisions) vs 구현(diff) 매칭 렌즈로 구조화 리뷰. 세션 편향 경고 내장 |
| [`/maymust:codex-review`](plugins/maymust/skills/codex-review/SKILL.md) | 새 읽기 전용 Codex 세션의 리뷰·최소 수정·재리뷰 루프. PR 통과 시 실제 리뷰한 head SHA에 연결된 마커 생성 |
| [`/maymust:merge-loop-review-gate`](plugins/maymust/skills/merge-loop-review-gate/SKILL.md) | 머지 전 현재 PR head의 독립 리뷰 통과 마커를 확인. 누락·오래된 마커는 머지 차단 |

## 설치 시 공통 작업 지침

`maymust` 0.6.0은 아래 스킬을 함께 배포합니다. SessionStart 훅이
[`team-defaults`](plugins/maymust/skills/team-defaults/SKILL.md)의 짧은 공통 지침과
설치된 원본 스킬 경로를 새 세션·재개·초기화·압축 후 컨텍스트에 전달합니다.
전체 원문은 필요한 단계에서 읽으며, 모든 스킬을 매 턴에 넣지 않습니다.

| 출처 / 스킬 | 기본 적용 |
| --- | --- |
| Superpowers / [`verification-before-completion`](plugins/maymust/skills/verification-before-completion/SKILL.md) | 완료·성공 보고 및 커밋·푸시·PR 전 실제 검증 결과 확인. **Superpowers의 다른 스킬·훅은 포함하지 않음** |
| Attention Span / [`attention-kind`](plugins/maymust/skills/attention-kind/SKILL.md) | 결과부터 간결하게 답하되 판단에 필요한 수치·조건·한계 유지 |
| Karpathy / [`karpathy-guidelines`](plugins/maymust/skills/karpathy-guidelines/SKILL.md) | 구현·리뷰·리팩터링 시 가정 명시, 단순한 구현, 최소 변경, 검증 가능한 목표 |

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
Attention Span은 **AGPL-3.0**, 두 다른 소스는 MIT를 선언합니다. 원본 라이선스,
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

### Claude Code CLI

```
/plugin marketplace add MayMustAI/ai-dev-playbook
/plugin install maymust@maymust-ai-dev-playbook
/reload-plugins
```

### Claude Desktop (Code 탭)

프롬프트 박스 옆 `+` 버튼 → **Plugins** → **Manage plugins** → **Add plugin** 으로 마켓플레이스 `MayMustAI/ai-dev-playbook` 추가한 뒤 `maymust` 플러그인 설치.

설치 후 **반드시 Code 탭에서 사용** — Chat 탭에서는 슬래시 명령이 거부됩니다.

### Codex

Codex 앱의 Plugins UI에서 이 레포를 로컬 마켓플레이스로 추가하거나, CLI에서 다음을 실행합니다:

```bash
codex plugin marketplace add /path/to/ai-dev-playbook
codex plugin add maymust@maymust-ai-dev-playbook
```

그 뒤 필요한 플러그인만 활성화합니다.

- `maymust`: MayMust 팀 컨벤션과 공통 작업 지침 (세션 훅은 별도 검토·신뢰)
- `independent-review`: 범용 독립 코드 리뷰
- `resource-status-sheets`: 범용 월별 리소스 현황표

로컬 설정으로 직접 연결할 때는 `~/.codex/config.toml` 에 다음 형태로 추가합니다:

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
   (작업 진행)
   /maymust:worklog log "..."  ← 중간 로그
   /maymust:commit [wip]       ← 중간 커밋
   ...
2. /maymust:worklog finish     ← 작업 종료, PR 본문 요약 생성
3. /maymust:pull-request       ← 검증 상태를 솔직하게 기록하여 PR 생성; 미완료 UI 증거는 draft
4. /maymust:self-review        ← (/clear 후 권장) PR의 의도와 구현 리뷰
5. /maymust:codex-review <PR>  ← 독립 리뷰·수정 루프, 현재 head에 통과 마커 생성
6. (동료 리뷰 — 사람)
7. /maymust:merge              ← 현재 head 리뷰 마커 + 팀 게이트 확인 후 squash merge + 정리
```

## 업데이트

레포가 업데이트되면 팀원은 다음으로 받아옵니다.

**CLI**:
```
/plugin marketplace update maymust-ai-dev-playbook
/reload-plugins
```

**Desktop (Code 탭)**: Plugins UI 에서 마켓플레이스 자동 업데이트, 또는 수동 "Refresh".

**Codex**:
```bash
codex plugin marketplace upgrade maymust-ai-dev-playbook
codex plugin add maymust@maymust-ai-dev-playbook
```

> `maymust` 버전은 Claude 마켓플레이스와 두 런타임의 plugin.json에서 함께 갱신합니다. 공개 Codex 플러그인 버전은 각각의 `.codex-plugin/plugin.json`에서 SemVer로 관리합니다.

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
