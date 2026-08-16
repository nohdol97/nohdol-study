# ADR 007 — 사용자용 다이내믹 사이트는 `_workspace` 단일 포털에서 연다

- 날짜: 2026-08-16
- 상태: 활성
- 대상: `AGENTS.md` 7절, `examples/workspace_portal/`, `_workspace/sites/`
- 관련 스펙: [Workspace Site Portal](../specs/2026-08-16-workspace-site-portal.md)

## 맥락

Robot AI Systems Academy는 처음에 `_workspace/robot-ai-expert-academy/`라는 독립 루트와 전용 HTTP 서버를 전제로 만들었다. 앞으로 시뮬레이터·대시보드·학습 지도 같은 사이트가 늘어나면 각 디렉터리에서 서버를 따로 띄우고 포트를 기억해야 한다. 파일은 모두 같은 `_workspace` 아래 있는데 진입점과 실행 수명주기만 갈라지는 구조였다.

`_workspace/`는 설치처별 미추적 산출물이라 실제 사이트를 Git에 넣을 수 없다. 반대로 경로와 등록 방법을 전혀 추적하지 않으면 다음 에이전트가 또 독립 서버를 만든다. 따라서 **정책과 생성 도구는 추적하고, 포털과 사이트 데이터는 미추적한다.**

## 결정

사용자가 브라우저에서 반복 이용하는 다이내믹 HTML 사이트는 다음 계약을 따른다.

```text
_workspace/
├── index.html
├── sites.json
├── assets/
└── sites/
    └── <slug>/
        └── index.html
```

- 사이트는 `_workspace/sites/<slug>/` 아래에 둔다.
- `_workspace/sites.json`에 상대 entry point를 등록하며 `_workspace/index.html`에서 검색·접근할 수 있어야 한다.
- 서버는 `_workspace`를 document root로 한 번만 띄운다. 사이트별 서버와 포트를 만들지 않는다.
- 사이트 내부 asset과 page URL은 portal root 아래에서 이동해도 깨지지 않는 상대 경로를 사용한다.
- 초기화·등록·검사는 `examples/workspace_portal/portal.py`가 담당한다. 이 도구는 기존 portal file을 덮어쓰지 않고, path traversal과 존재하지 않는 entry point를 거부한다.
- Understand 분석 결과, build cache, 임시 report, tool dashboard 같은 내부 산출물은 자동 등록하지 않는다. 사용자가 반복 이용할 사이트로 노출해 달라고 한 경우에만 등록한다.

현재 Robot AI Systems Academy는 `_workspace/sites/robot-ai-expert-academy/`로 이동하고 첫 번째 portal entry로 등록한다.

## 왜 하나의 거대한 SPA가 아닌가

사이트마다 데이터 구조·UI·수명주기가 다르다. 하나의 애플리케이션 bundle로 합치면 작은 수정도 모든 사이트의 배포와 회귀 범위를 넓힌다. 포털은 discovery와 공통 server root만 제공하고, 각 사이트는 독립적인 정적 자산과 테스트를 유지한다.

## 왜 자동 디렉터리 스캔이 아닌가

`_workspace/`에는 지식 그래프·임베딩 인덱스·transcript·테스트 출력 등 사용자에게 보여서는 안 되거나 entry point가 아닌 디렉터리가 많다. 디렉터리를 자동 카드로 만들면 내부 산출물이 공개 UI에 섞인다. 명시적 manifest는 무엇을 사용자용 사이트로 취급하는지 드러낸다.

## 정본과 보존 경계

포털과 사이트는 Markdown 지식의 파생물이며 근거가 아니다. `_workspace/`는 Git과 지식 동기화에서 제외되므로 장기 보존이 필요한 지식은 계속 vault에 기록한다. 사이트 생성 코드가 재사용 가치가 있으면 추적 영역에 template·generator를 두되, 설치 경로와 실제 manifest는 넣지 않는다.

## 결과

- 사용자는 `http://127.0.0.1:4173/` 하나만 열면 된다.
- 새 사이트는 디렉터리 생성과 manifest 등록만으로 발견된다.
- 각 사이트는 독립적으로 발전하지만 server 수명주기는 하나다.
- portal이 없거나 entry가 깨지면 결정적 검사에서 실패한다.
