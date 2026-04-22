---
name: worklog
description: 작업 단위로 한 장짜리 Worklog 를 관리. 현재 브랜치 기반으로 .worklogs/ 에 생성·조회·진행 로그 추가·완료 처리. feature 브랜치에 커밋되어 squash merge 시 main 에 자연 축적되는 팀 작업 아카이브. "worklog 시작", "진행 로그 남겨줘", "/worklog" 호출 시 사용.
---

# `/maymust:worklog` — 작업당 한 장 Worklog

> 발표의 원칙: **"작업마다 Worklog 한 장을 남긴다."** 이 스킬이 그 규칙을 단일 포맷으로 강제.

## 저장 위치 · 명명

`.worklogs/<YYYY-MM-DD>-<branch-slug>.md` (현재 프로젝트 루트 기준)

- `YYYY-MM-DD`: worklog 생성일
- `branch-slug`: 현재 브랜치에서 `/` · 공백 → `-` 로 변환
- 예: 브랜치 `feature/merge-skill` → `.worklogs/2026-04-22-feature-merge-skill.md`

**축적 방식**:
- feature 브랜치에서 worklog 파일을 **커밋**
- PR squash merge 시 `.worklogs/` 의 신규 파일이 dev/main 에 함께 들어감
- 시간이 지나면 `.worklogs/` 가 팀 전체 작업 아카이브 — grep/검색 가능

## 서브커맨드

| 호출 | 동작 |
| --- | --- |
| `/maymust:worklog` | 현재 브랜치의 worklog 파일 열기. 없으면 생성 (task 한 줄 입력 유도) |
| `/maymust:worklog new "<task>"` | 새 worklog 강제 생성 (같은 브랜치에서 이전 worklog 있어도 날짜로 분기) |
| `/maymust:worklog log "<메시지>"` | **진행 로그** 섹션에 `- HH:MM — <메시지>` 한 줄 추가 |
| `/maymust:worklog finish` | 상단 frontmatter `status: in-progress` → `complete`. PR 본문에 붙일 3–5줄 요약 생성 |

## 파일 포맷

```markdown
---
date: 2026-04-22
branch: feature/merge-skill
task: /merge 스킬 추가
status: in-progress
---

# /merge 스킬 추가

## 무엇 / 왜
<작업의 핵심 — 한 문단. 왜 이 작업을 하는가, 끝난 상태는 어떤 모습인가>

## 진행 로그
- 14:30 — 시작, gh pr view 게이트 설계
- 15:10 — squash 본문 스트립 로직 확정

## 막혔던 것 / 해결
<비어도 OK — 있을 때만 채움>

## 결정 노트 (재사용 가치)
<이 작업을 넘어 다른 작업에서도 참조할 설계·판단 — 있을 때만>

## 후속
<이 작업 후 남는 follow-up 거리>
```

**섹션 규약**:
- `## 무엇 / 왜` — 시작 시 필수
- `## 진행 로그` — 작업 중 계속 추가. 타임스탬프는 `HH:MM` (날짜는 frontmatter 에서)
- 나머지 3개 — **필요할 때만** 채움. 빈 상태로 finish 해도 OK

## 워크플로우

### 새 작업 시작

1. `/maymust:worklog` 호출
2. 현재 브랜치 · 프로젝트 루트 확인
3. `.worklogs/<slug>.md` 존재 여부 체크
4. 없으면: task 한 줄 입력 받고 템플릿 생성, `## 무엇 / 왜` 섹션 함께 채움
5. 있으면: 기존 내용 보여주고 이어서 작업

### 진행 중

- `/maymust:worklog log "...특정 변경에 대한 로그"` — `- HH:MM — ...` 로 진행 로그에 append
- 즉시 add + commit 하지 않음 — 사용자가 모아서 커밋하도록 둠 (worklog 업데이트마다 커밋은 과함)

### 작업 완료

1. `/maymust:worklog finish`
2. frontmatter `status: complete`
3. 전체 내용 분석 → PR 본문 `## Worklog` 섹션에 붙일 3–5줄 요약 생성
   - 예: "총 3시간. 14:30 설계 → 15:10 스트립 로직 → 17:00 예외 케이스 2건 발견·처리"
4. 요약 출력 → 사용자가 `/maymust:pull-request` 생성 시 그대로 복붙

## 금지 사항

- ❌ worklog 를 gitignore 에 넣기 — 이 스킬의 취지(팀 아카이브 축적) 정면 위배
- ❌ main/dev 브랜치에서 worklog 수정 — 반드시 feature 브랜치에서만
- ❌ 같은 파일에 날짜만 바꿔 덮어쓰기 — 다른 작업이면 새 파일
- ❌ 진행 로그에 날짜 반복 기입 — `HH:MM` 만 (frontmatter 에 date 있음). 다음 날 작업이면 구분선 `---` 로 일 경계 표시

## 예시

### `/maymust:worklog` (새로 시작)

```
작업 이름 한 줄? (예: /merge 스킬 추가)
> /merge 스킬 추가

무엇/왜 짧게? (1–2문장)
> PR 머지 시 팀 squash 컨벤션 강제 + 머지 후 dev 동기화 자동화

✅ 생성: .worklogs/2026-04-22-feature-merge-skill.md
```

### `/maymust:worklog log "게이트 설계 완료"`

```
✅ 진행 로그 추가: 
   - 14:30 — 게이트 설계 완료
```

### `/maymust:worklog finish`

```
✅ 완료 처리: .worklogs/2026-04-22-feature-merge-skill.md (status: complete)

PR 본문용 요약 (복붙):
---
총 2시간. 게이트 6개(author·mergeable·review·CI·draft·base) 설계 →
squash 메시지 스트립 규칙 확정(Self-verification/Screenshots 제거) →
로컬 정리 단계(dev sync + safe delete) 추가.
---
```
