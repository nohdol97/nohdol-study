# DevOps Public Learning Path Specification

- Date: 2026-09-03
- Status: Implemented
- Related Decision: [ADR 008](../adr/008-public-docs-gateway.md)
- Preceding implementation: [Public Docs Gateway](2026-09-03-public-docs-gateway.md)

## Goal

- It provides a learning path to design and operate a cloud-native system by connecting Linux, network, AWS, Terraform, Helm, operations, data, and back-end application layers to the current Kubernetes course.
- Rather than listing product features, it is described as the operating life cycle of `요구사항 → 선언 상태 → 실제 자원 → 관측 → 장애 복구 → 비용`.
- Each topic is presented as an independent card and its own roadmap, with prerequisite/successor relationships indicated, leading to the overall DevOps path.
- It is based on a locally reproducible lab, and the lab that creates AWS resources is separated into a selection process that specifies the expected impact, cost, and cleanup procedures.
- The in-depth product track covers the convergence of EKS' workload demands to AWS compute capacity, including only Karpenter.

## Target audience and completion results

The target audience is application developers who have experience creating files and executing basic shell commands. You may be new to Linux operation, network, AWS, and database operation tools. Kubernetes knowledge is not a prerequisite for the entire course, and you are advised to first complete the Kubernetes course on this site before entering Helm and Karpenter. This is not a course to prepare for a specific certification exam or memorize all AWS services.

This process is not a reference in which an expert compresses and searches for what he or she already knows, but is a learning process in which a first-time viewer acquires the expert's judgment order by repeatedly observing and explaining failures. So it doesn't eliminate jargon and product names, but it doesn't use them before defining them. Easy analogies are used only to create a first intuition and immediately explain how they differ from the boundaries of real systems.

After completing the entire path, the reader should be able to describe and reproduce the following:

- Find the first bottleneck of application failure in the Linux process·memory·filesystem·network state.
- Tracks DNS·TCP·TLS·load balancer·VPC·Kubernetes Service as one request path.
- Design ownership and trust boundary of AWS account·IAM·VPC·compute·storage·database.
- Explains the relationship between Terraform state and actual AWS resources and operates plan·apply·import·drift·rollback procedures.
- Render and verify the Helm chart and explain the boundaries where GitOps converges to the desired state and the actual cluster.
- Design alert and incident response by connecting metric·log·trace and SLI/SLO.
- Select PostgreSQL, Redis, and DynamoDB not by name but by transaction·access pattern·consistency·failure mode and check the backup and recovery results.
- Include least privilege, secret·encryption, artifact provenance, and audit boundaries in the deployment flow.
- Determine responsibility for duplication, ordering, retry, and dead-letter of queue·event stream.
- RPO, RTO, capacity, and cost goals are reflected in the architecture and operation runbook.
- Karpenter's provisioning·consolidation·disruption judgment is verified with pod scheduling, AWS capacity, and cost signals.
- Connects API contracts, transaction invariants, runtime capacity, distributed workflow, cache and compatible deployments to the actual failure and recovery boundaries of the infrastructure.

## range

### existing course

`kubernetes` is maintained as a common prerequisite process. The new process does not duplicate the Pod lifecycle, Service·DNS·NetworkPolicy, storage, scheduling, RBAC, observability, and production operation descriptions in the existing chapters. In new topics, internally link to prerequisite chapters as needed and expand product-specific operating agreements on top of them.

### New Topic Cards and Responsibilities

| order | topic ID | public title | Responsibilities and Core Scope |
|---:|---|---|---|
| 1 | `linux` | Linux system operations | process·signal·systemd, user·permission, filesystem·mount, memory·OOM, CPU·load, disk·I/O, namespace·cgroup, basic diagnostic tool |
| 2 | `networking` | Network and request path | CIDR·subnet, routing·NAT, DNS, TCP, TLS, HTTP, load balancer, firewall, connection·packet diagnosis |
| 3 | `aws-foundations` | Based on AWS infrastructure | Account·Organizations concept, shared responsibility of IAM·STS, VPC, EC2·ELB·Auto Scaling, Route 53, S3·EBS, RDS·EKS |
| 4 | `terraform-aws` | Terraform on AWS | language·provider, resource graph, module, version lock, state backend·locking, plan·apply, import·moved, drift, testing, CI approval |
| 5 | `helm-gitops` | Helm Charts and GitOps | chart structure, template·values·schema, dependency, hook·CRD, release·rollback, OCI registry, Kustomize boundary, Argo CD sync·drift·promotion |
| 6 | `observability-sre` | Observability and SRE | Prometheus·PromQL·Alertmanager, Grafana, OpenTelemetry Collector, log·trace connection, SLI·SLO·error budget, on-call·incident·postmortem |
| 7 | `postgresql` | PostgreSQL Operations | process·connection, MVCC, WAL·checkpoint·VACUUM, index·query plan, lock·wait diagnosis, PgBouncer, backup·PITR, replication·failover, RDS responsibility boundary |
| 8 | `nosql` | Redis and DynamoDB | NoSQL selection criteria, Redis data type·TTL·eviction·persistence·Sentinel/Cluster, DynamoDB partition key·index·consistency·capacity·Streams·backup, hot key response |
| 9 | `infrastructure-security` | infrastructure security | AWS IAM·STS and least privilege, KMS·Secrets Manager, network boundary, Kubernetes RBAC·Secret connection, container image scan·SBOM·signature, audit trail |
| 10 | `messaging` | Messaging and event infrastructure | Role of SQS·SNS·EventBridge and Kafka, queue and event log, delivery·ordering·idempotency, retry·backoff·DLQ, retention·replay·schema evolution |
| 11 | `reliability-finops` | Reliability·DR·FinOps | availability target, backup·restore, RPO·RTO, multi-AZ·region judgment, capacity planning, tagging·cost allocation, rightsizing, On-Demand·Reserved·Spot selection |
| 12 | `karpenter` | Karpenter Deepening | EKS integration, workload demand and node provisioning, NodePool·node class·claim hierarchy, topology·capacity type, consolidation·disruption, PDB·termination, observation·cost·recovery |
| 13 | `traffic-resilience` | Traffic control and service resilience | Gateway·Route ownership, full deadline·per-try timeout, retry budget, circuit breaker·outlier detection, blast radius and recovery verification |
| 14 | `backend-engineering` | Operational backend engineering | HTTP·API contract, domain invariant·transaction·outbox, concurrency·capacity·runtime, partial failure·fencing·saga, cache·performance, contract test·online migration·incremental deployment |

### Explicitly excluding in-depth tracks

Do not add the following as separate topics in the initial DevOps path.

- Separate image factory from Ansible·Packer
- Installation of Cilium/eBPF and Envoy·Istio and deepening of service mesh for each product. However, common traffic failure contracts are covered in `traffic-resilience`.
- Separate secret platform from Vault
- OpenTofu·Pulumi·Crossplane comparison process
- Independent Chaos Engineering product courses
- In-depth courses for each product in MongoDB, Cassandra, and OpenSearch
- Solving multi-cloud and AWS certification problems

Names may be mentioned briefly to explain concepts within the basic course, but the scope does not extend to installation/operation labs or product comparisons. New advanced topics will only revise this specification when you separately approve the scope.

## Full learning sequence

```text
Linux ──> Networking ──> AWS Foundations ──> Terraform on AWS
                                      │                 │
                                      └─> Kubernetes ───┴─> Helm & GitOps
                                                               │
                    ┌──────────────────────────────────────────┤
                    v                  v                        v
          Observability & SRE     PostgreSQL / NoSQL      Security / Messaging
                    └──────────────────┬────────────────────────┘
                                       v
                              Reliability & FinOps
                                       v
                                Karpenter Deepening
                                       │
        API contract ─> Transaction ─> Capacity ─> Distributed Workflow ─> Cache ─> Compatible deployment
                                       └────────────> AIOps evidence, diagnosis, and recovery
```

The order of cards in the catalog follows the prerequisite relationship above, but readers can open each topic directly. `00-roadmap.md` in each topic separates required prerequisite documents from independently skippable chapters.

## document construction agreement

### R1. Topic unit

Each new topic is located independently in `docs-site/content/<topic>/` and has the following:

1. `00-roadmap.md`: Problems to be solved, prerequisite knowledge, chapter sequence, final lab, out-of-scope items
2. Concept chapter: resource·state·owner and control/data path managed by technology
3. Chapter Implementation: The smallest reproducible configuration and observation instructions.
4. Operation field: change, expansion, upgrade, backup or rollback
5. Failure Chapter: Normal State, Representative Failure, Evidence Gathering, Recovery and Completion Judgment
6. Production judgment: security, reliability, performance, cost trade-off

The number of chapters may vary depending on topic complexity. A chapter is not an independent concept but is created simply for the sake of length, or, conversely, when a chapter has different operational responsibilities, it is separated.

### R2. Chapter unit

Each chapter uses only relevant items and is based on the following structure.

- The operational questions this chapter answers and what you can do when you're done.
- prerequisite concept and one-sentence mental model
- Relationship diagram, sequence diagram, and state diagram when there are three or more components or state transitions
- Minimal execution example and pre- and post-change observation commands
- Judgment criteria for distinguishing between normal and failed results
- At least one realistic failure scenario, diagnostic sequence and recovery
- Different choices in development, verification, and production environments
- Applicable trade-off among security, reliability, performance, and cost
- Review questions to reconstruct principles without memorizing answers
- Official source URL, confirmation date, version, translation, up-to-date non-exposed HTML annotation

Each topic is structured so that the reader can actually step onto the next learning ladder.

1. **Problem Spotting**: Shows one routine obstacle or repetitive task that you would experience without this technology.
2. **Learning words**: Terms that appear for the first time are introduced with easy Korean definitions, actual objects, and observation methods.
3. **Follow the action**: The process by which one input passes through several components and becomes a result is explained in numbers.
4. **Check by hand**: Reproduce steady state first with complete preparation procedures and examples.
5. **Fail on purpose**: Change only one condition at a time and find out what is different from the normal state.
6. **Recover and Prove**: Verify not only command success but also user results and remaining resources.
7. **Expanding on expert judgment**: Select trade-offs of security, reliability, performance, and cost with evidence.

When reading a document from top to bottom, readers should not have to look elsewhere for jargon that has not yet been defined. Place `처음 보는 사람을 위한 출발점` and the minimum terminology map in the topic roadmap, `이 장에서 처음 쓰는 말` in the concept chapter, and `실습 전에 준비할 것` in the lab chapter. Even if prerequisite concepts are connected by internal links, the one-sentence definition required to understand the current sentence is not omitted.

The kindness of the explanation is judged not by the tone of speech but by the connections that are not omitted.

- For key terms that appear for the first time, the boundaries between similar terms, management entity, and observation location are first explained.
- Abstract concepts are applied to a specific request, change, or failure situation to show the causal relationship from input to result.
- Before presenting commands and settings, state what you want to verify, and after execution, distinguish between what the output proves and what it does not yet prove.
- Normal and failed results are shown together, and the success of one step is not interpreted as the success of the entire service.
- Tables and diagrams are not used to re-list terms, but rather to explain differences in status, responsibility, and judgment criteria.
- English terms can first be introduced in the form of `쉬운 한국어 설명(공식 영문 용어)`, and then the English notation can be maintained to correspond to official documents and orders.
- If there are more than three key terms that appear for the first time in a paragraph, separate terminology explanations or action steps first.
- Review questions distinguish between `처음 이해했는지 확인` and `운영 판단으로 확장`, and for the previous questions, evidence of answers must be found in the text.
- Professional exceptions, optimization, and product comparison are separated into `더 깊이 보기` after understanding the basic flow.

Diagrams or failure labs are not forced into every chapter. Use diagrams only when relationships become clearer than a paragraph, and when failure is not actionable, write down testable thought experiments and necessary observational evidence.

### R3. Official sources and version policy

Sources take precedence over the official documentation and specifications of the implementation.

- Helm: <https://helm.sh/ko/docs/> and the latest English text
- Terraform: <https://developer.hashicorp.com/terraform/docs> and AWS provider official documentation
- PostgreSQL: Start from <https://www.postgresql.org/docs/current/>, but record the confirmed major version for version-sensitive operation.
- Redis: <https://redis.io/docs/latest/>
- DynamoDB·AWS: AWS Documentation and AWS Well-Architected Framework
- GitOps: Argo CD official documentation
- Observability: Prometheus, Grafana, OpenTelemetry official documentation
- Messaging: AWS SQS·SNS·EventBridge official documents and Apache Kafka official documents
- Karpenter: <https://karpenter.sh/docs/> and AWS EKS official documentation

The `latest` or `current` URL alone does not fix the behavior of a specific version. For content that may change, such as API, default values, support status, and cost, leave the version and `checked` date at the time of writing and check again before major revisions. AI summaries, search results, and existing vault notes are used only for source discovery and are not used as independent evidence of public facts.

Distinguish between the fact that an official document has been referenced and the claim that the official document directly states the same sentence. The easy meaning of terms, analogies, integrated scenarios, and operating tables connecting multiple products are indicated so that readers can see that they are not quotations from the original text but rather a synthesis for learning purposes. Facts determined directly by the implementation, such as API fields, default values, guarantees, and support status, are traced to the corresponding official source and version, and the comprehensive operation recommendation includes the scope of the evidence and assumptions.

### R4. Lab environment and safety

lab displays the following three levels near the title.

| rating | environment | contract |
|---|---|---|
| Local | Local shell·container·minikube or kind | No cost, just specify what tools you need and how to organize them |
| Plan only | Verification without remote change such as Terraform validate·test·plan | Specify whether AWS credential is required and backend access |
| AWS optional | Create and change actual AWS resources | Specify expected resources, charging possibilities, permissions, region, tag, success judgment and cleanup |

- Documents and examples do not include access keys, tokens, passwords, account IDs, or personal paths.
- Do not guide root users or long-term access keys to the default path. Use profile, role and temporary credentials.
- For examples of creating resources, idempotent confirmation and cleanup procedures are included in the same chapter. A separate warning is given as to whether deletion also removes backup·state·log.
- Rather than writing cost figures as fixed facts, region, point in time, usage conditions, and confirmation dates are indicated.
- `terraform apply`, AWS resource deletion, database failover, and Karpenter disruption show the scope of impact before execution and prepare signals to be observed first.
- CI does not create actual AWS resources. AWS live lab leaves verification records and limitations explicitly executed by the author in the document change description.

### R5. Required lab by topic

| topic | Minimum lab and proof of completion |
|---|---|
| Linux | Tracks the usage of one service's process·socket·memory·filesystem and diagnoses one of signal·OOM·disk pressure |
| Networking | Observe the request path from DNS lookup to TCP/TLS and load balancer or service backend and identify blocking in one section. |
| AWS Foundations | IAM role and VPC route are diagrammed, and public/private reachability is determined as an observation result rather than a setting. |
| Terraform on AWS | fmt·validate·test or plan, remote state·locking explanation, drift or import scenario, plan review and cleanup |
| Helm & GitOps | Chart lint·template·values ​​schema verification, install/upgrade/rollback, observation of convergence of Git desired state and cluster drift |
| Observability & SRE | Connect metrics·log·trace to the same request or failure time axis and verify one SLO-based alert |
| PostgreSQL | Observe query·lock·WAL or backup status and check restore/PITR or failover completion conditions |
| NoSQL | Redis TTL·eviction or persistence failure and DynamoDB partition/access pattern are studied separately and are not treated as the same product. |
| Security | Check both allow and deny of least-privilege policies and track the life cycle of secret or signed artifacts |
| Messaging | Generate duplicate·retry·DLQ or replay and check consumer idempotency and completion of recovery |
| Reliability & FinOps | Set RPO, RTO, capacity, and cost budget for one workload and verify with backup recovery or game-day results |
| Karpenter | Check the process of pending Pods converging to node capacity and consolidation/disruption results in event·metric·AWS resources |
| Traffic & Resilience | Review gateway·route attachment and ownership and check with plan-only evidence whether deadline·retry budget·circuit breaker closes the upper limit of retry storm |

### R6. Integrated Capstone

The required capstone is divided into two layers: local and AWS optional.

- Local: Deploy the sample service with Helm, connect to PostgreSQL or Redis, and observe with Prometheus/OpenTelemetry. Inject one of the following: incorrect image, DB connection exhaustion, or network denial to perform alert→diagnosis→recovery.
- AWS optional: Prepare isolated AWS network·IAM and EKS dependent resources with Terraform and deploy sample workload with Helm/GitOps. Karpenter adds this in a separate, deeper step, and can be verified with explicit disruption scenarios and observational evidence instead of actually waiting for spot interruptions.
- Capstone guides you to leave resource inventory, architecture diagram, apply/deploy evidence, SLI, incident timeline, and cleanup receipt. Receipt is a learning result and does not replace actual evidence.

## Writing steps

Each stage is released in the catalog after passing the completion criteria of the previous stage. Empty topic cards or `준비 중` pages are not deployed.

1. Foundation: Linux, Networking, AWS Foundations
2. Declaration and deployment: Terraform on AWS, Helm & GitOps
3. Operations: Observability & SRE, Infrastructure Security
4. Traffic & Resilience
5. Data: PostgreSQL, NoSQL, Messaging
6. Reliability and integration: Reliability & FinOps, local/AWS optional capstone
7. The only deepening: Karpenter

One-step topics can parallelize the creation work, but each topic is released at once when its roadmap, body, and verification are all ready.

## non-goal

- Translating the entire official document or creating a list of external links
- Kubernetes Repeating the existing 11 chapters on a new topic
- Copying a specific company's internal production architecture or disclosing confidential information
- Making actual AWS accounts, costs, and availability conditions for CI success
- Proposing a single correct architecture, unconditional multi-AZ/multi-region, or specific database selection
- Determining that operational capabilities are achieved solely through successful tool installation
- Adding in-depth tracks for each product other than Karpenter to the initial route. The backend topic is not a product in-depth, but a common contract that connects the existing DevOps layer to requests and work results.

## Criteria for completion of implementation

### Structure and scope of disclosure

- Each implemented topic has `docs-site/content/<topic>/00-roadmap.md` and at least one execution/failure verification chapter.
- In the catalog, only the text and verified topics are registered in prerequisite order.
- All open sources are Git tracking Markdown and pass the path deviation and private path rejection tests of the existing public docs gateway.
- Internal links between topics are interpreted as the document route of the built site, and there are no broken relative links.
- DevOps 15 topics and 57 documents are registered in the catalog, and the backend roadmap connects network·database·messaging·security·traffic·AIOps through internal routes.
- The entire content connection table of the backend roadmap places all the protocol·data·runtime·cache·distributed correctness·data platform·security·delivery·traffic·AI/robot intersection areas of the vault's 81 notes in the public domain.

### content quality

- Material claims for each chapter are tracked by official source notes and confirmation dates.
- The execution example includes the relevant items among commands, expected observations, failure judgments, and cleanup, and does not describe operations that are not actually executed as completed.
- The Terraform example goes through automatic format and validation, and the Helm example goes through lint and template render.
- YAML·JSON·shell·SQL examples automate syntax or parser checking to the extent possible.
- If you do not run AWS live lab, the scope of static verification and unverified behavior are specified in the chapter and delivery report.
- PostgreSQL, Redis, and DynamoDB distinguish between storage models and failure boundaries, and do not provide the same guarantee just because it is `NoSQL`.
- The Karpenter topic rechecks EKS compatibility with the official API at the time of writing and includes not only provisioning but also consolidation, disruption, PDB, cost, and recovery.
- Every new topic roadmap provides a map of problem context and minimal terminology that a first-time reader will understand.
- All concept chapters first define key terms used in the text, and do not use undefined abbreviations or technical terms as a premise for the first explanation.
- Every lab chapter provides pre-execution information about the tools needed, startup conditions, files to be created, and expected observations and cleanups.
- Completion of the beginner's route is not determined by reading the terms, but by reproducing normal results, explaining the cause of failure, and confirming the recovery results.

### Site and Delivery

- You can find new topics and documents through title, summary, and text searches.
- Even after increasing the number of topics on desktop and mobile, gateway, card, and document navigation do not overlap or are cut off.
- `npm test`, `npm run build`, focused example validation and overall harness validation pass.
- After pushing the step-by-step implementation to `origin/main`, check the success of the Pages workflow and the public URL HTTP response.
- `docs-site/dist/`, AWS credentials, Terraform state, and local test artifacts are not included in Git.

## Specification Phase Completion Criteria

- The scope and order of new topics are specified.
- Only Karpenter is included as an in-depth product topic, and the backend common contract and exclusion list are specified.
- Documentation, lab, source, version, and AWS security contract are written as verifiable requirements.
- Step-by-step implementation and final completion criteria are separated.
- This specification can be explored in the docs MOC, public study guide, and root README.
