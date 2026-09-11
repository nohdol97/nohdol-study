# Prometheus·Grafana·Loki·Tempo: 근거 파이프라인 운영하기

대시보드는 질문에 답하고 결정으로 이어져야 한다. 지금 사용자가 이 데이터셋을 쓸 수 있는가에서 시작해 처리·저장·텔레메트리 의존성을 조사한다.

## 이 장에서 처음 쓰는 말

| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| 카운터(counter) | 생산자 재시작 시 초기화될 수 있는 누적 건수 | 누적 사건 수를 기록하고 재시작에 따른 초기화를 고려해 선택한 구간의 발생률을 구한다. **구체적인 상황(가상 예시):** API 팀이 재시작을 포함한 초당 요청 수를 보고 싶다. → 누적 요청 카운터를 기록하고 적절한 변화율을 조회한다. → 누적값을 단순 차감하지 말고 초기화 처리를 시험한다. |
| 게이지(gauge) | 증가·감소할 수 있는 현재 값 | 오르내릴 수 있는 대기열 길이·진행 작업 수 같은 현재 수준을 관찰한다. **구체적인 상황(가상 예시):** 운영자가 증가와 감소를 반복하는 현재 큐 길이를 알아야 한다. → 현재값을 게이지로 기록한다. → 알고 있는 큐 변화가 측정값에 반영되는지 비교한다. |
| 히스토그램(histogram) | 관측값 분포의 표현 | 평균만으로 가려지는 값의 분포와 임계값 이하·이상의 비율을 살핀다. **구체적인 상황(가상 예시):** 여러 인스턴스를 합쳐 지연 목표 달성을 평가해야 한다. → 적절한 버킷 또는 지원되는 네이티브 히스토그램으로 분포를 기록한다. → 집계와 임계값 해상도가 목표에 맞는지 확인한다. |
| 서머리(summary) | 설정 시 클라이언트가 분위수를 계산하는 관측 형식 | 집계 제약이 질문에 맞는 경우 생성 주체별로 설정한 분위수를 얻는다. **구체적인 상황(가상 예시):** 라이브러리가 클라이언트에서 계산한 지연 분위수를 노출한다. → 요약 지표의 분위수가 계산된 범위를 확인한다. → 인스턴스 분위수를 평균내지 말고 전체 집계 방법을 별도로 검증한다. |
| 라벨 카디널리티 | 시계열을 만드는 서로 다른 라벨 조합의 수 | 감시 비용·안정성에 영향을 주는 라벨을 추가하기 전에 시계열 증가량을 예상한다. **구체적인 상황(가상 예시):** 지표에 사용자 ID 라벨을 붙이자 저장량이 급증한다. → 라벨 조합 수를 계산하고 무한히 늘어나는 차원을 바꾼다. → 활성 시계열 수를 비교하고 필요한 상세 정보는 적절한 신호에 남긴다. |
| 소진율(burn rate) | 관측 실패 비율을 SLO 허용 실패 비율로 나눈 값 | 현재 실패의 강도가 SLO의 오류 허용량을 얼마나 빠르게 소모하는지 연결한다. **구체적인 상황(가상 예시):** 짧은 장애가 월간 신뢰성 허용량을 빠르게 소모한다. → 적절한 시간 창으로 오류 예산 소진 속도를 계산한다. → 경보가 긴급한 지속 소모와 단순 잡음을 구분하는지 확인한다. |

## 먼저 이해하기

1. 의미·단위가 안정적이고 라벨 범위가 제한된 지표를 낸다.
2. Prometheus나 호환 백엔드에 저장하고 질의한다.
3. 로그는 Loki, 트레이스는 Tempo에 저장하거나 Jaeger를 대안으로 평가한다.
4. Grafana로 백엔드를 탐색하고 집계 증상을 실행에 연결한다.
5. 담당자·영향·진단 링크를 갖춘 조치 가능한 알림을 전달한다.

이 설계에서 Grafana는 탐색 계층이다. Prometheus·Loki·Tempo는 저장·질의 모델이 다르다. 같은 대시보드가 모든 신호의 보존·가용성·접근 정책이 같다는 뜻은 아니다.

## 의미가 명확한 PromQL

다음 쿼리는 Kafka·Spark·OTel 내장 이름이 아니라 **이 과정에서 정의한 사용자 애플리케이션 지표**를 가정한다. 앱은 대상 구간당 공개 결과 하나와 값의 범위를 제한한 `dataset`·`outcome` 라벨을 낸다. 시작되지 않은 구간은 별도 스케줄 장부가 찾는다.

```promql
# Publication attempts per second; apply rate before aggregating resets.
sum by (dataset) (rate(data_publications_total[5m]))

# Known failed attempts / all observed attempts over an hour.
sum by (dataset) (increase(data_publications_total{outcome="failed"}[1h]))
/
sum by (dataset) (increase(data_publications_total[1h]))

# p95 delay across classic histogram buckets; retain the le label.
histogram_quantile(
  0.95,
  sum by (dataset, le) (rate(data_publication_delay_seconds_bucket[5m]))
)
```

다른 구성 요소가 기록하지 않으면 실패 비율에 예약 실행 누락은 포함되지 않는다. 없는 시계열은 자동으로 0이 아니며 분모 0은 선언 정책에 따라 관측 부족이어야 한다. 필요하면 알려진 제한된 결과 시계열을 초기화하고 별도 누락 검사를 구현한다. 무조건 `or vector(0)`을 붙여 모든 부재를 숨기지 않는다.

고전 히스토그램은 버킷 경계가 분위수 해상도를 정한다. 600이 실제 경계라면 600초 안에 끝난 비율은 p95 추정보다 임계값 건수로 직접 답할 수 있다. 클라이언트 계산 summary 분위수는 일반적으로 평균내어 전체 분위수로 만들 수 없다. 네이티브 히스토그램은 표현이 다르므로 계약 변경 전에 SDK·수집·저장·질의 지원을 확인한다.

## 사고 전에 카디널리티 제한하기

예시 지표에 데이터셋 50, 결과 4, 환경 3, 인스턴스 20이 있으면 히스토그램 구성 전에도 라벨 조합이 12,000개다. 이벤트별 ID를 추가하면 이벤트 모집단만큼 곱해진다. 그 식별자는 로그·트레이스·기록 저장소에 둔다.

허용값과 교체 빈도를 함께 검토한다. 동시 수가 작아도 새 Pod·실행 ID가 과거 시계열 집합을 계속 늘릴 수 있다. 텔레메트리 양 예산과 보존 비용을 추정하고 대표 라벨로 백엔드 부하 시험을 한다.

## 네 가지 진단 화면 만들기

| 화면 | 질문 |
|---|---|
| 사용자 결과 | 어떤 데이터셋이 유효성·공개 기한을 놓쳤는가? 관측 범위는 완전한가? |
| 파이프라인 | 유입률·지연·처리 시간·출력 커밋이 어디에서 어긋나는가? |
| 실행 | 어떤 Spark stage·Kafka 파티션·호스트·쿼리가 지연을 설명하는가? |
| 텔레메트리 상태 | 수집·Collector·큐·적재·질의가 실패하는가? |

유용한 로그에는 시각, 심각도, 작업, 실행 ID, 사유 코드, 관련 버전 참조가 있다. 기본 로그에서 민감 페이로드를 제외한다. Loki에는 범위가 제한된 서비스·환경 라벨을 둔다. 모든 이벤트 ID를 인덱스 라벨로 넣으면 역할에 맞지 않는 인덱스가 된다. 추출 trace ID로 로그와 트레이스를 연결하고 선택한 대시보드 설정에서 링크를 검증한다.

## 결과에 알리고 원인은 추가 근거로 확인하기

99.9% SLO 예시에서 실패율 1%는 허용 속도의 10배로 예산을 소진한다. 여러 구간으로 지속적인 큰 사고와 일시적 표본을 구분하고 양·관측 누락 검사도 포함한다. 정확한 임계값은 트래픽·대응 시간 가정이 필요한 설계 선택이다.

Prometheus Alertmanager는 라우팅·그룹화·억제·무음을 추가한다. 무음에는 담당자와 만료가 필요하며 과거 SLO 성적은 바뀌지 않는다. 조치 범위로 알림을 묶어 상위 사고 하나가 모든 하위 담당자를 자동으로 각각 호출하지 않게 한다.

## 한 파이프라인의 counter·gauge·histogram·summary

완료된 공개 시도는 관측마다 이벤트를 더하므로 counter, 현재 적체는 오르내리므로 gauge, 공개 지연은 임계값·꼬리 분포가 중요하므로 histogram을 쓴다. 분위수를 설정한 summary는 관측 클라이언트에서 순위 추정을 계산하며 보통 이를 합쳐 올바른 전체 백분위로 만들 수 없다.

`rate(counter[5m])`는 구간 내 초기화를 고려해 초당 증가율을 추정한다. `increase(counter[1h])`는 구간 증가량을 추정하고 경계까지 외삽하므로 소수일 수 있다. 정확한 금전 장부가 아니다. 프로세스 재시작을 집계 안에 숨기지 않도록 개별 counter에 `rate`를 적용한 뒤 합한다. 적체 gauge에 `rate`를 쓰면 감소를 counter 동작으로 잘못 해석한다.

A가 초기화되고 B는 계속 증가한다면 `sum(rate(...))`는 개별 초기화 정보를 보존한다. 전체 합산 표본 둘을 빼면 A의 초기화를 음수 작업과 혼동할 수 있다. 정확한 예약 공개 건수는 장부에 두고 지표는 범위를 명시한 운영 추세에 쓴다.

## 고전 히스토그램 버킷: 백분위 직접 계산하기

고전 버킷 수는 누적이다. `le="5"`는 `le="1"`의 모든 관측을 포함한다. 호환 경계의 인스턴스들을 합칠 때 `le`를 유지한다. 다음 Python 예제는 의도적으로 불균등한 지연 분포의 누적 수와 선형 보간을 계산한다.

<!-- executable: histogram-math -->
```python
delays = [1, 2, 3, 4, 5, 10, 100, 200, 600, 900]
bounds = [5, 100, 600, 1000]
counts = [sum(value <= bound for value in delays) for bound in bounds]
rank = 0.95 * len(delays)
lower, upper = 600, 1000
before, through = counts[2], counts[3]
estimate = lower + (rank-before)/(through-before)*(upper-lower)
assert counts == [5,7,9,10]
assert estimate == 800
print('cumulative_buckets:', counts)
print('within_600_seconds: 9/10')
print('interpolated_p95_seconds:', int(estimate))
```

예상 출력:

```text
cumulative_buckets: [5, 7, 9, 10]
within_600_seconds: 9/10
interpolated_p95_seconds: 800
```

실제 마지막 관측은 900인데 버킷 기반 p95 추정은 800이다. 히스토그램은 해당 순위가 `(600,1000]` 안에 있음을 알 뿐 정확한 위치는 모른다. 계약 임계값의 비율을 직접 측정하려면 그 경계에 버킷을 둔다. 유한 경계 열 개인 고전 히스토그램은 `+Inf` 포함 버킷 11개와 count·sum, 즉 버킷 외 라벨 조합당 13개 시계열을 만들며 구현별 선택 항목은 별도다.

이 과정의 600초 임계값에는 다음을 사용한다.

```promql
sum by (dataset) (rate(data_publication_delay_seconds_bucket{le="600"}[5m]))
/
sum by (dataset) (rate(data_publication_delay_seconds_count[5m]))
```

이는 기록된 관측만 포함하며 지연값을 내지 않은 구간은 포함하지 않는다. 독립 스케줄 검사와 함께 쓴다. 네이티브 히스토그램으로 바꾸기 전에 생산자·백엔드·질의·기록 규칙 전체를 검증한다.

## 카디널리티: 곱셈과 교체

데이터셋 50 × 결과 4 × 환경 3 × 인스턴스 20 = 12,000조합이다. 고전 히스토그램 구성 시계열 13개면 예시 최대값은 156,000이다. 이벤트 ID 100만 개를 곱하면 집계 지표의 목적에 맞지 않는다. 실제 조합은 드물 수 있어도 이전 워커가 사라진 뒤에도 교체가 과거 시계열을 계속 만든다.

제한된 데이터셋 라벨은 지표에, 실행·이벤트 식별자는 로그·트레이스에 둔다. 지원된다면 exemplar로 대표 지표 관측을 트레이스에 연결한다. 이는 탐색 표본이지 버킷 안의 모든 요청이 아니다. 지원되는 곳에서 고유 URL 경로를 라우트 템플릿으로 정규화해 식별자가 우연히 라벨이 되지 않게 한다.

## Loki: 스트림을 고른 뒤 로그 줄 해석하기

Loki 라벨은 스트림을 식별한다. 제한된 서비스·환경 셀렉터로 범위를 줄이고 LogQL로 본문을 필터·파싱한다. 실행마다 인덱스 스트림을 만들지 말고 `run_id`는 구조화 본문이나 지원 구조화 메타데이터에 둔다. `reason`·`run_id`가 있는 JSON 로그에는 다음을 쓴다.

```logql
{service_name="study-pipeline", environment="study"}
  |= "QUALITY_FAILED"
  | json
  | reason="QUALITY_FAILED"
  | __error__=""
```

이 스트림 라벨은 교육용 수집 계약이며 OTel→Loki 기본값이 보장되는 것은 아니다. 줄 필터로 후보 텍스트를 줄이고 파싱으로 필드를 노출한 뒤 사유 필터로 이벤트를 선택한다. 파싱 오류는 별도 조사한다. 여기서 제외했다고 잘못된 로그 사고까지 지워서는 안 된다. 서비스 범위를 넓히기 전에 시간부터 제한한다.

## Tempo·Jaeger·Grafana 연계

Tempo는 트레이스 저장·질의를 제공하고 지원 span·trace 검색에는 TraceQL을 쓴다. Jaeger는 자체 배포·질의 동작을 가진 다른 추적 백엔드다. 지표·로그로 사고 범위를 좁힌 뒤 실행 경로를 복원한다. ID 또는 알려진 서비스·시간·작업 속성으로 찾는다. 부재는 샘플링, 전파 유실, 적재 실패, 보존 만료일 수 있다.

Grafana는 설정한 데이터 소스·링크로 조사 단계를 연결한다. 패널에는 시간 범위, 단위, 집계 범위, 관련 실행·진단 질의 경로가 필요하다. 5분 비율 패널과 일일 누적 테이블은 둘 다 맞아도 불일치처럼 보일 수 있다. 유실로 설명하기 전에 기간과 모집단을 맞춘다.

## 기록 규칙과 Alertmanager 동작

기록 규칙은 안정된 PromQL 식을 미리 계산해 저장·평가 비용과 예측 가능한 질의 비용·일관된 정의를 맞바꾼다. 분모를 바꾸면 버전도 바꾼다. 알림 규칙은 조건을 평가하며 `for`는 발동 전에 지속되어야 하는 시간이다. 수집 공백, 평가 주기, 시계열 누락이 수명 주기에 영향을 주므로 양성 사례와 함께 부재·초기화도 시험한다.

Alertmanager는 관련 알림을 묶고 수신처에 라우팅하며 억제·기한 있는 무음을 관리한다. 상위 실패가 하위 증상을 설명하면 억제로 중복 호출을 줄일 수 있지만 데이터셋을 정상으로 바꾸지는 않는다. 조치 가능한 담당자·데이터셋 범위로 묶는다. 환경으로만 묶으면 복구가 필요한 사용자를 숨길 수 있다. [SLO 실습](../../content/observability-sre/02-correlation-and-alert-lab.md)에 전체 기록·알림 규칙과 promtool 예제가 있다.

## 실패 실습과 해석

격리 실습에서 HTTP는 살려 두고 공개를 멈춘다. 서비스 가용성은 정상이어도 데이터셋 화면은 실패해야 한다. 공개를 복구해 누락 구간을 확인한 뒤 이번에는 공개를 유지하고 텔레메트리 전송을 멈춘다. 관측 범위 화면은 오류율이 갑자기 0이라고 하지 말고 근거 미정으로 보고해야 한다.

대시보드 시각을 원시 백엔드 질의·독립 장부와 비교한다. 데이터 없음은 라벨 변경, 보존 만료, 적재 실패, 빈 모집단일 수 있다. 알림 변경 전에 구분한다.

## 실행 결과 예시

백엔드 측정이 아닌 질의 결과 예시다.

```text
HTTP healthy + publication stopped: DATA FRESHNESS FAILURE
publication continues + telemetry absent: COVERAGE UNKNOWN
2 known failures / 100 observed attempts: 0.02
empty PromQL vector: NO EVIDENCE, not zero failures
```

시도 기반 비율에는 시작되지 않은 작업이 없다. 예약 구간을 독립적으로 대사하고 히스토그램 p95는 초 단위 추정으로 표시한다. 복구에는 공개와 관측 범위 모두 회복되어야 한다.

## 스스로 설명해 보기

느린 요청이 관측에서 빠지면 평균 지연이 좋아지는 이유는 무엇인가? 데이터셋별 p95를 평균내어 플랫폼 p95로 만들면 안 되는 이유는? 제한된 집계 지표에서 영향받는 데이터셋 버전까지 찾아가는 방법을 설명한다.

다음은 [계보와 거버넌스](../../../docs/guides/data-observability/11-lineage-governance.md)로 이어간다.

<!-- source: https://prometheus.io/docs/practices/histograms/ | checked: 2026-09-10 | histogram and summary interpretation -->
<!-- source: https://prometheus.io/docs/prometheus/latest/querying/functions/ | checked: 2026-09-10 | rate, increase, histogram_quantile -->
<!-- source: https://prometheus.io/docs/alerting/latest/alertmanager/ | checked: 2026-09-10 | grouping, routing, inhibition and silences -->
<!-- source: https://grafana.com/docs/loki/latest/get-started/labels/ | checked: 2026-09-10 | label cardinality -->
<!-- source: https://grafana.com/docs/loki/latest/query/log_queries/ | checked: 2026-09-10 | stream selection and parsing -->
<!-- source: https://grafana.com/docs/tempo/latest/traceql/ | checked: 2026-09-10 | trace search -->
