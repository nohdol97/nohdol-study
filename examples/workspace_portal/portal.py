#!/usr/bin/env python3
"""Initialize, register, validate, or serve the local _workspace site portal."""

from __future__ import annotations

import argparse
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = REPO_ROOT / "_workspace"
TEMPLATE_ROOT = Path(__file__).resolve().parent / "template"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_SITE_FIELDS = {"slug", "title", "description", "href", "category", "tags", "updated", "status"}


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"portal path must stay inside _workspace: {value}")
    return path


def initialize(workspace: Path) -> list[Path]:
    workspace.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for source in sorted(TEMPLATE_ROOT.rglob("*")):
        relative = source.relative_to(TEMPLATE_ROOT)
        target = workspace / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            created.append(target)
    (workspace / "sites").mkdir(exist_ok=True)
    return created


def load_manifest(workspace: Path) -> dict:
    manifest_path = workspace / "sites.json"
    if not manifest_path.is_file():
        raise ValueError("sites.json is missing; run portal.py init first")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read sites.json: {error}") from error
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("sites"), list):
        raise ValueError("sites.json must contain version=1 and a sites array")
    return data


def write_manifest(workspace: Path, data: dict) -> None:
    data["updated"] = date.today().isoformat()
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    target = workspace / "sites.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(target)


def register_site(
    workspace: Path,
    *,
    slug: str,
    title: str,
    description: str,
    href: str | None,
    category: str,
    tags: list[str],
    status: str,
) -> dict:
    initialize(workspace)
    if not SLUG.fullmatch(slug):
        raise ValueError("slug must use lowercase letters, digits, and single hyphens")
    relative = safe_relative_path(href or f"sites/{slug}/index.html")
    expected_prefix = PurePosixPath("sites") / slug
    if tuple(relative.parts[:2]) != tuple(expected_prefix.parts):
        raise ValueError(f"registered site must live below sites/{slug}/")
    if not (workspace / Path(*relative.parts)).is_file():
        raise ValueError(f"site entry does not exist: {relative}")
    record = {
        "slug": slug,
        "title": title.strip(),
        "description": description.strip(),
        "href": relative.as_posix(),
        "category": category.strip(),
        "tags": sorted({tag.strip() for tag in tags if tag.strip()}, key=str.casefold),
        "updated": date.today().isoformat(),
        "status": status,
    }
    if not record["title"] or not record["description"] or not record["category"]:
        raise ValueError("title, description, and category must not be empty")
    manifest = load_manifest(workspace)
    manifest["sites"] = [item for item in manifest["sites"] if item.get("slug") != slug]
    manifest["sites"].append(record)
    manifest["sites"].sort(key=lambda item: (item.get("category", "").casefold(), item.get("title", "").casefold()))
    write_manifest(workspace, manifest)
    return record


def validate(workspace: Path) -> list[str]:
    failures: list[str] = []
    for required in ("index.html", "sites.json", "assets/portal.css", "assets/portal.js"):
        if not (workspace / required).is_file():
            failures.append(f"missing portal file: {required}")
    try:
        manifest = load_manifest(workspace)
    except ValueError as error:
        return failures + [str(error)]
    seen: set[str] = set()
    for index, site in enumerate(manifest["sites"]):
        prefix = f"sites[{index}]"
        if not isinstance(site, dict):
            failures.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED_SITE_FIELDS - set(site)
        if missing:
            failures.append(f"{prefix} missing fields: {', '.join(sorted(missing))}")
            continue
        slug = site["slug"]
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            failures.append(f"{prefix}.slug is invalid: {slug}")
        elif slug in seen:
            failures.append(f"duplicate slug: {slug}")
        seen.add(slug)
        if not isinstance(site["tags"], list) or not all(isinstance(tag, str) and tag for tag in site["tags"]):
            failures.append(f"{prefix}.tags must be non-empty strings")
        try:
            relative = safe_relative_path(site["href"])
        except (TypeError, ValueError) as error:
            failures.append(f"{prefix}.href: {error}")
            continue
        if tuple(relative.parts[:2]) != ("sites", slug):
            failures.append(f"{prefix}.href must stay below sites/{slug}/")
        elif not (workspace / Path(*relative.parts)).is_file():
            failures.append(f"{prefix}.href does not exist: {relative}")
    return failures


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create missing portal files without overwriting existing files")
    register = commands.add_parser("register", help="add or update one site entry")
    register.add_argument("--slug", required=True)
    register.add_argument("--title", required=True)
    register.add_argument("--description", required=True)
    register.add_argument("--href")
    register.add_argument("--category", default="Study")
    register.add_argument("--tag", action="append", default=[])
    register.add_argument("--status", choices=("draft", "ready", "archived"), default="ready")
    commands.add_parser("check", help="validate portal files, manifest, and registered entry points")
    serve = commands.add_parser("serve", help="serve the entire _workspace tree from one local HTTP server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=4173)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    workspace = args.workspace.resolve()
    try:
        if args.command == "init":
            created = initialize(workspace)
            print(f"portal initialized: {workspace} ({len(created)} files created)")
        elif args.command == "register":
            record = register_site(
                workspace,
                slug=args.slug,
                title=args.title,
                description=args.description,
                href=args.href,
                category=args.category,
                tags=args.tag,
                status=args.status,
            )
            print(f"portal registered: {record['slug']} -> {record['href']}")
        elif args.command == "check":
            failures = validate(workspace)
            if failures:
                for failure in failures:
                    print(f"FAIL: {failure}", file=sys.stderr)
                return 1
            print(f"portal check: PASS ({len(load_manifest(workspace)['sites'])} sites)")
        elif args.command == "serve":
            failures = validate(workspace)
            if failures:
                raise ValueError("portal validation failed: " + "; ".join(failures))
            handler = lambda *handler_args, **handler_kwargs: SimpleHTTPRequestHandler(  # noqa: E731
                *handler_args, directory=str(workspace), **handler_kwargs
            )
            server = ThreadingHTTPServer((args.host, args.port), handler)
            print(f"workspace portal: http://{args.host}:{args.port}/")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nportal server stopped")
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
