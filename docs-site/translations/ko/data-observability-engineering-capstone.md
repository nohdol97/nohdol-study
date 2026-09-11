# 종합 프로젝트: 함께 발전하는 데이터·관측성 플랫폼

가상 주문으로 매출 보고서를 만들고, 공개된 결과에 답하는 AI 도우미를 붙인다. 프로젝트 내내 같은 시스템을 발전시킨다.

합의한 데이터 규칙을 유지하면서 분산 처리, 접근 제어, AI를 추가한다. 단계마다 다른 엔지니어가 다시 실행할 수 있는 검사와 결과를 남긴다.

## 실습 사전 조건과 범위

첫 실습은 Python 3만 필요하며 파일·네트워크를 쓰지 않는다. 이후에는 선택하고 버전을 고정한 로컬 서비스와 선택적인 관리형 계정이 필요하다. 전 과정에 가상 데이터를 쓰고 클라우드 실험에는 예산·임시 네임스페이스·정리 목록을 둔다.

아래는 학습 과제다. 문서 배포가 Kafka·Spark·Databricks·Snowflake·실시간 AI 서비스를 대신 배포하지 않는다. 완료하면서 직접 실행한 명령·버전·측정·공백을 기록한다.

## 먼저 이해하기

| 개체 | 식별자와 약속 |
|---|---|
| 이벤트 | 안정된 이벤트 ID·버전·이벤트 시간·금액 단위·통화·소스 위치 |
| 처리 실행 | 코드·계약 리비전, 소스 범위, 런타임·입력 버전 |
| 공개 | 데이터셋 버전, 대상 구간, 검사 결과, 공개 시각 |
| 검색 인덱스 | 소스 데이터셋·문서 버전, 청크·임베딩 리비전, 정책 버전 |
| 답변 | 요청 ID, 허용 근거 참조, 프롬프트·모델 리비전, 평가 결과 |

단계 전체에 같은 식별 관례를 쓴다. trace·계보 이벤트·공개 기록은 실행 ID로 연결하되 각자 책임은 보존한다.

## 1단계: 지금 실행할 수 있는 정확성 기준

임시 디렉터리에 `oracle.py`로 저장하고 `python3 oracle.py`를 실행한다. 작은 메모리 내 예제로, 유효 ID와 음수가 아닌 정수 센트의 USD 주문만 대상이다. 동일 재시도는 제거하고 충돌 페이로드는 따로 드러낸다. 예제 정답 기준이며 스트리밍 엔진이 아니다.

```python
def reconcile(events):
    accepted = {}
    rejected = []
    conflicts = []
    for event in events:
        if not isinstance(event, dict):
            rejected.append(event)
            continue
        event_id = event.get("event_id")
        amount = event.get("amount_cents")
        if (not isinstance(event_id, str) or not event_id
                or type(amount) is not int or amount < 0
                or event.get("currency") != "USD"):
            rejected.append(event)
            continue
        if event_id in accepted and accepted[event_id] != event:
            conflicts.append(event_id)
            continue
        accepted[event_id] = event.copy()
    return accepted, rejected, conflicts

def publish(events, expected_ids):
    accepted, rejected, conflicts = reconcile(events)
    if rejected or conflicts or set(accepted) != set(expected_ids):
        raise ValueError("publication blocked: invalid, conflicting, or incomplete input")
    return {key: accepted[key] for key in sorted(accepted)}

base = [
    {"event_id": "e1", "amount_cents": 100, "currency": "USD"},
    {"event_id": "e2", "amount_cents": 250, "currency": "USD"},
]
valid, rejected, conflicts = reconcile(base + base)
assert len(valid) == 2
assert sum(row["amount_cents"] for row in valid.values()) == 350
assert not rejected and not conflicts

bad = {"event_id": "e3", "amount_cents": -10, "currency": "USD"}
assert len(reconcile(base + [bad])[1]) == 1
changed = {"event_id": "e1", "amount_cents": 120, "currency": "USD"}
assert reconcile(base + [changed])[2] == ["e1"]
assert set(reconcile(base[:1])[0]) != {"e1", "e2"}  # Missing input detected.
assert reconcile(list(reversed(base)))[0] == reconcile(base)[0]
snapshot = publish(base + base, {"e1", "e2"})
for candidate in (base + [bad], base + [changed], [changed] + base,
                  base[:1], base + [None],
                  base + [{"event_id": "e3", "amount_cents": True, "currency": "USD"}]):
    try:
        publish(candidate, {"e1", "e2"})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid publication was accepted")
assert snapshot == publish(base, {"e1", "e2"})
print("PASS: replay, totals, invalid values, conflicts, missing input, ordering")
```

`publish`는 교체 스냅샷 반환 전에 거부·충돌·불완전 입력을 차단한다. 실패 시 이전 스냅샷은 그대로다. `reconcile`이 첫 승인 페이로드를 남기는 것은 진단용이며 테스트는 충돌의 두 도착 순서를 모두 거부한다. 분산 출력에 갱신 처리를 넣기 전에 버전 순서·수정 의미를 정의한다. 메모리 관문은 영속·동시 공개를 구현하지 않는다.

## 2단계: 파일과 커밋 테이블

승인한 이벤트를 Parquet에 쓰고 건수·합계를 확인하며 열 선택·필터 쿼리를 비교한다. 파일 누락을 넣어 완전성 실패를 요구한다. Iceberg 또는 Delta를 추가해 append 전후 버전을 기록하고 지원 스냅샷 조회·복원을 시연한다.

산출물은 데이터 생성기, 스키마, 예상 장부, 배치 측정, 테이블 이력, 복구 절차다. 물리 배치의 근거와 업무 합계의 근거를 구분한다.

## 3단계: Kafka와 Spark

같은 예제를 Kafka→Spark→테이블 출력으로 보낸다. 오프셋·이벤트 ID를 보존하고 동일 재시도, 충돌 버전, 순서 뒤바뀜, 늦은 레코드, 소비자 재시작을 넣는다. 기준 계약 범위에서 분산 결과를 정답과 비교하고 이벤트 시간·갱신 의미는 양쪽을 의도적으로 확장한다.

커넥터·런타임 매니페스트, 체크포인트·출력 커밋 전략, Spark 계획·태스크 근거, 재생 기록을 제출한다. 출력 공개 뒤 중단을 시연하고 업무 결과가 두 번 세어지지 않는지 확인한다.

## 4단계: 거버넌스가 있는 데이터 제품

dbt staging·일일 매출 마트를 만들고 명시 구간을 예약하며 스키마·키·단위·완전성·기한 검사로 공개를 제어한다. 담당자·계약 메타데이터를 추가하고 실제 실행 계보를 내어 소스 위치를 테이블 버전·마트 출력과 연결한다.

통과·실패 예제, 증분·전체 비교, 제한 백필, 허용·거부 시험, 영향 쿼리를 제출한다. 누락 계보는 빈 영향 범위가 아니라 공백으로 보여야 한다.

## 5단계: 운영 근거

OTel로 처리·공개를 계측한다. Prometheus 지표와 Grafana 사용자 결과 화면을 더하고 실행 참조로 로그·트레이스를 연결한다. 라벨 예산, 보존, 관측 범위 검사를 기록한다.

느린 stage 사고, HTTP는 정상인데 데이터가 오래된 사고, 독립적인 텔레메트리 장애를 제출한다. 복구를 시연하고 데이터 유실·신호 유실을 따로 대사한다.

## 6단계: 관리형 구현과 AI

정한 계약을 Databricks에서 다시 구현하고 예제 ID·예상 출력을 보존한다. 이후 같은 워크로드로 Snowflake를 비교한다. 작은 가상 검색 자료와 제한된 AI 도우미를 추가하고 소스·인덱스·모델·프롬프트 리비전을 기록한다.

계정별 기능 기록, 품질·계보·접근·복구 검사, 정리 근거, 비용 내역, 누락·과거·금지·충돌 근거를 포함한 평가 세트를 제출한다. 환경·예산이 있을 때까지 클라우드·AI 호출은 선택이며 로컬 정확성 단계만으로도 유용하다.

## 최종 실패 행렬

| 결함 | 복구 완료 전에 필요한 근거 |
|---|---|
| 중복 이벤트 | 재생 뒤 같은 의도한 고유 키·합계 |
| 충돌 갱신 | 조용한 선착순 정책 없이 격리 또는 선언한 버전 결정 |
| 늦은 이벤트 | 수락·수정·거부 건수와 하위 대사 |
| 스키마·단위 변경 | 사용자 호환성 결과와 버전 있는 전환 |
| 소비자·실행기 중단 | 진척 재개와 올바른 공개 출력 |
| 체크포인트·메타데이터 유실 | 시간 측정·공백 명시를 포함한 격리 복원·재생 |
| 예약 실행 누락 | SLO 분모 포함과 제한 백필 복구 |
| Collector·백엔드 장애 | 알려진 신호 적체·유실과 관측 범위 알림 |
| 계보 이벤트 누락 | 수집 공백 명시와 영향 사용자 조사 검증 |
| 소스 접근 폐기 | 금지 검색·프롬프트·답·디버그 노출 없음 |
| 잘못된 AI 답 | 근거 기반 진단과 보존한 회귀 평가 |

## 실행 결과 예시

독립 Python 예제의 출력이다.

```text
PASS: replay, totals, invalid values, conflicts, missing input, ordering
```

승인 스냅샷에는 고유 이벤트 두 개, 합계 350센트가 있다. 충돌의 두 도착 순서, 입력 누락, 음수·불리언 금액, 비레코드 입력은 교체 공개 전에 거부된다. 회귀가 나면 단언이 중단한다. 이후 단계에는 별도 서비스 기록이 필요하다. 이 로컬 기준은 Kafka·클라우드 복구·신호 전달·AI 평가를 실행하지 않는다.

## 스스로 설명해 보기

15분 아키텍처 검토와 15분 사고 재생을 발표한다. 성공 주장마다 예제·측정·소스 버전·정책 검사를 제시하고 실행하지 않은 것을 밝힌다. 다른 엔지니어가 작은 테스트를 재현하고 큰 규모 주장에 별도 근거가 필요한 이유를 이해할 수 있어야 한다.

## 세부 실습을 종합 프로젝트로 연결하기

서비스 연동 전에 장별 예제를 구성 요소 정답 기준으로 쓴다. 저장소 체크아웃에서 `python3 docs-site/labs/verify_data_course.py`를 실행하면 표시된 표준 라이브러리 예제 일곱 개의 출력과 Markdown을 비교한다. 윈도·재귀, 타입 거부, 과거 귀속, 품질 차원, 히스토그램 보간, 계보 탐색, 하이브리드 순위를 다룬다.

OTel SDK 1.44.0, DuckDB 1.5.0, dbt-duckdb 1.11.0, dbt-core 1.12.4가 이미 있는 임시 Python 환경에서는 `python docs-site/labs/verify_data_course.py --optional`을 실행한다. 새 로컬 dbt 프로젝트에서 문서의 증분 모델·매크로·검사를 그대로 실행해 수정·재시도·전체 재계산을 비교하고 삭제 한계를 재현한다. 설치·클라우드 자격 증명 사용은 없으며 검토할 임시 기록 경로를 출력한다.

| 가져올 예제 | 연동 근거 |
|---|---|
| 윈도·SCD 경계 | 분산 조인이 키·과거 귀속·합계를 보존 |
| 정렬·교차 Parquet 결과 | 파일 재작성이 행은 보존하고 측정 스캔·계획 작업은 변경 |
| Iceberg·Delta 버전 조사 | 성공 공개마다 읽을 수 있는 스냅샷·보존 경계 지정 |
| Spark 계획 비교 | 조인·AQE 변경이 결과를 보존하고 자원 변화가 측정으로 설명됨 |
| Kafka 중단·재균형 | 완료 작업까지만 진척하고 재시도가 업무 효과 보존 |
| dbt 갱신·삭제 | 지원 변경 유형 모두에서 증분과 전체 재구성 일치 |
| 품질 모집단 | 소스 ID 누락·검사 부재가 설계대로 승인 차단 |
| OTel 전파 | 전송 헤더가 관계를 보존하고 신호 유실은 별도 집계 |
| 히스토그램·알림 계산 | 백엔드 결과가 예제 모집단·관측 범위 정책과 일치 |
| 계보·접근 | 알려진 후손을 찾고 실제 신원으로 금지 읽기 실패 |
| 클라우드 구현 | 로컬·관리형 출력, 정책, 복구, 비용 비교 |
| 검색·평가 | 허용 근거가 순위·프롬프트·답·트레이스까지 버전 유지 |

로컬 구성 요소 예제 통과는 연동 시험의 진입 조건이다. SDK 예제는 전송 없는 전파를 입증하므로 Kafka 연동에서는 프로세스 간 전달 매체 직렬화·추출을 추가 검증해야 한다. 포트폴리오에서 구분해 다른 엔지니어가 수집한 근거를 정확히 재현하게 한다.

## 포트폴리오 점검

아키텍처 결정, 버전 잠금, 가상 예제, 정확성 테스트, 계획, 사고 시간선, 복원 기록, 비용 계산, 정리 단계를 한 프로젝트에 둔다. 측정 실패를 이상적인 그림으로 대체하지 않는다. 다음 실패가 공백을 드러내면 과정을 다시 본다.

[로드맵](../../../docs/guides/data-observability/00-roadmap.md)으로 돌아가거나 [출처 검토](../../../docs/guides/data-observability/16-source-review.md)를 읽는다.

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | one evolving project is curriculum input; fixture and graduation criteria are original synthesis -->
