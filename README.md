# AI Dev Playbook

MayMust 팀의 AI 기반 개발 방식 — **우리는 이렇게 일합니다.**

발표 자료 "AI 개발 워크플로우" 를 실제 팀 자산으로 옮겨둔 곳입니다.
공용 Claude Code 스킬, 팀 개발 플레이북 문서, 공용 템플릿을 한 곳에서 관리합니다.

## 이 레포에 뭐가 있나

| 디렉터리 | 내용 |
| --- | --- |
| `.claude/skills/` | 팀 공용 Claude Code 스킬. 현재: `commit`, `pull-request` |
| `playbook/` | 팀 개발 방법론 문서 (Git · 플래닝 · 셀프 리뷰 · 동료 리뷰 · 스프린트) |
| `templates/` | PR · Worklog 등 공용 템플릿 |

## 공용 스킬 사용법

> 배포 방식(플러그인 vs 심링크 vs 복사)은 팀과 결정 후 확정합니다. 이 섹션은 그때 업데이트됩니다.

임시 가이드:
1. 이 레포를 로컬에 클론
2. 사용할 프로젝트의 `.claude/skills/` 아래로 필요한 스킬 디렉터리를 복사(또는 심링크)
3. Claude Code 세션에서 `/commit`, `/pull-request` 로 호출

## 기여 방식

- 작업 단위는 브랜치 → PR → 리뷰 → **squash merge** (자세한 건 `playbook/git-workflow.md` 예정)
- 스킬 변경은 반드시 팀 공지 후 머지 (모든 팀원이 같은 스킬을 쓰는 게 이 레포의 목적)

## 상태

- [x] 레포 초기 구조
- [ ] `commit` 스킬 정의
- [ ] `pull-request` 스킬 정의
- [ ] `playbook/` 문서 (발표 자료 기반)
- [ ] 스킬 배포 방식 확정
