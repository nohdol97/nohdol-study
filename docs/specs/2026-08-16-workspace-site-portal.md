# Workspace Site Portal 스펙

- 날짜: 2026-08-16
- 상태: 구현됨
- 관련 결정: [ADR 007](../adr/007-single-workspace-site-portal.md)

## 목표

- `_workspace` 아래 사용자용 다이내믹 사이트에 하나의 진입점을 제공한다.
- 사이트별 HTTP 서버와 포트 운용을 없앤다.
- 실제 로컬 사이트를 추적하지 않으면서도 다음 에이전트가 같은 경로·manifest 계약을 재현하게 한다.

## 비목표

- vault Markdown을 portal이 대신하는 것
- 내부 분석물과 tool dashboard의 자동 노출
- site bundle을 하나의 framework나 build system으로 통합
- internet 공개, 인증, remote hosting

## 요구사항

### R1. 단일 document root

사용자용 사이트는 `_workspace/sites/<slug>/` 아래에 있고 `_workspace`가 HTTP document root다. 정상 사용 시 사이트별 server process를 요구하지 않는다.

### R2. 명시적 manifest

`_workspace/sites.json`은 version 1 object이며 각 site에 `slug`, `title`, `description`, `href`, `category`, `tags`, `updated`, `status`를 둔다. `href`는 `sites/<slug>/` 아래의 실재 파일만 가리킨다.

### R3. portal 탐색

`_workspace/index.html`은 manifest의 non-archived site를 카드로 보여주며 제목·설명·분류·tag 검색과 분류 filter를 제공한다. 각 카드는 상대 URL로 site entry를 연다.

### R4. 안전한 초기화와 갱신

`portal.py init`은 없는 portal file만 만들고 기존 로컬 편집을 덮어쓰지 않는다. `register`는 같은 slug를 중복 생성하지 않고 갱신한다. 절대 경로, `..`, slug 밖 entry, 존재하지 않는 entry를 거부한다.

### R5. 추적과 미추적 분리

template·manager·test·규칙은 Git에 추적한다. 생성된 `_workspace/index.html`, `sites.json`, 실제 site는 계속 Git에서 제외한다. 추적 파일에는 설치처 절대 경로를 기록하지 않는다.

### R6. 파생물 경계

portal과 등록 site는 지식 근거가 아니다. 내부 scratch와 분석 결과는 사용자가 노출을 요청하지 않는 한 manifest에 등록하지 않는다.

## 완료 기준

- 빈 임시 workspace에서 init이 portal file 4개를 만들고 재실행 시 0개를 덮어쓴다.
- 정상 site 등록·동일 slug 갱신·중복 tag 정규화가 통과한다.
- path traversal과 slug 밖 entry가 거부된다.
- 등록된 entry file 삭제 시 check가 실패한다.
- 실제 `_workspace` portal check가 Robot AI Systems Academy 1개 등록 상태로 통과한다.
- 단일 portal server에서 `/`, `/sites.json`, Academy entry와 핵심 asset이 HTTP 200을 반환한다.
