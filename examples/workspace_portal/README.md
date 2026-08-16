# Workspace Portal

`_workspace/sites/<slug>/` 아래의 사용자용 다이내믹 HTML 사이트를 `_workspace/index.html` 한 곳에서 여는 로컬 포털이다. 지식 정본은 아니며 `_workspace/`와 함께 Git에서 제외된다.

```sh
python3 examples/workspace_portal/portal.py init
python3 examples/workspace_portal/portal.py register \
  --slug sample-site \
  --title "Sample Site" \
  --description "무엇을 학습하는 사이트인지 한 문장으로 설명" \
  --category Study \
  --tag demo
python3 examples/workspace_portal/portal.py check
python3 examples/workspace_portal/portal.py serve
```

`register` 전에 `_workspace/sites/sample-site/index.html`이 있어야 한다. 등록 파일은 `_workspace/sites.json`이며, 같은 slug를 다시 등록하면 항목을 갱신한다. `init`은 없는 포털 파일만 만들고 기존 로컬 포털을 덮어쓰지 않는다.
