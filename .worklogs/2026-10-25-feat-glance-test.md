---
date: 2026-10-25
branch: feat/glance-test
task: glance-test 스킬 추가
status: complete
---

# glance-test 스킬 추가

## 무엇 / 왜

발표 슬라이드가 3초 안에 핵심 메시지 하나를 전하는지(낸시 두아르테의 글랜스 테스트) 장별로 점검하는 스킬을 maymust에 추가한다. 다른 세션에서 38장짜리 HTML 덱에 적용한 절차를 일반화한 요구사항을 따른다. 끝난 상태: `/maymust:glance-test`가 덱을 발표 크기 이미지로 렌더링하고, 맥락 없는 검토자의 판독을 의도와 대조해 정해진 형식의 한국어 보고서를 낸다.

## 진행 로그

- 12:18 — `origin/dev`(32ab247)에서 `feat/glance-test` 브랜치 생성. 렌더링 도구 확인: Chrome·pdftoppm 있음, LibreOffice 없음
- 12:26 — HTML 렌더러(`scripts/render_html.py`, `scripts/measure_slide.js`) 작성. 시험 덱 3장에서 지표가 예상값과 일치(글자 9·6·7자, 축소 배율 반영 20px, 페이드인 최종 상태 포함, 숨긴 글자 제외)
- 12:27 — 렌더러 테스트 4개 통과(2.2초). 레드 체크: 장별 재로딩·애니메이션 종료·축소 배율 처리를 각각 지우면 해당 테스트가 실패
- 12:31 — SKILL.md, 검토자 프롬프트, `agents/openai.yaml`, README·MANUAL 항목, 버전 0.9.0 반영. `claude plugin validate` 통과, 단위 테스트 5묶음 48개 통과. `quick_validate.py`는 `disable-model-invocation` 예외로만 실패(필드를 뺀 사본은 통과)

- 12:35 — `claude -p --plugin-dir plugins/maymust`로 `/maymust:glance-test`를 6장짜리 시험 HTML 덱에 실행(155초, 성공). `--selector "section.slide"`로 렌더링하고, 별도 서브에이전트가 이미지 6장만 열어 판독(프롬프트에 덱 경로와 의도 없음). 메인 에이전트가 2·3·4·5장 이미지를 직접 확인. 결과 PASS 2 · BORDERLINE 2 · FAIL 2, 3장은 의도("순서")와 대조해 PASS에서 BORDERLINE으로 변경, 의도를 주지 않은 5장은 "추론"으로 표시. 보고서가 지정 형식(실패 장 표, 원인별 경계 장, 지킬 것, 옮길 곳, 수정 범위 질문)과 일치하고 덱 파일은 바뀌지 않음

- 12:56 — codex 리뷰 R1~R5(PR #15). 수용한 must-fix: SVG 글자 배율과 PDF 렌더링 크기(709e395), 측정용 요소를 덱 CSS에서 격리(5bb4f60), 조상 overflow로 잘린 글자 제외(3690c59), 일부만 보이는 문단은 보이는 글자만 집계(8dd082c), 검토자가 부모 대화를 물려받지 않게 명시(R5). 리뷰 중 직접 찾아 함께 고친 것: 정수 offsetHeight로 생긴 글자 크기 반올림 오차, 표 칸을 상자로 세던 중복 집계. 각 수정은 레드 체크로 테스트가 실패하는 것을 확인

## 결정 노트 (재사용 가치)

- HTML 렌더러는 Chrome DevTools 파이프(`--remote-debugging-pipe`)로 구동한다. Python 표준 라이브러리만 쓰므로 WebSocket 클라이언트나 Playwright 설치가 필요 없다 (`plugins/maymust/skills/glance-test/scripts/render_html.py`)
- 장마다 `about:blank`를 거쳐 다시 불러온다. 해시만 다른 URL로 옮기면 같은 문서 안의 이동이라 load 이벤트가 오지 않고 덱 스크립트도 다시 돌지 않는다 (`test_each_target_is_one_slide_and_fragment_changes_reload_the_deck`, 레드 체크로 확인)
- 객관 지표는 판정의 근거로만 쓰고 기준값으로 판정하지 않는다. 시각 단위 수는 상자·카드와 목록 항목·표 행을 센 어림값이다

## 후속

- PDF·PPTX 경로(`pdftoppm`, LibreOffice 변환)는 이번에 실제 덱으로 실행하지 않았다. 이 PC에는 LibreOffice가 없다
- 수정 후 재판독(7단계)은 시험 실행에서 사용자 응답이 없어 진행하지 않았다
