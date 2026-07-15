# AI Dev Playbook

MayMust 팀의 AI 기반 개발 방식 — **우리는 이렇게 일합니다.**

이 레포는 **Claude Code 플러그인** 과 **Codex 플러그인** 으로 배포되어, 팀원 전체가 동일한 팀 컨벤션 기반 스킬을 씁니다.

## 이 레포에 뭐가 있나

| 경로 | 내용 |
| --- | --- |
| `.claude-plugin/marketplace.json` | Claude Code 팀 내부 마켓플레이스 정의 |
| `.agents/plugins/marketplace.json` | Codex 팀 내부 마켓플레이스 정의 |
| `plugins/maymust/.claude-plugin/plugin.json` | Claude Code용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/.codex-plugin/plugin.json` | Codex용 `maymust` 플러그인 매니페스트 |
| `plugins/maymust/skills/` | 5개 팀 공용 스킬 (아래 표) |
| `plugins/maymust/hooks/` | Claude/Codex별 팀 가드 훅 (dev·main 직접 커밋 시 사용자 확인) |

## 스킬 목록

| 호출 | 역할 |
| --- | --- |
| [`/maymust:commit`](plugins/maymust/skills/commit/SKILL.md) | 스테이지된 변경을 팀 컨벤션(Conventional Commits · 한글 본문) 으로 커밋. `meaningful` / `wip` 2 모드 |
| [`/maymust:pull-request`](plugins/maymust/skills/pull-request/SKILL.md) | 듀얼 오디언스(사람 30초 스캔 + AI claim 검증) 구조의 PR 생성. 5단계 루프 대화형 확인 |
| [`/maymust:merge`](plugins/maymust/skills/merge/SKILL.md) | squash-merge + 게이트(작성자·리뷰·mergeable·CI·명사형 제목). `(#PR)` 접미사와 Self-verification/Screenshots 스트립을 강제하고, 머지 후 dev 동기화·feature 브랜치 정리 |
| [`/maymust:worklog`](plugins/maymust/skills/worklog/SKILL.md) | 작업당 한 장 worklog. `.worklogs/<date>-<branch>.md` 로 feature 브랜치에 커밋 → squash 시 main 에 자연 축적 |
| [`/maymust:self-review`](plugins/maymust/skills/self-review/SKILL.md) | 5단계 루프 step 2. PR 본문의 의도(Why/Design decisions) vs 구현(diff) 매칭 렌즈로 구조화 리뷰. 세션 편향 경고 내장 |

## 작동 환경

이 플러그인은 **터미널 계열 Claude** 와 **Codex 플러그인 환경** 에서 작동합니다.

| 환경 | 작동 | 호출 |
| --- | --- | --- |
| Claude Code CLI | ✅ | `/maymust:commit` 등 슬래시 명령 |
| Claude Desktop — **Code 탭** | ✅ | 동일 |
| Claude Desktop — **Chat 탭** | ❌ | 지원 안 됨 ("일부 명령어는 Claude Code 터미널에서만 작동" 에러) |
| Claude Desktop — **Remote 세션** | ❌ | 플러그인 자체가 로드되지 않음 |
| Codex | ✅ | `maymust:commit` 등 플러그인 스킬 |

> 이유: 스킬이 `Bash` · `Edit` · `Read` 같은 파일시스템·셸 접근 도구를 쓰는데, Chat/Remote 환경은 이를 허용하지 않음.

## Claude/Codex 충돌 방지 설계

- Claude 전용 파일은 기존처럼 `.claude-plugin/` 만 사용합니다.
- Codex 전용 파일은 `.codex-plugin/` 과 `.agents/plugins/` 만 사용합니다.
- `plugins/maymust/skills/` 는 두 런타임이 공유하는 단일 원본입니다.
- 훅 설정은 분리되어 있습니다: Claude는 `hooks/hooks.json`, Codex는 `hooks/codex-hooks.json` 를 읽습니다.

## 설치 — 팀원용

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
```

그 뒤 `maymust` 플러그인을 활성화합니다.

로컬 설정으로 직접 연결할 때는 `~/.codex/config.toml` 에 다음 형태로 추가합니다:

```toml
[marketplaces.maymust-ai-dev-playbook]
source_type = "local"
source = "/path/to/ai-dev-playbook"

[plugins."maymust@maymust-ai-dev-playbook"]
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
3. /maymust:self-review        ← (/clear 후 권장) 처음 보는 것처럼 리뷰
4. /maymust:pull-request       ← 5단계 루프 대화형 확인 후 PR 생성
5. (동료 리뷰 — 사람)
6. /maymust:merge              ← 게이트 통과 후 squash merge + 정리
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
```

> Claude 버전은 `.claude-plugin/marketplace.json` 의 `plugins[0].version`, Codex 버전은 `plugins/maymust/.codex-plugin/plugin.json` 의 `version` 에서 관리합니다 (SemVer). 현재: Claude **0.3.1**, Codex **0.3.2**.

## 개발 — 스킬 수정 시

레포를 로컬에 클론한 뒤, Claude Code 를 `--plugin-dir` 로 띄우면 설치 없이 실험 가능:

```bash
git clone git@github.com:MayMustAI/ai-dev-playbook.git
cd ai-dev-playbook
claude --plugin-dir .
# Claude 내에서: /maymust:<skill> 호출 확인
# 파일 수정 후: /reload-plugins
```

Codex는 이 레포를 로컬 마켓플레이스로 연결한 뒤 `maymust` 플러그인을 활성화해서 확인합니다. Claude와 Codex가 같은 `skills/` 를 읽기 때문에 스킬 본문을 수정하면 두 환경에 함께 반영됩니다.

변경은 브랜치 → PR → 리뷰 → **squash merge** (자체 스킬을 써서 도그푸딩).
