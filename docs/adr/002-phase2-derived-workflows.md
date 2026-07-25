# ADR 002 — Phase 2 수집·NotebookLM·그래프는 파생 워크플로로 유지

- 날짜: 2026-07-25
- 상태: 활성
- 대상: 웹·논문·영상 ingest, NotebookLM, 결정적 그래프, 정확성 규칙

## 결정

| 결정 | 내용 | 이유 |
|---|---|---|
| 정확성 상시 적용 | 중요한 주장의 검증은 `AGENTS.md` 완료 조건으로 두고 상세 절차만 `note-writer` 참조에 둔다 | 별도 `evidence-check` 스킬은 라우팅되지 않는 순간 검증이 빠질 수 있다 |
| 캡처와 지식 분리 | 외부 자료는 `raw/` 불변 스냅샷, 해석은 `wiki/` 검증 노트로 저장한다 | 원문을 결론에 맞게 바꾸는 위험과 출처 유실을 막는다 |
| NotebookLM 소비자 모드 | 관련 파일만 해시 manifest와 함께 내보내는 packet을 기본 경계로 삼는다 | 수동 업로드와 후속 CLI bridge 모두 같은 범위·버전을 재현한다 |
| NotebookLM 산출물은 파생물 | 퀴즈·그림·답변은 원 출처 대조 전까지 근거로 인정하지 않는다 | 모델 생성물은 학습 보조이지 독립 관측이 아니다 |
| Enterprise 분리 | `gcloud`·프로젝트·라이선스·API·인증이 확인된 설치처만 공식 API 경로를 사용한다 | 개인 소비자 워크플로와 Cloud 관리형 API의 권한 모델이 다르다 |
| 공개 논문 경로 | paper-search의 공개 소스만 기본 경로로 사용한다 | 재현성과 합법적 접근 경계를 유지한다 |
| 영상 2-pass | 자막 우선 전체 파악 후 중요한 타임스탬프만 프레임으로 본다 | 긴 영상의 이미지 토큰 비용을 줄이고 시각 정보 누락도 보완한다 |
| Whisper 명시 승인 | 기본은 `--no-whisper`; 해당 영상의 오디오 외부 전송 승인 후에만 사용한다 | 전사 편의보다 데이터 전송 경계를 우선한다 |
| 결정적 그래프 기준 | Python 표준 라이브러리로 Markdown에서 JSON을 재생성한다 | 서버·MCP 없이 두 CLI에서 동일 결과를 만들고 원본 권위를 지킨다 |
| basic-memory 게이트 | 노트 수가 아니라 명시된 corpus·검색 질문·원본 hash 불변 조건으로 제한 파일럿한다 | 임의 규모 기준 대신 실제 검색 효용과 비파괴성을 측정한다 |

## 설치처 상태 판정

`study-install`은 NotebookLM 모드와 로컬 export 준비 여부, `defuddle`,
`paper-search`, `yt-dlp`, `ffmpeg`, 전역 `watch` 스킬을 관찰해 미추적
`REGISTRY.md`에 기록한다. 소비자 계정 로그인과 실제 업로드는 로컬 파일
검사만으로 확인할 수 없으므로 `account-unverified`로 남긴다.

API 키·Cloud 프로젝트·NotebookLM 계정 정보는 저장소나 vault에 쓰지 않는다.
설치 실패는 다른 소스 유형을 막지 않으며, 실제 사용 가능한 실행 파일을
다시 확인해 상태를 판정한다.

## 결과

Phase 2는 자료를 가져오고 학습 도구에 전달하는 능력을 추가하지만 지식
원본은 계속 Markdown이다. `_workspace/`의 NotebookLM 패킷과 그래프 JSON은
삭제해도 재생성할 수 있다.

개인용 NotebookLM의 선택적 CLI bridge와 Understand Anything 전체 스킬
통합은 [ADR 003](003-cli-learning-integrations.md)에서 별도로 제한한다.
