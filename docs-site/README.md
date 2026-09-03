# 공개 문서 사이트

GitHub Pages에 배포하는 nohdol-study 문서 게이트웨이다. `docs/`, 루트 안내서, 예제 README를 복사하지 않고 빌드 시 읽어 정적 사이트로 만든다.

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

## 문서 공개

`catalog.json`에 주제와 문서를 등록한다. `path`는 저장소 안에서 Git이 추적하는 Markdown만 허용한다. `vault/`, `REGISTRY.md`, `_workspace/`, 절대 경로, 상위 경로 이탈은 빌드가 거부한다.

`main`에 반영되면 `.github/workflows/docs-pages.yml`이 테스트·빌드 후 Pages artifact를 배포한다. 저장소의 **Settings → Pages → Build and deployment → Source**는 최초 한 번 `GitHub Actions`로 선택해야 한다.

이 저장소는 검증을 마친 일반 변경을 `origin/main`에 별도 확인 없이 commit·push하는 상시 승인을 갖는다. force push, 히스토리 재작성, 릴리스와 다른 원격·브랜치는 여기에 포함되지 않는다.

`dist/`는 생성물이며 커밋하지 않는다.
