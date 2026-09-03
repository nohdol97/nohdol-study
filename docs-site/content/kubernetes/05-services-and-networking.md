# 05. Service와 네트워킹

> **목차 단계** — Pod IP가 바뀌어도 요청이 올바른 백엔드에 도달하도록 만드는 계층을 순서대로 이해하는 장이다.

## 이 장을 마치면

- Pod 네트워크 모델과 CNI의 역할을 설명한다.
- Service가 selector와 EndpointSlice를 통해 백엔드를 찾는 방식을 안다.
- ClusterIP, NodePort, LoadBalancer와 headless Service의 차이를 구분한다.
- Ingress와 Gateway API가 L4 Service 위에 제공하는 L7 라우팅 책임을 이해한다.

## 목차

1. Pod-to-Pod 네트워크 모델
2. CNI 플러그인과 노드 간 연결
3. Service와 안정적인 가상 주소
4. selector, EndpointSlice와 readiness
5. ClusterIP, NodePort와 LoadBalancer
6. headless Service와 직접 discovery
7. 클러스터 DNS와 서비스 이름 해석
8. 외부에서 클러스터로 들어오는 요청
9. Ingress와 Ingress Controller
10. Gateway API의 GatewayClass·Gateway·Route
11. NetworkPolicy와 허용 목록 네트워크
12. 요청이 실패할 때 DNS → Service → Endpoint → Pod 순서로 추적하기

## 예정 다이어그램

- 외부 클라이언트 → LoadBalancer/Gateway → Service → EndpointSlice → Pod
- Service selector와 Pod label 연결
- NetworkPolicy 적용 전후 허용 흐름

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/services-networking/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/services-networking/service/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/cluster-administration/networking/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/services-networking/dns-pod-service/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/services-networking/ingress/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/tasks/network/ | checked: 2026-09-03 -->
