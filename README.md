# AI Dev Playbook

MayMust 팀의 AI 기반 개발 방식 — **우리는 이렇게 일합니다.**

이 레포는 **Claude Code 플러그인** 으로 배포되어, 팀원 전체가 동일한 `/commit` · `/pull-request` 스킬을 씁니다. 그리고 장기적으로는 팀 개발 방법론을 담는 플레이북 레포로 확장됩니다.

## 이 레포에 뭐가 있나

| 경로 | 내용 |
| --- | --- |
| `.claude-plugin/plugin.json` | 플러그인 매니페스트 |
| `.claude-plugin/marketplace.json` | 팀 내부 마켓플레이스 정의 |
| `skills/commit/` | `/maymust:commit` 스킬 |
| `skills/pull-request/` | `/maymust:pull-request` 스킬 |
| `playbook/` | 팀 개발 방법론 문서 (작성 예정) |
| `templates/` | PR · Worklog 등 공용 템플릿 (작성 예정) |

## 설치 — 팀원용

Claude Code 에서 다음 세 줄:

```
/plugin marketplace add MayMustAI/ai-dev-playbook
/plugin install maymust@maymust-ai-dev-playbook
/reload-plugins
```

Private 레포 인증은 로컬의 `gh auth` 설정을 자동으로 사용합니다. 미리 `gh auth login` 으로 `MayMustAI` 조직 접근 권한이 있는지 확인해 주세요.

## 사용법

플러그인 배포 후에는 스킬 호출 시 **`maymust:` 네임스페이스** 가 붙습니다:

```
/maymust:commit              # 스테이지된 변경을 팀 컨벤션으로 커밋
/maymust:commit wip          # WIP 모드 강제
/maymust:pull-request        # 현재 브랜치로 PR 생성
```

자세한 동작은 각 스킬 파일 참고:

- [skills/commit/SKILL.md](skills/commit/SKILL.md) — 커밋 컨벤션과 워크플로우
- [skills/pull-request/SKILL.md](skills/pull-request/SKILL.md) — PR 본문 구조와 5단계 루프

## 업데이트

레포가 업데이트되면 팀원은 다음으로 받아옵니다:

```
/plugin marketplace update maymust-ai-dev-playbook
/reload-plugins
```

> 버전은 `.claude-plugin/plugin.json` 의 `version` 필드에서 관리합니다 (SemVer).

## 개발 — 스킬 수정 시

레포를 로컬에 클론한 뒤, Claude Code 를 `--plugin-dir` 로 띄우면 설치 없이 실험 가능:

```bash
git clone git@github.com:MayMustAI/ai-dev-playbook.git
cd ai-dev-playbook
claude --plugin-dir .
# Claude 내에서: /maymust:commit 호출이 로드되는지 확인
# 파일 수정 후: /reload-plugins
```

변경은 브랜치 → PR → 리뷰 → **squash merge** (`/maymust:pull-request` 자체를 써서 이 흐름 자체를 도그푸딩).

## 상태

- [x] 레포 초기 구조
- [x] `commit` 스킬 정의
- [x] `pull-request` 스킬 정의
- [x] Claude Code 플러그인 패키징
- [ ] `playbook/` 문서 (발표 자료 기반)
- [ ] 팀 배포 완료 검증
