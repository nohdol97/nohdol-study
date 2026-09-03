# 01. 왜 Kubernetes인가와 첫 클러스터

> **목차 단계** — 컨테이너 오케스트레이션의 필요와 학습 환경을 이해하는 장이다. 개별 공식 문서 링크를 받으면 실행 화면과 상세 예시를 채운다.

## 이 장을 마치면

- 컨테이너 런타임과 오케스트레이터의 책임을 구분한다.
- 쿠버네티스가 제공하는 배포·확장·복구 자동화가 어떤 문제를 해결하는지 설명한다.
- 학습용 클러스터와 프로덕션 클러스터의 선택 기준이 다른 이유를 안다.
- `kubectl`과 kubeconfig가 어느 API 서버를 어떤 자격으로 호출하는지 설명한다.

## 목차

1. 컨테이너 하나에서 여러 서비스 운영으로 넘어갈 때 생기는 문제
2. 원하는 복제본 수, 장애 복구, 서비스 발견과 선언형 배포
3. 쿠버네티스가 하는 일과 하지 않는 일
4. 로컬 학습 환경 선택: minikube, kind와 기타 도구
5. `kubectl` 설치와 버전 확인
6. kubeconfig의 cluster·user·context
7. 첫 Namespace와 첫 애플리케이션
8. `get`, `describe`, `logs`, `delete`로 보는 기본 관찰 루프
9. 클러스터를 지우고 다시 만드는 연습

## 예정 실습

- 로컬 클러스터 생성 후 노드 상태 확인
- 예제 애플리케이션 배포와 외부 접근
- 현재 context를 바꿔 잘못된 클러스터를 조작하는 실수 재현
- 리소스 삭제 뒤 컨트롤러가 다시 만드는 대상과 만들지 않는 대상 비교

## 공식 시작 링크

- [Kubernetes 문서 홈](https://kubernetes.io/ko/docs/home/)
- [왜 쿠버네티스가 필요한가](https://kubernetes.io/ko/docs/concepts/overview/#쿠버네티스가-왜-필요하고-무엇을-할-수-있나)
- [학습 환경](https://kubernetes.io/ko/docs/setup/learning-environment/)
- [도구 설치](https://kubernetes.io/ko/docs/tasks/tools/)
- [Hello Minikube](https://kubernetes.io/ko/docs/tutorials/hello-minikube/)
- [쿠버네티스 기초 학습](https://kubernetes.io/ko/docs/tutorials/kubernetes-basics/)

[전체 로드맵으로 돌아가기](00-roadmap.md)
