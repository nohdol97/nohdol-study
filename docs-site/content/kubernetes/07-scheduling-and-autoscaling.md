# 07. 스케줄링과 리소스·오토스케일링

> **목차 단계** — scheduler의 배치 결정과 kubelet의 자원 집행, 오토스케일러의 피드백 루프를 연결하는 장이다.

## 이 장을 마치면

- requests가 스케줄링에, limits가 런타임 집행에 미치는 영향을 구분한다.
- nodeSelector, affinity, topology spread, taint와 toleration의 용도를 설명한다.
- 우선순위·선점·축출이 서로 다른 시점에 작동한다는 점을 안다.
- HPA, VPA와 node autoscaling이 서로 다른 대상을 조절함을 이해한다.

## 목차

1. 스케줄링 큐와 노드 필터링·점수화
2. CPU·메모리 requests와 limits
3. QoS class와 메모리 압박
4. nodeSelector와 node affinity
5. Pod affinity와 anti-affinity
6. topology spread constraints
7. taint와 toleration
8. priority와 preemption
9. eviction: 노드 압박과 API 기반 축출
10. PodDisruptionBudget
11. Horizontal Pod Autoscaler
12. Vertical Pod Autoscaler와 node autoscaling의 경계
13. GPU와 확장 리소스 스케줄링

## 예정 실습

- requests가 없어 과밀 배치되는 상황과 적정 설정 비교
- affinity와 taint를 이용한 전용 노드 배치
- PDB가 자발적 중단에 미치는 영향 확인
- 부하 생성 후 HPA의 metrics → desired replicas 계산 추적

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/scheduling-eviction/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/configuration/manage-resources-containers/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/scheduling-eviction/pod-overhead/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/run-application/horizontal-pod-autoscale/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/manage-gpus/scheduling-gpus/ | checked: 2026-09-03 -->
