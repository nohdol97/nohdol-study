# ADR 004 — NotebookLM export 스킬 제거

- 날짜: 2026-07-25
- 상태: 활성
- 대상: `notebooklm-export` 스킬 전체, `study-install`의 NotebookLM 모드,
  `REGISTRY.md`의 NotebookLM 필드
- 관계: [ADR 003](003-cli-learning-integrations.md)의 NotebookLM 부분을 대체한다.
  Understand Anything·Obsidian 결정은 그대로 유효하다.

## 맥락

ADR 003은 검증된 export packet과, 보안 게이트를 통과하면 열릴 선택적 CLI
bridge를 채택했다. 그 뒤 실제로 만들어 보고 측정한 결과는 이렇다.

- 스킬·스크립트·테스트 합계 **763줄**.
- 실사용 패킷 **1개**.
- NotebookLM 생성물이 vault로 회수된 사례 **0건**.
- CLI bridge는 릴리스 게이트에서 차단 판정([2b-E 기록](../reviews/2026-07-25-notebooklm-understand-anything-security.md),
  최신 안정 릴리스 v0.7.3에 download redirect 수정 부재).

회수가 한 번도 없었다는 점이 결정적이다. 매니페스트·해시·타임스탬프
디렉터리는 전부 "생성물을 나중에 원 출처로 되짚기" 위한 장부인데, 되짚는
행위가 일어나지 않으면 그 장부는 아무것도 보증하지 않는다. 일어나지 않는
일을 위해 763줄을 유지하는 셈이었다.

## 결정

`notebooklm-export` 스킬을 제거한다. NotebookLM을 쓰지 말라는 뜻이 아니다 —
브라우저에서 직접 쓰는 것은 언제든 가능하며, 그때 필요한 규율은 이미 다른
곳에 있다.

함께 제거하는 것:

- `study-install`의 NotebookLM 모드 인터뷰와 `bootstrap.sh --notebooklm` 플래그
- `REGISTRY.md`의 `NotebookLM`·`NotebookLM workflow` 필드
- `verify-packet.sh`(업로드 전 패킷 재검증)와 `bridge-gate.sh`(릴리스 게이트).
  전자는 회수 워크플로가 없으면 걸릴 일이 없고, 후자는 결론이 "쓰지 마라"인
  도구를 위한 게이트다.

## 남기는 것

- **"AI 출력은 독립 근거가 아니다"** 규칙(AGENTS 4절, `note-writer` 참조 2종).
  NotebookLM을 예시로 들지만 이건 브라우저로 직접 쓸 때도 그대로 적용되는
  일반 규칙이다. 오히려 자동화가 없어진 지금 더 중요하다.
- `_workspace/notebooklm/`의 기존 패킷. 미추적 사용자 산출물이라 삭제하지
  않는다.
- ADR 003과 보안 검토 문서. 기록은 고치지 않는다.

## 결과

주제별로 검증된 노트를 골라 NotebookLM에 올리고 싶으면 이제 사용자가 직접
파일을 고른다. 잃은 것은 `unverified` 노트 자동 거부이고, 그 판단은
`note-writer`가 노트 단위로 이미 하고 있다 — 노트에 `verification` 상태가
기록돼 있으므로 무엇이 검증됐는지는 여전히 파일에서 읽을 수 있다.

## 재검토 조건

NotebookLM 생성물을 실제로 vault에 회수하는 흐름이 생기고, 그때 "이 답이 어느
버전의 어느 파일에서 나왔나"를 되짚어야 할 필요가 관찰되면 다시 만든다. 그
경우에도 매니페스트부터 만들지 말고 회수 흐름을 먼저 돌려 본다.
