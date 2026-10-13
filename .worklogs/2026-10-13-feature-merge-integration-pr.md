---
date: 2026-10-13
branch: feature/merge-integration-pr
task: maymust:merge 통합 PR merge commit 판정과 리뷰 면제
status: complete
---

# maymust:merge 통합 PR merge commit 판정과 리뷰 면제

## 무엇 / 왜

`maymust:merge`는 모든 PR을 squash로 머지하고 head 브랜치를 지웠다. 그래서 release→main, release→dev, dev→release 같은 장기 브랜치 간 통합 PR에 쓰면 공통 조상이 사라지고, head가 release 브랜치이면 그 브랜치까지 삭제된다. 작업 PR은 그대로 squash로 두고, 통합 PR만 merge commit으로 판정해 머지하도록 고쳤다. 이미 리뷰된 커밋만 담긴 통합 PR은 사용자 승인으로 독립 리뷰를 면제한다.

## 진행 로그

- platform-core 이력 확인: release→main 예정 범위 510커밋 중 merge commit 2개, 머지된 PR에 속하지 않은 커밋 4개(dev 직접 push)
- `check_integration_pr.py` 작성: 머지 방식 판정(head 장기 브랜치 / 동기화 merge commit), 면제 상태(eligible·needs-ack·blocked)
- 임시 Git 저장소 기반 단위 테스트 11개 추가(기존 6개 포함 17개 통과)
- platform-core 실제 이력 대조: release→main = merge·needs-ack(4커밋), #1067 머지 전 상태 재현 = sync-merge·blocked(충돌 해결 merge commit)
- merge·merge-loop-review-gate 스킬 문서, README, 관련 스킬 문구 갱신, maymust 0.7.0
- codex R1(must-fix 2): base 의 merge queue, 장기 브랜치 head 를 지우는 자동 삭제 설정을 판정 스크립트가 막도록 수정(테스트 20개)
- 과잉 구현 정리(사용자 결정 B안): GitHub GraphQL 커밋-PR 연결 조회·needs-ack·저장소 설정 검사 코드 제거. 면제 검사는 어느 장기 브랜치에도 없는 새 커밋만 보고, 설정 확인은 merge 스킬의 문서 명령으로 옮김. 스크립트 211→143줄, 테스트 195→160줄(16개 통과)
- 실제 이력 재대조: release→main = merge·eligible, #1067 머지 전 상태 재현 = sync-merge·blocked

## 결정 노트

- 판정 기준은 base가 아니라 head다. 작업 PR도 release를 base로 삼을 수 있기 때문이다.
- 동기화 브랜치는 "base에 없는 다른 장기 브랜치의 커밋을 병합한 merge commit"으로 찾는다. 작업 브랜치가 자기 base를 병합한 경우는 squash로 남는다.
- 이미 어느 장기 브랜치에 들어간 커밋은 그 브랜치의 PR 게이트를 거친 것으로 본다. 면제 검사는 그 밖의 새 커밋만 보고, 새 커밋은 `git merge-tree --write-tree` 자동 병합 결과와 트리가 같은 merge commit일 때만 통과시킨다. 충돌 해결·병합 중 수정·추가 커밋은 리뷰를 요구한다.
- 장기 브랜치에 직접 push된 커밋은 잡지 않는다. GitHub 조회로 잡을 수 있지만 요청 범위를 넘는 코드라 뺐다.
- merge queue·자동 head 삭제 설정은 지금 팀 저장소에 해당하지 않으므로 코드 대신 merge 스킬 문서의 확인 명령으로 둔다.
- 면제 기록 comment는 감사용이며 `check_review_marker.py`가 통과 마커로 인정하지 않는다.

## 후속

- 이 변경으로 실제 통합 PR을 머지해 보는 검증은 아직 하지 않았다. 첫 사용처는 platform-core release/v0.1-oss → main이다.
- ort 이전 recursive 전략으로 만든 merge commit은 자동 병합 결과가 달라 `blocked`로 보수적으로 판정될 수 있다.
