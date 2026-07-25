---
name: context7
description: Retrieve current, version-specific library and framework documentation before answering API, configuration, migration, or debugging questions. Use for current SDK and library docs; use official vendor documentation as fallback when Context7 is unavailable. Do NOT use for Anthropic or Claude model IDs, pricing, and API questions, for reading one specific user-provided URL, or for general programming concepts and business-logic debugging.
---

# context7 — Current library documentation

## Why

Library APIs change faster than durable study notes. Version-specific retrieval
prevents an old signature or configuration from being taught as current.

1. Resolve the exact library and version before querying.
2. Use Context7 MCP when available; otherwise read the current official
   documentation directly.
3. Do not answer version-sensitive signatures or configuration from memory.
4. Treat indexed documentation as a retrieval aid. For material claims, inspect
   the official page and record the version and checked date.
5. A user-provided URL goes through direct web capture rather than Context7.
6. Never let MCP absence block the answer; fall back to official sources.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| API freshness | Memory or stale snippets | Exact version and current docs checked |
| MCP outage | Answer blocked or guessed | Official documentation fallback |
| Evidence | Indexed text treated as authority | Official passage and checked date retained |
