# 02. API와 오브젝트

> **목차 단계** — YAML 문법보다 먼저 쿠버네티스 API의 선언 모델을 이해하는 장이다.

## 이 장을 마치면

- `apiVersion`, `kind`, `metadata`, `spec`, `status`의 역할을 구분한다.
- desired state와 current state가 다른 동안 컨트롤러가 무엇을 하는지 설명한다.
- label·selector·annotation·owner reference가 오브젝트를 연결하는 방식을 안다.
- 명령형 작업과 선언형 적용의 차이를 상황에 맞게 선택한다.

## 목차

1. Kubernetes API와 API server
2. 오브젝트의 공통 구조
3. `spec`과 `status`: 의도와 관찰 결과
4. 이름, UID와 Namespace
5. label과 selector
6. annotation과 관리 메타데이터
7. owner reference와 garbage collection
8. 생성·조회·수정·삭제와 resourceVersion
9. `kubectl create`, `apply`, `patch`, `edit`의 차이
10. 서버 측 적용과 field manager
11. API discovery와 `kubectl explain`
12. YAML 작성·검증·diff 루프

## 예정 실습

- 같은 오브젝트를 명령형과 선언형으로 각각 생성
- label 변경으로 selector 연결이 끊기는 상황 확인
- `kubectl explain`으로 현재 클러스터의 필드 계약 확인
- 잘못된 API 버전과 필드가 거부되는 과정 관찰

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/overview/kubernetes-api/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/kubernetes-objects/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/object-management/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/labels/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/namespaces/ | checked: 2026-09-03 -->
