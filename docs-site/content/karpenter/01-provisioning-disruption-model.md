# Provisioning과 disruption model

## 세 resource의 책임

- **NodePool**: 허용할 requirement, taint, limit, disruption policy와 template를 정의한다.
- **EC2NodeClass**: AMI, subnet, security group, role, storage와 EC2-specific discovery를 정의한다.
- **NodeClaim**: 한 node capacity 요청의 구체화된 수명주기다. 일반적으로 controller가 만들고 관리한다.

```mermaid
stateDiagram-v2
    [*] --> PendingPod
    PendingPod --> NodeClaim: 요구와 NodePool 교집합
    NodeClaim --> Launched: EC2 capacity 확보
    Launched --> Registered: kubelet join
    Registered --> Initialized: startup resources ready
    Initialized --> Disrupting: consolidation·drift·expiry·interruption
    Disrupting --> [*]: drain and terminate
```

Pod requests가 없거나 실제 사용량보다 지나치게 작으면 Karpenter의 bin-packing 판단도 잘못된 입력을 받는다. node selector, required affinity, topology spread, toleration과 volume topology는 가능한 offering을 좁힌다. NodePool requirement와 Pod requirement의 교집합이 비면 provisioning되지 않는다.

## Capacity type과 diversification

Karpenter는 환경과 설정에 따라 reserved, spot, on-demand capacity type requirement를 사용할 수 있다. Spot은 interruption을 수용할 workload와 넓은 instance family·size·zone 선택으로 설계한다. critical stateful workload에 비용 이유만으로 Spot을 강제하지 않는다.

## Disruption의 종류

disruption은 controller가 판단하는 automated method와 cloud provider interruption 같은 흐름을 포함한다. consolidation은 empty 또는 underutilized node를 delete·replace할 수 있고, drift는 NodePool/NodeClass 변화에 맞지 않는 NodeClaim 교체를 유도할 수 있다. expiration은 node age를 제한하지만 동시에 많은 node가 교체되지 않도록 budget을 둔다.

```mermaid
flowchart TD
    N[NodeClaim] --> E{empty·underutilized?}
    N --> D{drifted·expired?}
    N --> I{interruption?}
    E --> B[budget·PDB·policy check]
    D --> B
    I --> B
    B --> R[replacement pre-spin when applicable]
    R --> T[taint·drain·terminate]
```

PDB는 voluntary disruption에서 application availability를 보호하지만 너무 엄격하거나 여러 PDB가 겹치면 drain을 막는다. PDB만 믿지 말고 terminationGracePeriod, application shutdown, queue handoff와 node termination deadline을 맞춘다.

## 관측과 비용

Kubernetes event, Karpenter controller log·metric, NodeClaim condition, Pod scheduling event와 EC2 instance identity를 같은 timestamp로 연결한다. provisioning latency, pending duration, failed launch, interruption, consolidation savings뿐 아니라 rescheduling 오류와 SLO impact를 본다.

## 스스로 설명해 보기

1. EC2NodeClass와 NodePool을 분리하면 어떤 변경 경계를 얻는가?
2. Pod request 오류가 node 비용과 안정성에 동시에 영향을 주는 이유는 무엇인가?
3. PDB가 허용해도 application shutdown이 실패할 수 있는 이유는 무엇인가?

<!-- source: https://karpenter.sh/docs/concepts/nodepools/ | checked: 2026-09-03 -->
<!-- source: https://karpenter.sh/docs/concepts/nodeclasses/ | checked: 2026-09-03 -->
<!-- source: https://karpenter.sh/docs/concepts/nodeclaims/ | checked: 2026-09-03 -->
<!-- source: https://karpenter.sh/docs/concepts/disruption/ | checked: 2026-09-03 -->
<!-- source: https://karpenter.sh/docs/concepts/scheduling/ | checked: 2026-09-03 -->
