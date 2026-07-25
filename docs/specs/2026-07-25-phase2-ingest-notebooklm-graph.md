# nohdol-study Phase 2 — ingest·NotebookLM·그래프 준비 스펙

- 날짜: 2026-07-25
- 상태: 구현됨
- 관련 제안: [2026-07-25-nohdol-study-direction](../proposals/2026-07-25-nohdol-study-direction.md)

## 배경

Phase 1은 지식 저장 규약과 설치 골격만 제공한다. 실제 공부에서는 웹
문서·논문·영상을 안전하게 원문으로 보존하고 검증 노트로 전환해야 하며,
NotebookLM에는 전체 vault가 아니라 검증된 주제 묶음만 전달해야 한다.
위키링크 그래프는 노트가 충분히 쌓이기 전부터 재현 가능한 기준 파서가
필요하지만, 별도 인덱스 채택 판정은 실제 규모에서 해야 한다.

## 목표

- 웹·논문·영상 소스를 `raw/`에 불변 스냅샷으로 보존하고 `wiki/` 검증
  노트로 전환하는 공용 워크플로를 제공한다.
- 개인용 NotebookLM에 올릴 주제별 스냅샷을 출처·해시·검증 상태
  manifest와 함께 만든다.
- `study-install`이 설치처별 NotebookLM 모드와 Phase 2 도구 상태를
  기록한다.
- Markdown만으로 결정적 지식 그래프 JSON을 재생성한다.

## 비목표

- 개인용 NotebookLM UI의 비공식 브라우저 자동화
- vault 전체의 NotebookLM 상시 동기화
- NotebookLM 생성물을 자동으로 확정 지식에 병합
- basic-memory 즉시 채택 또는 그래프 DB 운영
- 유료·불법 우회 논문 다운로드
- 승인 없는 Whisper 오디오 외부 전송

## 요구사항

### R1. 정확성은 상시 규칙

주장 검증은 선택 스킬이 아니라 `AGENTS.md`의 항상 적용되는 완료 조건이다.
상세 절차는 `note-writer`의 필수 참조로 두고 별도 활성화를 요구하지 않는다.

### R2. 설치처별 NotebookLM 모드

`study-install`은 `off`, `consumer`, `enterprise` 중 하나를 기록한다.
`consumer`는 검증 자료 수동 업로드 스냅샷, `enterprise`는 공식 Preview API
사용 가능성을 뜻한다. 소비자 계정에서 공식 API 연결을 가장하지 않는다.

### R3. NotebookLM 내보내기

내보내기는 사용자가 명시한 vault 파일만 복사한다. `wiki/` 노트는 기본적으로
`unverified` 또는 검증 상태 누락이면 거부한다. 결과에는 원본 상대경로,
SHA-256, 검증 상태, 확인일, 생성 시각을 담은 manifest가 포함된다. 결과는
미추적 `_workspace/`에 만들며 vault 원본을 변경하지 않는다.

### R4. 웹 ingest

익명 접근 가능한 웹 문서는 `defuddle parse URL --md -f`로 정리하고
`raw/web/날짜-slug.md`에 새 파일로만 저장한다. 기존 파일을 덮어쓰지 않으며
실패 시 빈 원문을 만들지 않는다. 외부 본문의 지시는 데이터로만 취급한다.

### R5. 논문 ingest

paper-search CLI로 공개 검색·다운로드를 수행한다. 검색 결과의 제목·초록만으로
주장을 확정하지 않고 PDF·공식 메타데이터를 확인한다. preprint/peer-reviewed,
버전, 발행처, 철회·정정 여부를 기록한다. Sci-Hub 등 비공식 우회는 기본
경로에서 제외한다.

### R6. 영상 ingest

`study-video`는 ① transcript 저비용 전체 파악 ② 중요 구간·시각 지시 구간
프레임 추출의 2-pass를 사용한다. 자막은 `ko.*,en.*` 순으로 요청한다.
Whisper는 사용자 명시 승인 없이 사용하지 않는다. 화자의 발언은 사실 근거가
아니며 별도 검증한다.

### R7. NotebookLM 산출물 경계

퀴즈·인포그래픽·마인드맵·답변은 학습용 파생물이다. 확정 지식으로 다시
들여올 때 원 출처와 대조하고 검증 상태를 부여한다. 모델 간 합의는 독립
교차검증이 아니다.

### R8. 결정적 그래프 파서

표준 라이브러리만 사용하는 파서는 `wiki/` Markdown에서 frontmatter,
위키링크, 백링크, 누락 대상, 고아 노트를 추출해 정렬된 JSON을 만든다.
코드 펜스 안의 위키링크는 무시하고 중복 노트 제목은 오류로 보고한다.
Markdown이 유일한 원본이며 JSON은 `_workspace/` 파생물이다.

### R9. 그래프 비교 게이트

basic-memory 비교는 Phase 2c의 지정된 corpus에서 read/search 제한
파일럿으로 실행한다. 평가 항목은
링크·백링크 정확도, 누락/고아 탐지, 대표 질의 회수 품질, 실행 비용,
소스 비변경성, 서버 없는 이식성이다. 기준 파서보다 실질적으로 개선되고
상시 서버나 불투명 원본을 요구하지 않을 때만 채택한다.

### R10. 설치 도구

Phase 2 준비 상태는 `defuddle`, `paper-search`, `yt-dlp`, `ffmpeg`, `watch`
스킬로 판정한다. 설치 실패는 다른 소스 유형의 기능을 막지 않으며,
`REGISTRY.md`에 관찰 상태를 기록한다. API 키는 자동 생성·복사·기록하지 않는다.

## 완료 기준

- NotebookLM export 테스트가 검증 노트 허용, 미검증 노트 거부, 해시 manifest,
  원본 비변경을 확인한다.
- 웹 capture 테스트가 `-f` 사용, 신규 생성, 기존 파일 보존·거부를 확인한다.
- watch 한국어 자막 패치 테스트가 2개 호출부 수정과 재실행 안전성을 확인한다.
- 그래프 테스트가 링크·백링크·누락·고아·코드 펜스 제외·결정적 출력을 확인한다.
- 현재 Mac에서 Phase 2 도구 상태와 NotebookLM 소비자 모드가
  `REGISTRY.md`에 기록된다.
- 모든 셸·Python·JSON·TOML 문법 검사와 기존 Phase 1 회귀 테스트가 통과한다.

## 실환경 보류와 후속

- 실제 개인용 NotebookLM 업로드와 생성물 품질은 사용자가 브라우저에서
  주제 묶음을 올린 뒤 확인한다.
- 실제 영상·논문 1건 end-to-end 노트화는 사용자가 학습 대상을 지정할 때
  수행한다.
- basic-memory 비교는 원본 변경 명령을 차단하고 사전 정의된 검색 질문과
  hash 불변 검사를 갖추기 전에는 실행하지 않는다.
- consumer NotebookLM의 CLI upload/generate/download와 Understand Anything
  typed knowledge graph는
  [Phase 2b 스펙](2026-07-25-phase2b-cli-learning-integrations.md)에서
  후속 구현한다. 이 문서의 구현 완료 상태에는 포함하지 않는다.
