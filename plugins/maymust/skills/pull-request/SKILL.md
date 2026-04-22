---
name: pull-request
description: MayMust 팀 컨벤션으로 Pull Request를 생성. 브랜치 변경 규모를 분석해 PR 제목(=`/commit` 규약 그대로)과 듀얼 오디언스(사람+AI 리뷰어) 최적화 본문을 제안하고, 5단계 루프를 대화형으로 확인한 뒤 `gh pr create` 로 실행. "PR 올려줘", "풀리퀘 만들어줘", "/pull-request" 호출 시 사용.
---

# `/pull-request` — 팀 공용 PR 생성 스킬

> PR 본문은 **사람 리뷰어가 30초 스캔** + **동료의 AI 리뷰어가 claim 검증** 을 동시에 잘 하도록 설계한다.

## 핵심 원칙

- **PR 제목 = `/commit` 제목 규약 그대로** — 이 PR 이 squash-merge 되면 그 제목이 커밋 메시지가 됨
- **PR 본문은 짧고 구조 고정** — 깊은 기술 디테일은 각 커밋 본문에, PR 본문은 "게이트 통과 증거" + "리뷰 유도 prompt"
- **베이스 브랜치 기본 `dev`** (main 머지는 릴리즈 PR 만)
- **5단계 루프 체크는 대화형 확인** — 임의 `[x]` 금지. 안 한 건 `[ ]` + 사유

## 왜 이 본문 구조인가

| 사람 리뷰어 | AI 리뷰어 |
| --- | --- |
| 30초 스캔으로 스코프 파악 | 명시된 의도·불변식 기준으로 코드 검증 |
| 어디 집중할지 안내 필요 | Out of scope 표시가 있어야 false-positive 방지 |
| 스크린샷·Before/After | Design decision 의 이유가 코드로 뒷받침되는지 체크 |

→ PR 본문의 각 섹션 ≈ "AI 에게 던지는 claim". 사람은 claim 이 전략적으로 말이 되는지, AI 는 claim 이 코드로 성립하는지.

## 제목 컨벤션 — `/commit` 과 동일

```
<type>(<scope>): <한글 설명>
```

- 타입·스코프·언어 규약은 [commit 스킬](../commit/SKILL.md) 참조
- **`(#N)` 수동 추가 금지** — PR 번호는 GitHub 이 squash-merge 시 자동 첨부
- 여러 커밋을 묶은 PR 이면, **대표가 될 제목** 하나를 추출 (보통 가장 큰 feat/fix)

## 본문 구조 (규모에 따라 차등 적용)

### 규모 기준

| 규모 | 기준 | 섹션 |
| --- | --- | --- |
| **소형** | <100 LOC · 1–2 파일 · 버그픽스 한 방 | Why + What changed + Self-verification |
| **중형** | 그 중간 | 소형 + Review focus |
| **대형** | >500 LOC · 여러 모듈 · 리팩터·마이그레이션 | 전체 섹션 |

스킬이 `git diff --stat base...HEAD` 로 규모 판단 → 구조 제안 → 사용자 조정.

### 섹션 템플릿 (전체)

```markdown
<상단 배지: 🚨 Breaking change / ⚠️ Migration / 🔒 Security — 해당 시만>

## Why
<1 문단: 문제 → 해결 → 결과. "이전에는 X, 이제 Y" 패턴 권장>

## What changed
- Backend: <1줄 요약>
- Frontend: <1줄 요약>
- Infra: <1줄 요약>

## Design decisions
- <선택 A (vs 고려한 B)>: <이유> — 리뷰어는 이 이유가 성립하는지 체크
- 불변식: <지켜야 할 규칙. 예: "cache key 에 regionID 필수">

## Review focus
- 🔍 주로 봐주세요: <위험 지점 / 설계 판단 지점 — 파일·함수 단위>
- ⏭️ 기계적 변경 (skip OK): <rename / fixture / 일괄 replace>

## Screenshots (UI 변경 시 필수)
| Before | After |
| --- | --- |
| <이미지> | <이미지> |

## Out of scope / Follow-up
- <의도적으로 이 PR 에서 제외한 것 — AI 가 "빠졌다" 고 잘못 지적하지 않게>
- Follow-up PR: <있으면 링크/계획>

## Self-verification (5단계 루프)
- [x] 1. 직접 테스트 — <어떤 시나리오 눌렀는지>
- [x] 2. 세션 초기화 셀프 리뷰 — <무엇을 찾아 고쳤는지>
- [x] 3. 다른 LLM PR 리뷰 — <모델명> · <피드백 요지>
- [x] 4. 피드백 선별 — 수용 N, 거절 N (<거절 이유>)
- [x] 5. Playwright — <테스트 파일 경로> 또는 N/A (<사유: 백엔드 전용 등>)

## Worklog
<링크 또는 3–5줄 요약>
```

### 소형 템플릿

```markdown
## Why
<1 문단>

## What changed
<1–2줄 요약>

## Self-verification
- [x] 1. 직접 테스트 — ...
- [x] 2. 셀프 리뷰 — ...
- [x] 3. LLM 리뷰 — <모델> · <요지>
- [ ] 4. 피드백 없었음
- [x] 5. N/A — <사유>

## Worklog
<링크>
```

## 상단 배지 기준

| 배지 | 언제 |
| --- | --- |
| 🚨 **Breaking change** | 기존 API·스키마·config 계약이 깨짐. 소비자 측 변경 필요 |
| ⚠️ **Migration** | DB 마이그레이션, 데이터 백필, 배포 순서 주의 필요 |
| 🔒 **Security** | 인증·권한·시크릿 취급·외부 입력 검증 관련 변경 |

해당 없으면 배지 생략.

## 워크플로우

1. **브랜치 · 푸시 상태 확인**
   - `git rev-parse --abbrev-ref HEAD` — 현 브랜치
   - `git status` — uncommitted 있으면 커밋 먼저 유도
   - `git rev-list @{u}..HEAD 2>/dev/null` — 미푸시 커밋 있으면 `git push -u origin <branch>`
2. **베이스 브랜치 결정** — 기본 `dev`. 사용자가 명시하면 변경
3. **규모 판단**
   - `git diff --stat <base>...HEAD`
   - 파일 수 · LOC · 모듈 범위로 소형/중형/대형 선택
4. **제목 초안**
   - `git log <base>..HEAD --oneline` 으로 커밋 분석
   - 단일 의미면 그대로 사용, 여러 커밋이면 대표 feat/fix 추출
5. **배지 판단** — diff 에서 API 시그니처 변경·migration 파일·auth 코드 변경 감지 시 제안
6. **본문 초안 작성** — 규모별 템플릿
7. **5단계 루프 대화형 확인**
   - 각 단계별로 물음:
     - "1. 직접 테스트 — 어떤 시나리오 눌러보셨나요?"
     - "2. 세션 초기화 후 셀프 리뷰 — 결과는?"
     - "3. 다른 LLM 으로 PR 리뷰 — 어느 모델, 뭐라고 하던가요?"
     - "4. 받은 피드백 중 수용 / 거절 갯수, 거절 이유는?"
     - "5. Playwright 테스트 — 경로 또는 N/A 사유?"
   - 답 없는 단계는 **`[ ]` + "미수행: <이유>"** 로 기록. 절대 `[x]` 로 가짜 통과 처리 금지
8. **Worklog 링크 물어봄** — 없으면 인라인 3–5줄 요약 유도
9. **Review focus · Out of scope 확인** — 중대형이면 사용자가 직접 채워야 의미 있음. 스킬이 후보를 diff 에서 추천
10. **스크린샷 확인** — UI 변경 감지 시 "Before/After 스크린샷 붙여주세요" 유도. 없으면 `Screenshots` 섹션에 TODO 남김
11. **최종 본문 프리뷰 → 사용자 승인**
12. **draft / ready 확인**
13. **실행**: `gh pr create --base <base> --head <branch> --title "..." --body "$(cat <<'EOF' ... EOF)"` (draft 시 `--draft`)
14. **결과 보고** — PR URL · 번호

## 금지 사항

- ❌ 5단계 체크박스를 확인 없이 `[x]` 로 찍기 — 게이트 무력화
- ❌ `Co-Authored-By` 추가 (글로벌 정책)
- ❌ 제목에 `(#N)` 수동 첨부
- ❌ 베이스를 `main` 으로 (릴리즈 PR 이라고 명시된 경우만 예외)
- ❌ Worklog 섹션 자체 생략 (링크가 없으면 인라인 요약이라도 남김)
- ❌ "변경사항을 모두 diff 에서 열거" — PR 본문을 diff 재탕으로 만들면 AI·사람 둘 다 못 읽음
- ❌ UI 변경에 스크린샷 없이 ready 로 올리기

## 예시

### 소형 — 버그픽스 한 방

**제목**: `fix(health): /healthz 에서 tenant-scoped DB pool 체크 제거`

**본문**:

```markdown
## Why
배포 후 /healthz 가 503 으로 떨어지던 문제. tenant 격리 리팩터 과정에서
handleHealth 가 `a.dbPoolFor(r.Context())` 를 호출하는데 /healthz 는
tenant-whitelist 경로라 ctx 에 tenant 가 없음 → nil → 503.

process liveness 관점에서 /healthz 는 tenant 무관해야 함. per-tenant
준비도는 필요 시 `/api/tenants/<id>/health` 로 분리.

## What changed
- [main.go] handleHealth 에서 dbPoolFor 호출 제거, static 200 응답

## Self-verification
- [x] 1. 직접 테스트 — `curl /healthz` → 200
- [x] 2. 셀프 리뷰 — /healthz 외 tenant-whitelist 경로에 dbPoolFor 호출 없는지 확인
- [ ] 3. LLM 리뷰 — 건너뜀 (1파일 1함수 트리비얼)
- [ ] 4. 피드백 없음
- [x] 5. N/A — 백엔드 핸들러

## Worklog
작업 1시간. 배포 직후 알람으로 탐지 → fix → 재배포.
```

### 대형 — 리팩터 + 신규 기능

**제목**: `feat(tenant): 테넌트별 DB/Cache 관리 + 실시간 알림 센터 + 빈 테넌트 UI 가드`

**본문**:

```markdown
⚠️ Migration — .env 의 DB_URL/CACHE_URL 을 Settings UI 로 이전

## Why
인증만 테넌트별이었고 DB/Cache 는 프로세스 전역 싱글톤이었던 비대칭 해소.
테넌트가 격리 경계가 되어 모든 인프라 엔드포인트가 테넌트마다 독립됨.
병행해서 실시간 알림 센터를 추가해 페이지 새로고침 없이 새 알림 확인 가능.

## What changed
- Backend: tenantRuntime 단일 구조체 · tenantRuntimeRegistry · dbConfig_validator
  · notify_service SSE 채널 · audit_service tenant-aware
- Frontend: apiFetch ?tenant 자동 주입 · Settings DB/Cache 탭 · NotifyCenter
  · TenantCapabilityGuard
- Infra: notifications 테이블 마이그레이션 · .env 축소

## Design decisions
- **tenantRuntime 단일 struct** (vs 3 parallel map): clone/sync 경로 줄이고 atomic
  교체 쉬움 → 리뷰어는 applyTenantSettings 의 swap 지점이 lock-free 인지 체크
- **알림 키 = (tenant_id, user_id) 페어**: user_id 단독은 cross-tenant 충돌 가능
  → 리뷰어는 모든 notify 조회 경로에서 tenant_id 가 포함되는지 체크
- **불변식**: response mask · in-memory clone · response shape 세 경로 모두 구조체
  필드 동기화 필요. 하나라도 누락되면 round-trip 에서 필드 소실

## Review focus
- 🔍 주로: tenantRuntime 의 lock 정책 · dbPool.Close 순서 · middleware_tenant
  의 화이트리스트 경로 · SSE 스트림 재연결 로직
- ⏭️ Skip OK: 57개 apiFetch 호출부의 기계적 시그니처 유지 · i18n 키 추가 · mock 핸들러

## Screenshots
| Before | After |
| --- | --- |
| Settings 에 DB 탭 없음 | DB · Cache 2 탭 + Primary 배지 |
| 새 알림 새로고침 필요 | NotifyCenter + 실시간 unread 배지 |

## Out of scope / Follow-up
- 각 서비스 메서드를 `rt *tenantRuntime` 인자로 변경 — 기계적 migration PR 로 분리
- 모든 cache/inflight key 에 tenant_id 포함 — 위와 동일 PR 에서
- SSE 서버 수평 확장 (Redis PubSub) 은 v2
- 모바일 푸시 알림은 POC 단계

## Self-verification
- [x] 1. 직접 테스트 — tenant A/B 추가·삭제·primary 전환 · NotifyCenter · 빈 테넌트 가드
- [x] 2. 셀프 리뷰 — 리뷰에서 3개 P0/P1 발견·수정 (별도 커밋)
- [x] 3. LLM 리뷰 — codex · round-trip + 런타임 격리 + 캐시 격리 블로커 지적
- [x] 4. 피드백 선별 — 3개 전부 수용
- [x] 5. Playwright — 미작성, 이후 PR 에서 추가. 현재는 수동 시나리오로 대체

## Worklog
총 3일. day1: tenant runtime · day2: 알림 채널 · day3: 리뷰 반영 + 가드 확장.
```
