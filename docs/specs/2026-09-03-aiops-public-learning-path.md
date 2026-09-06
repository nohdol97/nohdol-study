# AIOps Open Learning Path Specification

- Date: 2026-09-03
- Status: Implemented
- Related Decision: [ADR 009](../adr/009-public-docs-root-learning-paths.md)
- Implement prerequisites: [Public Docs Gateway](2026-09-03-public-docs-gateway.md), [DevOps Public Learning Path](2026-09-03-infra-specialist-public-learning-path.md)

## Goal

- The public document root provides a separate AIOps learning area from DevOps.
- AI Specialist's full map of models and applications and AI Transformation's full map of the operating platform are provided as prerequisite paths and taught in a `모델·검색·에이전트 → 배포 bundle → 운영 증거 계약 → 탐지·상관·진단 → 승인된 조치 → 사후 학습` closed loop.
- Avoid duplication by reusing existing DevOps Observability/SRE·Kubernetes·GitOps·Security·Traffic·Reliability documents as prerequisites and follow-up links.
- Distinguishes between AI-generated candidates and actual evidence, human approval and status change authority, command success, and user result recovery.

## non-goal

- Automatic posting or copying of sentences in personal `vault/` notes
- Full reference to specific observability/AIOps vendor products
- Design that confirms root cause or remediation authority with one model accuracy
- Live change lab that requires operating credentials
- Claiming that fully autonomous operation without humans is currently complete.

## public structure

| order | topic ID | public title | responsibility |
|---|---|---|---|
| A01 | `ai-specialist-core` | AI Specialist core models and applications | LLM·Vision/Generation·On-device·Time series/Recommendation·RAG/GraphRAG/NL2SQL/MCP input·Model·Evaluation·target contract |
| A02 | `ai-transformation-platform` | AI Transformation Operation Platform | GPU·distributed learning·LLM serving, MLOps/LLMOps, AI DevOps/FinOps, enterprise agent·identity·sandbox·durable operation |
| A03 | `aiops-foundations` | AIOps signals and operational topology | Connects metric·log·trace·event·change and service·deployment·resource relationships to incident bundle |
| A04 | `aiops-diagnosis` | Anomaly detection and evidence-based fault diagnosis | Step-by-step evaluation of symptom rule, anomaly candidate, alert grouping, evidence retrieval, RCA category and abstain |
| A05 | `aiops-remediation` | Approved Automated Recovery and Operational Learning | recommend·approve-to-run·auto-run rating, operation state machine, idempotency·abort·rollback·outcome verification |

The three operational closed-loop topics have three documents: `00-roadmap.md`, `01-*` concept chapters, and `02-*` guided lab chapters. The two hubs, which have a wide scope, have a roadmap and chapters for each module and pillar. AI Specialist has 6 documents including a roadmap, and AI Transformation has 5 documents including a roadmap, with a total of 5 topics and 20 documents.

## connection agreement

- A01 includes all five AI Specialist modules and connects the model/retrieval results to A02's bundle/evaluation unit and A03's evidence input.
- A02 includes all four AI Transformation pillars and creates model·prompt·index·tool·policy·runtime as a versioned bundle based on Kubernetes·GitOps·security·backend.
- A03 connects Infra's `observability-sre`, Kubernetes observation field, GitOps change revision, and A01·A02's model·bundle ID as prerequisites.
- A04 receives the A03 incident bundle as input and connects traffic retry/overflow and deployment cohort as examples of cause candidates.
- A05 receives the A04 diagnosis candidate, but separates the execution authority into a separate gate, and connects action·identity·rollback·SLO with Infra's backend·traffic·GitOps·security·reliability document.
- All relative links must be interpreted as the `#doc=<id>` internal route in the build results.

## Description and evidence contract

- Check material facts in official documents such as OpenTelemetry·Prometheus·Kubernetes·Gateway API or in the original paper and leave the URL, confirmation date, and version in the source comment.
- The private vault is only used for topic discovery and exploration of existing knowledge and is not cited as an open source.
- An anomaly score is not an incident or root cause, and temporal correlation is not causation.
- The LLM description is placed after the output contract with evidence ID, candidate category, counterevidence/omission, and abstain.
- Automation has a target·scope·precondition·approval·abort·rollback·verification contract that is separate from diagnostic confidence.

## lab safety agreement

- The lab is a Local or Plan only grade that uses only synthetic JSON and YAML.
- It does not change the actual cluster·cloud·ticket·monitoring state.
- When creating a temporary file, specify the exact `/tmp/aiops-incident-lab` target and cleanup.
- It distinguishes between the API/structural scope that dry-run verifies and the user results/external dependencies that cannot be verified.
- Operation with unknown results is not blind retried but is transferred to actual state reconciliation.

## Criteria for completion of implementation

- There are two paths in the catalog root, `infra` and `aiops`, and all topics are placed in exactly one.
- AIOps 5 topics and 20 documents are tracked in Git and searched and accessed through direct URL.
- The AI ​​Specialist roadmap places the LLM·Efficiency·Vision·Generation·On-device·Time Series·Recommendation·RAG·Structure Query/MCP items of 49 notes, and the AI ​​Transformation roadmap places all the infrastructure·serving·MLOps/LLMOps·DevOps/FinOps·enterprise agent·edge items of the hub and 49 sub-notes in the public domain.
- Each topic has a reviewable example of either Mermaid or JSON·YAML·shell showing relationships/states.
- Each roadmap has a beginner's problem situation, a glossary of terms, a learning sequence, completion criteria, verification problems, and operational judgments.
- Each detailed chapter first explains the terminology or preparatory conditions and distinguishes the scope of the results and the remaining uncertainties.
- Build tests identify representative cross-links between AIOps and DevOps.
- Source comments will be removed from public HTML and private paths will continue to be rejected.
- Path → topic → document navigation is not cut off on desktop and mobile.
