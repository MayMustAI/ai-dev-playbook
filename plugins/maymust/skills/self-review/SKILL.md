---
description: 5단계 루프 step 2 — PR 을 "처음 보는 것처럼" 리뷰. PR 본문의 Why/Design decisions/Out of scope 를 "의도" 로 삼고 diff 를 "구현" 으로 본 뒤 일치 여부·엣지 케이스·복잡도·테스트 공백을 구조화된 찾기로 출력. "셀프 리뷰", "PR 리뷰해줘", "/self-review" 호출 시 사용.
---

# `/maymust:self-review` — PR 에 대한 의도 vs 구현 셀프 리뷰

> 발표의 5단계 루프 step 2: **"세션 초기화 후 셀프 리뷰"**. 작성자 본인이 **새로운 눈** 으로 자기 PR 을 읽고 발견되는 것을 구조화해 내놓는다.

## 호출 예

```
/maymust:self-review             # 현재 브랜치의 PR
/maymust:self-review 42          # 명시적 PR 번호
```

## 핵심 원칙 — "의도 vs 구현" 리뷰

이 스킬은 코드를 **처음부터 평가** 하지 않는다. PR 본문에 작성자가 명시한 의도와 구현이 **일치하는지** 만 본다:

| PR 본문 섹션 | 리뷰 렌즈 |
| --- | --- |
| `## Why` | 이 코드가 그 문제를 정말 푸나? |
| `## Design decisions` | 선언된 선택·이유가 코드로 뒷받침되나? 불변식이 깨지는 곳 있나? |
| `## Out of scope / Follow-up` | 여기 명시된 건 빠져도 블로커 아님. 거꾸로, 명시 안 한 중요한 누락은 블로커 |

→ 작성자의 의도가 명확할수록 리뷰 품질이 올라감. PR 본문이 빈약하면 스킬이 "의도 선언 부족 — 일반 품질 체크만 가능" 표시.

## 세션 편향 경고

작성자 본인 세션에서 바로 호출하면 "방금 이거 짰다" 는 맥락이 편향으로 작용. 이상적인 호출:

```
/clear
/maymust:self-review
```

**세션 초기화 생략 시 경고만 띄우고 진행**. 출력 최상단에 `⚠️ 동일 세션 리뷰 — 편향 가능` 표시. 하드 블록 아님 (마찰 최소화).

## 리뷰 체크리스트

### 1. 의도 일치 (가장 중요)
- `## Why` 의 문제를 실제로 해결하는가?
- `## Design decisions` 의 선택이 코드 전반에 일관되게 적용되나?
- `## Design decisions` 의 **불변식** 이 깨지는 지점은?

### 2. 엣지 케이스
- nil/empty/undefined 처리
- concurrent 접근 · race
- 큰 입력 · 시간 초과
- 외부 의존(API/DB) 실패 경로

### 3. 잔재
- `TODO` / `FIXME` / `XXX` / `HACK` 태그 남아있나?
- 임시 디버그 로그 (`console.log`, `fmt.Println`, `print`) 섞였나?
- 주석 처리된 코드 덩어리
- 하드코딩된 테스트 값

### 4. 복잡도
- 한 함수 50줄 이상, 분리 가능한가?
- 중첩 depth 4단계 이상
- 재사용 가능한 추상화를 동일 패턴 3회 반복으로 피했나

### 5. 네이밍
- 이름이 "무엇" 이 아니라 "어떻게" 를 말하는가? (`userList` vs `activeUsersForDisplay`)
- 약어 남발 (`usrMgr`, `cfgSvc`)
- 불 boolean 이름이 `is/has/should` 로 시작하나

### 6. 테스트
- 변경된 로직에 새 테스트 있나?
- `Out of scope / Follow-up` 에 "테스트 follow-up" 이 명시돼 있나? (명시되어 있으면 OK)
- 기존 테스트가 새 동작을 커버하나, 회귀 방지는?

### 7. 보안·데이터
- 외부 입력 validation
- 시크릿 로깅·응답 바디 노출
- SQL injection · path traversal · XSS 가능 지점

## 출력 포맷

```markdown
⚠️ 동일 세션 리뷰 — 편향 가능 (미실행이면 생략)
   세션 초기화 후 재리뷰 권장: `/clear` → `/maymust:self-review`

# Self-review — PR #<N>: <title>

## 🚫 블로커 (머지 금지)
- `<파일>:<라인>` — <문제> → <제안>

## 🔧 머스트 픽스 (이번 PR 에서 처리)
- `<파일>:<라인>` — <문제> → <제안>

## 💡 닛픽 (원하면)
- `<파일>:<라인>` — <문제>

## 👍 좋음
- <짧은 한 줄 — 잘된 점 1–3개>

## 📋 체크리스트 결과
| 렌즈 | 결과 |
| --- | --- |
| 의도 일치 | ✅ / ⚠️ / 🚫 |
| 엣지 케이스 | ... |
| 잔재 | ... |
| 복잡도 | ... |
| 네이밍 | ... |
| 테스트 | ... |
| 보안·데이터 | ... |
```

- 문제 없으면 해당 섹션 생략 (블로커/머스트픽스/닛픽 빈 상태 OK)
- 최소 `👍 좋음` 한 줄 + 체크리스트 결과는 항상 출력

## 워크플로우

1. **PR 식별** — 인자 또는 현재 브랜치의 PR 자동
2. **PR 본문·diff 수집**
   ```
   gh pr view <N> --json title,body,author
   gh pr diff <N>
   ```
3. **의도 추출** — PR 본문에서 `## Why`, `## Design decisions`, `## Out of scope` 파싱. 없으면 "의도 선언 부족" 경고
4. **diff 분석** — 파일별로 읽으며 7개 렌즈 적용
5. **발견 정리** — 블로커 / 머스트픽스 / 닛픽 / 좋음 으로 분류
6. **출력** — 세션 편향 경고 + 리뷰 + 체크리스트

## 금지 사항

- ❌ PR 본문에 없는 의도를 추측해서 "이러려고 했을 것 같은데 다르네요" 류 지적
- ❌ "전반적으로 리팩터가 필요해 보입니다" 류 추상 피드백 (파일:라인 단위 구체성 필수)
- ❌ 스타일 기호 주장 (탭 vs 스페이스 등) — 린터가 할 일
- ❌ 다른 PR 에서 다뤄야 할 일 (Out of scope 에 명시된 것) 을 블로커로 올리기
- ❌ 이미 `## Design decisions` 에 "고려한 대안 B + 거절 이유" 가 있는데 B 를 재제안

## 예시

```markdown
⚠️ 동일 세션 리뷰 — 편향 가능
   세션 초기화 후 재리뷰 권장: `/clear` → `/maymust:self-review`

# Self-review — PR #42: feat(tenant): 테넌트별 DB/Cache 관리

## 🚫 블로커
- `tenant_settings_store.go:147` — clone() 이 새로 추가한 DBConfigs 필드를 복사하지 않음. State()/Replace() round-trip 마다 필드 소실 → runtime registry 비어있음. PR 의 "테넌트가 격리 경계" 의도 자체가 깨짐

## 🔧 머스트 픽스
- `middleware_tenant.go:23` — ?tenant= 파싱 실패 시 400 반환해야 하는데 panic. 사용자 입력 unvalidated
- `db_pool.go:89` — close(stopCh) 후 factory.Shutdown() 순서 반대. connection goroutine leak 가능

## 💡 닛픽
- `tenant_handlers.go:56` — `handleTenant` 보다 `handleTenantList` 가 구체적
- middleware 로깅에 tenantID 포함하면 debug 편함

## 👍 좋음
- apiFetch 래퍼에 ?tenant 자동 주입하는 설계 — 57개 호출부를 건드리지 않고 tenant-aware 로 만든 점이 깔끔

## 📋 체크리스트 결과
| 렌즈 | 결과 |
| --- | --- |
| 의도 일치 | 🚫 clone 누락으로 핵심 의도 깨짐 |
| 엣지 케이스 | ⚠️ tenant 파싱 실패 경로 |
| 잔재 | ✅ |
| 복잡도 | ✅ |
| 네이밍 | 💡 |
| 테스트 | ⚠️ clone round-trip 테스트 없음 |
| 보안·데이터 | ✅ DB URL 평문은 기존 auth 와 동일 패턴으로 명시됨 |
```
