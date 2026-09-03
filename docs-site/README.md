# 공개 학습 가이드

GitHub Pages에서 DevOps와 AIOps를 별도 학습 영역으로 제공하는 한국어 학습 가이드다. 파일을 만들고 기본 shell 명령을 실행해 본 애플리케이션 개발자를 출발점으로 삼으며, 처음 만나는 기술도 용어에서 시작해 정상 관찰·실패·복구와 운영 판단으로 이어지게 구성한다. 루트 2개 영역 아래 DevOps 15개 topic·57개 문서와 AIOps 5개 topic·20개 문서, 총 20개 topic·77개 문서를 공개한다.

- 공개 URL: <https://nohdol97.github.io/nohdol-study/>
- 공개 콘텐츠: `docs-site/content/<topic>/`
- 카탈로그: `docs-site/catalog.json`

`docs/`의 하네스 ADR·스펙과 개인 `vault/`는 공개 학습 본문이 아니며 사이트에 게시하지 않는다. vault 노트는 주제 발견에 참고할 수 있지만 공개 본문은 공식 문서와 1차 자료에서 사실을 다시 확인해 `docs-site/content/`에 별도로 작성한다.

## 주제와 링크를 확장하는 방식

사용자가 현재 주제의 공식 문서 링크를 주면 원자료 본문을 확인하고 해당 주제의 전체 목차에서 맞는 장을 찾아 학습 문서로 다시 쓴다. 공개 문서는 공식 문장의 번역본이 아니라, 확인한 사실에 학습 순서·비교·상황 예시를 더한 설명이다. 버전별 정확한 API와 전체 선택지는 공식 문서를 다시 확인해야 한다.

1. 이 기술이 없을 때 생기는 익숙한 문제 상황
2. 처음 등장하는 전문 용어의 학습용 쉬운 뜻과 공식 영문 이름
3. 한 입력이 결과가 되기까지의 단계별 흐름
4. 정상 상태를 먼저 만드는 준비 절차와 완전한 시작 조건
5. 한 조건만 바꾸는 실패 실습과 변경 전후 관찰
6. 명령 결과가 증명하는 것과 아직 증명하지 못하는 것
7. 복구 뒤 사용자 결과와 잔여 자원까지 확인하는 완료 기준
8. 초심자 확인 문제와 보안·신뢰성·성능·비용의 운영 판단 문제
9. 공식 출처 메타데이터, 확인일과 버전·번역 최신성

공식 한국어 문서가 원문보다 오래되었다고 표시된 경우 최신성이 중요한 API와 동작은 현재 영어 문서와 레퍼런스도 함께 확인한다. 원문을 통째로 복제하거나 외부 링크 모음으로 만들지 않고, 학습에 필요한 설명과 예시를 독자적으로 구성한다. 쉬운 뜻·비유·시나리오·비교표는 학습용 종합이며 공식 문서의 직접 인용이 아니다. 근거 URL과 확인일은 Markdown의 HTML 주석으로 남기며 빌드 결과에서는 제거한다.

Markdown의 `mermaid` 코드 블록은 사이트가 함께 배포하는 Mermaid 번들로 직접 렌더링한다. 외부 CDN에 의존하지 않으며 관계도와 시퀀스가 문서 안에 표시된다.

루트는 `infra`와 `aiops` 학습 영역을 보여 주고, 영역을 선택하면 그 안의 주제가 선수 순서로 열린다. 각 주제는 `docs-site/content/<topic>/`에 독립된 로드맵과 본문을 두고 `catalog.json`에 명시적으로 등록한다. 모든 주제는 정확히 한 영역에 속하며, 영역을 넘는 선수·후속 지식은 Markdown 상대 링크로 연결되어 빌드 후 내부 문서 route가 된다.

DevOps는 [DevOps 공개 학습 경로 스펙](../docs/specs/2026-09-03-infra-specialist-public-learning-path.md), AIOps는 [AIOps 공개 학습 경로 스펙](../docs/specs/2026-09-03-aiops-public-learning-path.md)을 구현한다. 작은 topic은 진입 로드맵·개념 모델·안내형 실습 3개 문서로 첫 학습 순환을 제공하고, 넓은 허브 topic은 vault의 전체 축을 누락하지 않도록 모듈별 장을 둔다. DevOps는 트래픽 제어에 더해 백엔드 요청·transaction·용량·분산 workflow·cache·호환 배포를 연결한다. AIOps는 AI Specialist의 LLM·Vision·On-device·시계열·추천·RAG/MCP와 AI Transformation의 GPU·MLOps/LLMOps·AI DevOps/FinOps·enterprise agent를 운영 증거→진단→승인된 자동 복구의 폐루프로 잇는다.

## 로컬 실행

Node.js 20 이상이 필요하며 CI는 Node.js 22를 사용한다.

```sh
cd docs-site
npm ci
npm test
npm run build
npm run preview
```

브라우저에서 `http://127.0.0.1:4174/`를 연다.

## 공개와 배포

`catalog.json`에는 저장소 안에서 Git이 추적하는 Markdown만 등록할 수 있다. 빌드는 `vault/`, `REGISTRY.md`, `_workspace/`, 절대 경로와 상위 경로 이탈을 거부한다.

`main`에 반영되면 `.github/workflows/docs-pages.yml`이 테스트·빌드 후 Pages artifact를 배포한다. 저장소의 **Settings → Pages → Build and deployment → Source**는 `GitHub Actions`여야 한다.

이 저장소는 검증을 마친 일반 변경을 `origin/main`에 별도 확인 없이 commit·push하는 상시 승인을 갖는다. force push, 히스토리 재작성, 릴리스와 다른 원격·브랜치는 여기에 포함되지 않는다.

`dist/`는 생성물이며 커밋하지 않는다.
