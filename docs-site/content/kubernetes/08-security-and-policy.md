# 08. 보안과 정책

> **목차 단계** — API 요청의 신원과 권한, 실행되는 Pod의 권한, 네트워크 통신 권한을 별도 층으로 나누는 장이다.

## 이 장을 마치면

- 인증, 인가와 admission control의 처리 순서를 설명한다.
- ServiceAccount와 RBAC을 최소 권한으로 구성한다.
- securityContext와 Pod Security Standards가 제한하는 실행 권한을 안다.
- NetworkPolicy, Secret 저장 보호와 공급망 보안을 서로 다른 통제 지점으로 구분한다.

## 목차

1. Kubernetes API 요청의 보안 단계
2. 사용자와 ServiceAccount
3. RBAC의 Role·ClusterRole·Binding
4. admission controller와 정책 검사
5. Pod Security Standards와 Pod Security Admission
6. container와 Pod securityContext
7. Linux capabilities, seccomp와 AppArmor
8. NetworkPolicy의 ingress·egress 허용 규칙
9. Secret의 저장·전달·노출 경로
10. etcd 저장 데이터 암호화
11. 이미지 서명·검증과 공급망 정책
12. 멀티테넌시와 Namespace 경계
13. 감사 로그와 보안 이벤트 추적

## 예정 실습

- 특정 Namespace만 읽는 ServiceAccount와 RoleBinding 작성
- privileged Pod를 제한 정책으로 거부
- default deny NetworkPolicy 뒤 필요한 통신만 허용
- 권한 오류를 `kubectl auth can-i`로 진단

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/security/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/reference/access-authn-authz/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/security/service-accounts/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/reference/access-authn-authz/rbac/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/security/pod-security-standards/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/services-networking/network-policies/ | checked: 2026-09-03 -->
