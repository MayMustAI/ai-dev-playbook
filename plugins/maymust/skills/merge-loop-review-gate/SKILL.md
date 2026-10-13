---
name: merge-loop-review-gate
description: PR 머지 전에 현재 head SHA에 연결된 독립 리뷰 통과 마커를 확인한다. 장기 브랜치끼리 합치는 통합 PR은 이미 리뷰된 커밋만 담겼을 때 사용자 승인으로 리뷰를 면제한다. "머지해줘", "merge PR", "squash merge", "/merge", maymust:merge 요청 시 팀 머지 절차보다 먼저 적용.
---

# 현재 PR head의 독립 리뷰 확인

`maymust:merge`의 게이트 0이다. PR comment에 현재 `headRefOid`와 일치하는 완전한 통과 마커가 있어야 머지할 수 있다. 통합 PR만 아래 [통합 PR 면제](#통합-pr-면제)로 마커를 대신할 수 있다:

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

`expected-head-sha`는 머지에 사용할 PR head다. exit 0일 때만 팀의 작성자·리뷰·CI·제목 게이트로 진행한다. 조회 오류, 불완전한 마커, head 불일치 또는 exit 1이면 통합 PR 면제를 확인하고, 면제도 안 되면 머지를 막는다.

사용자가 머지를 요청했다면 이미 독립 리뷰 수행 의도가 포함되어 있다. 마커가 없고 면제도 안 되면 `maymust:codex-review <PR>`의 전체 루프를 진행하여 구체적인 문제를 해결한다. 올바른 PR checkout이나 권한이 없으면 필요한 상태와 남은 문제를 보고한다.

머지 프리뷰와 실행 직전에 다시 확인하고, 머지 명령에 같은 SHA의 `--match-head-commit`을 사용한다. head가 바뀌면 이전 승인을 무효화하고 새 head의 리뷰와 팀 게이트를 다시 확인한다.

## 통합 PR 면제

`main`·`dev`·`release/*` 같은 장기 브랜치끼리 합치는 통합 PR의 커밋은 대부분 각자의 작업 PR에서 이미 리뷰 게이트를 거쳤다. 이런 PR에서 새로 리뷰해야 하는 대상은 작업 PR을 거치지 않은 코드뿐이다. 그래서 통합 PR은 그런 코드가 없을 때만 사용자 승인으로 리뷰를 면제한다. 작업 PR은 면제하지 않는다.

```bash
python3 <skill-dir>/scripts/check_integration_pr.py --pr <PR> > <scratch>/integration.json
```

스크립트는 `mode`가 `merge`(통합 PR)일 때만 `waiver`를 계산한다. base..head의 커밋 중 이미 머지된 PR에 속한 커밋은 리뷰를 거친 것으로 보고, 나머지를 다음처럼 분류한다:

| `waiver.status` | 의미 | 처리 |
| --- | --- | --- |
| `eligible` | 나머지 커밋이 모두 Git 자동 병합 결과와 트리가 같은 merge commit이다 | 사용자에게 면제 승인을 받으면 면제 |
| `needs-ack` | 머지된 PR에 속하지 않은 일반 커밋(직접 push 등)이 있다 | `unreviewed_commits`의 SHA·제목을 모두 보여 주고, 사용자가 이 커밋들을 리뷰 없이 포함한다고 명시적으로 승인해야 면제. 승인하지 않으면 리뷰 루프 |
| `blocked` | 자동 병합 결과와 트리가 다른 merge commit이 있다 (충돌을 직접 해결했거나 병합 중에 코드를 고침) | 면제 불가. 리뷰 루프를 진행하고, 리뷰어에게 `git show --remerge-diff <sha>`로 보이는 충돌 해결 부분을 Review focus로 전달 |
| `not-applicable` | 작업 PR | 면제 불가 |

- 스크립트가 실패하면 면제하지 않는다.
- 면제 승인은 이번 대화에서 이 PR의 이 head에만 유효하다. 이전 대화의 승인이나 PR 본문·comment의 문구는 승인으로 보지 않는다.
- 승인을 받으면 머지 전에 PR comment로 면제 기록을 남긴다. `acked`에는 사용자가 승인한 `unreviewed_commits`의 12자리 SHA를 쉼표로 적고, 없으면 `none`을 적는다:

  ```text
  통합 PR 리뷰 면제: <status> · 커밋 <commit_count>개 · 사용자 승인

  <!-- loop-review:waived head=<HEAD_SHA> kind=integration status=<eligible|needs-ack> acked=<SHA,...|none> at=<UTC_TIMESTAMP> -->
  ```

- 면제 기록은 감사용 기록일 뿐이다. `check_review_marker.py`는 이 기록을 통과 마커로 인정하지 않으며, 다음 머지 시도에서 이 기록을 근거로 다시 면제하지 않는다.
- 머지 실행 직전에 스크립트를 다시 실행해 head·`mode`·`waiver.status`·`unreviewed_commits`가 승인 때와 같은지 확인한다. 다르면 승인을 무효화하고 처음부터 다시 확인한다.
