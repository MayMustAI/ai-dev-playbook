---
name: codex-review
description: MayMust 코드 변경을 새 읽기 전용 Codex 세션에 리뷰받고, 검증된 blocker/must-fix만 최소 수정하여 재리뷰한다. PR 통과 시 현재 head에 연결된 리뷰 마커를 남긴다. "코덱스 리뷰", "codex 리뷰 루프", "/codex-review" 요청에 사용.
---

# `/maymust:codex-review` — 독립 리뷰와 최소 수정

현재 에이전트는 수정자, 새 `codex exec` 세션은 리뷰어다. 새 세션은 대화 이력을 공유하지 않지만, 독립 실행만으로 모든 편향이 제거된다고 보장하지 않는다.

[references/review-loop.md](references/review-loop.md)를 읽고 실행한다. 이 플러그인에 실행 절차와 리뷰 프롬프트를 함께 배포하므로 별도 `independent-review` 설치 없이도 동작한다.

지원 호출:

- `/maymust:codex-review`: 자동 스코프, 최대 5라운드
- `--once`: 읽기 전용 1회 리뷰; 수정·커밋·푸시·PR comment 없음
- `--max <양의 정수>`: 라운드 한도
- `--uncommitted`: index를 보존하며 미추적 파일까지 리뷰
- `--base <ref>`: 기준 브랜치 대비 전체 변경
- `--commit <sha>`: 현재 HEAD의 커밋과 이후 수정 커밋
- `<PR 번호|URL>`: 검증된 PR head를 라운드마다 재확인

PR 메타데이터 조회와 fetch는 현재 세션이 수행하고, 리뷰어는 `-s read-only`에서 로컬 diff와 관련 파일만 읽는다. 커밋 루프는 깨끗한 feature 브랜치에서만 진행하고, 검증한 수정 파일만 stage한다. PR push는 확인된 head 저장소와 브랜치에 명시적 refspec을 사용한다.

blocker와 must-fix가 모두 0이면 통과한다. PR 모드에서는 실제 리뷰한 SHA가 여전히 원격 head와 일치할 때만 `loop-review:pass` 마커를 남긴다. `--once`와 비PR 모드의 통과는 머지 증거가 아니다.

자동 머지는 수행하지 않는다. `/maymust:merge`가 현재 head의 통과 마커와 팀 머지 게이트를 확인한다. 닛픽은 선택 사항이며, 라운드 한도·정체·리뷰 실행 실패 시 남은 문제와 근거를 보고한다.
