# 04. Pod와 워크로드

> **목차 단계** — 컨테이너를 직접 다루는 대신 각 워크로드 컨트롤러에 수명주기를 맡기는 이유를 배우는 장이다.

## 이 장을 마치면

- Pod가 스케줄링과 네트워크의 기본 단위인 이유를 설명한다.
- Deployment, StatefulSet, DaemonSet, Job과 CronJob의 선택 기준을 구분한다.
- init container, sidecar, probe와 종료 절차가 Pod 수명주기에 미치는 영향을 안다.
- rollout과 rollback이 어떤 오브젝트 관계로 동작하는지 추적한다.

## 목차

1. Pod의 공유 네트워크·스토리지·수명
2. multi-container Pod를 써야 하는 경우
3. init container와 sidecar container
4. Pod lifecycle과 restartPolicy
5. startup·readiness·liveness probe
6. termination과 graceful shutdown
7. ReplicaSet과 Deployment
8. rolling update와 rollback
9. StatefulSet의 identity와 ordered lifecycle
10. DaemonSet과 노드별 에이전트
11. Job, CronJob과 완료 기반 워크로드
12. 무상태·상태·배치 워크로드 선택표

## 예정 실습

- readiness 실패와 liveness 실패의 결과 비교
- Deployment rollout 중 이미지 오류 재현과 rollback
- StatefulSet Pod 이름과 볼륨 identity 확인
- Job 실패 정책과 재시도 관찰

## 공식 시작 링크

- [워크로드와 파드](https://kubernetes.io/ko/docs/concepts/workloads/)
- [파드](https://kubernetes.io/ko/docs/concepts/workloads/pods/)
- [워크로드 리소스](https://kubernetes.io/ko/docs/concepts/workloads/controllers/)
- [파드 라이프사이클](https://kubernetes.io/ko/docs/concepts/workloads/pods/pod-lifecycle/)
- [애플리케이션 실행 태스크](https://kubernetes.io/ko/docs/tasks/run-application/)
- [잡 실행 태스크](https://kubernetes.io/ko/docs/tasks/job/)

[전체 로드맵으로 돌아가기](00-roadmap.md)
