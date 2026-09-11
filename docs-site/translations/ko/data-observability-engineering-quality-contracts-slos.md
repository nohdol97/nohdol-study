# 데이터 품질·계약·결과 중심 SLO

플랫폼 담당자가 좋은 데이터의 의미를 혼자 정할 수는 없다. 도메인 담당자가 업무 의미와 허용 결함을 정의하고 플랫폼 엔지니어는 이를 측정·강제 가능하게 만든다. 사용자도 기한과 대체 동작을 정하는 데 참여한다.

## 이 장에서 처음 쓰는 말

| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| 유효성(validity) | 값이 선언한 타입·범위·형식 규칙을 만족하는지 | 데이터 공개 전에 허용한 스키마·값의 영역을 위반하는 값을 거부한다. |
| 완전성(completeness) | 기대한 레코드·필드가 존재하는지 | 도착한 행만 검사해서는 찾을 수 없는 예상 입력의 누락을 발견한다. |
| 정확성(accuracy) | 현실의 사실이나 권위 있는 기준과 일치하는지 | 형식상 유효한 데이터도 틀릴 수 있으므로 신뢰할 기준과 실제 내용을 비교한다. |
| 신선도(freshness) | 지정한 시계·전달 모델에서 데이터가 얼마나 최신인지 | 데이터셋에 정한 시계·소비자 기대를 기준으로 오래된 전달 상태를 찾는다. |
| 계약(contract) | 의미·소유권·구조·서비스 기대를 담은 버전 있는 합의 | 생산자·소비자가 의미·변경·서비스 책임에 관해 검토할 수 있는 합의를 갖게 한다. |
| 오류 예산(error budget) | SLO가 정한 기간 안에서 허용하는 실패량 | 남은 실패 허용량을 기준으로 신뢰성 개선과 릴리스 판단의 우선순위를 정한다. |

## 먼저 이해하기

1. 사용자 결과와 평가 대상 모집단을 정의한다.
2. 명시적 규칙으로 레코드나 전달 구간을 측정한다.
3. 측정 시각, 입력 버전, 검사 구현을 기록한다.
4. 공개·격리·실패·표시된 이전 버전 제공 중 정책을 결정한다.
5. 담당자에게 알리고 수정 후 사용자 복구를 검증한다.

유일성·NOT NULL 검사는 유용하지만 완전성을 입증하지 못한다. 완벽하게 유효한 열 행도 기대보다 9천 행 부족할 수 있다. 독립 예상 장부, 상위 제어 합계, 추정임을 명확히 밝힌 값과 비교한다. 정확성에도 기준이나 도메인 검토가 필요하다. 정규식은 그럴듯한 주소가 실제로 맞는지 입증할 수 없다.

## 계약 예시

이 YAML은 설계 산출물이며 dbt·Soda·Great Expectations가 받아들이는 설정이 아니다. 각 규칙을 선택한 구현의 실행 가능한 검사로 대응시킨다.

```yaml
dataset: orders.accepted
contract_version: "1.0"
owner: commerce-data
grain: one_current_record_per_event_id
time_basis: UTC
key: event_id
amount_unit: cents
required_fields: [event_id, event_time, amount_cents, currency]
delivery:
  interval_minutes: 5
  deadline_after_interval_end_minutes: 10
  eligible_intervals: all_scheduled_intervals
  missing_measurement: unknown_and_alert
quality:
  duplicate_ids: 0
  unknown_currency_rows: 0
  reconcile_to: source_control_totals
publication:
  on_failure: hold_candidate_and_label_last_good
```

단위, 시계, 기대 구간, 측정 누락, 공개 동작도 합의에 포함된다. 스키마만 있는 계약은 사고 중 운영자에게 필요한 대부분을 빠뜨린다.

## 공백을 숨기지 않는 신선도 정의

`now - max(event_time)`은 가장 최근 관측 이벤트의 나이를 측정한다. 지역·파티션이 빠져도 새 이벤트 하나가 정상처럼 보이게 할 수 있다. 조용한 소스는 올바르게 작동해도 오래돼 보일 수 있고 시계 오차로 음수가 될 수도 있다.

예약 데이터셋은 기대 구간과 공개 기한을 기준으로 신선도를 정의한다. 연속 스트림은 이벤트→공개 지연, 기대 소스 진척·heartbeat, 관련 구간별 완전성을 결합한다. 이벤트·수집·공개 시간은 서로 다른 질문에 답하므로 따로 기록한다.

| 측정 | 분모와 경계 사례 |
|---|---|
| 중복 비율 | 유효 고유 식별자를 초과한 행 / 대상 수신 행. 입력 0일 때 동작 정의 |
| 완전성 | 승인된 기대 식별자 / 독립적으로 기대한 식별자. 기준 없으면 알 수 없음 |
| 정시 공개 | 기한 전 공개된 유효 구간 / 실행 누락까지 포함한 모든 대상 구간 |
| 검사 범위 | 새 결과를 낸 기대 검사 / 전체 기대 검사 |

## SLO 계산 예제

30일에 대상 5분 구간이 정확히 8,640개 있다고 하자. 정시·유효 공개 SLO가 99.9%이고 관측 성공률이 목표 이상이어야 한다면 실패 구간은 최대 8개다. 9개면 99.9% 미만이다. 수학 예제이며 보편적 업무 목표가 아니다.

스케줄러가 실행을 시작하지 않았어도 그 구간은 분모에 남는다. 품질 검사기가 멈추면 미정과 통과를 구분한다. 사용자 요구에 따라 공개를 차단하거나 명확히 표시한 이전 버전을 제공한다.

정시 전달 오류 예산이 잘못된 금액 합계나 접근 정책 위반을 허용하지는 않는다. 일부 불변식은 위반 허용 0과 별도 대응이 필요하다.

## 품질 도구와 공개

SQL 단언문·dbt 데이터 테스트로 시작한다. 재사용 검사 정의, 커넥터, 보고가 데이터셋 전반의 일을 줄이면 Great Expectations·Soda를 평가한다. 검사 엔진이 업무 담당자를 정하거나 공개 트랜잭션을 자동 생성하지는 않는다.

노출 전에 후보 버전을 검사한다. 실패 레코드 샘플은 통제된 정책으로 보관하고 전체 실패 건수를 기록하며 마지막 유효 버전을 사용자에게 알린다. 나쁜 행을 버리는 정책은 완전성을 바꾸므로 집계에 드러나야 한다.

## 여섯 품질 차원에는 서로 다른 근거가 필요하다

유효성은 지원 통화·음수가 아닌 정수 금액처럼 선언한 값 영역을 만족하는지 묻는다. 유일성은 식별자 반복 여부이며 중복 비율이 추가 복사본만 세는지 중복 집단의 모든 행을 세는지 정한다. 완전성은 기대 데이터 중 누락을 묻기 때문에 소스 장부·제어 합계·한계를 명시한 기대치에서 분모를 가져온다. 정확성은 권위 있는 사실과 일치하는지이며 유효해도 실패할 수 있다.

일관성은 승인 주문 항목의 합과 주문 헤더, 두 마트의 통화·단위처럼 같아야 할 표현을 비교한다. 신선도는 선언한 이벤트·진척·공개 시계를 기한과 비교한다. 이 차원들은 서로 어긋날 수 있다. 새 120센트 값은 100센트 소스에 비해 부정확하고, 오래된 100센트 값은 정확하지만 현재 상태 사용자에게 낡은 값일 수 있다.

다음은 공급업체 품질 API가 아니라 로컬 실행 가능한 지표 계산이다. 소스 정답 기준을 명시하며 승인 후보는 무효 레코드를 제외하고 후보 중복 제거 전에 중복 전달을 센다. 식별자별 값 충돌은 단순화한 예제를 쓰기 전에 종합 프로젝트의 충돌 관문으로 처리해야 한다.

<!-- executable: quality-dimensions -->
```python
expected = {'e1': 100, 'e2': 250, 'e3': 50}
deliveries = [('e1',100), ('e1',100), ('e2',270), ('bad',-1)]
valid = [(key,amount) for key,amount in deliveries
         if key in expected and type(amount) is int and amount >= 0]
candidate = dict(valid)  # Only identical duplicates exist in this fixture.
extra = len(valid) - len(candidate)
complete = len(set(candidate) & set(expected)) / len(expected)
accurate = sum(candidate[k] == expected[k] for k in candidate) / len(candidate)
assert (len(valid), extra, len(candidate)) == (3,1,2)
assert sum(candidate.values()) == 370
print(f'validity={len(valid)}/{len(deliveries)}')
print(f'extra_duplicate_fraction={extra}/{len(valid)}')
print(f'completeness={complete:.3f} accuracy_on_present={accurate:.3f}')
print(f'candidate_total={sum(candidate.values())} source_total={sum(expected.values())}')
print('publication=HOLD: missing e3 and incorrect e2')
```

예상 출력:

```text
validity=3/4
extra_duplicate_fraction=1/3
completeness=0.667 accuracy_on_present=0.500
candidate_total=370 source_total=400
publication=HOLD: missing e3 and incorrect e2
```

합계만 비교해서는 부족하다. e2를 300으로 바꾸면 합이 400이 되어도 e3는 없고 e2는 틀리다. 도메인이 요구하면 식별자별 대사를 유지한다. 빈 모집단은 0으로 나누거나 정확도 100%를 선언하지 말고 관측 없음으로 보고한다.

## 검사를 공개 상태 머신으로 만들기

`BUILDING -> CHECKING -> APPROVED -> PUBLISHED` 같은 상태를 사용하고 실패하면 후보를 보류한다. 각 결과를 후보 버전, 규칙 리비전, 측정 모집단, 완료 시각에 묶는다. A의 검사 통과가 1분 후 작성한 B를 승인해서는 안 된다. 모든 필수 검사 뒤 지원되는 원자적 포인터·교환·트랜잭션으로 공개하고 커밋 출력 식별자를 기록한다.

경고·격리·삭제·실패는 다른 정책이다. 경고는 결함을 표시하며 공개를 허용한다. 격리는 수정을 위해 거부 레코드를 남기며 대사가 필요하다. 삭제는 전달 모집단을 바꾸므로 버린 건수를 완전성에 포함한다. 실패는 갱신을 막지만 이전 버전의 가용성과 오래된 데이터 표시는 별도 제공 설계가 필요하다.

스키마 변경은 호환 필드 추가, 채우기, 이전·새 사용자 예제 실행, 사용자 이동, 이전 표현 제거 순으로 진행한다. 총매출→순매출 같은 의미 변경은 SQL 열 이름·타입이 같아도 정의 버전을 바꾼다. 플랫폼팀에 모든 업무 결정을 맡기지 말고 규칙 승인자와 실패 시 호출 대상을 명시한다.

## 같은 워크플로에서 dbt·Great Expectations·Soda 비교

dbt 데이터 테스트는 SQL 변환 그래프로 이미 만든 관계에 맞는다. Great Expectations는 expectations를 suite·검증 절차로 구성하고 Soda는 지원 검사 언어와 scan·runtime으로 표현한다. 실행 엔진, 배포 방식, 실패 행 처리, 결과 저장이 공개 경계에 맞는지 비교한다. 커넥터 목록만으로 작성자가 공개할 것과 같은 트랜잭션 스냅샷을 검사할 수 있음이 입증되지는 않는다.

도메인 규칙의 의미는 도구와 독립적으로 유지하되 정확히 지원되는 설정으로 옮긴다. 앞의 계약 예시는 SodaCL이나 GX suite가 아니다. 이벤트 ID에 NULL이 없어야 한다는 조건은 쉽게 대응되지만 기대한 고객 파티션이 기한 전에 모두 도착했는지는 스캔 외에 스케줄·기준 모집단도 필요하다. 라이브러리 선택 전에 누가 그 모집단을 보관할지 정한다.

## SLO 측정·소진율·데이터량 이상

허용 실패율 0.001, 관측 실패율 0.02라면 소진율은 `0.02 / 0.001 = 20`이다. 비교 가능한 일정 이벤트율에서 목표의 20배 속도로 한 시간 실패하면 목표 속도의 20시간분 허용량을 소모한다. 유입 급증이나 구간 기반 SLO는 실제 대상 모집단이 필요하며 시간 길이만으로 대체할 수 없다.

데이터량 이상 탐지는 엄격한 대사 전에도 비정상 감소를 잡을 수 있지만 계절성·휴일·알려진 소스 중지가 기준선에 영향을 준다. 같은 종류의 구간·세그먼트를 비교하고 과거 기준을 기록하며 이상과 입증된 누락 건수를 구분한다. 이상 임계값이 금액·접근의 무관용 불변식을 조용히 면제해서는 안 된다.

검사기도 측정한다. 독립 스케줄이 있어야 할 검사 결과를 알고 범위 규칙이 누락·오래된 결과를 탐지한다. 수정 후에도 SLO 이력을 보존한다. 어제 구간을 백필하면 오늘 완전성은 회복되지만 어제 놓친 기한이 정시로 바뀌지는 않는다.

## 실패 실습과 해석

예약 구간 누락 하나, 중복 ID 하나, 검사 결과 부재 하나를 만든다. 시스템은 서로 다른 세 문제를 식별해야 한다. 중복 수정, 구간 재생, 검사기 재시작 후 데이터와 관측 범위를 검증한다. 복구 후 현재 녹색 상태로 과거 실패를 덮지 말고 실패 장부를 유지한다.

## 실행 결과 예시

예약 구간 열 개의 계산 워크시트다.

```text
scheduled intervals: 10
on-time and valid: 8
late: 1
never ran: 1
good / eligible: 8 / 10 = 80%
incorrect denominator using completed runs only: 8 / 9
missing checker result: UNKNOWN, not PASS
```

복구로 현재 데이터를 쓸 수 있게 되어도 기한 실패 이력은 남는다. 중복 키 실패, 구간 누락, 검사 근거 부재를 구분하며 시작되지 않은 구간도 센다.

## 스스로 설명해 보기

신선도가 좋아지면서 완전성은 나빠질 수 있는 이유는 무엇인가? 대시보드의 모든 백분율에 대해 분모와 기준의 권위를 설명한다. 도메인 승인이 필요한 규칙과 기계적인 타입 검사를 구분한다.

다음은 [OpenTelemetry](../../../docs/guides/data-observability/09-opentelemetry.md)로 이어간다.

<!-- source: https://docs.getdbt.com/docs/build/data-tests | checked: 2026-09-10 | executable data assertions; contracts and SLO arithmetic are teaching synthesis -->
<!-- source: https://sre.google/workbook/implementing-slos/ | checked: 2026-09-10 | outcome-oriented SLIs and SLOs -->
<!-- source: https://docs.greatexpectations.io/docs/core/introduction/ | checked: 2026-09-10 | GX expectations and validation workflow -->
<!-- source: https://docs.soda.io/soda-cl/soda-cl-overview.html | checked: 2026-09-10 | Soda check-language scope -->
