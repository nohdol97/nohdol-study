# SQL과 Python: 확장하기 전에 결과를 입증하기

분산 엔진은 잘못된 조인도 매우 효율적으로 증폭한다. 먼저 행 하나의 의미와 반복·누락·과거 데이터가 답에 미치는 영향을 정의한다.

## 이 장에서 처음 쓰는 말

| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| 행 단위(grain) | 주문 항목 하나처럼 행 하나가 나타내는 대상 | 각 행이 무엇을 표현하는지 명시해 중복 집계와 잘못된 조인을 막는다. **구체적인 상황(가상 예시):** 주문 머리 정보와 항목을 조인하자 집계 수가 늘었다. → 의도한 행 단위를 명시·유지한다. → 올바른 행 식별자로 합계를 대조한다. |
| 카디널리티(cardinality) | 값이나 행의 수. 조인에서는 양쪽이 만들 수 있는 대응 수 | 합계를 믿기 전에 조인 결과 증가를 예상하고 의도하지 않은 다대다 대응을 찾는다. **구체적인 상황(가상 예시):** 일대일이라고 생각한 조인이 추가 행을 만든다. → 양쪽 조인 키의 대응 수를 센다. → 집계를 믿기 전에 중복 키를 찾는다. |
| 윈도 함수(window function) | 관련 행들을 하나의 집계 행으로 줄이지 않고 함께 계산하는 함수 | 개별 행을 유지하면서 순위·누적 합계·이웃 값을 계산할 때 쓴다. **구체적인 상황(가상 예시):** 고객별 최신 주문을 다른 열과 함께 조회해야 한다. → 고객 안에서 순서가 명확하도록 주문에 순위를 매긴다. → 시각이 같은 주문까지 포함해 고객마다 한 행이 선택되는지 확인한다. |
| 쿼리 계획(query plan) | 엔진이 결과를 얻기 위해 수행할 단계 | 쿼리 최적화를 선택하기 전에 스캔·조인·데이터 교환·추정값을 해석한다. **구체적인 상황(가상 예시):** 테이블이 커지자 보고서 조회가 느려졌다. → 실행 계획에서 스캔·조인·예상 행 수를 살핀다. → 원인에 맞게 수정한 뒤 실제 처리량과 시간을 비교한다. |
| 멱등성(idempotence) | 같은 논리 작업을 반복해도 의도한 결과가 유지되는 성질 | 결과가 불확실한 작업을 재시도·재생해도 의도한 업무 결과를 유지하도록 한다. **구체적인 상황(가상 예시):** 통신 시간 초과로 결제 이벤트가 두 번 전달된다. → 변하지 않는 업무 이벤트 식별자로 중복을 처리한다. → 재전송해도 잔액은 한 번만 바뀌는지 확인한다. |

## 먼저 이해하기

1. 각 입력의 행 단위와 키를 명시한다.
2. NULL, 통화, 취소, 이벤트 버전을 포함해 업무 결과를 정의한다.
3. 손으로 계산할 만큼 작은 예시 데이터를 만든다.
4. 성능 조사 전에 결과를 확인한다.
5. 계획을 읽고 입력 크기에 따라 늘어나는 작업을 측정한다.

고객별 과거 행이 두 개 있는 고객 차원 테이블은 적절한 버전을 선택하지 않으면 조인한 주문을 두 배로 만든다. `DISTINCT`는 증상을 숨기면서 값이 우연히 같은 정상 주문까지 지울 수 있다. 관계와 시간 경계를 고쳐야 한다.

## 실습 전에 준비할 것

표준 라이브러리 SQLite 모듈을 갖춘 Python 3으로 임시 작업 디렉터리에서 실행한다. 메모리 내 데이터베이스와 가상 값만 사용하며 네트워크나 자격 증명은 쓰지 않는다.

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE orders (
  event_id TEXT, customer_id TEXT, amount_cents INTEGER
);
INSERT INTO orders VALUES
  ('e1', 'c1', 100), ('e1', 'c1', 100),
  ('e2', 'c1', 250), ('e3', NULL, 50);
""")

# This fixture defines duplicates as identical retries of one event.
result = db.execute("""
WITH unique_events AS (
  SELECT event_id, customer_id, amount_cents
  FROM orders
  GROUP BY event_id, customer_id, amount_cents
)
SELECT customer_id, SUM(amount_cents)
FROM unique_events
WHERE customer_id IS NOT NULL
GROUP BY customer_id
""").fetchall()
assert result == [("c1", 350)], result
print(result)
db.close()
```

## 실행 결과 예시

독립 실행 가능한 Python/SQLite 예제의 출력이다.

```text
[('c1', 350)]
```

원시 c1 행의 합은 450센트이고 동일한 e1 재시도의 중복을 제거하면 350이다. 중복 제거를 없애면 단언문이 실패해야 한다. 같은 식별자의 페이로드 충돌에는 종합 프로젝트의 별도 충돌 관문이 필요하다.

## 결과를 이렇게 읽는다

올바른 대상 합계는 350센트다. `c1`을 단순 합산하면 재시도를 세어 450이 된다. NULL 고객은 의도적으로 제외했으므로 모든 입력 주문이 사용자에게 도달했음을 입증하는 쿼리는 아니다. 제외 건수를 별도로 추적한다.

두 번째 `e1`을 120센트로 바꾼다. 같은 이벤트 ID의 페이로드가 충돌하므로 그룹화로 중복 제거되지 않는다. 운영 계약은 충돌을 거부하거나 버전과 결정적인 우선순위를 정의해야 한다. 조용히 `MAX(amount_cents)`를 고르면 없는 업무 규칙을 만들어 버린다.

조인 전에 차원 키의 유일성을 검사한다. 다음으로 존재하지 않는 차원 키를 넣어 내부 조인과 왼쪽 조인을 비교하고 대응하지 않는 행 수를 명시적으로 센다. 쿼리 성공은 데이터베이스가 실행했다는 것만 입증하며 모든 업무 개체가 결과에 포함됐음을 입증하지 않는다.

## SQL 더 깊이 이해하기

### JOIN: 엔진 선택 전에 행 증폭부터 이해하기

입력 키가 왼쪽에 `m`번, 오른쪽에 `n`번 있으면 동등 조인은 그 키에 대해 `m × n`개 대응을 만든다. 주문 세 개와 고객 이력 두 버전을 조인하면 여섯 행이다. 해시 조인, 병합 조인, 인덱스 중첩 루프 모두 이 논리적 중복도를 유지하므로 알고리즘 교체로 고칠 수 없다.

내부 조인은 대응하지 않는 주문을 제거한다. 왼쪽 조인은 차원 필드를 NULL로 채워 보존하지만 이후 `WHERE dimension.region = 'KR'`를 쓰면 그 행들이 제거된다. 모든 주문을 보존하되 한국 차원 행만 연결하려면 조건을 `ON`에 둔다. 누락 차원은 `NOT EXISTS`로 찾는다. `NOT IN`의 하위 쿼리에 NULL이 있으면 예상과 달리 미정 결과가 생길 수 있다. 튜닝 전에 입력 행, 출력 행, 고유 사실 키, 미대응 건수를 비교한다.

### 윈도 함수: 순위·동순위 행·명시적 프레임

`GROUP BY`는 여러 입력을 그룹당 출력 하나로 줄인다. 윈도는 각 입력 행 옆에 값을 계산한다. `PARTITION BY customer_id`는 독립적인 계산을 나누며 윈도의 `ORDER BY`는 계산 순서만 정하고 최종 결과 순서는 보장하지 않는다. 표시 순서는 바깥 `ORDER BY`로 정한다.

현재 상태 중복 제거에는 권위 있는 버전 순서를 명시한 `ROW_NUMBER()`를 사용한다. 타임스탬프만으로는 동률이 생긴다. 누적합에는 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`와 결정적인 순서를 지정한다. range 프레임은 정렬값이 같은 동순위 행을 포함해 여러 행의 합이 한꺼번에 증가할 수 있다. `LAG`는 앞선 행과 비교할 뿐 그 행이 달력상 하루 전이라는 뜻은 아니다.

다음 별도 메모리 내 SQLite 예제를 Python 3으로 실행한다. 동률, 명시적 행 프레임, 재귀 CTE를 보여 준다. 버전 규칙은 이 예제의 입력 계약이다. `(event_id, source_seq)`가 같은 충돌은 이 쿼리 전에 거부해야 한다.

<!-- executable: sql-windows -->
```python
import sqlite3

with sqlite3.connect(":memory:") as db:
    db.executescript("""
    CREATE TABLE changes(event_id TEXT, source_seq INT, amount INT);
    INSERT INTO changes VALUES ('e1',1,100),('e1',2,120),('e2',1,250);
    CREATE TABLE payments(id INT, minute INT, amount INT);
    INSERT INTO payments VALUES (1,10,100),(2,10,250),(3,11,50);
    """)
    current = db.execute("""
      WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (
          PARTITION BY event_id ORDER BY source_seq DESC
        ) AS position FROM changes
      )
      SELECT event_id, amount FROM ranked WHERE position=1 ORDER BY event_id
    """).fetchall()
    frames = db.execute("""
      SELECT id,
        SUM(amount) OVER (ORDER BY minute RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        SUM(amount) OVER (ORDER BY minute,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      FROM payments ORDER BY id
    """).fetchall()
    depth = db.execute("""
      WITH RECURSIVE steps(n) AS (
        SELECT 1 UNION ALL SELECT n+1 FROM steps WHERE n<4
      ) SELECT SUM(n) FROM steps
    """).fetchone()[0]
    assert current == [('e1',120),('e2',250)]
    assert frames == [(1,350,100),(2,350,350),(3,400,400)]
    assert depth == 10
    print('current:', current)
    print('id, range_total, rows_total:', frames)
    print('recursive_sum:', depth)
```

예상 출력:

```text
current: [('e1', 120), ('e2', 250)]
id, range_total, rows_total: [(1, 350, 100), (2, 350, 350), (3, 400, 400)]
recursive_sum: 10
```

분 값이 10인 결제 둘이 동순위이므로 첫 결제의 range 누적합부터 350이다. 재귀 `WHERE`를 없애면 종료 조건이 사라진다. 그래프 탐색에서는 방문 식별자 추적이나 깊이 제한으로 순환의 무한 확장도 막는다. CTE는 쿼리 식에 붙인 이름이며 모든 엔진에서 캐시된 임시 테이블인 것은 아니다. 비용이 큰 CTE를 재사용한다면 엔진의 실체화 동작을 확인한다.

### 집계: 소계와 누락값

`GROUPING SETS ((region, day), (region), ())`는 일별 지역 합계, 전체 날짜의 지역 합계, 총합을 한 식으로 구한다. `GROUPING(region)`과 `GROUPING(day)`로 소계 표시용 NULL과 실제 누락값을 구분한다. `SUM`은 NULL 입력을 무시하며 금액이 모두 NULL인 그룹은 NULL이다. 매출 0의 증거가 아니다. `COUNT(*)`는 행을, `COUNT(amount)`는 NULL이 아닌 금액을 센다. SQLite는 `GROUPING SETS`를 지원하지 않으므로 이 확장은 DuckDB나 PostgreSQL에서 실행한다.

금액은 `DECIMAL(precision, scale)` 또는 고정 정수 단위와 통화를 정의한다. 환산 전 서로 다른 통화를 더하면 안 된다. 시간은 소스 오프셋을 보존하거나 알려진 시점을 UTC로 정규화한 뒤 사용자의 업무 시간대에서 보고 날짜를 구한다. 일광 절약 시간 전환 중의 현지 시각은 모호할 수 있고 시간대 없는 문자열로는 누락 오프셋을 복원할 수 없다.

### 피할 수 있는 가장 큰 작업부터 실행 계획 읽기

이벤트 날짜 필터가 있는 `events JOIN users USING (user_id)`를 생각해 보자. 파티션 제거 후 남을 이벤트 행 수를 먼저 추정하고 조인·결과에 필요한 열만 선택한다. predicate pushdown은 지원하는 필터를 스캔 쪽으로 내리고, 열 제거는 불필요한 열 청크 읽기를 피하며, 분산 shuffle은 남은 행을 키에 따라 워커 사이로 이동시킨다. 서로 다른 종류의 작업을 줄이는 기법이다.

PostgreSQL의 `EXPLAIN (ANALYZE, BUFFERS)`는 쿼리를 실제 실행하고 관측 행 수와 반복 수를 보고한다. 반복당 5,000행을 1,000번 실행하면 대략 500만 행 방문이며 5,000행이 아니다. 처음 크게 어긋난 추정값·실측값을 찾는다. 오래된 통계나 열 사이 상관관계는 잘못된 조인 선택을 유발할 수 있다. 선택도가 높은 OLTP 쿼리는 B-tree와 임의 조회가 유리할 수 있고 대부분의 행을 읽으면 순차·열 기반 스캔이 유리할 수 있다. 인덱스 유지에는 쓰기 작업도 추가된다.

트랜잭션은 실행 계획과 별도로 읽는다. PostgreSQL Read Committed는 한 트랜잭션의 두 문장에서 서로 다른 커밋 데이터를 볼 수 있다. Repeatable Read는 안정된 트랜잭션 스냅샷을 사용하지만 행 간 불변식에는 애플리케이션 로직이 여전히 필요할 수 있다. Serializable은 트랜잭션을 거부할 수 있고 전체 재시도가 필요하다. 주문 공개에서는 대사와 후보 선택이 같은 소스 스냅샷을 공유해야 하는지 정한다. 그렇지 않으면 각각 올바른 두 쿼리가 서로 다른 입력 모집단을 설명할 수 있다.

## 파이프라인 기반으로서의 Python

### 타입·dataclass·직렬화 경계

타입 주석은 독자와 정적 검사기에 레코드 형태를 알려 주고 dataclass는 오브젝트 메서드를 생성한다. 둘 다 입력 JSON을 자동 검증하지 않는다. 역직렬화 시 산술 전에 검증한다. Python에서는 `isinstance(True, int)`가 참이므로 금액 필드는 `type(value) is int`가 필요할 수 있다. 스키마 버전과 단위도 직렬화한다. JSON 자체는 Python dataclass, decimal 타입, 타임스탬프 시간대를 보존하지 않는다. 변환 규칙을 명시하고 신뢰할 수 없는 pickle을 레코드 형식으로 역직렬화하지 않는다.

### 반복자·제너레이터·컨텍스트 관리자

제너레이터는 `yield`에서 멈춰 하위 코드가 한 행 또는 제한된 배치씩 소비하게 한다. 제한하는 것은 처리 중 배치이며 모든 자료구조가 아니다. 무제한 중복 제거 집합은 고유 식별자 수만큼 계속 커진다. `list(generator)`는 모든 행을 메모리에 만든다. 컨텍스트 관리자의 종료 경로는 예외가 전파되는 중에도 실행되므로 파일 닫기와 트랜잭션에 사용한다. SQLite 연결 컨텍스트는 커밋·롤백을 관리한다. 연결 수명 자체도 끝내려면 `close()`나 `contextlib.closing`을 사용한다.

이 예제는 파싱과 소비를 분리하고 거부 건수를 드러낸다. Python 표준 라이브러리만 사용한다.

<!-- executable: python-records -->
```python
import json
from dataclasses import dataclass
from itertools import islice

@dataclass(frozen=True)
class Event:
    event_id: str
    amount_cents: int

def parse(line: str) -> Event:
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError('record must be an object')
    key, amount = value.get('event_id'), value.get('amount_cents')
    if not isinstance(key, str) or not key or type(amount) is not int or amount < 0:
        raise ValueError('invalid identity or amount')
    return Event(key, amount)

def batches(rows, size):
    if size < 1:
        raise ValueError('positive batch size required')
    iterator = iter(rows)
    while batch := tuple(islice(iterator, size)):
        yield batch

lines = [
    '{"event_id":"e1","amount_cents":100}',
    '{"event_id":"bad","amount_cents":true}',
    '{"event_id":"e2","amount_cents":250}'
]
accepted, rejected = [], 0  # Small fixture; stream accepted records in production.
for line in lines:
    try:
        accepted.append(parse(line))
    except (ValueError, TypeError):
        rejected += 1
sizes = [len(batch) for batch in batches(iter(accepted), 1)]
assert (len(accepted), rejected, sizes) == (2, 1, [1, 1])
assert sum(row.amount_cents for row in accepted) == 350
print('accepted=2 rejected=1 total_cents=350 batch_sizes=[1, 1]')
```

예상 출력:

```text
accepted=2 rejected=1 total_cents=350 batch_sizes=[1, 1]
```

불리언을 음수 정수나 문자열로 바꿔도 거부되어야 한다. 운영 환경에서는 전체 입력을 로그에 덤프하지 않고 통제된 거부 사유와 식별자를 보존한다.

### 비동기·다중 프로세스·메모리·테스트

`asyncio`는 네트워크·데이터베이스 클라이언트가 제어권을 양보할 때 대기를 겹친다. 코루틴 안에서 블로킹 클라이언트를 호출하면 여전히 이벤트 루프를 막는다. 세마포어나 고정 워커 큐로 동시성을 제한하고 시간 제한을 적용하며 취소가 이미 승인된 원격 쓰기에 미칠 영향을 정한다. 시간 초과 후 재시도는 쓰기를 반복할 수 있으므로 안정적인 멱등 식별자를 사용한다. `TaskGroup`은 관련 태스크의 수명을 묶지만 태스크 100만 개를 생성하면 오브젝트도 100만 개 할당된다.

일반적인 CPython 빌드에서 CPU 작업이 큰 Python 변환은 프로세스로 나누면 단일 인터프리터의 실행 잠금과 독립적으로 수행할 수 있다. 프로세스 시작, pickle 변환, 프로세스 간 전송도 측정한다. 작은 계산마다 큰 DataFrame을 전달하면 계산보다 비용이 클 수 있다. 워커 함수는 import 가능하게 두고 spawn 실행을 위해 진입점을 `if __name__ == '__main__':`로 보호한다.

`tracemalloc` 스냅샷으로 Python 할당 증가를 찾고 프로세스 RSS로 더 넓은 메모리 사용을 본다. 네이티브 배열 버퍼가 Python 할당 추적에 전부 보이지 않을 수 있다. 같은 입력에서 스트리밍 파서와 `list(...)`를 비교해 최대 메모리와 시간을 기록한다. CLI 진입점과 의존성이 선언된 import 가능 모듈로 변환을 구성해 테스트와 예약 작업이 같은 코드를 실행하게 한다. pytest에서는 NULL·중복·충돌·빈 입력·시간 경계 예제를 매개변수화하고 함수 반환 여부만 확인하지 말고 증분 출력을 전체 재계산과 비교한다.

구조화 로그에는 작업, 코드 리비전, 실행 ID, 사유를 넣는다. Linux 도구는 작업과 CPU·RSS·디스크 공간·파일 디스크립터·소켓을 연결하고 Git은 동작을 리비전·diff와 연결한다. 느리거나 바뀐 결과를 진단할 때 쿼리 계획과 함께 기록한다.

## 스스로 설명해 보기

정수 센트가 이 예제에는 유용하지만 보편적인 금액 모델을 정의하지 않는 이유는 무엇인가? 예제는 고정 단위 하나만 사용하며 실제 데이터셋에는 통화, 소수 자릿수, 반올림 정책, 경우에 따라 환산 시점의 의미가 필요하다. 네 행 테스트가 정확성 오류는 드러내면서 분산 처리량은 거의 설명하지 못하는 이유를 말해 보자.

다음은 [Parquet와 오브젝트 스토리지](../../../docs/guides/data-observability/03-parquet-object-storage.md)로 이어간다.

<!-- source: https://docs.python.org/3/library/sqlite3.html | checked: 2026-09-10 | standard-library API; fixture independently executable -->
<!-- source: https://www.postgresql.org/docs/current/using-explain.html | checked: 2026-09-10 | estimates and execution plans -->
<!-- source: https://www.postgresql.org/docs/current/tutorial-window.html | checked: 2026-09-10 | windows and peers -->
<!-- source: https://www.postgresql.org/docs/current/queries-with.html | checked: 2026-09-10 | recursive CTEs and materialization -->
<!-- source: https://www.postgresql.org/docs/current/transaction-iso.html | checked: 2026-09-10 | isolation levels -->
<!-- source: https://docs.python.org/3/library/asyncio-task.html | checked: 2026-09-10 | task lifetime and concurrency -->
<!-- source: https://docs.python.org/3/library/tracemalloc.html | checked: 2026-09-10 | allocation tracing scope -->
