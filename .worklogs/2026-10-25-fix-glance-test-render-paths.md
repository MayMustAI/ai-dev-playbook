---
date: 2026-10-25
branch: fix/glance-test-render-paths
task: glance-test PDF·PPTX 렌더링 경로 수정
status: complete
---

# glance-test PDF·PPTX 렌더링 경로 수정

## 무엇 / 왜

0.9.0의 glance-test는 PPTX를 LibreOffice로만 PDF로 바꾸게 안내했다. Codex 데스크톱에서 실제로 시험해 보니 LibreOffice 변환이 한글 PPTX의 2·3·5장에서 글자를 빠뜨렸고, 스킬은 대조 단계에서 멈췄다. 덱을 만든 앱(PowerPoint)으로 내보내는 경로를 먼저 쓰고, 판독 전에 렌더링 결함을 확인하도록 고친다. PDF는 크기를 정확히 맞추고, pdftoppm이 없을 때의 대안을 추가한다.

## 진행 로그

- 13:42 — headless Chrome은 PDF를 뷰어로 열지만 툴바·썸네일이 찍히고, `#toolbar=0&navpanes=0&view=Fit`이면 장만 화면에 맞춰짐
- 14:02 — Claude Code의 파일 읽기 도구는 PDF를 장별 이미지로 열고(1067×800), PPTX는 "This tool cannot read binary files"로 거부. `codex exec`는 셸 없이 PDF를 열지 못함. Codex 데스크톱 시험 프롬프트 작성(14:09)
- 14:34 — Codex 데스크톱 시험 결과 확인(사용자 실행, danger-full-access): `view_image`는 PNG만 열고 PDF·PPTX는 거부. HTML 렌더러·pdftoppm·Chrome 뷰어·PowerPoint 내보내기·LibreOffice 모두 실행됨. PowerPoint는 출력 폴더에 "파일 액세스 부여" 창을 띄움. 스킬 실행에서 LibreOffice 변환본의 2·3·5장 글자 누락을 검토자와 메인 에이전트가 확인. `spawn_agent` 기본값(`fork_turns: "all"`)으로 띄운 서브에이전트는 확인 문구를 맞혔고, `"none"`은 몰랐음
- 14:35 — SKILL.md·MANUAL 수정, 0.9.1. 확인: `pdftoppm -scale-to-x 1600 -scale-to-y 900`으로 16:9 PDF 6쪽 모두 1600×900(이전 방식은 1600×901), Chrome 뷰어로 1~3쪽이 서로 다른 1600×900 이미지(2쪽이 실제 2장), SKILL.md의 AppleScript가 그대로 컴파일됨(osacompile 종료 코드 0). hooks·glance-test·scripts 테스트와 claude plugin validate 통과

## 결정 노트 (재사용 가치)

- PPTX는 덱을 만든 앱으로 PDF를 내보내는 것이 가장 정확하다. LibreOffice는 덱의 글꼴이 없으면 글자를 빠뜨리거나 바꾼다 (Codex 데스크톱 시험, 2·3·5장)
- 판독 전에 렌더링 결함을 먼저 확인한다. 결함이 있는 이미지로 판독하면 렌더링 문제를 덱의 문제로 오판한다
- Codex의 `spawn_agent`는 대화를 물려주는 것이 기본값이므로, 검토자는 `fork_turns: "none"`으로 띄워야 한다 (확인 문구 시험)

## 후속

- 더 좁은 샌드박스(`workspace-write`)에서 Chrome·osascript·PowerPoint가 막히는지는 확인하지 못했다
