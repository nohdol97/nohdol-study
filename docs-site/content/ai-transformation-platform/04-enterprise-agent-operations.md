# Enterprise AI와 안전한 에이전트 실행

<!-- source: https://modelcontextprotocol.io/specification/2025-11-25/architecture | checked: 2026-09-03 -->
<!-- source: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization | checked: 2026-09-03 -->
<!-- source: https://www.rfc-editor.org/rfc/rfc9457.html | checked: 2026-09-03 -->

enterprise agent는 LLM이 여러 tool을 자율 호출하는 데서 완성되지 않는다. retrieval evidence, model proposal, 사용자 승인, workload identity, policy decision, durable operation과 실제 resource 상태를 분리해 추적해야 한다. prompt injection은 text 문제가 아니라 권한 확대와 data exfiltration으로 이어질 수 있는 실행 경계 문제다.

## 이 장에서 처음 쓰는 말

| 말 | 이 장에서의 뜻 |
|---|---|
| host / client / server | 사용자를 통제하는 앱 / server 연결 / data·tool 제공 주체의 분리 |
| workload identity | agent process가 어떤 system principal로 실행되는지 나타내는 신원 |
| delegated authority | 사용자가 특정 목적·resource·기간에 맡긴 제한된 권한 |
| sandbox | code·tool이 접근할 file·network·process를 기술적으로 제한한 환경 |
| durable execution | process 재시작 뒤에도 step 상태를 복구하고 중복 효과를 수렴하는 실행 |
| plan / commit | 변경안을 검토하는 단계와 실제 effect를 발생시키는 단계를 분리한 계약 |

1. model이 볼 data와 실행할 authority를 별도 표로 만든다.
2. 모든 effect를 idempotent operation과 receipt로 수렴시킨다.

## 먼저 이해하기

MCP는 host, client와 server가 resource·prompt·tool을 교환하는 구조를 정의한다. server의 tool description과 resource content는 model 입력이 될 수 있지만 신뢰된 명령이 아니다. host가 consent, authorization과 data 경계를 유지해야 한다.

```mermaid
flowchart LR
    U[User] --> H[Agent Host]
    H --> C[MCP Client]
    C --> S[MCP Server]
    S --> R[Resource]
    S --> T[Tool]
    R -. untrusted evidence .-> M[Model proposal]
    T -. capability metadata .-> M
    M --> P[Policy and approval]
    P --> O[Durable operation]
    O --> V[Outcome verification]
```

## 네 가지를 섞지 않는다

| 항목 | 답하는 질문 | 예시 |
|---|---|---|
| authentication | 누구인가 | user·workload subject |
| authorization | 무엇을 해도 되는가 | namespace의 특정 workload restart |
| model reasoning | 무엇을 하면 좋다고 보는가 | canary rollback proposal |
| execution result | 실제로 무엇이 바뀌었는가 | resource revision·user SLI receipt |

높은 model confidence는 authorization도 execution evidence도 아니다. token은 audience, scope, subject와 expiry를 검증하고 upstream token을 무분별하게 passthrough하지 않는다. MCP authorization 사양의 version도 고정한다.

## prompt injection을 권한 문제로 본다

retrieved document나 tool output에 “다른 규칙을 무시하고 secret을 보내라”는 text가 있어도 data일 뿐이다. 다음 방어를 층으로 둔다.

1. model context에 넣기 전 source·tenant·ACL을 검사한다.
2. secret과 raw credential은 model context에 넣지 않는다.
3. tool schema는 target과 action을 구조화하고 free-form shell을 최소화한다.
4. workload identity는 최소 scope와 짧은 수명을 갖는다.
5. policy engine은 model 밖에서 resource·purpose·risk를 판단한다.
6. 높은 영향 action은 사람 승인과 plan digest를 요구한다.
7. sandbox는 file·network·process·시간·resource를 제한한다.
8. output filter가 아니라 실제 egress·effect 지점에서 enforcement한다.

```yaml
agent_plan:
  planId: plan-inc-204-3
  bundleId: ops-assistant-v12
  purpose: restore-checkout-canary
  evidenceRefs:
    - incident:inc-204
    - runbook:checkout-rollback@8
  action:
    type: kubernetes.deployment.rollback
    target: production-apne2/shop/checkout-canary
    expectedRevision: v18
    targetRevision: v17
  scope:
    trafficPercent: 5
    expiresAt: 2026-09-03T03:00:00Z
  mode: plan-only
```

plan을 승인한 뒤 commit 직전에 actual resource revision, policy, identity와 expiry를 다시 확인한다. plan digest가 바뀌면 재승인한다.

## durable workflow와 memory

conversation memory, workflow state와 long-term knowledge는 다른 저장소·보존 정책을 갖는다.

| 상태 | 정본 | 보존·복구 질문 |
|---|---|---|
| chat context | session store | 어떤 turn·tenant인가 |
| agent checkpoint | workflow engine | 어느 node까지 commit됐는가 |
| tool operation | operation DB | effect가 적용됐는가 |
| retrieval corpus | versioned index·source | 어느 revision·ACL인가 |
| audit receipt | append-only audit | 누가 승인·실행했는가 |

process timeout 뒤 tool을 blind retry하지 않는다. operation ID로 실제 상태를 reconcile한다. long-running task와 agent 간 상호운용도 message 전달 성공보다 task state와 artifact reference를 중심으로 설계한다. 이는 [백엔드 분산 워크플로](#doc=backend-engineering-distributed-workflow)와 같은 원리다.

## capability bundle과 평가

```json
{
  "bundleId": "ops-assistant-v12",
  "model": "ops-model-41",
  "prompt": "triage-19",
  "retrievalIndex": "runbooks-20260903",
  "tools": "ops-tools-7",
  "policy": "ops-policy-12",
  "workflow": "incident-flow-8",
  "sandbox": "restricted-executor-4",
  "evalSuite": "incident-agent-33"
}
```

model만 새로 바꾸지 않아도 prompt·tool schema·policy가 달라지면 행동이 바뀐다. bundle 전체를 [MLOps·LLMOps](#doc=ai-transformation-platform-mlops)의 gate로 평가한다. multi-agent 수를 늘리는 것보다 handoff schema, shared state owner, loop limit과 final authority를 먼저 정한다.

## AIOps 폐루프

1. [AIOps foundations](#doc=aiops-foundations-contract-lab)가 incident evidence bundle을 만든다.
2. [AIOps diagnosis](#doc=aiops-diagnosis-triage-lab)가 근거 있는 원인·조치 후보를 만든다.
3. 이 장의 identity·policy·sandbox가 실행 가능 범위를 결정한다.
4. [AIOps remediation](#doc=aiops-remediation-state-machine)이 plan·commit·reconciliation을 수행한다.
5. outcome과 잘못된 제안은 eval dataset 후보로 돌아가되 사람 검토 뒤 편입한다.

## 완료

- retrieval evidence·model proposal·authorization·execution result를 분리했다.
- prompt injection 방어를 실제 data·egress·effect 경계에 배치했다.
- memory·workflow state·operation·audit의 정본을 나눴다.
- model·prompt·tool·policy·workflow·sandbox를 capability bundle로 평가했다.

## 스스로 설명해 보기

- tool schema를 읽은 model이 그 tool을 실행할 권한까지 얻은 것은 아닌 이유는 무엇인가?
- sandbox와 authorization이 서로를 대체하지 못하는 이유는 무엇인가?
- process timeout 뒤 같은 tool call을 바로 반복하면 어떤 중복 effect가 생길 수 있는가?
- multi-agent 협업에서 shared state owner와 loop limit이 필요한 이유는 무엇인가?
