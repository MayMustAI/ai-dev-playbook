<!-- pstack(cursor/plugins@f2bad52, MIT) skills/why/references/sources/incident-postmortem.md를 수정해 이식. 출처: THIRD_PARTY_NOTICES.md -->

# 장애·회고 맥락 (방어 코드일 때 추가)

대상 코드가 방어 코드(null 검사, 재시도, 타임아웃, 속도 제한, 기능 플래그, 메모리 부족 처리)처럼 보이면, 자기 출처 안에서 다음을 함께 찾는다.

- **이슈 트래커**: `incident`, `sev-*`, `postmortem-action-item`, `reliability` 라벨이 붙은 티켓
- **장문 문서**: 대상 코드가 추가된 시점 전후의 장애 회고와 런북
- **실시간 채팅**: 대상 코드가 추가된 날짜 전후의 `#sev-*`, `#incident-*` 채널
- **소스 관리**: "장애 수정", "방어 코드 추가" 같은 메시지의 커밋. revert 뒤에 "다시 적용"이 이어지는 커밋은 강한 신호다
