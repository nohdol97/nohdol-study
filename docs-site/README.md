# 공개 학습 가이드

GitHub Pages에서 여러 기술 주제를 차례로 제공하는 한국어 학습 가이드다. 게이트웨이와 카탈로그는 여러 주제를 지원하며, **현재 공개한 주제는 Kubernetes 하나**다. [Kubernetes 한국어 문서 홈](https://kubernetes.io/ko/docs/home/)의 설치·개념·태스크·튜토리얼·레퍼런스를 학습하기 좋은 11개 문서 순서로 재구성한다.

- 공개 URL: <https://nohdol97.github.io/nohdol-study/>
- 공개 콘텐츠: `docs-site/content/kubernetes/`
- 카탈로그: `docs-site/catalog.json`

`docs/`의 하네스 ADR·스펙과 개인 `vault/`는 이 학습 과정의 내용이 아니며 사이트에 게시하지 않는다.

## 주제와 링크를 확장하는 방식

사용자가 현재 주제의 공식 문서 링크를 주면 해당 주제의 전체 목차에서 맞는 장을 찾아 다음 요소를 추가한다.

1. 기능이 해결하는 문제를 요약한 한 문장 모델
2. 컴포넌트 관계, 요청·데이터·제어 흐름 다이어그램
3. 최소 실행 가능한 YAML과 `kubectl` 예시
4. 필드와 동작 원리를 연결한 상세 해설
5. 흔한 실패 상태, 오류 메시지와 복구 순서
6. 개발 환경과 프로덕션 환경의 선택 차이
7. 공식 출처, 확인일과 버전·번역 최신성
8. 원리를 재구성하는 복습 질문

공식 한국어 문서가 원문보다 오래되었다고 표시된 경우 최신성이 중요한 API와 동작은 현재 영어 문서와 레퍼런스도 함께 확인한다. 원문을 통째로 복제하지 않고, 학습에 필요한 설명과 예시를 독자적으로 구성한다.

새 학습 주제를 시작할 때는 `docs-site/content/<topic>/`에 독립된 목차와 본문을 만들고 `catalog.json`에 새 주제 카드를 등록한다. Kubernetes 목차와 다른 주제의 내용은 섞지 않는다.

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
