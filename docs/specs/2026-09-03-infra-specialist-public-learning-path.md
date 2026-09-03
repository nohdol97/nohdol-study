# Infra Specialist 공개 학습 경로 스펙

- 날짜: 2026-09-03
- 상태: 구현됨
- 관련 결정: [ADR 008](../adr/008-public-docs-gateway.md)
- 선행 구현: [Public Docs Gateway](2026-09-03-public-docs-gateway.md)

## 목표

- 현재 Kubernetes 과정에 Linux·네트워크·AWS·Terraform·Helm·운영·데이터 계층을 연결해 AWS 기반 cloud-native 인프라를 설계하고 운영하는 학습 경로를 제공한다.
- 제품 기능을 나열하지 않고 `요구사항 → 선언 상태 → 실제 자원 → 관측 → 장애 복구 → 비용`의 운영 수명주기로 설명한다.
- 각 주제를 독립 카드와 자체 로드맵으로 제공하되, 선수·후속 관계를 표시해 전체 Infra Specialist 경로로 이어지게 한다.
- 로컬에서 재현 가능한 실습을 기본으로 하고, AWS 자원을 만드는 실습은 예상 영향·비용·정리 절차를 명시한 선택 과정으로 분리한다.
- 심화 제품 트랙은 Karpenter 하나만 포함해 EKS의 workload 요구가 AWS compute capacity로 수렴하는 과정을 다룬다.

## 대상 독자와 수료 결과

대상 독자는 파일을 만들고 기본적인 shell 명령을 실행해 본 애플리케이션 개발자다. Linux 운영, 네트워크, AWS, 데이터베이스 운영 도구는 처음 접해도 된다. Kubernetes 지식은 전체 과정의 선행 조건이 아니며 Helm과 Karpenter에 들어가기 전에 이 사이트의 Kubernetes 과정을 먼저 이수하도록 안내한다. 특정 자격증 시험 대비나 모든 AWS 서비스를 암기하는 과정은 아니다.

이 과정은 전문가가 이미 아는 내용을 압축해 찾아보는 reference가 아니라, 처음 보는 사람이 반복해서 관찰하고 실패를 설명하면서 전문가의 판단 순서를 획득하는 학습 과정이다. 따라서 전문 용어와 제품 이름을 없애지는 않지만, 정의하기 전에 사용하지 않는다. 쉬운 비유는 첫 직관을 만드는 데만 사용하고 실제 시스템의 경계와 다른 점을 즉시 설명한다.

전체 경로를 마친 독자는 다음을 설명하고 재현할 수 있어야 한다.

- Linux process·memory·filesystem·network 상태에서 애플리케이션 장애의 첫 병목을 찾는다.
- DNS·TCP·TLS·load balancer·VPC·Kubernetes Service를 하나의 요청 경로로 추적한다.
- AWS account·IAM·VPC·compute·storage·database의 소유권과 trust boundary를 설계한다.
- Terraform state와 실제 AWS 자원의 관계를 설명하고 plan·apply·import·drift·rollback 절차를 운영한다.
- Helm chart를 렌더링·검증하고 GitOps가 원하는 상태와 실제 클러스터를 수렴시키는 경계를 설명한다.
- metric·log·trace와 SLI/SLO를 연결해 alert와 incident 대응을 설계한다.
- PostgreSQL, Redis, DynamoDB를 이름이 아니라 transaction·access pattern·consistency·failure mode로 선택하고 백업·복구 결과를 확인한다.
- least privilege, secret·encryption, artifact provenance와 감사 경계를 배포 흐름에 포함한다.
- queue·event stream의 중복·순서·retry·dead-letter 책임을 정한다.
- RPO·RTO·용량·비용 목표를 아키텍처와 운영 runbook에 반영한다.
- Karpenter의 provisioning·consolidation·disruption 판단을 Pod scheduling, AWS capacity와 비용 신호로 검증한다.

## 범위

### 기존 과정

`kubernetes`는 공통 선수 과정으로 유지한다. 새 과정은 기존 장의 Pod lifecycle, Service·DNS·NetworkPolicy, storage, scheduling, RBAC, observability, production 운영 설명을 복제하지 않는다. 새 주제에서 필요한 경우 선수 장을 내부 링크로 연결하고 그 위에서 제품별 운영 계약을 확장한다.

### 신규 주제 카드와 책임

| 순서 | topic ID | 공개 제목 | 책임과 핵심 범위 |
|---:|---|---|---|
| 1 | `linux` | Linux 시스템 운영 | process·signal·systemd, user·permission, filesystem·mount, memory·OOM, CPU·load, disk·I/O, namespace·cgroup, 기본 진단 도구 |
| 2 | `networking` | 네트워크와 요청 경로 | CIDR·subnet, routing·NAT, DNS, TCP, TLS, HTTP, load balancer, firewall, 연결·packet 진단 |
| 3 | `aws-foundations` | AWS 인프라 기반 | account·Organizations 개념, IAM·STS, VPC, EC2·ELB·Auto Scaling, Route 53, S3·EBS, RDS·EKS의 shared responsibility |
| 4 | `terraform-aws` | Terraform on AWS | language·provider, resource graph, module, version lock, state backend·locking, plan·apply, import·moved, drift, testing, CI 승인 |
| 5 | `helm-gitops` | Helm Charts와 GitOps | chart 구조, template·values·schema, dependency, hook·CRD, release·rollback, OCI registry, Kustomize 경계, Argo CD sync·drift·promotion |
| 6 | `observability-sre` | Observability와 SRE | Prometheus·PromQL·Alertmanager, Grafana, OpenTelemetry Collector, log·trace 연결, SLI·SLO·error budget, on-call·incident·postmortem |
| 7 | `postgresql` | PostgreSQL 운영 | process·connection, MVCC, WAL·checkpoint·VACUUM, index·query plan, lock·wait 진단, PgBouncer, backup·PITR, replication·failover, RDS 책임 경계 |
| 8 | `nosql` | Redis와 DynamoDB | NoSQL 선택 기준, Redis data type·TTL·eviction·persistence·Sentinel/Cluster, DynamoDB partition key·index·consistency·capacity·Streams·backup, hot key 대응 |
| 9 | `infrastructure-security` | 인프라 보안 | AWS IAM·STS와 least privilege, KMS·Secrets Manager, network boundary, Kubernetes RBAC·Secret 연결, container image scan·SBOM·signature, audit trail |
| 10 | `messaging` | 메시징과 이벤트 인프라 | SQS·SNS·EventBridge와 Kafka의 역할, queue와 event log, delivery·ordering·idempotency, retry·backoff·DLQ, retention·replay·schema evolution |
| 11 | `reliability-finops` | 신뢰성·DR·FinOps | availability target, backup·restore, RPO·RTO, multi-AZ·region 판단, capacity planning, tagging·cost allocation, rightsizing, On-Demand·Reserved·Spot 선택 |
| 12 | `karpenter` | Karpenter 심화 | EKS 연동, workload 요구와 node provisioning, NodePool·node class·claim 계층, topology·capacity type, consolidation·disruption, PDB·termination, 관측·비용·복구 |

### 명시적으로 제외하는 심화 트랙

초기 Infra Specialist 경로에는 다음을 별도 topic으로 추가하지 않는다.

- Ansible·Packer와 별도 image factory
- Cilium/eBPF 심화와 service mesh(Envoy·Istio)
- Vault와 별도 secret platform
- OpenTofu·Pulumi·Crossplane 비교 과정
- 독립 Chaos Engineering 제품 과정
- MongoDB·Cassandra·OpenSearch의 제품별 심화 과정
- multi-cloud와 AWS 자격증 문제 풀이

기초 과정 안에서 개념을 설명하기 위해 이름을 짧게 언급할 수는 있지만, 설치·운영 실습이나 제품 비교로 범위를 넓히지 않는다. 새 심화 topic은 사용자가 별도로 범위를 승인할 때만 이 스펙을 개정한다.

## 전체 학습 순서

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
                                Karpenter 심화
```

카탈로그의 카드 순서는 위 선수 관계를 따르되, 독자는 각 topic을 직접 열 수 있다. 각 topic의 `00-roadmap.md`는 필수 선수 문서와 독립적으로 건너뛸 수 있는 장을 구분한다.

## 문서 구성 계약

### R1. Topic 단위

각 신규 topic은 `docs-site/content/<topic>/`에 독립적으로 두고 다음을 갖는다.

1. `00-roadmap.md`: 해결할 문제, 선수 지식, 장 순서, 최종 실습, 범위 밖 항목
2. 개념 장: 기술이 관리하는 resource·state·owner와 control/data path
3. 실행 장: 가장 작은 재현 가능한 구성과 관찰 명령
4. 운영 장: 변경·확장·업그레이드·백업 또는 rollback
5. 장애 장: 정상 상태, 대표 실패, 증거 수집, 복구와 완료 판정
6. 프로덕션 판단 장: 보안·신뢰성·성능·비용 trade-off

장 수는 주제 복잡도에 따라 달라질 수 있다. 한 장이 독립 개념이 아니라 단순히 길이를 맞추기 위해 생기거나, 반대로 하나의 장이 서로 다른 운영 책임을 함께 가지면 분리한다.

### R2. Chapter 단위

각 장은 관련 있는 항목만 사용하되 다음 구조를 기본으로 한다.

- 이 장이 답하는 운영 질문과 완료 후 할 수 있는 일
- 선수 개념과 한 문장 mental model
- 3개 이상 컴포넌트나 상태 전이가 있을 때 관계도·시퀀스·상태도
- 최소 실행 예시와 변경 전후 관찰 명령
- 정상 결과와 실패 결과를 구분하는 판정 기준
- 적어도 하나의 실제적인 실패 시나리오, 진단 순서와 복구
- 개발·검증·프로덕션 환경에서 달라지는 선택
- 보안·신뢰성·성능·비용 중 해당하는 trade-off
- 답을 외우지 않고 원리를 재구성하는 복습 질문
- 공식 출처 URL·확인일·버전·번역 최신성의 비노출 HTML 주석

각 topic은 다음 학습 사다리를 독자가 실제로 밟을 수 있게 구성한다.

1. **문제 발견**: 이 기술이 없을 때 겪는 한 가지 일상적인 장애나 반복 작업을 보여 준다.
2. **말 익히기**: 처음 등장하는 용어를 쉬운 한국어 정의, 실제 대상, 관찰 방법과 함께 소개한다.
3. **동작 따라가기**: 입력 하나가 여러 구성 요소를 지나 결과가 되는 과정을 번호로 끊어 설명한다.
4. **손으로 확인하기**: 완전한 준비 절차와 예제로 정상 상태를 먼저 재현한다.
5. **일부러 실패하기**: 한 번에 한 조건만 바꾸고 정상 상태와 무엇이 달라졌는지 찾는다.
6. **복구하고 증명하기**: 명령 성공이 아니라 사용자 결과와 잔여 자원까지 확인한다.
7. **전문가 판단으로 확장하기**: 보안·신뢰성·성능·비용의 trade-off를 근거와 함께 선택한다.

독자는 문서를 위에서 아래로 읽을 때 아직 정의되지 않은 전문 용어 때문에 다른 문서를 찾아야 해서는 안 된다. topic roadmap에는 `처음 보는 사람을 위한 출발점`과 최소 용어 지도를 두고, 개념 장에는 `이 장에서 처음 쓰는 말`, 실습 장에는 `실습 전에 준비할 것`을 둔다. 내부 링크로 선수 개념을 연결하더라도 현재 문장을 이해하는 데 필요한 한 문장 정의는 생략하지 않는다.

설명의 친절함은 말투가 아니라 생략하지 않은 연결로 판정한다.

- 처음 등장하는 핵심 용어는 서로 비슷한 용어와의 경계, 관리 주체와 관찰 위치를 먼저 설명한다.
- 추상 개념은 한 가지 구체적인 요청·변경·장애 상황에 적용해 입력에서 결과까지의 인과관계를 보여 준다.
- 명령과 설정을 제시하기 전에 무엇을 확인하려는지 밝히고, 실행 뒤에는 출력이 증명하는 것과 아직 증명하지 못하는 것을 구분한다.
- 정상과 실패 결과를 함께 보여 주며, 한 단계의 성공을 전체 서비스 성공으로 확대 해석하지 않는다.
- 표와 다이어그램은 용어를 다시 나열하는 데 쓰지 않고 상태·책임·판정 기준의 차이를 설명할 때 사용한다.
- 영어 용어는 처음에 `쉬운 한국어 설명(공식 영문 용어)` 형태로 소개하고, 이후 공식 문서·명령과 대응시키기 위해 영문 표기를 유지할 수 있다.
- 한 문단에 처음 등장하는 핵심 용어가 세 개를 넘으면 용어 설명이나 동작 단계를 먼저 분리한다.
- 복습 질문은 `처음 이해했는지 확인`과 `운영 판단으로 확장`을 구분하고, 앞쪽 질문은 본문에서 답의 근거를 찾을 수 있어야 한다.
- 전문가용 예외·최적화·제품 비교는 기본 흐름을 이해한 뒤 `더 깊이 보기`로 분리한다.

모든 장에 억지로 다이어그램이나 장애 실습을 넣지는 않는다. 관계가 한 문단보다 명확해질 때만 다이어그램을 사용하고, 실행 가능한 실패가 아닌 경우에는 검증 가능한 사고 실험과 필요한 관측 증거를 적는다.

### R3. 공식 출처와 버전 정책

출처는 구현체의 공식 문서와 specification을 우선한다.

- Helm: <https://helm.sh/ko/docs/>와 최신 영어 원문
- Terraform: <https://developer.hashicorp.com/terraform/docs>와 AWS provider 공식 문서
- PostgreSQL: <https://www.postgresql.org/docs/current/>를 출발점으로 하되 version-sensitive 동작은 확인한 major version을 기록
- Redis: <https://redis.io/docs/latest/>
- DynamoDB·AWS: AWS Documentation과 AWS Well-Architected Framework
- GitOps: Argo CD 공식 문서
- Observability: Prometheus, Grafana, OpenTelemetry 공식 문서
- Messaging: AWS SQS·SNS·EventBridge 공식 문서와 Apache Kafka 공식 문서
- Karpenter: <https://karpenter.sh/docs/>와 AWS EKS 공식 문서

`latest`나 `current` URL만으로 특정 버전의 동작을 고정하지 않는다. API·기본값·지원 상태·비용처럼 바뀔 수 있는 내용은 작성 시점의 version과 `checked` 날짜를 남기고, 큰 개정 전에 다시 확인한다. AI 요약, 검색 결과와 기존 vault 노트는 출처 탐색에만 쓰며 공개 사실의 독립 근거로 사용하지 않는다.

공식 문서를 참고했다는 사실과 공식 문서가 같은 문장을 직접 말한다는 주장을 구분한다. 용어의 쉬운 뜻, 비유, 통합 시나리오, 여러 제품을 잇는 운영 표는 원문 인용이 아니라 학습용 종합임을 독자가 알아볼 수 있게 표시한다. API field, 기본값, 보장과 지원 상태처럼 구현체가 직접 정하는 사실은 해당 공식 출처와 version으로 추적하고, 종합한 운영 권고는 그 근거 범위와 가정을 함께 적는다.

### R4. 실습 환경과 안전

실습은 다음 세 등급을 제목 근처에 표시한다.

| 등급 | 환경 | 계약 |
|---|---|---|
| Local | 로컬 shell·container·minikube 또는 kind | 비용 없음, 필요한 도구와 정리 방법 명시 |
| Plan only | Terraform validate·test·plan 등 원격 변경 없는 검증 | AWS credential 필요 여부와 backend 접근 여부 명시 |
| AWS optional | 실제 AWS resource 생성·변경 | 예상 resource, 과금 가능성, 권한, region, tag, 성공 판정과 cleanup 명시 |

- 문서와 예제에는 access key, token, password, account ID나 개인 경로를 넣지 않는다.
- root user나 장기 access key를 기본 경로로 안내하지 않는다. profile, role과 temporary credential을 사용한다.
- resource를 만드는 예제에는 같은 장에 idempotent한 확인과 정리 절차를 둔다. 삭제가 backup·state·log까지 제거하는지는 별도로 경고한다.
- 비용 수치는 고정 사실처럼 쓰지 않고 region·시점·사용량 조건과 확인일을 표시한다.
- `terraform apply`, AWS resource 삭제, database failover와 Karpenter disruption은 실행 전 영향 범위를 보여 주고 관찰할 신호를 먼저 준비한다.
- CI는 실제 AWS resource를 만들지 않는다. AWS live 실습은 작성자가 명시적으로 실행한 검증 기록과 한계를 문서 변경 설명에 남긴다.

### R5. 주제별 필수 실습

| topic | 최소 실습과 완료 증거 |
|---|---|
| Linux | service 한 개의 process·socket·memory·filesystem 사용량을 추적하고 signal·OOM·disk pressure 중 하나를 진단 |
| Networking | DNS 조회에서 TCP/TLS와 load balancer 또는 Service backend까지 요청 경로를 관찰하고 한 구간의 차단을 식별 |
| AWS Foundations | IAM role과 VPC route를 도식화하고 public/private reachability를 설정이 아니라 관측 결과로 판정 |
| Terraform on AWS | fmt·validate·test 또는 plan, remote state·locking 설명, drift 또는 import 시나리오, plan review와 cleanup |
| Helm & GitOps | chart lint·template·values schema 검증, install/upgrade/rollback, Git desired state와 cluster drift의 수렴 관찰 |
| Observability & SRE | metric·log·trace를 같은 요청 또는 장애 시간축으로 연결하고 SLO 기반 alert 한 개를 검증 |
| PostgreSQL | query·lock·WAL 또는 backup 상태를 관찰하고 restore/PITR나 failover 완료 조건을 확인 |
| NoSQL | Redis TTL·eviction 또는 persistence 실패와 DynamoDB partition/access pattern을 각각 실습하고 동일 제품으로 취급하지 않음 |
| Security | least-privilege 정책의 허용·거부를 모두 확인하고 secret 또는 signed artifact의 수명주기를 추적 |
| Messaging | duplicate·retry·DLQ 또는 replay를 발생시키고 consumer의 idempotency와 복구 완료를 확인 |
| Reliability & FinOps | 하나의 workload에 RPO·RTO·용량·비용 budget을 정하고 backup 복구 또는 game-day 결과로 검증 |
| Karpenter | pending Pod가 node capacity로 수렴하는 과정과 consolidation/disruption 결과를 event·metric·AWS resource에서 확인 |

### R6. 통합 캡스톤

필수 캡스톤은 local과 AWS optional 두 층으로 나눈다.

- Local: sample service를 Helm으로 배포하고 PostgreSQL 또는 Redis와 연결하며 Prometheus/OpenTelemetry로 관측한다. 잘못된 image, DB connection exhaustion 또는 network denial 중 하나를 주입해 alert→진단→복구를 수행한다.
- AWS optional: Terraform으로 격리된 AWS network·IAM과 EKS 의존 자원을 준비하고 Helm/GitOps로 sample workload를 배포한다. Karpenter는 별도 심화 단계에서 추가하며, Spot interruption을 실제로 기다리는 대신 명시적 disruption 시나리오와 관측 증거로 검증할 수 있다.
- 캡스톤은 resource inventory, architecture diagram, apply/deploy evidence, SLI, incident timeline, cleanup receipt를 남기도록 안내한다. receipt는 학습 결과이며 사실 근거를 대신하지 않는다.

## 작성 단계

각 단계는 앞 단계의 완료 기준을 통과한 뒤 카탈로그에 공개한다. 빈 topic 카드나 `준비 중` 페이지는 배포하지 않는다.

1. 기반: Linux, Networking, AWS Foundations
2. 선언과 배포: Terraform on AWS, Helm & GitOps
3. 운영: Observability & SRE, Infrastructure Security
4. 데이터: PostgreSQL, NoSQL, Messaging
5. 신뢰성과 통합: Reliability & FinOps, local/AWS optional capstone
6. 유일한 심화: Karpenter

한 단계의 topic은 작성 작업을 병렬화할 수 있지만, 각 topic은 자체 roadmap·본문·검증이 모두 준비됐을 때 한 번에 공개한다.

## 비목표

- 공식 문서 전체를 번역하거나 외부 링크 목록을 만드는 일
- Kubernetes 기존 11개 장을 새 topic에서 반복하는 일
- 특정 회사의 내부 production architecture를 모사하거나 비공개 자료를 공개하는 일
- 실제 AWS 계정·비용·가용성을 CI 성공 조건으로 만드는 일
- 하나의 정답 architecture, 무조건적인 multi-AZ·multi-region 또는 특정 database 선택을 제시하는 일
- 도구 설치 성공만으로 운영 역량이 생겼다고 판정하는 일
- Karpenter 이외의 심화 제품을 초기 경로에 추가하는 일

## 구현 완료 기준

### 구조와 공개 범위

- 구현된 각 topic은 `docs-site/content/<topic>/00-roadmap.md`와 적어도 한 개의 실행·장애 검증 장을 가진다.
- 카탈로그에는 본문과 검증이 완료된 topic만 선수 순서로 등록된다.
- 모든 공개 source는 Git 추적 Markdown이며 기존 public docs gateway의 경로 이탈·비공개 경로 거부 테스트를 통과한다.
- topic 간 내부 링크는 빌드된 사이트의 document route로 해석되고 깨진 상대 링크가 없다.

### 콘텐츠 품질

- 각 장의 material claim은 공식 source 주석과 확인일로 추적된다.
- 실행 예시는 명령, 예상 관찰, 실패 판정과 cleanup 중 해당 항목을 갖추고 실제 실행하지 않은 동작을 실행 완료로 서술하지 않는다.
- Terraform 예제는 자동 format과 validate를 통과하고, Helm 예제는 lint와 template 렌더를 통과한다.
- YAML·JSON·shell·SQL 예제는 가능한 범위에서 syntax 또는 parser 검사를 자동화한다.
- AWS live 실습을 실행하지 않은 경우 정적 검증 범위와 미검증 동작을 장과 전달 보고에 명시한다.
- PostgreSQL·Redis·DynamoDB는 저장 모델과 failure boundary를 구분하며 `NoSQL`이라는 이유만으로 동일한 보장을 부여하지 않는다.
- Karpenter topic은 작성 당시 공식 API와 EKS 호환성을 다시 확인하고, provisioning뿐 아니라 consolidation·disruption·PDB·비용과 복구를 포함한다.
- 모든 신규 topic roadmap은 처음 보는 독자가 이해할 문제 상황과 최소 용어 지도를 제공한다.
- 모든 개념 장은 본문에서 사용하는 핵심 용어를 먼저 정의하며, 정의하지 않은 약어와 전문 용어를 첫 설명의 전제로 삼지 않는다.
- 모든 실습 장은 필요한 도구, 시작 상태, 만들 파일, 예상 관찰과 정리 대상을 실행 전에 알려 준다.
- 초심자 경로의 완료는 용어를 읽었다는 사실이 아니라 정상 재현, 실패 원인 설명, 복구 결과 확인으로 판정한다.

### 사이트와 전달

- 제목·요약·본문 검색에서 신규 topic과 문서를 찾을 수 있다.
- 데스크톱·모바일에서 topic 수 증가 뒤에도 게이트웨이, 카드, 문서 탐색이 겹치거나 잘리지 않는다.
- `npm test`, `npm run build`, focused example validation과 전체 하네스 검증이 통과한다.
- 단계별 구현을 `origin/main`에 push한 뒤 Pages workflow 성공과 공개 URL HTTP 응답을 확인한다.
- `docs-site/dist/`, AWS credential, Terraform state와 local test artifact는 Git에 포함되지 않는다.

## 스펙 단계 완료 기준

- 신규 topic의 범위와 순서가 명시되어 있다.
- Karpenter만 심화 topic으로 포함되고 제외 목록이 명시되어 있다.
- 문서·실습·출처·버전·AWS 안전 계약이 판정 가능한 요구사항으로 작성되어 있다.
- 단계별 구현과 최종 완료 기준이 분리되어 있다.
- 이 스펙이 docs MOC, 공개 학습 가이드와 루트 README에서 탐색 가능하다.
