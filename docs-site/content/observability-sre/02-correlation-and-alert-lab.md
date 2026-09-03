# Signal 상관관계와 SLO alert 실습

> 실습 등급: **Local**. 이미 Prometheus와 OpenTelemetry demo 환경이 있다면 그 환경을 사용하고, 없으면 아래 데이터로 질의 의미를 먼저 검증한다.

## 먼저 이해하기

이 실습에서 만들려는 것은 dashboard가 아니라 하나의 설명 가능한 incident chain이다. 사용자가 실패한 요청 하나를 출발점으로 request ID와 trace ID를 찾고, 그 요청이 전체 실패율에 포함됐는지 확인한 뒤 어떤 span과 dependency에서 시간이 늘었는지 좁힌다.

`http_server_requests_total` 같은 counter는 process가 시작된 뒤 누적된다. 따라서 현재 값끼리 나누기보다 일정 window의 `rate`를 사용한다. histogram bucket은 각 latency 경계 이하의 누적 요청 수이며 `histogram_quantile`이 여러 bucket을 이용해 percentile을 추정한다. 개별 요청의 정확한 시간을 보여 주는 trace와 역할이 다르다.

| 관찰 | 알 수 있는 것 | 주의할 점 |
|---|---|---|
| 5분 error ratio | 최근 traffic에서 실패 비중 | traffic이 적으면 작은 수에도 크게 흔들림 |
| p95 latency | 대부분의 요청이 경험한 상단 지연 | 가장 느린 요청 하나의 값은 아님 |
| trace span | 선택된 요청의 hop별 시간 | sampling으로 모든 요청을 대표하지 않음 |
| error log | component가 기록한 상세 맥락 | 기록 누락과 clock 차이 가능 |
| burn-rate alert | budget 소진 속도가 대응 기준을 넘음 | threshold는 SLO window에서 계산해야 함 |

## 1. 요청 계약 정하기

sample API에 다음 공통 필드를 둔다.

```text
request_id=8f3... trace_id=4bf... route=/checkout status=503 duration_ms=842
```

counter는 `http_server_requests_total{route,status_class}`처럼 bounded label을 쓴다. `request_id`나 `user_id`를 metric label로 넣지 않는다. 개별 요청 identity는 log와 trace에 둔다.

## 2. Availability와 latency 관찰

5분 availability 비율의 예다.

```promql
sum(rate(http_server_requests_total{status_class!="5xx"}[5m]))
/
sum(rate(http_server_requests_total[5m]))
```

histogram에서 95 percentile을 계산하는 예다.

```promql
histogram_quantile(
  0.95,
  sum by (le, route) (rate(http_server_request_duration_seconds_bucket[5m]))
)
```

traffic이 0일 때 분모가 0이 되는 상황, retry가 요청 수를 늘리는 상황과 ingress/client 중 어느 지점에서 측정하는지를 기록한다.

## 3. 장애 시간축 연결

오류 요청 하나를 골라 다음 표를 채운다.

| 시간 | 증거 | 가설 | 조치 | 판정 |
|---|---|---|---|---|
| T0 | availability SLI 하락 | upstream 오류 | trace ID 조회 | 조사 중 |
| T1 | DB span latency 증가 | connection saturation | pool metric 확인 | active=max |
| T2 | pool 제한 조정 후 burn 감소 | 병목 완화 | rollback 준비 | 관찰 중 |

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database
    participant O as On-call
    U->>A: request + trace context
    A->>D: query span
    D--xA: timeout
    A-->>U: 503 + request ID
    A-->>O: metric alert
    O->>A: log에서 trace ID 확인
    O->>D: span·pool 상태 확인
```

## 4. Alert 검증

alert rule은 테스트 가능한 expression, `for`, severity와 runbook label을 가진다.

```yaml
groups:
  - name: sample-api-slo
    rules:
      - alert: SampleApiFastBurn
        expr: sample_api:error_budget_burn_rate5m > 14
        for: 2m
        labels:
          severity: page
        annotations:
          summary: Sample API error budget is burning quickly
```

실제 threshold는 예시 값을 복사하지 말고 SLO window와 alerting policy로 계산한다. 정상·오류·무트래픽 시계열을 입력해 firing과 recovery를 모두 시험한다.

## 완료 판정과 정리

- alert 발생 시 사용자 impact와 연결되는 dashboard·runbook이 열린다.
- request 또는 trace ID로 log와 trace를 오갈 수 있다.
- 복구 후 짧은 window와 긴 window가 정상화되는 시점을 확인한다.
- 임시 alert rule, demo workload와 telemetry 저장 데이터를 삭제한다.

## 결과를 이렇게 읽는다

availability 식의 값이 `0.98`이면 선택한 5분 window와 label 범위에서 약 98%가 good으로 분류됐다는 뜻이다. 어떤 request를 valid 또는 good에서 제외했는지에 따라 의미가 달라진다. health check나 client cancel을 무심코 분모에서 빼면 실제 사용자 실패를 숨길 수 있다.

p95가 상승한 시각과 DB span 증가가 겹치면 dependency 병목 가설이 강해지지만 아직 인과관계가 확정된 것은 아니다. 같은 trace의 parent-child 시간, connection pool, DB wait와 변경 시점을 함께 본다. 완화 후에는 단일 성공 요청뿐 아니라 burn rate, tail latency와 backlog가 정상 범위로 돌아오는지 확인한다.

alert가 firing됐지만 on-call이 할 수 있는 행동이 없다면 rule을 더 민감하게 만드는 것이 해법이 아니다. 사용자 영향과 연결되는 조건, owner, 첫 진단 query와 안전한 완화 동작을 runbook에 묶어야 한다.

## 스스로 설명해 보기

1. request ID를 metric label에 넣으면 왜 위험한가?
2. 503 증가와 DB span latency 증가가 인과관계를 곧바로 증명하지는 않는 이유는 무엇인가?
3. alert recovery를 시험하지 않으면 어떤 운영 문제가 남는가?

<!-- source: https://prometheus.io/docs/prometheus/latest/querying/basics/ | checked: 2026-09-03 -->
<!-- source: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ | checked: 2026-09-03 -->
<!-- source: https://opentelemetry.io/docs/concepts/signals/ | checked: 2026-09-03 -->
<!-- source: https://sre.google/workbook/alerting-on-slos/ | checked: 2026-09-03 -->
