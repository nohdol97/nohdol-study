# 캐시·데이터 흐름과 성능 증거

<!-- source: https://www.rfc-editor.org/rfc/rfc9111.html | checked: 2026-09-03 -->
<!-- source: https://www.postgresql.org/docs/current/using-explain.html | checked: 2026-09-03 -->

캐시는 느린 계산과 전송을 줄이지만 새로운 상태, freshness와 무효화 경계를 만든다. hit ratio만 높이면 오래된 값, tenant 혼합과 stampede를 놓칠 수 있다. 성능 개선은 사용자 워크로드, 정본과 허용된 stale window를 고정한 뒤 전후 결과로 증명해야 한다.

## 이 장에서 처음 쓰는 말

| 말 | 이 장에서의 뜻 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| cache key | 저장된 응답이나 값을 다시 찾는 식별 정보 | 결과의 의미나 접근 범위를 바꾸는 입력별로 캐시 결과를 구분한다. **구체적인 상황(가상 예시):** 한 테넌트가 다른 테넌트의 캐시 보고서를 본다. → 권한에 영향을 주는 범위를 캐시 키에 포함한다. → 나머지는 같은 요청으로 격리를 시험한다. |
| freshness | 원본에 다시 묻지 않고 재사용해도 되는 기간·조건 | 캐시 응답을 재사용해도 되는지 원본과 확인해야 하는지 판단할 때 쓴다. **구체적인 상황(가상 예시):** 캐시 가격이 허용된 재사용 기간보다 오래됐다. → 신선도 정책에 따라 재검사하거나 읽어 온다. → 응답 데이터의 나이가 요구를 만족하는지 확인한다. |
| validator | 저장 값이 아직 유효한지 조건부 확인하는 ETag 같은 값 | 응답 전체를 매번 다시 전송하지 않고 캐시 내용의 유효성을 조건부로 확인한다. **구체적인 상황(가상 예시):** 큰 응답이 지난 조회 이후 바뀌지 않았을 수 있다. → validator로 조건부 요청을 보낸다. → 응답이 재사용을 허용하는지 확인한다. |
| invalidation | 원본 변경 뒤 더 이상 재사용하면 안 되는 캐시 entry를 제거·갱신하는 일 | 기준값이 바뀐 뒤 낡은 캐시 데이터를 계속 제공하지 않도록 한다. **구체적인 상황(가상 예시):** 프로필 수정 후에도 이전 캐시 화면이 보인다. → 관련 항목을 무효화하거나 갱신한다. → 각 소비 경로에서 수정 내용을 확인한다. |
| stampede | 같은 miss에서 많은 요청이 동시에 원본 계산을 시작하는 현상 | 동시에 발생하는 캐시 실패를 알아보고 원본을 중복 재계산 폭증으로부터 보호한다. **구체적인 상황(가상 예시):** 인기 키가 만료되자 수백 요청이 동시에 재계산한다. → 검토한 정책으로 재생성을 조정·분산한다. → 원본 부하와 응답 신선도를 비교한다. |
| benchmark | 고정한 워크로드와 환경에서 전후를 비교하는 측정 | 비교 가능한 조건에서 최적화가 목표 워크로드를 실제로 개선하는지 확인한다. **구체적인 상황(가상 예시):** 다른 데이터셋에서 최적화가 빨라 보인다. → 같은 대표 워크로드로 두 버전을 반복한다. → 시간과 정확성을 함께 기록한다. |

1. 먼저 정본과 허용 가능한 stale window를 정한다.
2. 그다음 캐시 key, 채움, 무효화와 실패 정책을 설계한다.

## 먼저 이해하기

RFC 9111의 HTTP 캐시는 method와 target URI를 기본 key로 사용하고 `Vary`, freshness, validator와 directive에 따라 저장 응답 재사용을 제한한다. application 캐시도 같은 질문을 피할 수 없다. 어떤 요청 차원이 key에 들어가며, 언제 stale이고, origin이 없을 때 stale을 제공할지 실패 계약이 필요하다.

```mermaid
flowchart LR
    R[read request] --> K{cache key}
    K -->|fresh hit| H[return cached value]
    K -->|stale| V[validate revision]
    K -->|miss| S[single-flight load]
    V -->|unchanged| H
    V -->|changed| S
    S --> O[origin query]
    O --> C[cache with revision and TTL]
    C --> H
```

## cache contract

| 항목 | 주문 조회 예시 | 빠지면 생기는 문제 |
|---|---|---|
| 정본 | PostgreSQL order row | 캐시를 복구 불가능한 원본처럼 취급 |
| key | tenant + order ID + representation version | tenant data 혼합·구형 형식 충돌 |
| freshness | 완료 주문 60초, 진행 중 주문 2초 | 업무 상태와 무관한 TTL |
| validator | order revision 또는 ETag | 값 전체를 다시 전송·lost update |
| invalidation | commit된 order ID event | rollback된 write가 캐시를 지움 |
| miss control | key별 single-flight | hot key가 origin을 동시에 압박 |
| failure mode | 진행 상태는 stale 금지, 완료 상태는 제한 허용 | 장애 때 임의의 오래된 값 노출 |

```yaml
cache_policy:
  namespace: order-summary-v3
  key: "tenant:{tenantId}:order:{orderId}"
  source_of_truth: postgres.orders
  ttl_seconds:
    active: 2
    terminal: 60
  validator: order_revision
  stale_if_origin_unavailable_seconds: 0
  fill: single_flight
```

이는 구현 예시이며 금융·권한 데이터의 stale 허용값은 업무 계약으로 결정해야 한다. `no-store`, `private`, `must-revalidate` 같은 HTTP directive도 이름이 비슷하다고 application 캐시 정책과 자동으로 같아지지 않는다.

## 쓰기와 무효화 사이

DB write 전에 캐시를 지우면 transaction rollback 뒤 유효한 값만 사라져 부하가 늘 수 있다. DB commit 뒤 무효화 event를 보내면 전달 지연 동안 stale window가 생긴다. outbox event에 aggregate ID와 revision을 담고 소비자가 old revision invalidation을 무시하도록 설계할 수 있다.

| 사건 | 캐시가 볼 수 있는 상태 | 방어 |
|---|---|---|
| 같은 key 동시 miss | origin query N개 | single-flight·request coalescing |
| old invalidation 늦게 도착 | 새 값을 삭제할 위험 | monotonic revision 비교 |
| cache 전체 장애 | origin으로 부하 집중 | origin load shed·점진 bypass |
| hot key 집중 | 한 shard·연결 포화 | local 캐시·key 분산은 의미 보존 검토 |
| deploy 뒤 schema 변경 | old entry decode 실패 | versioned namespace·dual read 제한 |

[Redis와 DynamoDB](#doc=nosql-roadmap)는 TTL, hot key와 저장 모델의 구체 동작을 다룬다. 여기서는 그 제품 설정이 API freshness 계약과 연결되는지를 검토한다.

## 성능 증거 만들기

평균 응답 시간만으로 캐시 성공을 판정하지 않는다. 동일한 dataset, query mix, concurrency와 warm-up 조건에서 측정한다.

```json
{
  "scenario": "order-summary-read-v3",
  "datasetRevision": "orders-fixture-20260903-a",
  "requestMix": {"active": 0.3, "terminal": 0.7},
  "concurrency": 40,
  "durationSeconds": 300,
  "result": {
    "successRatio": 0.999,
    "p95Ms": 84,
    "p99Ms": 171,
    "cacheHitRatio": 0.81,
    "staleViolationCount": 0,
    "originQps": 19
  }
}
```

PostgreSQL `EXPLAIN`은 planner가 고른 실행 계획을 보여 주며 `EXPLAIN ANALYZE`는 실제 statement를 실행한다. 쓰기 statement나 무거운 query에 함부로 사용하지 않는다. query plan, rows estimate, buffer·I/O와 lock wait를 [PostgreSQL 운영](#doc=postgresql-lock-restore)에서 확인하고 application span과 같은 request ID로 연결한다.

## 검토 순서

1. 사용자 결과와 정본을 고정한다.
2. key에 tenant, 권한, locale과 representation version이 필요한지 확인한다.
3. active·terminal 상태별 freshness와 stale 허용을 정한다.
4. fill, invalidation과 캐시 장애 시 origin 보호를 설계한다.
5. 평균이 아니라 p95·p99, 오류, stale violation과 origin 부하를 함께 잰다.
6. 캐시 off, cold, warm과 장애 모드를 분리한다.
7. 변경 결과는 [AIOps incident bundle](#doc=aiops-foundations-contract-lab)에 deploy·캐시 revision으로 남긴다.

## 완료

- 캐시 정본, key, freshness와 invalidation owner를 적었다.
- miss stampede와 캐시 장애의 origin 보호를 설계했다.
- query와 캐시 지표를 사용자 결과에 연결했다.
- 재현 가능한 워크로드와 correctness gate를 성능 결과에 포함했다.

## 스스로 설명해 보기

- hit ratio 99%여도 잘못된 결과를 제공할 수 있는 두 경우는 무엇인가?
- TTL과 invalidation을 함께 쓰면 어떤 경쟁을 검토해야 하는가?
- `EXPLAIN ANALYZE`를 production write에 무심코 실행하면 안 되는 이유는 무엇인가?
- 캐시 장애 때 단순 bypass가 origin 장애로 번질 수 있는 이유는 무엇인가?
