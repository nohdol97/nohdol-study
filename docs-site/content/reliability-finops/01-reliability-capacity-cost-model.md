# Reliability, capacity와 cost model

## 이 장에서 처음 쓰는 말

- **신뢰성(reliability)**: 필요한 기간 동안 시스템이 기대한 기능을 계속 수행하는 성질이다.
- **SLI/SLO**: 실제 사용자 결과를 재는 방법과 그 측정값의 목표다.
- **failure mode**: 무엇이 어떤 방식으로 실패할 수 있는지를 구체적으로 적은 시나리오다.
- **복구(restore/recovery)**: backup이나 남은 시스템을 사용해 데이터와 서비스를 다시 사용 가능하게 만드는 과정이다.
- **여유 용량(capacity margin)**: 평소 사용량을 넘는 급증이나 일부 장애를 견디기 위해 남겨 둔 처리 능력이다.
- **FinOps**: cloud 비용을 기술·업무 소유권과 연결해 측정하고 개선하는 운영 방식이다.

처음에는 작은 주문 API를 예로 들어 “30일 동안 요청의 몇 퍼센트가 성공해야 하는가?”, “database가 사라지면 언제까지 복구해야 하는가?” 두 질문에 숫자를 붙인다. 복잡한 architecture는 목표가 생긴 뒤에 선택한다.

## 먼저 이해하기

“항상 켜져 있어야 한다”는 요구는 설계 입력으로 쓰기 어렵다. 어느 사용자 요청을 성공으로 볼지, 얼마 동안의 실패를 허용할지, 장애 뒤 언제까지 서비스를 되살리고 어느 시점까지의 데이터를 복구해야 하는지를 측정 가능한 값으로 바꿔야 한다. 그래야 redundancy와 비용이 필요한 이유를 설명할 수 있다.

예를 들어 주문 API의 30일 availability SLO가 99.9%, RTO가 15분, RPO가 5분이라고 하자. SLO는 평상시 전체 요청 결과를 평가하고, RTO는 특정 disruption 뒤 service level을 되찾는 시간을, RPO는 복구된 data가 장애 직전에서 얼마나 뒤로 물러날 수 있는지를 말한다. 세 값은 관련 있지만 같은 값이 아니다.

| 목표 | 설계를 바꾸는 질문 | 검증 증거 |
|---|---|---|
| availability SLO | 몇 개 failure를 흡수하고 언제 page하는가? | valid request 기반 SLI |
| RTO | 어떤 event부터 어떤 readiness까지 재는가? | game-day timeline |
| RPO | 마지막 recoverable data point는 언제인가? | marker data와 restore 결과 |
| capacity margin | peak·AZ loss에서 얼마가 남는가? | load test와 queue·tail latency |
| cost budget | 어느 owner와 unit이 비용을 만든가? | allocation과 unit cost trend |

multi-AZ를 선택하면 비용이 늘지만 모든 장애가 해결되지는 않는다. 한 AZ 장애에는 강해질 수 있어도 잘못된 배포나 data corruption은 여러 AZ에 동시에 퍼질 수 있다. 비용 판단은 resource 수가 아니라 어떤 failure mode와 objective를 사는지 연결해야 한다.

## 막연한 요구를 검증 가능한 설계로 바꾸기

1. 먼저 사용자가 성공했다고 느끼는 결과를 정한다. 예: 유효한 주문 요청이 제한 시간 안에 성공한다.
2. 그 결과를 성공률과 latency 같은 SLI로 측정한다.
3. 30일 동안 허용할 실패 범위를 SLO로 정한다.
4. database 손실이나 한 AZ 중단처럼 구체적인 failure mode를 고른다.
5. 중복 구성, backup, autoscaling 같은 완화책과 필요한 capacity를 설계한다.
6. test나 game day에서 실제 사용자 결과, RTO와 RPO를 측정한다.
7. 목표를 만족한 근거와 그 설계의 지속 비용을 함께 검토한다.

비용을 먼저 줄이거나 resource를 먼저 늘리는 대신, 어떤 사용자 영향과 failure를 다루기 위한 선택인지 순서대로 연결한다.

## 목표부터 failure mode로 내려간다

availability target은 architecture 그림이 아니라 측정한 사용자 결과의 목표다. RPO는 복구 시 허용할 수 있는 data loss의 시간 범위, RTO는 disruption 이후 service level을 복원하기까지의 목표 시간이다. 둘 다 시작·종료 event와 측정 책임자가 필요하다.

```mermaid
flowchart TD
    O[workload objective] --> F[failure modes]
    F --> M[mitigation·backup]
    M --> E[evidence test]
    E --> R{target met?}
    R -->|아니오| D[design·runbook 개선]
    R -->|예| G[operational guardrail]
    D --> F
```

failure domain은 process, node, AZ, region, identity/control plane과 dependency로 나눈다. multi-AZ는 AZ failure 대응에 도움을 주지만 bad deployment, credential revocation, data corruption과 regional dependency를 자동으로 해결하지 않는다.

## Backup과 restore의 계약

backup policy에는 source, frequency, retention, encryption, immutability 또는 deletion guard와 cross-account/region 필요성을 적는다. restore test에서는 다음을 측정한다.

- 마지막 recoverable point와 실제 data gap
- restore 요청 시각부터 dependency 포함 service readiness까지의 시간
- schema·row·object integrity와 representative request
- owner 승인과 cleanup 또는 promoted environment의 후속 상태

## Capacity는 tail과 degraded mode를 본다

```text
required capacity = forecast peak × safety margin × failure-mode factor
```

이 식은 답이 아니라 가정을 드러내는 틀이다. traffic mix, p95/p99 latency, queue depth, dependency quota와 한 AZ 상실 시 남은 capacity를 load test로 검증한다. autoscaling은 늦게 반응할 수 있으므로 startup·warm-up 시간도 budget에 넣는다.

## FinOps는 소유권과 단위를 연결한다

| 요소 | 운영 질문 |
|---|---|
| allocation | account·tag·cost category로 owner와 workload를 찾을 수 있는가? |
| unit cost | request, tenant, job 또는 GB당 비용이 어떻게 움직이는가? |
| forecast | growth·seasonality·commitment를 어떤 가정으로 계산했는가? |
| optimization | rightsizing이 SLO와 recovery margin을 침해하지 않는가? |
| purchase | On-Demand·commitment·Spot 위험을 workload interruption tolerance와 맞췄는가? |

비용 숫자는 region, 시점과 usage에 따라 달라진다. 문서에 고정 가격을 박기보다 공식 pricing 도구와 실제 billing data의 확인 시점을 기록한다.

## 스스로 설명해 보기

1. backup frequency와 실제 RPO가 다를 수 있는 이유는 무엇인가?
2. 한 AZ가 사라진 상태의 capacity를 따로 시험해야 하는 이유는 무엇인가?
3. unit cost 상승이 infrastructure 단가 외에 어떤 신호일 수 있는가?

<!-- source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_network_topology.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost-aware-culture.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/aws-backup/latest/devguide/whatisbackup.html | checked: 2026-09-03 -->
