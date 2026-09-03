# Lock, backup과 restore 실습

> 실습 등급: **Local**. disposable PostgreSQL 18 instance를 사용한다. production query를 그대로 복사해 실행하지 않는다.

## 1. 실습 데이터

```sql
CREATE TABLE accounts (
  id bigint PRIMARY KEY,
  balance numeric(12,2) NOT NULL CHECK (balance >= 0)
);
INSERT INTO accounts VALUES (1, 100.00), (2, 100.00);
```

두 session을 연다. session A에서 row를 변경하고 transaction을 유지한다.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
```

session B에서 같은 row를 변경하면 대기한다.

```sql
UPDATE accounts SET balance = balance + 10 WHERE id = 1;
```

세 번째 session에서 waiter와 blocker를 관찰한다.

```sql
SELECT a.pid, a.wait_event_type, a.wait_event, pg_blocking_pids(a.pid) AS blockers, a.query
FROM pg_stat_activity AS a
WHERE cardinality(pg_blocking_pids(a.pid)) > 0;
```

session A를 `COMMIT` 또는 `ROLLBACK`한 뒤 B가 어떻게 진행되는지 확인한다. 완료 후 잔여 transaction이 없는지 검사한다.

## 2. Logical backup과 별도 restore

```bash
pg_dump --format=custom --file=accounts.dump replace_source_db
createdb replace_restore_db
pg_restore --dbname=replace_restore_db --clean --if-exists accounts.dump
psql replace_restore_db -c 'TABLE accounts ORDER BY id;'
```

backup 성공 exit code와 파일 size만으로 복구 가능성을 증명하지 않는다. 별도 database에 restore하고 row count, constraint, 대표 query와 application compatibility를 확인한다.

```mermaid
flowchart LR
    S[source DB] --> B[backup artifact]
    B --> V[checksum·보관]
    V --> R[isolated restore]
    R --> Q[data·schema query]
    Q --> T[RPO·RTO receipt]
```

## 3. PITR와 failover 판정

PITR에는 연속적인 WAL archive와 그보다 앞선 base backup, recovery target이 필요하다. 실제 운영 훈련에서는 다음을 기록한다.

- 마지막 복구 가능한 timestamp와 예상 RPO
- restore 시작부터 read/write 승인까지 실제 RTO
- timeline과 target 전후의 marker row
- application DNS/endpoint 전환과 stale client 처리
- replica promotion 뒤 원 primary 재합류 절차

managed service가 backup과 promotion API를 제공해도 application consistency와 client 전환 검증 책임은 사라지지 않는다.

## 정리

두 test database와 `accounts.dump`를 삭제한다. 실제 backup 보관 정책의 artifact에는 동일한 cleanup을 적용하지 않는다.

```bash
dropdb replace_restore_db
rm -f accounts.dump
```

## 스스로 설명해 보기

1. waiter가 아니라 blocker를 먼저 찾아야 하는 이유는 무엇인가?
2. restore된 row count만 같아도 복구 검증이 부족한 이유는 무엇인가?
3. database promotion 완료와 서비스 복구 완료는 어떻게 다른가?

<!-- source: https://www.postgresql.org/docs/18/explicit-locking.html | checked: 2026-09-03 | version: PostgreSQL 18 -->
<!-- source: https://www.postgresql.org/docs/18/monitoring-stats.html | checked: 2026-09-03 | version: PostgreSQL 18 -->
<!-- source: https://www.postgresql.org/docs/18/app-pgdump.html | checked: 2026-09-03 | version: PostgreSQL 18 -->
<!-- source: https://www.postgresql.org/docs/18/continuous-archiving.html | checked: 2026-09-03 | version: PostgreSQL 18 -->
