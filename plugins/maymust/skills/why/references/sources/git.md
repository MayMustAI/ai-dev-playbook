<!-- pstack(cursor/plugins@f2bad52, MIT) skills/why/references/sources/code-archaeology.md를 수정해 이식. 출처: THIRD_PARTY_NOTICES.md -->

# 소스 관리 이력 (git, `gh`, 저장소 안)

## 이 출처에 있는 것

- 커밋 이력(메시지, 날짜, 작성자, diff)
- PR 본문, 리뷰 댓글, 논의 스레드(`gh`)
- 코드 주석, TODO, FIXME, 폐기 예정 표시
- ADR(아키텍처 결정 기록), 저장소에 있다면
- 테스트. 테스트 이름과 단언에는 변경의 동기가 된 엣지 케이스가 담겨 있는 경우가 많다
- 같은 커밋에서 함께 바뀐 파일(동시 변경 신호)
- 저장소 안의 CHANGELOG와 릴리스 노트
- `.worklogs/`의 작업 기록(무엇·왜, 결정 노트)
- 커밋 메시지와 PR 본문의 이슈·티켓 ID

코드와 직접 연결된 가장 믿을 만한 출처이고 가장 완전하다. 저장소를 거친 것은 모두 여기에 있다.

## 찾는 방법

시작 커밋 목록을 넓힌다.

```bash
# 이름 변경을 따라간 이력
git log --follow --oneline -- <file>

# 이 문자열을 정확히 추가하거나 지운 커밋
git log -S '<exact_string_from_code>' -- <file>

# 패턴으로 찾기
git log -G '<regex>' -- <file>

# 줄마다 누가 언제 썼는지
git blame -L <start>,<end> <file>

# 커밋 하나의 전체 diff
git show <hash>

# 두 지점 사이에서 이 파일에 영향을 준 커밋
git log <old>..<new> -p -- <file>
```

저장소 안의 다른 기록을 찾는다.

```bash
# ADR은 docs/adr/ 같은 곳에 있는 경우가 많다
rg -l -i 'architecture.decision' --glob '*.md'

# 대상 근처의 TODO와 FIXME
rg -n -C2 '(TODO|FIXME|HACK|XXX|NOTE)' <target_file>

# 관련 테스트
rg -l '<symbol>' --glob '*test*'

# 이 기능이나 심볼을 다룬 작업 기록
rg -l '<feature-or-symbol>' .worklogs/
```
