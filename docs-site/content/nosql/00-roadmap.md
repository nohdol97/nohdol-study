# Redis와 DynamoDB 로드맵

## 처음 보는 사람을 위한 출발점

모든 데이터를 같은 데이터베이스에 같은 모양으로 저장할 필요는 없다. 10분 뒤 사라져도 되는 로그인 인증 정보와 수년간 남아야 하는 주문 기록은 요구가 다르다. 이 과정은 “NoSQL이 더 빠르다”는 결론에서 시작하지 않고, 어떤 질문을 얼마나 자주 하고 데이터가 사라져도 되는지를 먼저 정한다.

| 처음 만나는 말 | 학습용 쉬운 뜻 |
|---|---|
| 키(key) | 데이터를 다시 찾을 때 사용하는 고유한 이름 |
| 값(value) | 키에 연결해 저장하는 실제 데이터 |
| TTL | 데이터가 자동으로 사라질 때까지 남은 시간 |
| 메모리(memory) | 매우 빠르지만 전원 장애 뒤 보존 방법을 따로 고려해야 하는 저장 공간 |
| 파티션 키(partition key) | DynamoDB가 데이터를 어느 저장 구역에 둘지 결정할 때 쓰는 키 |
| 일관성(consistency) | 쓰기 직후 읽었을 때 최신 값이 보이는지에 관한 보장 |

Redis와 DynamoDB는 둘 다 key를 사용하지만 같은 제품의 대체재가 아니다. Redis의 만료되는 cache와 DynamoDB의 지속되는 주문 조회를 별도 사례로 따라가며 차이를 배운다.

## 먼저 제품이 아니라 access pattern을 고른다

Redis와 DynamoDB는 모두 “NoSQL”로 묶이지만 상태 위치, durability, partition, consistency와 failure boundary가 다르다. 이 과정은 동일 제품의 대체재 비교가 아니라 각 access pattern에 어떤 운영 계약이 필요한지 다룬다.

```mermaid
flowchart TD
    Q[access pattern] --> L{latency·data structure}
    L -->|in-memory structure·cache| R[Redis]
    L -->|managed key-value·document| D[DynamoDB]
    R --> RP[TTL·eviction·persistence·topology]
    D --> DP[partition key·index·consistency·capacity]
    RP --> F[failure contract]
    DP --> F
```

## 선수 지식

- key-value, hash와 partition의 기본 개념
- latency, throughput, durability와 consistency의 차이
- AWS IAM과 VPC endpoint의 기본 경계

## 학습 순서

1. **두 저장 모델**: Redis와 DynamoDB의 state·partition·failure를 구분한다.
2. **TTL·hot key 실습**: Redis expiration을 관찰하고 DynamoDB key design을 검증한다.

## 완료 조건

이 주제는 한 번 읽고 끝내지 않는다. 먼저 용어 표를 자신의 말로 바꾸고, 개념 장에서 한 요청의 흐름을 따라간다. 실습에서는 정상 상태를 먼저 기록한 뒤 조건 하나만 바꿔 실패를 만들고, 증거로 원인을 설명한 뒤 복구한다. 마지막으로 아래 운영 판단 질문에 답하면서 더 복잡한 환경으로 확장한다.

- cache miss와 durable data loss를 구분한다.
- DynamoDB access pattern에서 partition key와 index를 먼저 설계한다.
- hot key가 client retry, capacity와 latency에 미치는 영향을 설명한다.

## 범위 밖

MongoDB·Cassandra·OpenSearch 운영과 제품별 migration 비교는 포함하지 않는다.

## 처음 이해했는지 확인

1. cache와 source of truth는 데이터가 사라졌을 때 어떤 차이가 있는가?
2. Redis와 DynamoDB가 모두 key를 사용해도 같은 역할이라고 볼 수 없는 이유는 무엇인가?

**확인 기준:** cache는 원본에서 다시 만들 수 있지만 source of truth 손실은 업무 데이터 손실이 될 수 있다고 구분하면 된다. 두 제품은 저장 위치·지속성·분산 방식과 조회 계약이 다르다.

## 운영 판단으로 확장하기

1. Redis를 cache로 쓰는 경우와 source of truth로 쓰는 경우의 복구 계약은 어떻게 다른가?
2. DynamoDB에서 임의 ad-hoc query를 나중에 추가하기 어려울 수 있는 이유는 무엇인가?
3. 평균 traffic이 낮아도 hot partition이 생길 수 있는 이유는 무엇인가?

<!-- source: https://redis.io/docs/latest/develop/data-types/ | checked: 2026-09-03 -->
<!-- source: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html | checked: 2026-09-03 -->
