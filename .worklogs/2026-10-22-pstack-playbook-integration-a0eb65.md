---
date: 2026-10-22
branch: pstack-playbook-integration-a0eb65
task: pstack 방법론을 이식해 플레이북 분석 스킬 고도화
status: complete
---

# pstack 방법론을 이식해 플레이북 분석 스킬 고도화

## 무엇 / 왜

pstack(cursor/plugins)을 플레이북과 함께 쓰는 방안을 검토했다. poteto-mode가 커밋·PR·리뷰·머지 단계를 maymust와 반대 규칙으로 수행해서, 머지 게이트 우회, 리뷰 마커 무효화 루프, 무인 실행 교착, 세션 워크트리 삭제 위험이 확인되었다. 그래서 pstack은 설치하지 않고, 팀 흐름과 충돌하지 않는 방법론만 고정 commit 기준으로 팀 스킬에 이식한다. 끝난 상태는 maymust 0.8.0이 blast-radius·benchmark-checklist·how·why 스킬과 테스트 판정 기준·근거 기록 규칙을 Claude와 Codex에 함께 배포하는 것이다.

## 진행 로그

세션 기준 진행 기록. 절대 시각은 커밋 메타데이터 참고.

- pstack 0.15.29(cursor/plugins `f2bad52`)의 Claude Code 트리와 플레이북 스킬·훅을 대조해 사용 충돌 14건 정리 — 근거: `worktree-audit.sh`를 읽기 전용으로 실행하자 활성 세션 워크트리가 `safe`로 분류됨, `branch-guard.sh`에 `git -C . commit`을 넣자 확인 없이 통과
- 통합 대신 이식으로 결정 — 이유: 원본을 래퍼로 덮으면 지시가 겹쳐 충돌, 업스트림 변경이 잦음 · 근거: `gh api "repos/cursor/plugins/commits?path=pstack&since=2026-07-22"` 결과 93건
- 1단계: blast-radius·benchmark-checklist 추가, self-review와 codex 리뷰어 테스트 렌즈 보강, worklog 근거 규칙, pull-request 연결, team-defaults 성능 수치 규칙
- 2단계: how·why 이식. 명시 호출 전용, 서브에이전트는 선택 사항, why 출처는 git·Linear·Notion·Slack과 `.worklogs/`
- lock에 pstack 출처 추가(LICENSE는 원본 hash, 이식 파일은 `adapted`에 원본 hash), THIRD_PARTY_NOTICES·README·버전(maymust 0.8.0, independent-review 1.1.0) 갱신
- 테스트 3개 추가(출처 추적, how·why 명시 호출, 리뷰어 프롬프트 사본 일치) — 근거: 스크래치 사본에서 각 규칙을 깨면 이 3개만 실패하고, 작업 트리에서는 11개 모두 통과
- `/maymust:how`를 `claude -p --plugin-dir plugins/maymust --permission-mode plan`으로 실행해 동작 확인 — 근거: exit 0, 설명자 서브에이전트 사용, 출력이 핵심 개념·동작 방식(mermaid)·코드 위치·주의할 점 구조와 한국어를 따름, 실행 전후 `git status` 동일

## 결정 노트 (재사용 가치)

- 외부 스킬이 다른 스킬·설정·런타임을 참조하면 원본 복사 대신 수정해서 이식한다 — 이유: 래퍼로 덮으면 지시가 서로 충돌 · 근거: pstack how·why가 poteto-mode의 Subagents 절, `pstack-models` 규칙, Cursor 어댑터를 참조
- 수정 이식한 파일은 lock의 `adapted`에 원본 hash를 남기고 첫 줄에 출처 주석을 단다 — 이유: 업스트림 변경을 나중에 비교 · 근거: `test_adapted_pstack_material_is_traceable_to_pinned_upstream`
- 서브에이전트를 여러 개 띄우는 스킬은 두 런타임 모두 명시 호출 전용으로 둔다 — 이유: 실행 비용, 자동 호출을 끄면 설명이 컨텍스트에 들어가지 않음 · 근거: Claude Code skills 문서의 `disable-model-invocation` 설명
- maymust codex-review와 independent-review loop-review의 리뷰어 프롬프트는 같은 파일로 유지한다 — 근거: `test_bundled_reviewer_prompt_matches_standalone_loop_review`

## 후속

- pstack 도입과 별개로 `branch-guard.sh` 정규식이 `git -C`, `git -c` 형태를 놓친다. 별도 PR로 보완한다
- 머지 게이트가 스킬 안에만 있어서 `gh pr merge`를 직접 호출하면 우회된다. 훅이나 GitHub 필수 상태 검사로 강제할지 결정이 필요하다
- how는 헤드리스 plan 모드에서 한 번 확인했다. why(Notion·Slack·Linear MCP 인증 필요), blast-radius, benchmark-checklist의 실제 대화 동작과 Codex에서의 로딩은 아직 확인하지 않았다
- claude-review의 리뷰어 프롬프트는 별개 파일이라 이번 테스트 렌즈 보강을 적용하지 않았다
