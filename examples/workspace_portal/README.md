# Workspace Portal

This local portal opens user-facing dynamic HTML sites under `_workspace/sites/<slug>/` from a single entry point, `_workspace/index.html`. It is not a knowledge source of truth and is excluded from Git along with `_workspace/`.

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

There must be `_workspace/sites/sample-site/index.html` before `register`. The registration file is `_workspace/sites.json`, and the item is updated if the same slug is registered again. `init` only creates portal files that do not exist and does not overwrite existing local portals.
