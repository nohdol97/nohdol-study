# Redis와 DynamoDB의 서로 다른 모델

## 먼저 이해하기

온라인 상점의 장바구니와 주문 원장을 비교해 보자. 장바구니 cache는 잠시 사라져도 source database에서 다시 만들 수 있고 아주 낮은 latency가 중요할 수 있다. 주문 원장은 특정 주문을 안정적으로 찾고 보존·감사해야 한다. 둘 다 key로 접근할 수 있지만 필요한 durability와 복구 계약은 다르다.

Redis는 memory에 data structure를 두고 매우 빠르게 조작하는 서버다. persistence와 replication을 구성할 수 있지만 어떤 설정을 선택했는지에 따라 restart 시 잃을 수 있는 범위가 달라진다. DynamoDB는 AWS가 partitioned storage 운영을 관리하는 서비스이며, application은 access pattern을 primary key와 index에 미리 투영해야 한다.

| 먼저 물을 질문 | Redis에서의 의미 | DynamoDB에서의 의미 |
|---|---|---|
| key는 무엇인가? | data type을 찾는 identifier | item의 partition·sort identity |
| 데이터가 사라져도 되는가? | cache인지 source of truth인지 결정 | backup·PITR·replication 요구 결정 |
| 어떻게 확장하는가? | memory, replica, shard와 client routing | key 분포와 partition capacity |
| 읽은 값은 얼마나 최신이어야 하는가? | replication·failover 시점 고려 | read consistency 옵션과 index 경계 |
| 한 key에 몰리면? | single-threaded command path와 large key 영향 | hot partition과 throttling 가능성 |

“NoSQL은 schema가 없다”는 설명도 부족하다. table DDL이 자유로울 수 있어도 key format, TTL 의미, value shape와 consumer expectation은 application contract로 존재한다. 이 contract를 versioning하지 않으면 데이터는 저장돼도 읽는 쪽이 해석하지 못한다.

## Redis: memory의 data structure를 운영한다

Redis의 string, hash, set, sorted set, stream 같은 type은 명령 의미와 비용을 바꾼다. TTL은 logical expiration 정책이며 memory pressure의 eviction policy와 같지 않다. expired key 제거 시점도 access와 background cycle의 영향을 받으므로 TTL 직후 memory가 정확히 즉시 반환된다고 가정하지 않는다.

```mermaid
flowchart LR
    C[client command] --> M[in-memory data]
    M --> T[TTL expiration]
    M --> E[eviction under maxmemory]
    M --> A[AOF]
    M --> S[RDB snapshot]
    A --> REC[restart recovery]
    S --> REC
```

RDB snapshot과 AOF는 durability·recovery time·write overhead가 다르다. replication은 availability에 도움을 주지만 backup을 대체하지 않는다. Sentinel과 Cluster는 topology 목적이 다르며 client가 failover와 redirection을 지원해야 한다.

## DynamoDB: access pattern을 partition key에 투영한다

DynamoDB table의 item은 primary key로 식별된다. partition key 또는 partition+sort key를 사용하며 secondary index는 별도의 query access pattern을 제공한다. key 분포가 치우치면 전체 table capacity가 충분해도 특정 key에 요청이 몰릴 수 있다.

```mermaid
flowchart TD
    A[access patterns] --> K[partition·sort key]
    K --> P1[partition A]
    K --> P2[partition B]
    K --> P3[partition C]
    A --> G[secondary index]
    G --> GP[index partitions]
```

eventually consistent read와 strongly consistent read의 선택은 API, 비용·latency와 지원 범위를 확인한다. global secondary index read는 eventually consistent다. transaction API가 존재해도 relational join과 arbitrary multi-row transaction model을 그대로 기대하지 않는다.

## 선택 표

| 질문 | Redis 쪽 핵심 | DynamoDB 쪽 핵심 |
|---|---|---|
| data identity | key와 data type | primary key와 item |
| scale boundary | memory·shard·replica | partition key 분포·capacity mode |
| lifetime | TTL·eviction | TTL deletion은 비동기적 수명주기 기능 |
| recovery | RDB/AOF·backup·replication | PITR·on-demand backup·global table 판단 |
| failure symptom | memory pressure·failover·fork/I/O | throttling·hot key·index lag |

## 스스로 설명해 보기

1. Redis TTL과 maxmemory eviction이 서로 다른 정책인 이유는 무엇인가?
2. DynamoDB의 GSI가 base table과 다른 failure·consistency 경계를 갖는 이유는 무엇인가?
3. replica가 존재해도 별도 backup이 필요한 이유는 무엇인가?

<!-- source: https://redis.io/docs/latest/develop/data-types/ | checked: 2026-09-03 -->
<!-- source: https://redis.io/docs/latest/develop/reference/eviction/ | checked: 2026-09-03 -->
<!-- source: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/ | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html | checked: 2026-09-03 -->
