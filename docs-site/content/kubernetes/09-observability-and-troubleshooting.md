# 09. 관측과 트러블슈팅

> **목차 단계** — 리소스 상태, 이벤트, 로그와 메트릭을 증상에 맞는 순서로 읽는 장이다.

## 이 장을 마치면

- `get`, `describe`, events, logs와 metrics가 각각 어떤 질문에 답하는지 구분한다.
- Pending, ImagePullBackOff, CrashLoopBackOff, NotReady의 원인 범위를 좁힌다.
- probe 실패와 애플리케이션 장애를 혼동하지 않고 진단한다.
- rollout 실패 시 사용자 영향, 배포 상태와 근본 원인을 순서대로 확인한다.

## 목차

1. desired state와 current state 비교
2. condition, phase와 event 읽기
3. 컨테이너 로그와 이전 인스턴스 로그
4. 임시 디버그 컨테이너와 `kubectl debug`
5. CPU·메모리·네트워크·스토리지 메트릭
6. startup·readiness·liveness probe 진단
7. Pending Pod: 스케줄링 실패
8. 이미지 가져오기 실패
9. CrashLoopBackOff와 종료 코드
10. Service에 endpoint가 없는 문제
11. DNS와 네트워크 경로 디버깅
12. rollout 상태와 rollback
13. 노드 NotReady와 자원 압박
14. 감사 가능한 장애 타임라인과 사후 분석

## 기본 진단 순서

1. 영향 범위와 Namespace를 확인한다.
2. 상위 워크로드와 Pod 상태를 비교한다.
3. condition과 최신 event를 읽는다.
4. 현재·이전 컨테이너 로그를 확인한다.
5. 스케줄링, 구성, 네트워크, 스토리지와 애플리케이션 중 실패 계층을 좁힌다.
6. 수정 후 rollout과 사용자 경로를 다시 검증한다.

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/tasks/debug/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/debug/debug-application/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/debug/debug-cluster/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/debug/debug-cluster/resource-usage-monitoring/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/workloads/pods/pod-lifecycle/ | checked: 2026-09-03 -->
