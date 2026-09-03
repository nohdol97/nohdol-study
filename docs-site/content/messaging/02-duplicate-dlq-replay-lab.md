# Duplicate, DLQ와 replay 실습

> 실습 등급: state machine은 **Local**, managed broker 검증은 **AWS optional**이다. 실제 queue·topic을 만들면 과금과 cleanup 가능성을 먼저 확인한다.

## 먼저 이해하기

이 실습에서 duplicate는 예외적인 broker 오작동이 아니라 정상적으로 대비해야 할 delivery 결과다. consumer가 business DB commit에는 성공했지만 acknowledgement 직전에 종료되면 broker는 완료 사실을 알지 못해 같은 event를 다시 보낼 수 있다.

idempotency는 “두 번째 요청을 무시한다”는 문장만으로 완성되지 않는다. 어떤 값을 동일 event의 identity로 볼지, 그 key를 어디에 얼마나 오래 저장할지, business change와 같은 transaction에 기록할 수 있는지를 정해야 한다.

| 설계 | crash가 끼어드는 위치 | 결과 |
|---|---|---|
| effect 후 processed key 저장 | 두 작업 사이 | effect 중복 가능 |
| processed key 저장 후 effect | 두 작업 사이 | effect 누락 가능 |
| 같은 DB transaction | commit 전·후 | rollback 또는 원자적 완료 |
| 외부 API side effect | local transaction 밖 | provider idempotency key·reconciliation 필요 |

## 1. Idempotent consumer 계약

message는 immutable event ID를 가진다고 가정한다.

```json
{
  "event_id": "evt-00042",
  "type": "order.accepted",
  "schema_version": 1,
  "occurred_at": "2026-09-03T00:00:00Z",
  "data": { "order_id": "demo-42" }
}
```

consumer는 business effect와 processed ID 기록을 가능한 한 같은 transaction boundary에 둔다.

```sql
BEGIN;
INSERT INTO processed_events(event_id) VALUES ('evt-00042')
ON CONFLICT DO NOTHING;
-- 위 INSERT가 실제로 새 row를 만든 경우에만 business change 수행
COMMIT;
```

단순 `SELECT 후 INSERT`는 concurrent delivery race를 만들 수 있다. unique constraint 또는 동등한 atomic conditional write를 사용한다.

## 2. 중복과 poison message 주입

동일한 `event_id`를 두 번 보내고 business row가 한 번만 바뀌는지 확인한다. 다음에는 지원하지 않는 `schema_version`을 보내 반복 실패와 DLQ 이동을 관찰한다.

```mermaid
stateDiagram-v2
    [*] --> Available
    Available --> InFlight: receive
    InFlight --> Deleted: success + ack
    InFlight --> Available: timeout
    Available --> DLQ: max receives exceeded
    DLQ --> Available: controlled redrive
```

관측 항목은 queue depth, oldest age, receive count, processing latency, duplicate suppression count와 DLQ depth다.

## 3. Controlled redrive

- consumer가 새 schema를 안전하게 거부하거나 처리하도록 수정한다.
- DLQ snapshot과 message 수를 기록한다.
- 낮은 rate로 일부를 redrive해 정상 처리와 idempotency를 확인한다.
- 전체 redrive 뒤 source/DLQ/business record 수를 reconciliation한다.

AWS optional에서는 SQS source queue와 redrive policy, DLQ를 전용 prefix/tag로 만든다. queue URL, ARN과 payload에 민감 정보가 없는지 확인한다. 완료 후 source queue, DLQ, alarm, IAM policy를 inventory 역순으로 삭제한다.

## 실패 판정

- duplicate delivery마다 business side effect가 반복된다.
- poison message가 hot loop를 만들거나 DLQ 없이 사라진다.
- redrive 뒤 처리·실패·잔여 합계가 원래 DLQ count와 맞지 않는다.
- ack 전에 side effect, ack 뒤 state 기록처럼 atomic boundary가 갈라져 있다.

## 결과를 이렇게 읽는다

동일 event를 두 번 보낸 뒤 `processed_events`는 한 row, business 결과도 한 번이어야 한다. processed row만 하나인데 business effect가 두 번이면 두 작업의 atomic boundary가 갈라진 것이다. process memory의 set으로 중복을 막았다면 restart 뒤 같은 시험을 반복해 한계를 확인한다.

poison message가 DLQ로 이동하면 main consumer의 hot loop는 멈췄지만 business 처리는 아직 실패 상태다. payload와 schema version, error class를 조사해 consumer를 고친 뒤 제한된 rate로 redrive한다. 원래 DLQ 수는 성공·재실패·잔여 수의 합과 맞아야 한다.

oldest message age가 계속 늘면 새 메시지를 처리하고 있어도 backlog의 앞부분은 회복되지 않는 것이다. queue depth, 처리율, retry와 downstream capacity를 함께 봐야 예상 drain 시간을 계산할 수 있다.

## 스스로 설명해 보기

1. idempotency key를 process memory에만 두면 restart 뒤 어떤 문제가 생기는가?
2. DLQ message를 수정 없이 바로 redrive하면 왜 장애가 반복되는가?
3. retry 횟수뿐 아니라 oldest message age가 필요한 이유는 무엇인가?

<!-- source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue-redrive.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html | checked: 2026-09-03 -->
<!-- source: https://kafka.apache.org/documentation/#semantics | checked: 2026-09-03 -->
