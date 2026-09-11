# Databricks부터 Snowflake까지: 같은 약속 비교하기

파이프라인의 보장을 말할 수 있게 된 뒤 관리형 플랫폼을 배우면 더 유용하다. 같은 데이터셋·품질 규칙·복구 사례·접근 검사를 다시 구현하고 비교 가능한 근거로 아키텍처 절충을 설명한다.

## 이 장에서 처음 쓰는 말

| 용어 | 의미 |
|---|---|
| 관리형 계산(managed compute) | 공급자에게 공급·운영 일부를 맡긴 처리 용량 |
| Unity Catalog | 지원 자산에 대한 Databricks 거버넌스·탐색 계층 |
| Lakeflow | Databricks의 수집·파이프라인·작업 기능군 |
| 동적 테이블(dynamic table) | 쿼리로 정의하고 갱신으로 유지하는 Snowflake 테이블 |
| DMF | 데이터 속성을 측정하는 Snowflake Data Metric Function |
| Warehouse | Snowflake에서 지원 워크로드를 처리하는 계산 자원 |

## 먼저 이해하기

1. 입력 예제와 예상 결과를 플랫폼별 구현 밖에 보존한다.
2. 수집·변환·공개·품질·계보·권한·텔레메트리를 플랫폼 기능에 대응시킨다.
3. 임시 개발 환경에서 파이프라인을 구현한다.
4. 로컬 설계와 같은 실패·접근 시험을 실행한다.
5. 정확성·복구·운영 노력·성능·비용을 별도로 비교한다.

이 장은 안내된 클라우드 실습이며 실행 완료한 데이터 플랫폼 배포가 아니다. 관련 기능이 있는 계정, 지출 한도, 임시 스키마·카탈로그, 실습 리소스만 생성·삭제할 권한이 필요하다. 이 과정에서 배포된 산출물은 문서 사이트다.

## Databricks: Spark·Delta·거버넌스 심화

워크스페이스 작업, 계산, 저장, 카탈로그 권한의 분리를 공부한다. 저장 위치의 소유자, 작업 실행 신원, 코드 버전 관리, 이벤트 로그·쿼리 이력 보존 위치를 확인한다. 노트북 상태만 운영 변환의 기록으로 삼지 않는다.

raw·accepted·daily-revenue 테이블을 만든다. raw에는 이벤트 ID·수집 시각을 보존한다. 공개 전 유효 버전을 결정하고 결함을 격리한다. Lakeflow Spark Declarative Pipelines의 expectations는 정책에 따라 무효 행을 유지하며 지표를 수집하거나 버리거나 갱신을 실패시킨다. 사용자 계약으로 고른다. 무효 매출 행을 버리면 accepted의 범위 검사가 통과해도 완전성이 달라진다.

Unity Catalog 계보는 문서화된 범위·권한 제한 아래 지원 작업의 관계를 기록한다. 열 계보에 등록 테이블이 필요하면 이를 참조하고 실제 연동을 시험한다. 검토 문서는 지원되는 테이블 이름 참조와 열 계보가 수집되지 않는 경로 기반 사례를 구분한다. 보이는 그래프가 모든 외부 스크립트·내보내기를 담았다는 증거는 아니다.

필요한 워크플로 운영에 Lakeflow Jobs를 사용한다. 코드·런타임 버전, 입력·출력 ID, 재시도·복구 결과를 기록한다. 모델·AI 평가 단계에 이르면 MLflow를 추가하고 결과를 정확한 자료 집합·애플리케이션 묶음에 연결한다.

## Databricks 실습

종합 프로젝트 예제로 개발 파이프라인을 만들고 전용 신원으로 실행한다. NULL 키, 알 수 없는 통화, 늦은 수정을 넣는다. 유지·삭제·실패 정책을 별도 실행해 대상 입력, 격리 출력, 공개 행, 업무 합계를 기록한다. 실패 실행을 재시작해 승인 이벤트가 이중 집계되지 않는지 확인한다.

등록 테이블과 의도적으로 미지원·외부 실행한 단계의 계보를 보고 범위 차이를 기록한다. 제한 뷰·정책의 소비자 신원과 비허용 신원으로 원본 테이블을 시험한다. 계산 사용량을 확인하고 실습 스케줄·리소스를 제거해 실행 중 계산이 남지 않았는지 검증한다.

## Snowflake: 저장·계산·관리형 갱신 비교

Snowflake SQL과 Snowpark는 다른 처리 표현이다. PySpark가 그대로 이식된다고 가정하기 전에 실행·데이터 이동을 배운다. 기본 Snowflake 테이블과 Iceberg 연동도 관리·상호 운용 책임이 다르다.

동적 테이블은 쿼리를 실체화하고 target lag와 지원 갱신 동작으로 결과를 유지한다. 목표는 측정할 스케줄 의도이며 종단 간 업무 기한 보장이 아니다. Streams·Tasks는 변경 중심·절차형 워크플로의 다른 방식이다. Openflow는 지원 커넥터가 소스에 맞을 때 수집 비교에 넣으며 모든 스트림 처리기의 다른 이름이 아니다.

Snowflake 품질 검사는 DMF·expectation을 쓴다. 검토 문서는 Data Quality Monitoring을 Enterprise Edition 기능으로 표시한다. 채택 전에 계정 에디션, 지원 오브젝트, 권한, 스케줄, 비용을 확인한다. NULL 수 측정·expectation이 원본을 고치거나 대체 동작을 자동 정의하지는 않는다.

Horizon Catalog에서는 계보·분류·접근·정책의 거버넌스와 탐색을 조사한다. Cortex는 거버넌스가 있는 데이터에서 AI 함수·제공을 평가하는 후속 단계다. 제품 이름을 정확한 동등품으로 취급하지 말고 요구·현재 계정 가용성과 비교한다.

## Databricks 구조: 신원과 실행 경계

워크스페이스의 코드·작업 설정, 태스크 계산 자원, 데이터 위치, Unity Catalog 등록 오브젝트·권한을 나눈다. 노트북 사용자와 예약 작업 run-as 신원은 권한이 다를 수 있다. 예약 신원의 bronze 읽기, silver/gold 쓰기, 체크포인트·관리 저장소 접근을 시험한다. 관리자 대화형 실행 성공은 좋은 운영 검증이 아니다.

Unity Catalog는 지원 자산에 catalog/schema/object 계층을 사용한다. 관리 테이블과 외부 테이블은 저장 수명 책임이 다르다. storage credential·external location은 클라우드 저장소로의 통제된 연결이며 모든 노트북에 원시 비밀을 주라는 뜻이 아니다. 등록 테이블 참조는 임의 경로 읽기보다 지원 거버넌스·계보 연동이 더 많이 관측하게 한다.

SQL warehouse는 SQL 워크로드를, 다른 지원 계산 방식은 작업·대화형 Spark를 실행한다. 워크로드, 런타임·라이브러리, 격리, 시작 지연, 측정 동시성으로 선택한다. 공급자가 장비를 관리해도 주문 행 단위·재시도 식별자·사용자 기한은 대신 결정하지 않는다.

## Lakeflow 실습: bronze·silver·gold와 expectations

기존 개발 카탈로그의 임시 Databricks 스키마 `study_lab`에서만 실행한다. `pyspark.pipelines`와 Databricks expectations를 지원하는 런타임의 개발 파이프라인이 같은 카탈로그·스키마에 공개하도록 구성한다. 네 입력 행을 쉽게 보려고 배치 materialized view를 사용한다. 관리형 플랫폼 실습이며 로컬 실행 결과가 아니다.

선택한 카탈로그의 새 스키마에서 다음 SQL을 한 번 실행한다.

```sql
CREATE SCHEMA study_lab;
CREATE TABLE study_lab.orders_bronze (
  event_id STRING, amount_cents BIGINT, currency STRING
) USING DELTA;
INSERT INTO study_lab.orders_bronze VALUES
  ('e1',100,'USD'),('e2',250,'USD'),
  (NULL,50,'USD'),('e4',70,'UNKNOWN');
SELECT COUNT(*) AS raw_rows FROM study_lab.orders_bronze;
```

개발 파이프라인에 다음 Python 소스를 추가한다. 함수는 DataFrame을 반환하고 파이프라인이 의존 그래프를 구성·실행한다. 데이터셋 정의 함수는 계획 중 평가될 수 있으므로 알림 전송이나 명령형 외부 쓰기를 넣지 않는다.

```python
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(name='orders_silver')
@dp.expect_or_drop(
    'valid_order',
    "event_id IS NOT NULL AND amount_cents >= 0 AND currency = 'USD'"
)
def orders_silver():
    return spark.read.table('study_lab.orders_bronze')

@dp.materialized_view(name='orders_gold')
def orders_gold():
    return (spark.read.table('study_lab.orders_silver')
            .groupBy('currency')
            .agg(F.count('*').alias('event_count'),
                 F.sum('amount_cents').alias('total_cents')))
```

갱신 성공 뒤 다음 결과와 파이프라인 품질·이벤트 근거를 확인한다.

```sql
SELECT COUNT(*) AS accepted_rows FROM study_lab.orders_silver;
SELECT currency,event_count,total_cents FROM study_lab.orders_gold;
```

논리적 예상 결과:

```text
bronze raw_rows=4
silver accepted_rows=2
gold currency=USD event_count=2 total_cents=350
valid_order violations=2, with drop policy recorded
```

drop 정책은 이 학습 비교에만 적합하다. 생산자 기준 완전성을 입증하거나 이벤트 ID 중복을 제거하지 않는다. 매출 제품으로 삼기 전에 종합 프로젝트의 충돌·버전·예상 입력 검사를 추가하고 raw 결함은 조사용으로 유지한다.

별도 개발 실행에서 `expect_or_drop`을 `expect`로 바꿔 무효 행 유지·위반 보고를 확인하고, `expect_or_fail`로 바꿔 해당 흐름을 실패시킨다. 갱신 결과와 여전히 보이는 이전 출력을 기록한다. 흐름 하나의 실패는 파이프라인 전체 데이터셋·흐름에 대한 보편적 트랜잭션이 아니다. 실패한 갱신이라고 다른 출력이 전혀 바뀌지 않았다고 해석하지 않는다.

### Auto Loader와 스트리밍 테이블

Auto Loader는 지원 오브젝트 저장소의 새 파일을 발견하고 진척을 유지한다. `cloudFiles` 스트리밍 읽기와 스트리밍 테이블은 증분 파일 수집에 맞는다. 스키마 추론·진화·rescued data 동작을 명시적으로 설정·확인한다. 파일 발견 진척은 업무 이벤트 유일성의 증거가 아니다. 두 파일에 같은 이벤트가 있을 수 있다. bronze에 소스 경로, 수집 시각, 스키마 정보, 이벤트 ID를 보존한다.

CDC는 계약에 맞는 경우 지원 AUTO CDC 절차로 소스 키·순번·갱신·삭제를 대응시킨다. 파일 도착 시각을 업무 갱신의 권위 있는 순서로 취급하지 않는다. 늦은 수정에는 소스 순번과 대상 이력 정책이 필요하다.

## Jobs·복구·Delta 유지 관리·MLflow 제공

Lakeflow Jobs는 태스크 의존성·인자·스케줄·재시도·복구를 조정한다. 안정된 업무 구간과 소스 스냅샷을 명시적으로 전달한다. repair run은 지원 동작 아래 실패·의존 작업을 다시 실행할 수 있지만 앞서 성공한 부수 효과는 남는다. 추가 공개·외부 효과 전에 출력·실행 ID를 대사한다.

Delta 유지 관리는 파일 배치와 보존 이력을 다룬다. 병합·데이터 건너뛰기는 특정 워크로드를 개선하므로 쓰기·계산 비용과 비교해 측정한다. vacuum·보존 정책은 과거 조회·재생 범위를 정한다. 작업 체크포인트와 Delta 로그는 다른 상태를 보호하므로 복구 계약에 맞춰 둘 다 백업·재구성한다.

MLflow는 지원 연동으로 모델·앱 실행, 산출물, 트레이스, 평가 기록을 추적한다. 등록 모델·AI 앱 버전을 학습·자료 스냅샷, 매개변수, 평가 모음과 연결한다. 모델 제공은 선택 산출물을 통제된 런타임·엔드포인트로 노출한다. 배포에는 오프라인 점수 외에 호환성·인가·지연·용량·롤백 검사가 필요하다. 모델 등록 성공은 제공 롤아웃이 아니다.

## Snowflake 구조: SQL·마이크로 파티션·warehouse

기본 테이블은 관리되는 열 기반 마이크로 파티션에 저장하고 메타데이터로 읽기를 줄인다. warehouse는 계산을 공급하며 크기 확장과 동시성 확장은 다른 문제를 푼다. 증설 전 쿼리 프로파일, 읽은 파티션·바이트, spill, 대기, 캐시를 본다. 캐시된 쿼리 반복은 첫 실행 비용을 숨길 수 있다.

Snowpark는 지원 API로 Snowflake 안에서 실행할 연산을 표현한다. DataFrame 식 구성과 로컬 결과 실체화는 다르며 `collect()`는 결과를 클라이언트에 가져온다. Python 프로시저·UDF에는 런타임·패키지 제약이 있다. PySpark 메서드 이름만 바꿔서는 계획 동작·함수 지원·데이터 이동을 보존할 수 없다.

## Streams와 Tasks: 변경 위치와 실행 스케줄

Snowflake stream은 소스 테이블의 변경 위치를 추적하며 Kafka 브로커나 독립적인 전체 복사본이 아니다. 조회만으로 오프셋이 전진하지 않는다. 커밋된 DML 트랜잭션에서 소비해야 규칙에 따라 전진한다. 독립 소비자의 진척에는 별도 stream을 쓰고 소스 변경 보존 한도와 비교해 staleness를 감시한다.

수동 변경 적용 실습에는 새 임시 Snowflake 스키마와 승인된 warehouse가 필요하다. 테이블 둘과 stream 하나를 만들며 스케줄은 만들지 않는다. 문장을 순서대로 실행한다. 메타데이터 action 필드로 삽입·삭제 행 이미지와 갱신 쌍을 구분한다.

```sql
CREATE TABLE study_source (event_id STRING, amount_cents NUMBER(18,0));
CREATE TABLE study_target (event_id STRING, amount_cents NUMBER(18,0));
CREATE STREAM study_changes ON TABLE study_source;
INSERT INTO study_source VALUES ('e1',100),('e2',250);

BEGIN;
MERGE INTO study_target t USING (
  SELECT event_id,amount_cents FROM study_changes
  WHERE METADATA$ACTION='INSERT'
) s ON t.event_id=s.event_id
WHEN MATCHED THEN UPDATE SET amount_cents=s.amount_cents
WHEN NOT MATCHED THEN INSERT (event_id,amount_cents)
VALUES (s.event_id,s.amount_cents);
COMMIT;

SELECT COUNT(*),SUM(amount_cents) FROM study_target;
SELECT COUNT(*) AS pending_changes FROM study_changes;

UPDATE study_source SET amount_cents=120 WHERE event_id='e1';
SELECT event_id,METADATA$ACTION,METADATA$ISUPDATE FROM study_changes;
```

첫 예상 결과는 `(2,350)`이고 커밋 후 대기 변경은 0이다. 다음 갱신에서 변경 표현을 확인하고 같은 MERGE 트랜잭션을 다시 실행하면 `(2,370)`, 반복해도 `(2,370)`이다. 이벤트 ID별 현재 소스 행 하나를 가정하고 삽입·갱신을 처리한다. 소스 삭제는 의도적으로 구현하지 않았으므로 확장 전에 트랜잭션으로 조정한 삭제 분기와 예제를 추가한다. 다중 소스 대응은 MERGE 전에 결정적으로 대사해야 한다.

task는 스케줄·지원 trigger에 따라 SQL·프로시저를 실행한다. task 그래프는 의존성을 설명하며 재개·중지, 권한, 중첩·재시도, 계산 선택은 운영 책임이다. 검증한 트랜잭션을 프로시저로 감싼 뒤 예약하고 소스·대상 결과 ID를 유지한다. task 예약이 모호한 MERGE를 고치거나 stale stream의 변경을 복원하지는 않는다.

## 동적 테이블과 절차형 변경 적용

동적 테이블은 유지할 쿼리 결과를 선언한다. Snowflake가 지원 갱신 모드를 선택·사용하고 target lag를 향해 갱신한다. 쿼리가 적합하면 증분 갱신은 영향 부분을, 전체 갱신은 전체 결과를 계산한다. 실제 모드·이력·상위 의존성·비용을 본다. `TARGET_LAG`는 의도한 신선도 관계이며 실패한 소스 적재가 업무 기한 안에 들어온다는 보장이 아니다.

원하는 결과가 지원 선언형 쿼리이고 관리 갱신에 맞으면 동적 테이블을 선택한다. 명시적 절차, 부수 효과, 트랜잭션 순서가 필요하면 streams/tasks를 고른다. 같은 운영 계약의 교환 가능한 문법이 아니다. 단순 `SELECT COUNT(*)` 미리보기로는 조인·UDF·미지원 구문이 있는 큰 쿼리의 갱신 적합성을 알 수 없다.

## DMF·Horizon·Openflow·Cortex의 책임

DMF는 NULL 수·신선도 같은 속성을 측정하고 expectation은 허용 조건과 비교한다. 예약 감시는 실행·권한·비용 요구를 더한다. NULL 키 0도 유일성·완전한 소스 전달을 입증하지 않는다. 예약 전 계정 에디션·현재 지원 오브젝트를 확인한다. 검토한 Data Quality Monitoring에는 Enterprise Edition이 필요하다.

Horizon은 정책·분류·계보 등 거버넌스·탐색 기능을 묶는다. Unity Catalog처럼 독자 신원으로 행 접근·마스킹을 시험하고 계보 범위를 본다. Openflow는 지원 흐름·커넥터의 수집·연동을 제공하므로 선택 커넥터의 소스 체크포인트, 오류 경로, 재생을 평가한다. Cortex의 AI·검색·추론도 다른 AI 엔드포인트처럼 접근·신선도·평가·비용 계약이 필요하다.

정리 시 실습 task·pipeline·schedule을 멈추고 상태를 확인한 뒤 임시 리소스만 제거한다. 실제 실행했다면 계산·청구 근거를 기록한다. 여기 예상 결과를 만들기 위해 계정을 만들거나 비용을 청구하지 않았다.

## 비교 워크시트

| 요구 | Databricks 조사 | Snowflake 조사 |
|---|---|---|
| 변환·공개 | Spark·Delta·Lakeflow pipelines | SQL·Snowpark·동적 테이블·Tasks |
| 품질 | Expectations·모니터링·사용자 검사 | DMF·expectations·사용자 검사 |
| 계보·접근 | Unity Catalog 범위·정책 | Horizon 계보·정책 범위 |
| 재생·복구 | 소스 위치·체크포인트·작업 복구 | 변경 보존·갱신·task 동작·과거 재구성 |
| AI 수명 주기 | MLflow·지원 AI 플랫폼 기능 | Cortex·지원 평가·제공 기능 |
| 경제성 | 계산·런타임·저장·전송·오케스트레이션 | warehouse·serverless·저장·전송·갱신·검사 |

유용한 비교는 소스 크기, 쿼리 동시성, 캐시 상태, 런타임 설정, 반복 측정, 출력 동등성, 복구 시간, 비용 내역을 기록한다. 한 번의 준비된 쿼리나 체험 크레딧 잔액으로 승자를 정하지 않는다.

## 실행 결과 예시

유효 두 행·무효 두 행의 가상 정책 워크시트이며 관리형 실행 기록이 아니다.

```text
retain policy: 4 candidates with violations reported
drop policy: 2 valid candidates; 2 dropped rows recorded
fail policy: no approved new publication
retry after correction: business total unchanged by duplicate delivery
cleanup: no lab compute or schedule remains active
```

무효 행은 NULL 키와 알 수 없는 통화를 가진다. 이전 출력 가시성은 공개 계약에 달려 있다. 실제 갱신 ID, 계보 공백, 접근 시험, 청구 근거를 기록해야 클라우드 실습 완료다.

## 스스로 설명해 보기

어떤 책임이 공급자에게 가고 무엇이 팀에 남는가? 플랫폼 감시, 업무 품질, 접근 강제, 복원에 각각 다른 근거가 필요한 이유를 설명한다. 첫 플랫폼의 실패 동작을 시연하기 전에는 Snowflake 전문화를 미룬다.

다음은 [AI용 데이터와 평가](../../../docs/guides/data-observability/13-ai-ready-data-evaluation.md)로 이어간다.

<!-- source: https://docs.databricks.com/aws/en/ldp/expectations | checked: 2026-09-10 | retain/drop/fail policies and limitations -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage | checked: 2026-09-10 | lineage coverage and access -->
<!-- source: https://docs.snowflake.com/en/user-guide/data-quality-intro | checked: 2026-09-10 | DMFs, expectations, Enterprise requirement -->
<!-- source: https://docs.snowflake.com/en/user-guide/dynamic-tables/overview | checked: 2026-09-10 | maintained query results and target lag -->
<!-- source: https://docs.databricks.com/aws/en/ldp/developer/python-dev | checked: 2026-09-10 | pyspark.pipelines and materialized view development -->
<!-- source: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/ | checked: 2026-09-10 | incremental file ingestion -->
<!-- source: https://docs.databricks.com/aws/en/jobs/repair-job-failures | checked: 2026-09-10 | job repair and retry scope -->
<!-- source: https://docs.snowflake.com/en/user-guide/streams-intro | checked: 2026-09-10 | offsets, change images and consumption -->
<!-- source: https://docs.snowflake.com/en/user-guide/tasks-intro | checked: 2026-09-10 | task execution responsibilities -->
<!-- source: https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes | checked: 2026-09-10 | incremental/full refresh -->
<!-- source: https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions | checked: 2026-09-10 | managed micro-partitions and pruning -->
<!-- source: https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes | checked: 2026-09-10 | lazy expressions and result materialization -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/ | checked: 2026-09-10 | registered objects and permissions -->
