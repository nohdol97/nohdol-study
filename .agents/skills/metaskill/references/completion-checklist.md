# Harness improvement completion checklist

- [ ] `REGISTRY.md` profile allowed tracked changes.
- [ ] The user requested or approved the harness change.
- [ ] Always-on rules live in `AGENTS.md`; repeatable optional work lives in a
      skill.
- [ ] Every changed skill has valid frontmatter, a matching directory name, a
      bounded description, reasons, boundaries, commands where relevant, and a
      With / without table.
- [ ] Created/renamed/retired skills are reflected in root `README.md` and
      `.agents/skills/README.ko.md`.
- [ ] `AGENTS.ko.md` matches the current `AGENTS.md` meaning and source hash.
- [ ] New or changed ADR/spec/proposal state is reflected in `docs/README.md`.
- [ ] `docs/harness-changelog.md` records the change.
- [ ] Installation data and vault content remain untracked.
- [ ] Relevant focused tests and the full verification pass.
- [ ] Symlinks still resolve: `.claude/skills` and `.claude/agents`.
- [ ] Unverified live-session or external-service behavior is reported
      explicitly.
