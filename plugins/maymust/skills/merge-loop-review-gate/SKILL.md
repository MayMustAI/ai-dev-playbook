---
name: merge-loop-review-gate
description: PR 머지 전에 현재 head SHA에 연결된 독립 리뷰 통과 마커를 확인한다. "머지해줘", "merge PR", "squash merge", "/merge", maymust:merge 요청 시 팀 머지 절차보다 먼저 적용.
---

# 현재 PR head의 독립 리뷰 확인

`maymust:merge`의 게이트 0이다. PR comment에 현재 `headRefOid`와 일치하는 완전한 통과 마커가 있어야 머지할 수 있다:

```text
<!-- loop-review:pass head=<HEAD_SHA> blockers=0 mustfix=0 nits=<N> round=<R> at=<UTC_TIMESTAMP> -->
```

`independent-review:loop-review` 또는 `maymust:codex-review`의 PR 수정·재리뷰 루프가 마커를 생성한다. 대화에서의 통과 선언, PR 본문, 이전 head의 마커, `--once` 결과는 대신 사용할 수 없다.

## 확인

명시적 PR 또는 현재 브랜치의 PR을 식별하고, 메타데이터와 comments를 하나의 조회로 읽는다. scratch는 저장소 밖에 둔다:

```bash
gh pr view <PR> --json headRefOid,comments > <scratch>/review-gate.json
python3 <skill-dir>/scripts/check_review_marker.py --head <expected-head-sha> < <scratch>/review-gate.json
```

`expected-head-sha`는 머지에 사용할 PR head다. exit 0일 때만 팀의 작성자·리뷰·CI·제목 게이트로 진행한다. 조회 오류, 불완전한 마커, head 불일치 또는 exit 1이면 머지를 막는다.

사용자가 머지를 요청했다면 이미 독립 리뷰 수행 의도가 포함되어 있다. 마커가 없으면 `maymust:codex-review <PR>`의 전체 루프를 진행하여 구체적인 문제를 해결한다. 올바른 PR checkout이나 권한이 없으면 필요한 상태와 남은 문제를 보고한다.

머지 프리뷰와 실행 직전에 다시 확인하고, 머지 명령에 같은 SHA의 `--match-head-commit`을 사용한다. head가 바뀌면 이전 승인을 무효화하고 새 head의 리뷰와 팀 게이트를 다시 확인한다.
