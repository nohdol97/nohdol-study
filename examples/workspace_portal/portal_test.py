#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


MODULE_PATH = Path(__file__).with_name("portal.py")
SPEC = importlib.util.spec_from_file_location("workspace_portal", MODULE_PATH)
assert SPEC and SPEC.loader
portal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(portal)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory) / "_workspace"
    created = portal.initialize(workspace)
    check(len(created) == 4, f"init should create four files, got {len(created)}")
    check(not portal.validate(workspace), "empty initialized portal should validate")
    original = (workspace / "index.html").read_text(encoding="utf-8")
    check(not portal.initialize(workspace), "second init should preserve all files")
    check((workspace / "index.html").read_text(encoding="utf-8") == original, "init must not overwrite portal")

    site = workspace / "sites" / "robot-ai" / "index.html"
    site.parent.mkdir(parents=True)
    site.write_text("<!doctype html><title>Robot AI</title>", encoding="utf-8")
    record = portal.register_site(
        workspace,
        slug="robot-ai",
        title="Robot AI",
        description="통합 학습 사이트",
        href=None,
        category="Academy",
        tags=["robot", "VLA", "robot"],
        status="ready",
    )
    check(record["href"] == "sites/robot-ai/index.html", "default href should stay below the slug")
    check(record["tags"] == ["robot", "VLA"], "tags should be unique and sorted")
    check(not portal.validate(workspace), "registered portal should validate")

    portal.register_site(
        workspace,
        slug="robot-ai",
        title="Robot AI Academy",
        description="갱신된 설명",
        href=None,
        category="Academy",
        tags=["VLA"],
        status="ready",
    )
    manifest = json.loads((workspace / "sites.json").read_text(encoding="utf-8"))
    check(len(manifest["sites"]) == 1, "register should update a slug, not duplicate it")
    check(manifest["sites"][0]["title"] == "Robot AI Academy", "updated record should be stored")

    try:
        portal.register_site(
            workspace,
            slug="escape",
            title="Escape",
            description="invalid",
            href="../outside.html",
            category="Test",
            tags=[],
            status="ready",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal must be rejected")

    site.unlink()
    failures = portal.validate(workspace)
    check(any("does not exist" in failure for failure in failures), "missing site entry should fail validation")

print("workspace portal tests: PASS")
