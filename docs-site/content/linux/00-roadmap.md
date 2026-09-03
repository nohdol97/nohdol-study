# Linux 시스템 운영 로드맵

Linux 운영의 출발점은 명령어 암기가 아니라 **한 workload가 어떤 process로 실행되고 어떤 kernel resource를 소비하는지 연결하는 것**이다. Kubernetes Pod와 AWS EC2도 결국 이 경계 위에서 실행된다.

## 이 과정이 답하는 질문

- service가 실행되지 않을 때 unit, process, socket 중 어디부터 확인하는가?
- CPU 사용률, load average와 runnable task는 어떻게 다른가?
- memory 사용량이 늘 때 process RSS, page cache와 cgroup limit을 어떻게 구분하는가?
- disk가 찼을 때 block 여유, inode, 열린 삭제 파일 중 무엇이 원인인가?
- container resource limit이 Linux cgroup에서 어떤 상태로 보이는가?

## 한 문장 모델

> Linux 운영은 `service manager → process/thread → file descriptor/socket → memory·CPU·I/O → kernel event` 순서로 실제 상태를 좁히는 일이다.

```mermaid
flowchart LR
    U[systemd unit] --> P[process와 thread]
    P --> F[file descriptor와 socket]
    P --> M[memory와 CPU]
    F --> IO[filesystem와 network I/O]
    M --> C[cgroup controller]
    IO --> K[kernel event와 log]
    C --> K
```

## 읽는 순서

1. [Process와 resource의 연결](01-process-and-resource-model.md): PID, unit, `/proc`, file descriptor, cgroup의 책임을 연결한다.
2. [Service 장애 진단 실습](02-service-failure-lab.md): 정상 기준을 기록한 뒤 start failure, port 충돌과 resource pressure를 증거로 구분한다.

## Kubernetes와 이어지는 지점

| Linux | Kubernetes |
|---|---|
| process와 signal | container process와 Pod 종료 |
| cgroup CPU·memory | requests·limits와 runtime 격리 |
| namespace | container가 보는 PID·mount·network 범위 |
| socket·route | Pod IP, Service와 CNI datapath |
| filesystem·mount | volume, PV/PVC와 node storage |
| systemd·journal | kubelet·container runtime node service |

이 과정은 container runtime 내부 구현이나 eBPF 심화를 별도 topic으로 확장하지 않는다. 장애를 kernel 경계까지 추적할 수 있는 운영 기초에 집중한다.

## 완료 기준

- service 이름에서 main PID, 열린 socket, cgroup과 최근 log를 찾는다.
- CPU·memory·disk 증상을 하나의 `top` 출력으로 단정하지 않고 서로 다른 관찰값으로 확인한다.
- process 종료가 signal, OOM kill, service restart policy 중 무엇 때문인지 증거를 제시한다.
- 다음 과정인 [네트워크와 요청 경로](../networking/00-roadmap.md)에서 process의 listening socket부터 요청 추적을 시작할 수 있다.

## 스스로 설명해 보기

1. service가 `active`인데 요청이 실패할 수 있는 이유를 세 가지 말해 보자.
2. container의 memory limit과 host의 free memory가 서로 다른 질문인 이유는 무엇인가?
3. disk 사용률이 100%가 아닌데 새 파일 생성이 실패할 수 있는 이유는 무엇인가?

<!-- source: https://docs.kernel.org/admin-guide/cgroup-v2.html | checked: 2026-09-03 -->
<!-- source: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html | checked: 2026-09-03 | retrieval-warning: direct page unavailable; implementation claims limited to stable unit/process model -->
