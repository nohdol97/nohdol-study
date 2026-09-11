# OpenTelemetry: 텔레메트리를 통제하며 실행 연결하기

실패한 파이프라인의 단서는 스케줄러 로그, 실행기 지표, 데이터베이스 오류에 흩어질 수 있다. OpenTelemetry는 일관된 컨텍스트로 신호를 계측·전송해 연결을 돕는다. 저장 백엔드, 질의 인터페이스, 의도적인 식별자 모델은 여전히 필요하다.

## 이 장에서 처음 쓰는 말

| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| span / trace | 기록된 작업 / trace 컨텍스트로 연결한 관련 작업들 | 요청 하나의 작업을 여러 연산 경계에 걸쳐 설명하고 지연이 쌓인 곳을 찾는다. |
| 리소스(resource) | 서비스처럼 텔레메트리 생산 개체를 식별하는 속성 | 배포·장애를 비교할 때 관측 데이터를 이를 생성한 서비스·인스턴스에 연결한다. |
| 컨텍스트 전파(context propagation) | 호출·메시지 경계를 넘어 실행 맥락을 전달하는 것 | HTTP 호출·메시지 처리 경계를 넘어 실행의 연결 관계를 유지한다. |
| baggage | 요청과 함께 전달할 수 있는 키·값 컨텍스트 | 하위 구성 요소에 필요할 때 승인된 작은 문맥 값을 호출 사이에 전달한다. |
| OTLP | OpenTelemetry의 텔레메트리 전송 프로토콜 | 백엔드마다 별도 전송 방식을 만들지 않고 공통 프로토콜로 관측 데이터를 보낸다. |
| 샘플링(sampling) | 정의한 정책에 따라 보존할 트레이스 정보를 선택하는 것 | 트레이스의 양·비용을 조절하고 선택 정책으로 잃을 수 있는 근거를 명시한다. |

## 먼저 이해하기

1. SDK나 지원 자동 계측으로 애플리케이션 작업을 계측한다.
2. 서비스·환경 식별자를 일관되게 설정한다.
3. 필요한 메시지 헤더 등 지원 경계를 넘어 컨텍스트를 전파한다.
4. 직접 또는 Collector 파이프라인을 통해 신호를 내보낸다.
5. 백엔드에 질의해 작업을 데이터셋 버전·공개 결과와 연결한다.

지표는 모집단을 요약하고 로그는 이벤트를 기록하며 트레이스는 작업·관계를 설명한다. 리소스는 생산자를 설명하며 별도 저장 백엔드가 아니다. 선택한 구성 요소가 지원하면 프로파일로 코드 수준 자원 소비를 조사할 수 있다. 모든 언어·신호의 성숙도가 같다고 가정하지 말고 SDK, Collector 배포판, 백엔드별 신호 지원과 의미 규약 상태를 확인한다.

## Collector의 책임

| 구성 요소 | 책임 | 흔한 오해 |
|---|---|---|
| Receiver | 텔레메트리 수신·수집 | span 수신이 백엔드 영속 저장을 뜻하지 않음 |
| Processor | 변환·필터·배치·샘플링·신호 제한 | 순서와 지원 신호 유형이 중요함 |
| Exporter | 목적지로 전송 | 재시도·큐 제한 때문에 유실 가능 |
| Extension | 상태 검사·저장 같은 프로세스 지원 | 선언만으로 활성화되지 않음 |
| Service pipelines | 활성 구성 요소 연결 | 설정만 하고 연결하지 않으면 작동하지 않음 |

다음은 `otlp`, `memory_limiter`, `batch`, `debug`가 포함된 호환 Collector 배포판용 최소 로컬 트레이스 파이프라인이다. 가상 트레이스를 출력할 뿐 영속 백엔드나 운영 설정이 아니다. 시작 전에 해당 배포판·버전의 설정 검증 명령으로 검사한다.

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 127.0.0.1:4318
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 128
    spike_limit_mib: 32
  batch: {}
exporters:
  debug:
    verbosity: basic
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
```

loopback 바인딩은 애플리케이션과 Collector가 호스트 네트워크 네임스페이스를 공유한다고 가정한다. 네트워크가 분리된 컨테이너는 다른 컨테이너의 loopback에 접근하지 못한다. 컨테이너 실습은 명시적 내부 네트워크를 설계하고 필요한 호스트 포트만 연다. 원격 배포는 신원·전송 보안·접근 통제를 의도적으로 구성한다.

## 질문에 맞는 식별자 선택

실행 조사에는 trace ID를 사용한다. 안정적인 파이프라인 이름, 실행 ID, 소스 범위, 데이터셋 버전은 통제된 span·로그 속성이나 참조 기록에 넣는다. 데이터셋 생성은 여러 시간·작업이 필요할 수 있다. 전체 수명을 끝나지 않는 트레이스 하나로 묶으면 상태·샘플링이 불편해진다.

배치 소비, 파티션 집단 변환, 후보 검증, 스냅샷 공개처럼 범위 있는 작업을 모델링한다. 여러 입력 컨텍스트가 한 작업에 참여하면 부모 하나를 꾸며내지 말고 link를 쓴다. 실행 ID·이벤트 ID는 계속 새 시계열을 만드는 무제한 값이므로 지표 라벨에서 제외한다.

baggage에 비밀, 프롬프트, 고객 레코드, 접근 토큰을 넣지 않는다. 전파는 신뢰 경계를 넘을 수 있고 baggage는 인가 수단이 아니다. 가능한 한 수집 지점에서 비식별화하고 각 목적지에 실제 도착한 내용을 검증한다.

## 샘플링과 복원력

Head 샘플링은 일찍 결정해 최종 결과 정보가 제한된다. Tail 샘플링은 이후 트레이스 정보를 사용할 수 있지만 버퍼와 동일 trace span의 일관된 라우팅이 필요하다. 트레이스가 보존되지 않았다고 작업이 없었던 것은 아니다. SLO 분모는 샘플 트레이스 수 대신 적절한 완전 카운터나 결과 장부에서 만든다.

Collector 큐·재시도는 제한된 하위 장애를 흡수한다. 메모리 큐는 재시작에 사라질 수 있다. 지원 영속 큐도 디스크 용량, 보존·재시도 제한, 목적지 복구에 달려 있다. 실제 선택 버전이 노출하는 수신·거부·전송·실패·삭제 텔레메트리와 큐·디스크 사용을 감시한다.

## 리소스·span 속성·컨텍스트·baggage

리소스는 `service.name=orders-transform`, `deployment.environment.name=study`처럼 생산자를 식별한다. span 속성은 통제된 데이터셋 이름·소스 버전처럼 개별 작업을 설명하고 instrumentation scope는 신호를 내는 라이브러리를 식별한다. 배치마다 리소스에 실행 ID를 넣으면 서비스 신원이 불안정해져 하위 그룹화가 나빠진다. 안정된 생산자 신원과 작업별 식별자를 분리한다.

trace ID는 관련 작업들을, span ID는 각 span을 식별하며 선택적인 부모가 있다. 컨텍스트는 프로세스 안에서 현재 실행 관계를 전달한다. propagator는 선택한 컨텍스트를 HTTP·Kafka 헤더 같은 전달 매체에 직렬화하고 수신 경계에서 추출한다. W3C `traceparent`에는 버전·trace ID·부모 span ID·플래그가 있다. 관계 전달 수단이며 신뢰할 사용자 신원이 아니다.

baggage는 span 속성과 별도로 애플리케이션 키·값 맥락을 전파한다. baggage 설정이 자동 span 기록을 만들지 않고 속성 기록도 자동 전파하지 않는다. 허용한 값을 필요한 곳에 의도적으로 복사해야 한다. 유입 전파값을 신뢰하지 말고 크기를 제한하며 비밀·임의 고객 필드가 이를 통해 하위 서비스로 가지 않게 한다.

## 실제 SDK 실습: 주입·추출·전파 누락 탐지

이 로컬 실습은 `opentelemetry-sdk==1.44.0`과 대응 API 의존성을 사용한다. 설치한다면 임시 가상 환경을 쓴다. `python3 -m venv .venv` 후 `.venv/bin/python -m pip install opentelemetry-sdk==1.44.0`을 실행한다. 전체 코드를 `trace_lab.py`로 저장하고 `.venv/bin/python trace_lab.py`로 실행한다. 메모리 내 exporter는 네트워크로 전송하지 않으며 Collector·계정이 필요 없다.

전파가 깨진 소비자에 명시적 빈 컨텍스트를 주면 아직 활성인 로컬 생산자 span이 전송 누락을 우연히 숨기는 것을 막는다. 예제에서는 소비자 시작 전에 생산자가 끝나며 큐 메시지 경계와 비슷하다.

<!-- executable-optional: otel-propagation -->
```python
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.propagate import inject, extract
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

exporter = InMemorySpanExporter()
provider = TracerProvider(resource=Resource.create({
    'service.name': 'study-pipeline',
    'deployment.environment.name': 'study',
}))
provider.add_span_processor(SimpleSpanProcessor(exporter))
tracer = provider.get_tracer('study.propagation', '1.0')
headers = {}
with tracer.start_as_current_span('produce'):
    inject(headers)
with tracer.start_as_current_span('consume', context=extract(headers)):
    trace.get_current_span().set_attribute('study.dataset', 'orders.accepted')
with tracer.start_as_current_span('consume_broken', context=Context()):
    pass

spans = {span.name: span for span in exporter.get_finished_spans()}
parent, child, broken = (spans[name] for name in ('produce','consume','consume_broken'))
assert child.context.trace_id == parent.context.trace_id
assert child.parent.span_id == parent.context.span_id
assert broken.parent is None
assert broken.context.trace_id != parent.context.trace_id
assert all(s.resource.attributes['service.name']=='study-pipeline' for s in spans.values())
print('exported_spans:', len(spans))
print('traceparent_present:', 'traceparent' in headers)
print('parent_child_same_trace:', child.context.trace_id == parent.context.trace_id)
print('broken_consumer_new_trace:', broken.context.trace_id != parent.context.trace_id)
provider.shutdown()
```

예상 출력이다. 무작위 trace ID는 의도적으로 출력하지 않는다.

```text
exported_spans: 3
traceparent_present: True
parent_child_same_trace: True
broken_consumer_new_trace: True
```

`extract(headers)`를 `Context()`로 바꾸면 부모·자식 단언이 실패해야 한다. 실제 SDK 전파·export를 시험하지만 Kafka 헤더 직렬화, 네트워크 OTLP, tail 샘플링, 백엔드 보존은 시험하지 않는다. 같은 예제에 경계를 하나씩 추가한다.

## 부모·자식 관계와 span link

요청 하나가 하위 요청 하나를 만들면 부모·자식 span이 인과적 중첩을 자연스럽게 표현한다. 독립 trace 컨텍스트의 메시지 500개를 소비하는 배치는 잠재 입력이 500개라 부모 하나를 만들면 관계 대부분을 숨긴다. 소비자 span은 제한된 실행 트레이스를 유지하며 입력 컨텍스트에 link를 둘 수 있다. 데이터셋 계보는 무엇에서 파생됐는지, span link는 실행 관계를 답한다. 공통 실행·공개 참조를 유지해 연결한다.

측정하려는 작업의 시작·종료를 기록한다. 큐 제출을 감싼 span은 워커 완료가 아니라 큐 입력 시간을 측정한다. 재시도는 제한된 논리 작업 아래 시도 자식으로 표현하고 결과·시도 메타데이터를 남길 수 있다. 프레임워크와 수동 래퍼가 같은 호출을 계측한다면 생성 span 수를 확인해 이중 계측을 피한다.

## 지표·로그와 SDK 의미

SDK counter는 승인 이벤트처럼 음수가 아닌 증가분을 기록한다. up/down counter는 활성 작업처럼 늘거나 줄 수 있는 가산 변화를 표현한다. histogram은 초 단위 공개 지연 같은 분포를 기록하고 observable 계측기는 콜백으로 값을 보고한다. 모든 숫자를 gauge로 취급하지 말고 수량의 수학적 성질로 계측기를 선택한 뒤 exporter·백엔드 대응을 확인한다.

집계 시간 방식(temporality)은 한 구간의 변화인지 시작점 이후 누적인지를 뜻한다. 누적 카운터를 기대하는 백엔드에 delta를 보내려면 호환 변환이 필요하다. 재시작 시 초기화·시작 시각 처리가 중요하다. 속성 집합은 집계 차원을 정의한다. 샘플 span에는 괜찮던 `run_id`도 지표에 넣으면 실행마다 시계열을 만들 수 있다.

로그는 trace·span 컨텍스트를 담아 이벤트를 실행에 연결할 수 있다. 활성 span 밖의 로그에는 유효한 trace 컨텍스트가 없을 수 있으므로 작업·실행 참조가 독립적으로 의미 있게 남아야 한다. 로그 본문, span 이벤트, 속성은 모두 양을 늘리고 페이로드를 노출할 수 있다. 전체 입력 복사 대신 필드를 의도적으로 선택한다.

## Head 샘플링·tail 샘플링·라우팅

Head 샘플링은 트레이스 시작 때 결정하며 흔히 결정적인 trace-ID 비율과 부모 기반 정책을 쓴다. 30초 뒤 실패를 미리 알 수는 없다. Tail 샘플링은 버퍼한 근거로 오류·고지연 트레이스를 보존할 수 있지만 같은 trace의 span들이 해당 결정 상태에 모여야 한다. 독립 tail sampler들에 임의 span을 분산하면 트레이스가 조각나 정책이 깨질 수 있다.

상위 head sampler가 99%를 버리면 하위 tail sampler가 누락 span을 복원할 수 없다. 관측한 오류 전부와 성공 일부를 남기는 정책은 보존 모집단을 편향시킨다. SLO는 비샘플 결과 지표나 공개 장부로 세고, 알려진 예제 결과별 생성·보존 트레이스로 샘플링을 평가한다.

초당 1,000 trace, trace당 10 span, tail 결정 구간 30초라면 늦은 span·오버헤드 전에도 결정 기간 동안 최대 300,000 span이 들어온다. 이는 유입량 추정이며 메모리 측정이 아니다. 선택한 processor·버전에서 실제 보존 상태, 용량, 시간 초과를 측정한다.

## Collector 순서·큐·유실 집계

앞선 트레이스 파이프라인은 receiver가 OTLP를 받고 memory limiter가 이후 처리의 할당 전에 압력을 걸며 batch가 묶고 exporter가 보낸다. memory limiter는 추가 저장소가 아니다. 거부된 신호의 복구는 상위 재시도에 달려 있다. processor는 신호 파이프라인별로 설정하므로 traces용이 지표·로그에도 자동 적용되지 않는다.

exporter 큐가 벌어 주는 시간은 유한하다. 초당 2 MB, 가용 용량 600 MB인 빈 바이트 큐는 오버헤드·재시도 제한 전 대략 5분 여유다. 일부 exporter는 바이트 대신 요청·배치 수로 용량을 정하므로 측정한 배치 크기로 환산한다. 복구 처리율 3 MB/s, 지속 유입 2 MB/s라면 600 MB 적체를 비우는 데 약 10분 걸린다.

영속 큐 저장소는 지원되는 재시작을 넘어 전송 대기 데이터를 보존할 수 있지만 디스크 소진, 복구 불가 목적지, 만료, 영구 오류는 여전히 고려해야 한다. Collector 수신 승인이 백엔드 영속 저장 승인은 아닐 수 있다. 가상 실패 시험에서 생성 ID와 수신·보존 ID를 대사하고 전체 파이프라인 유실은 독립 경로로 텔레메트리 상태를 감시한다.

## 단계별 실패 실습

가상으로 계측한 작업 하나, 로컬 Collector, 복원력 단계용 별도 임시 목적지가 필요하다. 작업 하나가 기대 리소스·trace 컨텍스트로 나타나는지 먼저 확인한다. 경계 하나의 전파를 끊어 분리된 트레이스를 관찰하고 고친 뒤 반복한다.

이후 목적지를 멈춰 큐 증가·실패를 관찰하고 용량 소진 전에 재시작한다. 생성·보존 이벤트 수를 비교한다. 별도 실행에서는 제한 큐를 초과시켜 유실을 기록한다. Collector 상태 엔드포인트가 녹색이라고 모든 span 전송이 입증되지는 않는다.

## 실행 결과 예시

관찰 기록 예시다. 실제 debug exporter 형식은 Collector 배포판에 달려 있다.

```text
service.name: study-pipeline
propagation intact: parent and child share trace ID
propagation broken: disconnected child trace
destination stopped: bounded export queue grows
queue exhausted: record dropped or unretained spans
example count reconciliation: 100 generated - 93 retained = gap of 7
```

정상 엔드포인트나 빈 큐는 무손실 전송의 증거가 아니다. debug 파이프라인은 수신을 보여 주며 목적지 장애 동작에는 별도 exporter·큐 설정이 필요하다. 복구를 주장하기 전에 관측 건수를 기록한다.

## 스스로 설명해 보기

어떤 근거가 span과 정확한 입력 스냅샷을 연결하는가? 트레이스를 샘플링해도 어떤 지표는 남는가? 같은 파이프라인에만 의존하지 않고 텔레메트리 장애를 탐지할 방법을 설명한다.

다음은 [지표·로그·트레이스 운영](../../../docs/guides/data-observability/10-metrics-logs-traces.md)으로 이어간다.

<!-- source: https://opentelemetry.io/docs/collector/configuration/ | checked: 2026-09-10 | components and service wiring -->
<!-- source: https://opentelemetry.io/docs/collector/resiliency/ | checked: 2026-09-10 | queue persistence and loss boundaries -->
<!-- source: https://opentelemetry.io/docs/concepts/context-propagation/ | checked: 2026-09-10 | context and baggage -->
<!-- source: https://opentelemetry.io/docs/languages/python/instrumentation/ | checked: 2026-09-10 | SDK spans/resources/export; lab pinned to 1.44.0 -->
<!-- source: https://opentelemetry.io/docs/languages/python/propagation/ | checked: 2026-09-10 | inject/extract transport boundary -->
<!-- source: https://opentelemetry.io/docs/concepts/sampling/ | checked: 2026-09-10 | head and tail sampling tradeoffs -->
<!-- source: https://opentelemetry.io/docs/specs/otel/metrics/data-model/ | checked: 2026-09-11 | temporality and aggregation identities -->
