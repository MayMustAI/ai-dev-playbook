---
date: 2026-10-06
branch: feature/skillbook-sync
task: 스킬북과 Codex 사용본 동기화 및 팀 공통 작업 지침 추가
status: complete
---

# 스킬북과 Codex 사용본 동기화

## 무엇 / 왜

배포본과 개인 Codex 스킬에 서로 다른 개선이 쌓여 동일한 리뷰·머지·리소스 출력 절차를 재사용하기 어려웠다. 범용 리뷰의 검증된 스코프와 최소 수정 절차를 기준으로 팀 PR 검증 표시, 현재 head의 머지 게이트, XLSX 출력 보완을 통합했다.

## 진행 로그

세션 기준 진행 기록. 절대 시각은 커밋 메타데이터 참고.

- 스킬북 9개와 설치된 팀 스킬·개인 스킬을 비교하고 실행 결함 재현
- feature 브랜치에서 기존 공개 플러그인 초안을 포함해 리뷰 절차 수정
- 읽기 전용 reviewer, 고정 SHA, 수정 파일만 staging, PR head 재확인 규칙 통일
- Claude 리뷰 worktree를 PR head에 고정하고 제목·본문 전달 및 검증 체크리스트 기록 추가
- 현재 head의 리뷰 marker 검증기를 팀 플러그인에 배포하고 maymust 0.5.0으로 갱신
- 반차 날짜와 근무지 이동 분리, 대상 월 제출자 선택, 빈 근무시간 수식과 XLSX 검증 보완
- 회귀 테스트 17개, 스킬 형식 10개, JSON·참조 링크·marker CLI 검증 통과
- 개인 스킬을 백업 후 동기화하고 개인 리소스 기본값을 로컬 참조로 보존; maymust 설치본 0.5.0과 원본 일치 확인
- 후속 요청의 세 외부 저장소를 확인하고 고정 commit의 원본 스킬 6개·Claude output style 3개를 배포 번들에 추가
- Superpowers는 verification-before-completion 하나만 선택; 원본 파일과 라이선스·SHA-256을 함께 보존
- Attention-kind·Karpathy·완료 전 검증의 짧은 팀 지침을 SessionStart 훅으로 전달; 다른 응답 스타일은 선택형 유지
- 사용자 언어와 명시적 스타일 우선, 진단 가정 제거, 비례적 검증 및 승인된 작업 완수 원칙을 별도 적용 지침에 기록
- maymust 0.6.0으로 두 런타임 버전 동기화; Codex 훅의 설치 루트 경로 보정
- 공통 지침/배포 테스트 8개와 기존 회귀 테스트 17개 통과; 일반 스킬 13개 형식 검증 및 Claude 플러그인 검증 통과

## 결정 노트

- maymust와 independent-review는 각각 단독 설치할 수 있으므로 독립 리뷰의 실행 절차·프롬프트를 각 배포 번들에 포함한다.
- 공개 플러그인은 개인 경로·Drive 기본값을 포함하지 않는다. 개인 기본값은 Codex 로컬 참조로 유지한다.
- 단일 Claude 리뷰 및 `--once` 결과는 PR head의 독립 리뷰 루프 통과 마커를 대신하지 않는다.
- 공통 지침은 세션 시작에 짧게 주입하고 원문은 관련 단계에서 읽는다. 런타임 설정·사용자 AGENTS.md·CLAUDE.md를 덮어쓰지 않는다.
- Attention Span의 AGPL-3.0과 두 다른 소스의 MIT 선언을 분리 기록한다. Karpathy 원본의 별도 LICENSE 파일 부재도 명시한다.
- Codex 플러그인 훅은 설치와 별개로 정확한 정의를 검토·신뢰해야 한다. 행동 유도와 CI/머지 게이트의 강제 검증을 구분한다.

## 후속

- 실제 PR에 대한 유료 LLM 리뷰·Google Sheets/XLSX 출력은 이번 변경 검증에서 실행하지 않았다.
- SessionStart JSON 출력과 설치 경로는 두 런타임 명령을 직접 실행해 확인했다. 훅 신뢰 이후 실제 모델 대화에서의 적용은 별도 확인이 필요하다.
- GitHub 기본 설치 경로는 dev 브랜치다. feature/skillbook-sync를 dev에 머지한 뒤 팀원에게 0.6.0 업데이트를 배포한다.
