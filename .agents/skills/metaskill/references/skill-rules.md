# Skill authoring rules

Apply these rules to every skill in this workspace.

1. `SKILL.md` starts on line 1 with YAML frontmatter. `name` matches the
   directory, and `description` is a single English line.
2. The description says what the skill does, when it triggers, includes Korean
   trigger phrases where useful, and states negative boundaries when adjacent
   skills overlap. Keep it under the CLI hard limit with margin.
3. Keep the body under 500 lines. Move detailed schemas, command catalogs, and
   conditional variants into one-level `references/`.
4. Explain why a gate exists, not only what to do. This lets the rule survive
   cases not named in the checklist.
5. Include real commands for mechanical procedures. A routing-only skill must
   name the concrete downstream skill or script.
6. End with a small **With / without** table that makes the intended behavioral
   difference observable.
7. For behavioral disciplines, test a realistic pressure or failure case. For
   deterministic scripts, use executable tests. Reference-only skills do not
   need artificial pressure tests.
8. Author model-read assets in English and update the Korean summary view in
   the same change.
9. Skill edits are reliably discovered on the next CLI session. Report this
   when a new or renamed skill was added.

For `.agents/skills/README.ko.md`, every actual skill directory gets one
`## <skill-name>` section with:

- 한 줄 역할
- 언제 쓰나
- 언제 안 쓰나
- 핵심 절차
- 주요 산출물 또는 완료 기준

The summary is a user-readable map, not a copy of the full skill.
