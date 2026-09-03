# 03. 클러스터 아키텍처와 제어 루프

> **목차 단계** — API 요청이 실제 컨테이너 실행으로 이어지는 경로를 컴포넌트별로 추적하는 장이다.

## 이 장을 마치면

- 컨트롤 플레인과 워커 노드의 책임을 구분한다.
- API server, etcd, scheduler, controller manager, kubelet의 협력 흐름을 설명한다.
- 선언을 즉시 실행하는 중앙 명령이 아니라 여러 reconciliation loop가 상태를 맞춘다는 점을 이해한다.
- Lease, heartbeat와 노드 상태가 장애 판단에 쓰이는 방식을 안다.

## 목차

1. 클러스터, 컨트롤 플레인과 노드
2. kube-apiserver: 모든 변경의 관문
3. etcd: API 상태 저장소
4. kube-scheduler: 아직 배치되지 않은 Pod의 노드 선택
5. kube-controller-manager와 제어 루프
6. cloud-controller-manager의 경계
7. kubelet과 컨테이너 런타임
8. kube-proxy와 네트워크 구현
9. add-on: DNS, metrics와 네트워크 플러그인
10. API 요청부터 컨테이너 시작까지의 시퀀스
11. heartbeat, Lease와 노드 장애
12. 고가용성 컨트롤 플레인의 기본 구조

## 예정 다이어그램

- `kubectl apply` → API server → etcd → controller → scheduler → kubelet 흐름
- 컨트롤 플레인과 워커 노드의 네트워크 경계
- desired state와 current state를 맞추는 reconciliation loop

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/overview/components/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/architecture/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/architecture/controller/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/architecture/nodes/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/architecture/leases/ | checked: 2026-09-03 -->
