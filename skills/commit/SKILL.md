---
name: commit
description: MayMust 팀 컨벤션으로 git 커밋을 생성. 스테이지된 변경을 분석해 Conventional Commits 형식(한글 본문)으로 메시지를 제안·실행. meaningful 모드(본문 포함, 대부분의 의미 있는 작업)와 wip 모드(제목만, feature 브랜치 임시 저장)를 구분해 지원. "커밋 메시지 뽑아줘", "이거 커밋해줘", "/commit" 호출 시 사용.
---

# `/commit` — 팀 공용 커밋 스킬

> MayMust 팀의 모든 레포에서 동일한 커밋 포맷을 유지한다. 개인 취향과 달라도 본 규약을 우선한다.

## 모드

| 모드 | 언제 | 구조 |
| --- | --- | --- |
| **meaningful** (기본) | dev/main 머지 대상이 될 작업. squash-merge 시 남을 메시지. 리뷰받을 단위 | 제목 + 풀 본문 |
| **wip** | feature 브랜치 작업 중 임시 저장. 결국 squash 될 것 | 제목만 |

호출 방식:

- `/commit` — 변경 규모 분석 후 모드를 제안, 사용자 확인
- `/commit meaningful` — meaningful 강제
- `/commit wip` — wip 강제

## 컨벤션 — 제목

```
<type>(<scope>): <한글 설명>
```

- **type** (Conventional Commits): `feat` `fix` `docs` `chore` `style` `refactor` `test` `perf` `build` `ci`
- **scope**: 도메인 단위 소문자, 하이픈 허용 (`auth`, `tenant`, `notify`, `cache`, `api`, `ui`, `settings`, `health`). 여러 도메인 걸치면 대표 하나만. 적당한 스코프 없으면 생략 가능 (`docs: ...`)
- **설명**: 한글 본문 + 영문 기술 용어 (`singleflight`, `TTL`, `round-trip`, `backoff` 등)
- **길이 제한 없음**. 구조 변경이면 핵심을 다 표현해도 됨 (한 줄에 담길 것)
- **PR 번호 `(#N)` 수동 추가 금지** — GitHub squash-merge 가 자동 첨부
- **Co-Authored-By 금지** — 모든 경우에

## 컨벤션 — 본문 (meaningful 모드만)

본문은 "무엇을 했나" 가 아니라 **"왜 / 어떻게 / 검증했나"** 를 담는다.

### 1. 도입부 1–2 문단

문제 상황과 동기. "이전에는 X, 이제 Y" 패턴이 깔끔하다. 무엇이 망가져 있었거나 비대칭이었거나 느렸는지, 이 PR 이 그걸 어떻게 해소하는지.

### 2. `##` 섹션 분할 (변경 규모에 따라)

- **레이어**: `## Backend` / `## Frontend` / `## Infra`
- **논리**: `## 설계 원칙` / `## 남은 작업` / `## 남은 작업 (follow-up PR)`
- **이슈 단위**: `## P0-1: 제목` / `## P1-3: 제목` (리뷰 피드백 반영 커밋)

### 3. 파일·함수 단위 리스트

```
- <파일 또는 심볼>: <변경 요약> → <효과>
```

경로 강조 시 `[region_settings_store.go]` 브라켓 OK. 불릿 속 불릿 허용.

### 4. 검증 섹션 (필수)

`## 테스트` · `## 검증` · `## 배포 검증` · `## 수동 검증` 중 적절한 헤더로:

- `go test` · `go build` 통과 여부
- `npm run lint` · `npm run build` 통과 여부
- 수동 시나리오로 확인한 것
- **미실시 항목은 솔직하게 명시** — "UI 수동 검증 미실시 — X 로 재현 가능" 식으로

### 5. 남은 작업 (있을 때만)

follow-up PR 으로 뺄 거리. 커밋 안에 "이건 여기까지, 다음은 저기" 라고 경계를 긋는다.

## 워크플로우

1. **스테이지 상태 확인**
   - `git status` · `git diff --staged --stat` 로 범위 파악
   - 스테이지 비어 있으면 사용자 확인 — `git add .` 자동 실행 금지. 어떤 파일만 포함할지 묻는다
2. **diff 읽기**
   - `git diff --staged` 로 실제 변경 이해
   - 여러 논리 단위가 섞였으면 커밋 분리 제안
3. **type / scope 추론**
   - 파일 경로 패턴 + 변경 성격으로 초안
   - 애매하면 사용자에게 확인
4. **모드 결정**
   - 인자 없으면 분석으로 제안 ("변경이 커서 meaningful 로 가는 게 맞아 보입니다. wip 로 갈까요?")
5. **초안 제시**
   - meaningful: 제목 + 본문 풀 구조
   - wip: 제목만
6. **사용자 확인 → 커밋**
   - 멀티라인은 HEREDOC 으로:
     ```bash
     git commit -m "$(cat <<'EOF'
     <type>(<scope>): <제목>
     
     <본문>
     EOF
     )"
     ```
7. **결과 보고**
   - 커밋 해시 + 제목 한 줄

## 금지 사항

- ❌ `Co-Authored-By` 라인 추가 (어떤 경우에도)
- ❌ PR 번호 `(#N)` 수동 추가
- ❌ `--no-verify` (훅 실패 시 원인 수정 후 재커밋)
- ❌ 확인 없는 `git add .` / `git add -A`
- ❌ "파일 수정" / "코드 정리" 류 공허한 제목 (왜 했는지가 없음)
- ❌ 본문을 diff 재탕으로 채우기 (파일명 나열 ≠ 문맥 설명)

## 예시

### meaningful — 리뷰 블로커 처리

```
fix(cache): 리뷰 블로커 3개 처리 — 캐시 키 격리 + 시그니처 정리 + race

PR 리뷰에서 지적된 3개 P0/P1 이슈 수정. 전부 유닛테스트는 통과하지만
멀티 테넌트 환경의 캐시 격리가 실제로는 동작하지 않던 문제.

## P0-1: cloneCacheConfig 가 신규 필드 누락
[cache_store.go] clone 함수가 TenantKeys/PrimaryKeyID 를 복사하지 않아
State()/Replace() 라운드트립마다 필드 소실. 저장은 되지만 applyCacheConfig
가 받아오는 사본은 empty → runtime registry 비어있음.
→ 모든 필드를 clone 에 추가. 구조체 확장 시 clone 동반 변경 필요 경고 추가.

## P0-2: ?tenant= 검증만 되고 핸들러가 primary runtime 을 그대로 사용
middleware 가 tenant 를 ctx 에 주입했지만 핸들러들은 여전히 a.cache
전역 포인터를 읽어 선택한 tenant 와 무관하게 primary 데이터만 반환.
[middleware_tenant.go] a.cacheFor(ctx) 헬퍼 추가. 모든 a.cache 읽기를
a.cacheFor(ctx) 로 교체.

## P1-3: responseCache 가 tenant 분리 없이 전역 공유
[response_cache.go] getOrSetJSONBytes 시그니처에 ctx 추가. 내부에서
tenantCacheKey(ctx, key) 로 prefix 자동 주입. 기존 호출부 52곳에 ctx
전달하도록 일괄 수정. 시그니처 변경은 의도적 — 누락 call site 가 컴파일
에러로 즉시 발견됨.

## 검증
- `go build ./...` + `go test -race -count=1 ./...` 전체 통과
- `npm run lint` 경고 0 + `npm run build` 성공
- 수동: tenant A/B 라운드트립 격리 확인 필요 (integration)
```

### meaningful — 신규 기능

```
feat(notify): 실시간 알림 SSE 채널 + 알림 센터 UI

이전에는 사용자가 페이지 새로고침해야 새 알림을 확인할 수 있었고, 알림을
한 화면에 모아볼 공간도 없었다. SSE 기반 실시간 스트림과 통합 알림 센터를
도입해 즉시 확인·관리 가능하게 한다.

## Backend
- notify_service: SSE 채널 (/api/notify/stream) + PubSub 버스, 재연결 시
  Last-Event-ID 기반 재전송
- notify_handlers: POST /api/notify/{mark-read,mark-all-read,dismiss}
- storage: notifications 테이블 + unread 인덱스 (tenant_id, user_id, read_at IS NULL)

## Frontend
- NotifyCenter (shadcn Sheet + 무한 스크롤, Badge 로 카테고리 구분)
- useNotifyStream 훅 (EventSource + exponential backoff 재연결)
- Header unread 배지 — 서버 재호출 없이 스트림으로만 갱신

## 테스트
- backend: 6개 신규 유닛 테스트 통과 (구독/해제, 배달, 재연결 idempotency)
- frontend: npm run lint/build 통과
- UI 수동: 두 탭 동시 열고 한 쪽 발송 → 다른 쪽 즉시 반영 확인
```

### wip

```
feat(notify): WIP — 알림 센터 무한 스크롤 페이지네이션 시도
```

```
fix(cache): WIP — invalidation race 재현 케이스 작성 중
```
