# Lineage, catalog, and governance: find impact and enforce access

A quality alert becomes actionable when it identifies affected outputs, processing runs, owners, and consumers. A lineage graph provides relationships to investigate. A catalog provides meaning and discovery. An execution policy decides who can actually read or change data.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Job / run / dataset | A processing definition / one execution / an identified data collection |
| Facet | An extensible metadata structure in OpenLineage |
| Column lineage | A relationship between input and output columns |
| RBAC / ABAC | Access based on roles / access based on attributes and policy |
| Classification | A label such as public, internal, or sensitive that informs handling rules |
| Audit | A retained record of access and administrative actions |

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

## Failure exercise and interpretation

Create `raw -> accepted -> daily_revenue -> retrieval_index` with two documented consumers. Introduce a breaking amount-unit change. Query descendants to identify candidate impact and owners, then inspect whether the lineage emitter captured the actual transformation. Disable one emitter and repeat: the missing edge must become a coverage gap, not evidence that nothing is affected.

Test three identities: authorized reader, unauthorized reader, and pipeline writer. The reader should access only allowed rows/columns, the unauthorized reader should fail at the execution boundary, and the writer should not gain unrelated dataset access. Verify the audit record for each attempt. Restore the original policy and check both allow and deny behavior again.

## Explain it in your own words

Can an accurate lineage edge prove the output is accurate? No; it describes derivation, not correctness. Can a graph prove no other consumer exists? Only within declared, verified coverage. Explain the evidence needed to make a downstream-impact claim.

Continue with [cloud platform implementations](12-cloud-platforms.md).

<!-- source: https://openlineage.io/docs/spec/object-model/ | checked: 2026-09-10 | datasets, jobs, runs and facets -->
<!-- source: https://openlineage.io/spec/2-0-2/OpenLineage.json | checked: 2026-09-10 | illustrative event schema -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage | checked: 2026-09-10 | lineage coverage and permissions are bounded -->
