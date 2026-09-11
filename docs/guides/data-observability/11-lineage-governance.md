# Lineage, catalog, and governance: find impact and enforce access

A quality alert becomes actionable when it identifies affected outputs, processing runs, owners, and consumers. A lineage graph provides relationships to investigate. A catalog provides meaning and discovery. An execution policy decides who can actually read or change data.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Job / run / dataset | A processing definition / one execution / an identified data collection | Distinguish a recurring transformation from one execution and the datasets it reads or writes. **Concrete situation (illustrative):** A daily transformation fails, and responders need its inputs and outputs. → Identify the logical job, this specific run, and involved datasets. → Follow those identities through lineage events to affected downstream data. |
| Facet | An extensible metadata structure in OpenLineage | Attach structured lineage details without forcing every domain into a single fixed record shape. **Concrete situation (illustrative):** A lineage event needs schema or execution metadata beyond basic identities. → Attach an appropriate versioned facet to the correct entity. → Verify consumers interpret its type and scope consistently. |
| Column lineage | A relationship between input and output columns | Trace how sensitive or incorrect input columns affect published output fields. **Concrete situation (illustrative):** A sensitive source column may feed several reports through transformations. → Inspect captured column-level lineage and transformation coverage. → Confirm suspected dependencies in the actual SQL where instrumentation is incomplete. |
| RBAC / ABAC | Access based on roles / access based on attributes and policy | Express who may access data using roles or evaluated attributes appropriate to the policy. **Concrete situation (illustrative):** Analysts need access by team role, while some datasets also depend on classification. → Model role-based and attribute-based policy conditions explicitly. → Test allowed and denied combinations with representative identities. |
| Classification | A label such as public, internal, or sensitive that informs handling rules | Apply handling, access, and retention rules according to a dataset's sensitivity. **Concrete situation (illustrative):** A new dataset contains contact details that should receive restricted handling. → Classify fields using the organization's defined categories. → Verify downstream access and retention rules consume those classifications. |
| Audit | A retained record of access and administrative actions | Investigate who accessed or changed protected resources and review policy enforcement afterward. **Concrete situation (illustrative):** A team must explain who queried a restricted table yesterday. → Retain attributable access audit events with appropriate protection. → Reconstruct the action, actor, target, and time from the recorded evidence. |

## Understand the model first

1. Assign stable namespace/name identities to datasets and jobs.
2. Record each run's actual inputs, outputs, status, and version information.
3. Connect lineage to ownership, documentation, classification, and quality results.
4. Use those relationships to discover candidate impact.
5. Verify access at the query, storage, or serving boundary and audit the outcome.

OpenLineage's core model separates datasets, jobs, and runs. Facets extend their metadata. OpenTelemetry spans describe operations; a shared run reference can join the two models without treating a trace as a table version. Instrumentation coverage determines what lineage is actually observed.

## A minimal event to review

This synthetic OpenLineage event illustrates a completed transformation. A complete implementation also emits appropriate lifecycle events and validates them against the pinned schema. Replace the illustrative producer URL with the actual emitter's documented identity.

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-09-10T01:00:00Z",
  "run": {"runId": "0c847daa-238e-4eca-8054-5583bb212d29"},
  "job": {"namespace": "study", "name": "orders.clean"},
  "inputs": [{"namespace": "study", "name": "orders.raw"}],
  "outputs": [{"namespace": "study", "name": "orders.accepted"}],
  "producer": "https://example.org/study-emitter",
  "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json"
}
```

The event does not yet identify physical snapshots, column transformations, ownership, or downstream consumers. Add supported facets and a controlled receipt reference rather than assuming the three names capture all those details. An event saying `COMPLETE` also does not prove a quality gate passed unless the contract and implementation connect those outcomes.

## Catalog metadata with an owner

| Metadata | Why a consumer needs it |
|---|---|
| Meaning, grain, units, time basis | Avoid a syntactically valid but semantically wrong query |
| Owner and support route | Find a person or team responsible for recovery |
| Schema and contract version | Know whether an integration remains compatible |
| Current publication and quality status | Distinguish discoverable data from usable data |
| Classification and usage policy | Determine the permitted handling and purpose |
| Input/output lineage and coverage | Investigate changes and qualify gaps in impact analysis |
| Retention and deprecation | Plan reproducibility, migrations, and removal |

Start with explicit metadata for a handful of datasets. Evaluate DataHub or OpenMetadata when search, ownership workflows, ingestion integrations, and scale justify a catalog service. Marquez is an alternative for exploring OpenLineage-backed run relationships. Compare using your actual integrations and permission model, not a feature-count table alone.

## Governance follows the data into derivatives

Catalog tags are inputs to policy, not automatic enforcement. Test reader identities at SQL engines, object storage, exports, caches, and retrieval services. Row filters and column masks must be checked under the identities that real consumers use. A service account with broad access can bypass an otherwise careful user-facing UI if the service fails to enforce the caller's scope.

Keep query permission separate from permission to discover metadata. Even table names and lineage can reveal sensitive business structure. Audit allowed reads, denied reads, policy changes, exports, and ownership changes. Set retention and access for audit records themselves.

When a source record is removed under your data policy, identify every relevant derivative: table history, materialized marts, cached responses, embeddings, and captured prompts. Decide which are deleted, expired, or retained under an applicable policy. This is an engineering propagation exercise; the course does not prescribe legal retention periods.

## Dataset, job, run, and facet identities

A dataset identity must distinguish namespaces such as production and development; a display name alone is ambiguous. A job identifies the transformation definition, while a run identifies one execution attempt or lifecycle instance according to the integration. A retry can use a new run identity while retaining a parent/logical-operation relationship. The output snapshot identity belongs beside those references so an investigation does not confuse “the same table name” with “the same data.”

Emit appropriate lifecycle events such as START and COMPLETE or FAIL. Events can arrive late or be delivered again, so a lineage backend must reconcile their identities and ordering. A missing COMPLETE can mean a failed run, a still-running job, or lost emission. Compare with scheduler and publication records before declaring a cause.

Facets attach typed metadata to the appropriate entity. Dataset schema belongs with the dataset; a source revision or execution detail belongs with the relevant job/run facet. Use standard facets where they express the meaning; custom facets need stable names and schema references. A field containing arbitrary JSON is not interoperable merely because it is inside an OpenLineage envelope.

### Table lineage versus column lineage

If `daily_revenue.total` is `SUM(orders.amount_cents)`, a column edge identifies the contributing field and transformation. A table edge only says that daily_revenue depends on orders. Renaming an unrelated source column might affect a `SELECT *` consumer even when a more precise projected consumer is safe. Conversely, an unchanged column name with a changed unit can break meaning without changing the graph structure.

Static SQL parsing describes potential dependencies; runtime instrumentation can record what executed. Dynamic SQL, UDF internals, file exports, and manual copies can leave gaps in either approach. State collection coverage explicitly and compare emitted input/output identities with a known fixture graph.

## Compute downstream impact with a cycle-safe traversal

This Python example walks an explicitly declared synthetic graph. It does not discover hidden consumers or validate data truth. The cycle deliberately tests termination; sorted output makes the result reproducible.

<!-- executable: lineage-impact -->
```python
edges = {
    'raw': {'accepted'},
    'accepted': {'daily_revenue'},
    'daily_revenue': {'retrieval_index'},
    'retrieval_index': {'accepted'},
}
def descendants(start):
    seen, pending = {start}, [start]
    while pending:
        for node in edges.get(pending.pop(), set()):
            if node not in seen:
                seen.add(node)
                pending.append(node)
    return sorted(seen - {start})

found = descendants('raw')
assert found == ['accepted','daily_revenue','retrieval_index']
print('candidate_impact:', ', '.join(found))
print('coverage: declared edges only')
```

Expected output:

```text
candidate_impact: accepted, daily_revenue, retrieval_index
coverage: declared edges only
```

Remove an edge and the answer shrinks without proving the real impact shrank. Attach owners and known consumers to the resulting nodes, then validate the suspected breaking change against their contracts. A lineage service should also report when the relevant collection integration was last observed.

## RBAC, ABAC, masking, and row/column enforcement

RBAC grants capabilities through roles: a transformation role writes a curated table, a consumer role reads an approved view, and a steward role manages metadata. ABAC evaluates attributes of the caller, resource, and context, such as domain membership and classification. Tags are inputs; a query/storage/serving enforcement point must actually evaluate them. Trustworthy attribute issuance matters because a caller-supplied `department=finance` string cannot authorize itself.

Row-level security limits which records are visible; column permissions can prevent selecting sensitive fields; masking transforms a field's visible value under policy. A mask in a view provides little protection if the same role can read the unmasked base table. A shared service identity also needs caller-specific enforcement when acting for users. Test direct table reads, views, exports, caches, and retrieval endpoints under the actual consumer identity.

For PostgreSQL, table owners and privileged roles can bypass RLS under documented conditions. An RLS test run only as the owner therefore does not prove the consumer policy. In a disposable database, compare a non-owner reader's permitted region query with a forbidden-region query and a forbidden-column query. Expected outcomes are permitted rows, zero forbidden rows, and a permission error respectively; use a separate administrative fixture to prove the forbidden rows actually exist.

## Classification, PII, and auditing through derivatives

Classification assigns handling requirements to fields/datasets. Automated detection can suggest candidates such as email-like values, but a pattern does not establish the business purpose or complete sensitivity classification. A hash of a stable identifier can remain linkable; “hashed” should not automatically mean “safe for unrestricted sharing.” Propagate the handling decision to aggregates, extracts, embeddings, and debug captures according to what they can reveal.

An audit record should identify the actor, action, resource/version, policy decision, time, and correlation reference. Capture denied actions and policy changes as well as successful reads. Protect the audit store from the identity being audited and test its observation path. Audit logging answers what was attempted/allowed; it does not prevent a forbidden read by itself.

Catalog tools such as DataHub/OpenMetadata organize discovery, ownership, descriptions, and integration metadata; Marquez specializes in the OpenLineage execution graph. Evaluate identity reconciliation and your actual ingestion adapters first. Ten duplicate representations of one dataset split impact analysis and ownership even if the UI graph looks rich.

## Failure exercise and interpretation

Create `raw -> accepted -> daily_revenue -> retrieval_index` with two documented consumers. Introduce a breaking amount-unit change. Query descendants to identify candidate impact and owners, then inspect whether the lineage emitter captured the actual transformation. Disable one emitter and repeat: the missing edge must become a coverage gap, not evidence that nothing is affected.

Test three identities: authorized reader, unauthorized reader, and pipeline writer. The reader should access only allowed rows/columns, the unauthorized reader should fail at the execution boundary, and the writer should not gain unrelated dataset access. Verify the audit record for each attempt. Restore the original policy and check both allow and deny behavior again.

## Example results

Illustrative impact and access review.

```text
changed: raw
candidate descendants: accepted, daily_revenue, retrieval_index
documented consumers: 2
disabled emitter: INCOMPLETE COVERAGE
authorized reader: allowed permitted rows/columns
unauthorized reader: denied
pipeline writer on unrelated dataset: denied
```

Fewer descendants after disabling an emitter is not a smaller blast radius. Actual identity-specific executions and audit receipts are needed to pass the policy exercise. Recheck retrieval and debug paths after revocation.

## Explain it in your own words

Can an accurate lineage edge prove the output is accurate? No; it describes derivation, not correctness. Can a graph prove no other consumer exists? Only within declared, verified coverage. Explain the evidence needed to make a downstream-impact claim.

Continue with [cloud platform implementations](12-cloud-platforms.md).

<!-- source: https://openlineage.io/docs/spec/object-model/ | checked: 2026-09-10 | datasets, jobs, runs and facets -->
<!-- source: https://openlineage.io/spec/2-0-2/OpenLineage.json | checked: 2026-09-10 | illustrative event schema -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage | checked: 2026-09-10 | lineage coverage and permissions are bounded -->
<!-- source: https://www.postgresql.org/docs/current/ddl-rowsecurity.html | checked: 2026-09-10 | row-policy enforcement and bypass roles -->
