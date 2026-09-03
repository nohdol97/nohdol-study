# 공개 학습 가이드

GitHub Pages에서 Infra Specialist 기술을 선수 순서로 제공하는 한국어 학습 가이드다. Kubernetes 11개 문서와 Linux·네트워크·AWS·Terraform·Helm/GitOps·관측성·PostgreSQL·Redis/DynamoDB·보안·메시징·신뢰성·Karpenter의 12개 topic, 총 47개 문서를 공개한다.

- 공개 URL: <https://nohdol97.github.io/nohdol-study/>
- 공개 콘텐츠: `docs-site/content/<topic>/`
- 카탈로그: `docs-site/catalog.json`

`docs/`의 하네스 ADR·스펙과 개인 `vault/`는 이 학습 과정의 내용이 아니며 사이트에 게시하지 않는다.

## 주제와 링크를 확장하는 방식

사용자가 현재 주제의 공식 문서 링크를 주면 그 링크를 공개 페이지에 연결하지 않는다. 원자료 본문을 확인하고 해당 주제의 전체 목차에서 맞는 장을 찾아, 링크를 열지 않아도 이해하고 실습할 수 있는 내부 문서로 다시 쓴다.

1. 기능이 해결하는 문제를 요약한 한 문장 모델
2. 컴포넌트 관계, 요청·데이터·제어 흐름 다이어그램과 시퀀스 다이어그램
3. 최소 실행 가능하거나 안전하게 검토 가능한 shell·YAML·HCL·SQL 예시
4. 필드와 동작 원리를 연결한 상세 해설
5. 흔한 실패 상태, 오류 메시지와 복구 순서
6. 개발 환경과 프로덕션 환경의 선택 차이
7. 공개 본문에 노출하지 않는 공식 출처 메타데이터, 확인일과 버전·번역 최신성
8. 원리를 재구성하는 복습 질문

공식 한국어 문서가 원문보다 오래되었다고 표시된 경우 최신성이 중요한 API와 동작은 현재 영어 문서와 레퍼런스도 함께 확인한다. 원문을 통째로 복제하거나 외부 링크 모음으로 만들지 않고, 학습에 필요한 설명과 예시를 독자적으로 구성한다. 근거 URL과 확인일은 Markdown의 HTML 주석으로 남기며 빌드 결과에서는 제거한다.

Markdown의 `mermaid` 코드 블록은 사이트가 함께 배포하는 Mermaid 번들로 직접 렌더링한다. 외부 CDN에 의존하지 않으며 관계도와 시퀀스가 문서 안에 표시된다.

각 주제는 `docs-site/content/<topic>/`에 독립된 로드맵과 본문을 두고 `catalog.json`에 명시적으로 등록한다. 카탈로그 순서는 Linux 기반에서 선언·배포, 운영·데이터, 신뢰성과 Karpenter 심화로 이어지는 선수 관계를 따른다.

전체 과정은 [Infra Specialist 공개 학습 경로 스펙](../docs/specs/2026-09-03-infra-specialist-public-learning-path.md)을 구현한다. 각 신규 topic은 로드맵·운영 모델·실습 3개 문서로 완결했으며, Karpenter만 `Advanced`로 구분한다. AWS 실습은 Local·Plan only·AWS optional 등급과 비용·권한·cleanup 경계를 명시한다.

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
