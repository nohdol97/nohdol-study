# 10. 프로덕션 운영과 확장

> **목차 단계** — 학습용 클러스터를 넘어 업그레이드 가능하고 복구 가능한 플랫폼으로 운영하는 기준을 정리하는 장이다.

## 이 장을 마치면

- 관리형 클러스터와 자체 관리 클러스터의 책임 차이를 설명한다.
- 업그레이드, 인증서, etcd 백업과 노드 유지보수의 기본 계획을 세운다.
- CRD와 Operator가 Kubernetes API를 확장하는 방식을 이해한다.
- Helm과 Kustomize를 배포 패키징 문제에 맞게 선택하고 레퍼런스를 찾는다.

## 목차

1. 학습 환경과 프로덕션 환경의 차이
2. 관리형 서비스와 자체 관리의 책임 배분
3. kubeadm 기반 클러스터 구성
4. 컨트롤 플레인 고가용성
5. 노드 추가·제거·drain과 유지보수
6. 버전 skew와 업그레이드 계획
7. 인증서 수명과 갱신
8. etcd 백업·복원과 재해 복구
9. 리소스 쿼터, 비용과 멀티테넌시 운영
10. CustomResourceDefinition
11. custom controller와 Operator 패턴
12. admission webhook과 API extension
13. Helm chart와 배포 패키징
14. Kustomize overlay와 환경별 변형
15. API·kubectl·컴포넌트 레퍼런스 찾는 법

## 예정 산출물

- 프로덕션 준비 체크리스트
- 업그레이드 전후 검증 및 rollback 흐름
- CRD → custom controller → 외부 시스템 reconciliation 다이어그램
- 같은 애플리케이션의 Helm과 Kustomize 구성 비교

## 공식 시작 링크

- [쿠버네티스 설정](https://kubernetes.io/ko/docs/setup/)
- [프로덕션 환경](https://kubernetes.io/ko/docs/setup/production-environment/)
- [클러스터 관리](https://kubernetes.io/ko/docs/concepts/cluster-administration/)
- [쿠버네티스 확장](https://kubernetes.io/ko/docs/concepts/extend-kubernetes/)
- [커스텀 리소스](https://kubernetes.io/ko/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes 레퍼런스](https://kubernetes.io/ko/docs/reference/)

[전체 로드맵으로 돌아가기](00-roadmap.md)
