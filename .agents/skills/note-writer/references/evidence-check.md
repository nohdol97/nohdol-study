# Evidence-check protocol

This protocol is mandatory for material factual claims. It is a reference
behind the always-on rules in `AGENTS.md`, not an optional skill.

## Standard

Correctness is a claim-by-claim property, not a tone. Do not infer truth from
fluent prose, repeated model answers, citation count, popularity, or a source
title.

## Procedure

1. Extract the material claims whose falsity would change the answer or the
   user's understanding.
2. Classify each as sourced fact, synthesis, inference, hypothesis, prediction,
   or value judgment.
3. Find the best available evidence:
   - original paper, specification, official documentation, dataset, law,
     filing, or first-party statement;
   - reputable independent analysis when interpretation or corroboration
     matters;
   - secondary summaries only as discovery aids when primary material exists.
4. Inspect the exact supporting passage, table, method, version, date,
   population, and scope. A search snippet or citation list is not enough.
5. For high-stakes, disputed, surprising, quantitative, causal, unfamiliar, or
   time-sensitive claims, seek independent corroboration and actively look for
   counterevidence.
6. Check source independence. Multiple articles repeating one press release
   count as one source.
7. Assign one status:
   - `unverified`: not adequately checked;
   - `source-backed`: inspected relevant evidence, but authority or
     corroboration is limited;
   - `primary-confirmed`: an authoritative primary source directly establishes
     the claim;
   - `cross-checked`: independent evidence corroborates the claim;
   - `contested`: credible evidence conflicts or interpretation is unresolved.
8. State the checked date for facts that can change. Reverify rather than
   relying on memory.
9. Report limits plainly. Absence of found counterevidence is not proof of
   absence, and no process guarantees that every error has been eliminated.

## Claim ledger

For substantive verification, use:

| Claim | Kind | Status | Supporting evidence | Counterevidence or limit | Checked |
|---|---|---|---|---|---|

Place citations next to the claim they support. If evidence is insufficient,
narrow the statement or mark it unresolved instead of writing a confident
conclusion.

## AI and NotebookLM rule

Claude, Codex, Gemini, NotebookLM, and other model outputs are analysis tools,
not independent sources. NotebookLM citations are useful navigation, but
verification requires opening the underlying source and checking whether the
cited passage supports the claim in context.
