---
name: commit
description: MayMust 팀 컨벤션에 맞는 git 커밋을 생성합니다. 스테이지된 변경을 분석하여 메시지를 제안하고, 확인 후 커밋합니다. 이 스킬은 팀과 함께 설계하는 중이며 컨벤션 확정 후 정식 버전이 됩니다.
---

# `/commit` — 팀 공용 커밋 스킬

> 🚧 **Draft.** 아직 컨벤션이 확정되지 않았습니다. 다음 항목을 팀과 결정한 뒤 이 문서를 채웁니다.

## 결정해야 할 것

- [ ] 커밋 메시지 포맷 (예: Conventional Commits `feat: ...` vs 자유 형식)
- [ ] 언어 (한글 / 영문 / 혼용)
- [ ] 제목 길이 가이드 (50자? 72자?)
- [ ] 본문 사용 기준 (언제 쓰고 언제 생략)
- [ ] `Co-Authored-By` 정책
- [ ] feature 브랜치의 WIP 커밋 정책 (squash merge 전제이니 자유롭게? 아니면 깨끗하게?)

## 참고 — 발표에서 합의된 전제

- 브랜치 전략: `feature → dev → main` 한 방향
- 머지 방식: **squash merge** (feature → dev 시점에 임시 커밋 → 의미 있는 한 줄)
- 따라서 feature 브랜치의 개별 커밋보다 **squash commit 메시지 = PR 제목**이 더 중요함

## 동작 설계 (초안)

1. `git status` · `git diff --staged` 로 변경 범위 파악
2. 팀 컨벤션에 맞는 메시지 초안 제시
3. 사용자 승인 후 `git commit`
4. (정책에 따라) `Co-Authored-By` 없이 작성

---

_정식 스킬로 완성되면 이 경고 블록은 제거됩니다._
