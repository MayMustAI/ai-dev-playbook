---
date: 2026-04-23
branch: feature/remove-empty-dirs
task: playbook/ · templates/ 빈 디렉터리 제거 + 플러그인 도그푸딩
status: complete
---

# playbook/ · templates/ 빈 디렉터리 제거

## 무엇 / 왜

0.3.0 을 픽스 릴리즈로 선언한 뒤에도 `playbook/README.md` · `templates/README.md` 두 placeholder 문서가 남아 있어 레포 구조에 forward-looking 노이즈. 현재 스킬·훅 구성이 확정된 상태라 제거.

동시에 **maymust 플러그인 워크플로우 전체를 이 레포에 직접 적용하는 첫 도그푸딩** 사례. feature 브랜치 → worklog → commit → PR → squash merge 흐름을 실제로 한 번 굴려봄.

## 진행 로그

- 13:20 — feature/remove-empty-dirs 브랜치 생성 (dev 브랜치도 이 시점에 신규 생성 후 origin 푸시)
- 13:22 — `git rm -r playbook templates` 로 두 디렉터리 삭제
- 13:25 — README grep 으로 참조 없음 재확인 (이전 0.3.0 커밋에서 이미 정렬됨)
- 13:28 — worklog 정리 · 커밋 준비

## 막혔던 것 / 해결

없음. dev 브랜치 미존재만 초기 장애였고 신규 생성으로 해소.

## 결정 노트

- **dev 브랜치 신규 생성**: 팀 컨벤션 `feature → dev → main` 을 실제로 적용하려면 dev 가 필요. 레포가 젊어서 이 시점까지 없었음 — 지금 만드는 게 맞다고 판단
- **README 추가 수정 불필요**: 0.3.0 에서 이미 playbook/templates 테이블 행을 제거했으므로 이번엔 디렉터리 자체만 삭제
- **버전 bump 불필요**: 코드/스킬 변경 없고 이미 없어진 placeholder 정리라 0.3.0 유지 적절

## 후속

- dev → main 릴리즈 PR 한 번 굴려보기 (필요 시 별도 PR)
- 이후 모든 작업을 `/maymust:*` 스킬 호출로 진행 — 도그푸딩 계속
