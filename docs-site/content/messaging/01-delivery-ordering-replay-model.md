# Delivery, ordering과 replay model

## 먼저 이해하기

주문 서비스가 `order.accepted` event를 보낸 뒤 결제 consumer가 처리한다고 하자. producer는 broker에 event를 기록했지만 consumer가 결제 DB를 갱신한 직후 acknowledgement를 보내기 전에 죽을 수 있다. broker는 처리되지 않았다고 판단해 같은 event를 다시 전달한다. 메시징 시스템이 정상 작동했는데도 business side effect가 두 번 실행될 수 있는 이유다.

| 시점 | broker가 아는 것 | broker가 모르는 것 |
|---|---|---|
| publish 성공 | event를 수락했다 | 모든 consumer의 business 처리 성공 |
| delivery | consumer에게 보냈다 | consumer transaction commit 여부 |
| acknowledgement | consumer가 완료라고 응답했다 | 외부 시스템 전체의 일관성 |
| retention/replay | event를 다시 읽을 수 있다 | 재실행해도 side effect가 안전한지 |

그래서 delivery guarantee와 processing outcome을 분리한다. at-least-once delivery에서는 중복 가능성을 인정하고 consumer가 durable idempotency key를 사용한다. ordering도 “전체가 순서대로”가 아니라 queue group이나 Kafka partition처럼 보장되는 범위를 명시한다.

SQS·SNS·EventBridge·Kafka는 이 문제의 서로 다른 모양을 해결한다. SQS는 작업을 consumer 사이에 분배하는 queue에 가깝고, SNS와 EventBridge는 여러 target으로 fan-out·routing하며, Kafka는 retained partition log를 consumer group이 offset으로 읽는다. 이름을 고르기 전에 누가 event를 소유하고 누가 retry·replay를 책임지는지 정해야 한다.

## 서비스 이름보다 책임을 본다

| 구성 | 주된 목적 | 운영 질문 |
|---|---|---|
| SQS queue | consumer 간 작업 분배와 buffering | visibility timeout, retry, DLQ, standard/FIFO |
| SNS topic | subscriber fan-out | subscription filter, delivery retry, target failure |
| EventBridge bus | event routing과 target integration | rule, schema, archive/replay, target DLQ |
| Kafka log | partitioned durable log와 consumer group | partition key, offset, retention, rebalance |

SQS standard queue는 at-least-once delivery와 best-effort ordering을 전제로 consumer를 설계한다. FIFO 기능도 ordering과 deduplication scope·throughput 조건을 확인해야 하며 외부 side effect의 transaction을 대신하지 않는다.

Kafka의 ordering은 topic 전체가 아니라 partition 안에서 이해한다. partition을 늘리면 병렬성은 커질 수 있지만 같은 key의 ordering, rebalance와 consumer state에 영향을 준다.

```mermaid
sequenceDiagram
    participant P as Producer
    participant B as Broker
    participant C as Consumer
    participant D as Business DB
    P->>B: event(id=42)
    B->>C: delivery 1
    C->>D: idempotency key 42 + effect
    C--xB: ack timeout
    B->>C: delivery 2
    C->>D: key 42 already committed
    C->>B: ack
```

## Retry와 DLQ

retry는 transient failure를 흡수하지만 immediate retry storm은 downstream 장애를 키운다. exponential backoff, jitter와 retry budget을 둔다. poison message는 retry 횟수만 늘리지 말고 격리해 payload, schema version과 consumer error를 조사한다.

DLQ redrive 전에 다음을 확인한다.

1. 원인이 code, dependency, permission 또는 data 중 무엇인지 분류한다.
2. consumer fix와 idempotency가 배포됐는지 확인한다.
3. redrive rate가 정상 traffic과 downstream capacity를 압도하지 않는지 정한다.
4. 성공·재실패·누락 수를 reconciliation한다.

## Schema evolution과 replay

producer와 consumer가 동시에 배포되지 않는다면 schema는 additive change와 compatibility 규칙을 가져야 한다. retained event를 새 consumer로 replay할 때 당시 의미와 현재 reference data가 달라질 수 있다. event time, schema version, producer identity와 replay run ID를 기록한다.

## 스스로 설명해 보기

1. visibility timeout이 너무 짧거나 길 때 각각 어떤 문제가 생기는가?
2. Kafka partition key가 ordering과 load distribution을 동시에 좌우하는 이유는 무엇인가?
3. event replay가 단순 파일 재읽기가 아닌 운영 변경인 이유는 무엇인가?

<!-- source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive-event.html | checked: 2026-09-03 -->
<!-- source: https://kafka.apache.org/documentation/#intro_concepts_and_terms | checked: 2026-09-03 -->
