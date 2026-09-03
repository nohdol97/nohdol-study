# Service 장애 진단 실습

> 실습 등급: **Local — Linux VM 또는 systemd가 실행되는 Linux host**. root 권한을 쓰는 단계는 임시 unit 생성과 삭제뿐이다.

## 먼저 이해하기

이 실습은 일부러 두 process가 같은 port를 가지려고 경쟁하게 만든다. TCP listener는 IP address와 port 조합에 bind된다. 첫 번째 Python process가 `127.0.0.1:18080`을 차지한 상태에서 systemd가 두 번째 process를 시작하면 새 process는 socket을 만들지 못하고 종료한다. systemd의 `failed`, journal의 bind error, `ss`에 보이는 기존 PID는 같은 사건을 서로 다른 관점에서 보여 준다.

| 관찰 | 답하는 질문 | 답하지 못하는 질문 |
|---|---|---|
| unit `active` | manager가 main process를 실행 중인가? | 올바른 port에서 정상 응답하는가? |
| listening socket | kernel이 어느 process에 address를 할당했는가? | HTTP handler가 정상인가? |
| `curl` 성공 | 이 client 위치에서 요청·응답이 끝났는가? | 다른 network 위치에서도 접근 가능한가? |

세 관찰을 모두 정상 기준으로 만든 뒤 장애를 주입한다. 그래야 실패 후 무엇이 달라졌는지 비교할 수 있다.

## 목표

정상 service의 unit·PID·socket·log 기준을 기록한 뒤 port 충돌을 만들어 `failed`라는 결과가 아니라 실패 원인을 찾는다.

## 1. 임시 service 만들기

다음 unit은 loopback의 18080 port에서 정적 HTTP server를 실행한다.

```ini
# /etc/systemd/system/infra-http.service
[Unit]
Description=Infra study HTTP server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m http.server 18080 --bind 127.0.0.1
Restart=no
MemoryMax=128M

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start infra-http
systemctl is-active infra-http
curl -fsS http://127.0.0.1:18080/ >/dev/null
systemctl show infra-http -p MainPID -p ControlGroup -p MemoryCurrent
ss -ltnp | grep ':18080'
```

완료 기준은 네 가지다.

- unit이 `active`다.
- `MainPID`가 0이 아니다.
- `127.0.0.1:18080`에 listening socket이 있다.
- HTTP 요청이 성공한다.

## 2. port 충돌 만들기

```bash
sudo systemctl stop infra-http
python3 -m http.server 18080 --bind 127.0.0.1
```

위 foreground process를 유지한 다른 terminal에서 service를 시작한다.

```bash
sudo systemctl start infra-http
systemctl status infra-http --no-pager
journalctl -u infra-http -n 20 --no-pager
ss -ltnp | grep ':18080'
```

```mermaid
flowchart TD
    A[service start 실패] --> B{unit log에 bind 오류가 있는가?}
    B -->|예| C[같은 port의 listener 찾기]
    B -->|아니오| D[ExecStart 경로·권한·환경 확인]
    C --> E[소유 process와 의도 확인]
    E --> F[충돌 process 종료 또는 port 변경]
    F --> G[service 재시작과 HTTP 확인]
```

핵심은 `curl` 실패를 곧바로 network 문제라고 부르지 않는 것이다. 이 경우 kernel은 이미 다른 process에 port를 할당했고 새 process의 bind를 거부한다. `journalctl`의 bind 오류와 `ss`의 기존 listener가 같은 원인을 가리켜야 한다.

## 3. 복구하고 증거 남기기

foreground server를 `Ctrl-C`로 종료한 뒤 다음을 실행한다.

```bash
sudo systemctl reset-failed infra-http
sudo systemctl start infra-http
systemctl is-active infra-http
curl -i http://127.0.0.1:18080/
```

incident 기록에는 증상, 최초 실패 시각, 기존 listener PID, 복구 동작과 마지막 성공 요청 시각을 남긴다.

## resource pressure 확장 실습

`MemoryMax`를 무작정 낮춰 production process를 죽이지 않는다. 별도 VM에서만 test process를 사용하고 다음 증거를 준비한다.

```bash
systemctl show infra-http -p MemoryCurrent -p MemoryMax -p NRestarts
journalctl -k --since "10 minutes ago" | grep -i -E 'oom|killed process'
cat /proc/pressure/memory
```

OOM을 재현하지 않았으면 “OOM 복구 완료”라고 기록하지 않는다. 위 명령은 재현 전 관측 경로만 확인한다.

## 정리

```bash
sudo systemctl disable --now infra-http 2>/dev/null || true
sudo rm /etc/systemd/system/infra-http.service
sudo systemctl daemon-reload
sudo systemctl reset-failed
```

삭제 대상이 정확히 `/etc/systemd/system/infra-http.service`인지 먼저 확인한다. 다른 unit이나 Python process는 이 정리 명령이 제거하지 않는다.

## 결과를 이렇게 읽는다

정상 상태에서는 `MainPID`와 `ss`의 process가 같고 `curl`이 성공한다. 충돌 상태에서는 systemd가 시작한 process가 bind 단계에서 종료하므로 안정된 `MainPID`가 없고, journal에는 address 사용 중이라는 원인이 남는다. 동시에 `ss`에는 foreground Python process가 계속 보인다. 이 세 증거가 일치할 때 port 충돌로 판정한다.

`ss`에 listener가 없다면 port를 차지한 process가 원인이 아니다. listener가 있고 local `curl`은 성공하지만 remote request만 실패하면 bind address, route, host firewall과 상위 network policy로 조사 범위를 옮긴다. 복구 후에는 새 `MainPID`, 기대한 listener owner와 마지막 HTTP 성공을 다시 확인한다.

## 스스로 설명해 보기

1. `active`, listening socket, HTTP 성공 중 어느 하나만 확인하면 부족한 이유는 무엇인가?
2. port 충돌과 firewall 차단은 어떤 관찰값이 다른가?
3. OOM 의심 시 application log만으로 결론내리면 안 되는 이유는 무엇인가?

<!-- source: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html | checked: 2026-09-03 | retrieval-warning: direct page unavailable -->
<!-- source: https://docs.kernel.org/admin-guide/cgroup-v2.html | checked: 2026-09-03 -->
<!-- source: https://docs.kernel.org/accounting/psi.html | checked: 2026-09-03 -->
