# 02. API와 오브젝트

쿠버네티스에서 YAML은 설정 파일 그 자체가 아니라 **API에 전달하는 의도**다. 사용자는 원하는 상태를 오브젝트의 `spec`에 기록하고, 컨트롤러는 실제 상태를 관찰해 그 차이를 줄인다. 이 선언 모델을 이해하면 수많은 리소스도 같은 문법으로 읽을 수 있다.

## 먼저 잡을 mental model

일반적인 스크립트는 “A를 실행한 다음 B를 실행하라”고 명령한다. 쿠버네티스는 “웹 서버 세 개가 계속 준비된 상태여야 한다”고 선언한다. 한 Pod가 사라져도 선언은 남아 있으므로 컨트롤러가 새 Pod를 만든다.

```mermaid
flowchart LR
    U["사용자 또는 자동화"] -->|"원하는 상태 제출"| A["API server"]
    A -->|"오브젝트 저장"| E["etcd"]
    C["Controller"] -->|"현재 상태 관찰"| A
    C --> D{"spec과 status가 같은가?"}
    D -->|"아니오"| X["생성·수정·삭제"]
    X --> A
    D -->|"예"| W["다음 변화를 기다림"]
```

중요한 점은 “적용 명령이 컨테이너를 직접 띄운다”가 아니라는 것이다. API server가 의도를 저장하고, 여러 제어 루프가 각자의 책임 범위에서 비동기로 상태를 맞춘다.

## 모든 오브젝트를 읽는 다섯 칸

| 필드 | 질문 | 예시 |
|---|---|---|
| `apiVersion` | 어느 API 그룹과 버전의 계약인가? | `apps/v1` |
| `kind` | 어떤 종류의 리소스인가? | `Deployment` |
| `metadata` | 이름·Namespace·연결 정보는 무엇인가? | `name`, `labels` |
| `spec` | 사용자가 원하는 상태는 무엇인가? | `replicas: 3` |
| `status` | 시스템이 관찰한 현재 상태는 무엇인가? | `availableReplicas: 2` |

`status`는 보통 컨트롤러가 쓰는 관찰 결과다. Git에 저장할 매니페스트에는 원하는 `spec`을 적고, 실행 결과는 `kubectl get ... -o yaml`이나 `kubectl describe`로 확인한다.

### 이름과 UID는 다르다

같은 Namespace에서 같은 종류의 오브젝트는 이름으로 찾는다. 그러나 삭제 후 같은 이름으로 다시 만든 오브젝트는 새 UID를 받는다. 이름은 사람이 쓰는 주소이고 UID는 오브젝트 생애를 구분하는 식별자라고 생각하면 된다.

## Namespace는 무엇을 나누는가

Namespace는 하나의 클러스터 안에서 관련 리소스를 묶고 **이름·조회·권한·정책·자원 한도의 적용 범위**를 만드는 API 오브젝트다. 파일 시스템의 폴더와 비슷해 보이지만, 모든 리소스가 그 안에 들어가거나 하위 Namespace를 만들 수 있는 계층형 폴더는 아니다. 각 namespaced 리소스는 정확히 하나의 Namespace에 속하고 Namespace끼리는 중첩되지 않는다.

```mermaid
flowchart TD
    C["한 Kubernetes 클러스터"] --> A["Namespace team-a"]
    C --> B["Namespace team-b"]
    C --> G["클러스터 범위 리소스<br/>Node와 PersistentVolume"]
    A --> A1["Deployment api"]
    A --> A2["Service api"]
    B --> B1["Deployment api"]
    B --> B2["Service api"]
    PA["RBAC와 정책"] -.-> A
    QA["ResourceQuota와 LimitRange"] -.-> A
```

그림의 두 Deployment는 모두 `api`라는 이름을 쓸 수 있다. 전체 주소가 `team-a`의 `Deployment/api`와 `team-b`의 `Deployment/api`로 다르기 때문이다. 반면 Node, Namespace, StorageClass와 PersistentVolume 같은 클러스터 범위 리소스에는 `metadata.namespace`를 붙이지 않는다. 설치된 CRD까지 포함한 실제 범위는 다음 명령으로 확인한다.

```bash
kubectl api-resources --namespaced=true
kubectl api-resources --namespaced=false
```

### Namespace를 쓰는 이유

| 용도 | Namespace가 제공하는 범위 | 함께 필요한 것 |
|---|---|---|
| 이름 충돌 방지 | 팀마다 같은 `Deployment/api`나 `Service/api` 이름을 사용할 수 있다. | 일관된 이름·label 규칙 |
| 작업 대상 구분 | `kubectl -n team-a ...`로 조회와 변경 대상을 좁힌다. | 올바른 cluster·context 확인 |
| 권한 위임 | RoleBinding으로 한 Namespace 안의 권한을 팀이나 ServiceAccount에 부여한다. | 최소 권한 RBAC |
| 정책 적용 | NetworkPolicy와 Pod Security Admission 같은 정책을 Namespace 단위로 연결할 수 있다. | [보안과 정책](08-security-and-policy.md)의 실제 정책 오브젝트와 이를 구현하는 구성 요소 |
| 자원 분배 | ResourceQuota로 Namespace 전체 사용량을, LimitRange로 개별 Pod·container의 기본값과 범위를 제한한다. | [스케줄링과 리소스](07-scheduling-and-autoscaling.md)의 request·limit와 용량 계획 |
| 서비스 발견 | Service DNS 이름에 Namespace가 포함된다. | [Service와 네트워킹](05-services-and-networking.md)의 교차 Namespace DNS 이름과 통신 정책 |

Namespace **자체만으로는 보안 경계를 완성하지 않는다.** 새 Namespace를 만들었다고 network traffic이 자동 차단되거나 CPU·memory가 자동 할당되고, 그 안의 모든 리소스가 팀 밖에서 보이지 않게 되는 것은 아니다. 실제 분리는 RBAC, NetworkPolicy, Pod Security Admission, ResourceQuota·LimitRange 등을 각각 설정해야 생긴다. 더 강한 장애·관리·보안 경계가 필요하면 별도 cluster나 계정 수준 분리도 비교해야 한다.

여러 팀이나 프로젝트가 한 클러스터를 공유해 서로 다른 권한·정책·quota가 필요할 때 Namespace가 유용하다. 같은 애플리케이션의 버전만 구분하려고 Namespace를 계속 늘리기보다는 label과 workload의 rollout 기능을 먼저 고려한다. 운영 workload는 실수로 `default`에 섞이지 않도록 목적이 드러나는 Namespace를 두는 편이 낫다. `kube-system`, `kube-public`, `kube-node-lease`는 시스템 용도가 있으므로 일반 workload에 사용하지 않고, 새 이름에 예약 접두사 `kube-`를 쓰지 않는다.

### 실행 예제: 두 Namespace에서 같은 이름 사용하기

아래 내용을 `namespace-demo.yaml`로 저장한다. Namespace는 클러스터 범위 오브젝트라 자체 `metadata.namespace`가 없고, 각 ConfigMap은 어느 Namespace에 속하는지 명시한다.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: namespace-demo-a
---
apiVersion: v1
kind: Namespace
metadata:
  name: namespace-demo-b
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: namespace-demo-a
data:
  environment: team-a
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: namespace-demo-b
data:
  environment: team-b
```

적용 전에는 현재 cluster와 context를 확인한다. 적용 뒤 같은 이름의 ConfigMap이 서로 다른 값을 갖는지 Namespace별 조회와 전체 조회로 비교한다.

```bash
kubectl config current-context
kubectl cluster-info
kubectl apply --dry-run=client -f namespace-demo.yaml
kubectl apply -f namespace-demo.yaml
kubectl get namespace namespace-demo-a namespace-demo-b
kubectl get configmap app-config -n namespace-demo-a -o jsonpath='{.data.environment}{"\n"}'
kubectl get configmap app-config -n namespace-demo-b -o jsonpath='{.data.environment}{"\n"}'
kubectl get configmap --all-namespaces --field-selector metadata.name=app-config
```

처음 실행할 때는 뒤의 ConfigMap이 참조할 Namespace도 같은 파일에서 만들어진다. 그래서 아직 존재하지 않는 Namespace까지 API server가 문서별로 검증해야 하는 server dry-run 대신, 이 예제의 전체 형태는 client dry-run으로 먼저 검사한다. Namespace를 실제로 만든 뒤에는 `kubectl apply --dry-run=server -f namespace-demo.yaml`로 admission 정책까지 다시 확인할 수 있다.

`-n`은 `--namespace`의 짧은 형태이며 **그 요청 하나**의 범위를 정한다. 반복 작업이라면 현재 kubeconfig context의 기본 Namespace를 설정할 수 있지만, 이후 `-n`을 생략한 명령의 대상이 조용히 바뀌므로 설정 직후와 변경 작업 직전에 다시 확인한다.

```bash
kubectl config set-context --current --namespace=namespace-demo-a
kubectl config view --minify -o jsonpath='{..namespace}{"\n"}'
```

매니페스트의 `metadata.namespace`, 명령의 `-n`, context의 기본 Namespace가 서로 다르면 어느 값이 실제 요청에 적용되는지 추측하지 말고 server dry-run과 `kubectl get ... -n <name>`으로 확인한다. GitOps에서는 재현성을 위해 namespaced 오브젝트의 `metadata.namespace`를 명시하고, 배포 도구가 별도로 강제하는 Namespace 규칙도 검토한다.

실습을 마치면 현재 context의 기본값을 `default`로 되돌린 뒤 두 Namespace를 지운다. **Namespace 삭제는 그 안의 리소스를 함께 제거하는 큰 작업**이므로, 운영 환경에서는 삭제 전에 `kubectl get all -n <name>`만 보지 말고 해당 Namespace의 ConfigMap, Secret, PVC, custom resource까지 inventory와 백업·보존 정책을 확인한다. `all`은 모든 종류를 뜻하지 않는다.

```bash
kubectl config set-context --current --namespace=default
kubectl delete namespace namespace-demo-a namespace-demo-b
```

삭제가 오래 `Terminating`에 머물면 finalizer를 바로 제거하기 전에 남은 API 리소스와 정리 controller의 상태를 확인한다. finalizer 강제 제거는 외부 자원이나 저장소 정리를 건너뛸 수 있다.

## 오브젝트를 연결하는 메타데이터

- **label**은 선택을 위한 짧고 안정적인 분류다. Service와 Deployment selector가 Pod label을 찾는다.
- **annotation**은 빌드 정보, 도구 설정처럼 선택에 쓰지 않는 부가 데이터다.
- **ownerReference**는 누가 이 오브젝트의 수명주기를 소유하는지 나타낸다. Deployment가 ReplicaSet을, ReplicaSet이 Pod를 소유한다.
- **finalizer**는 삭제 요청 뒤 정리 작업이 끝날 때까지 실제 제거를 지연한다.

```mermaid
flowchart TD
    D["Deployment<br/>label: app=web"] -->|"ownerReference"| R["ReplicaSet"]
    R -->|"ownerReference"| P1["Pod A<br/>app=web"]
    R -->|"ownerReference"| P2["Pod B<br/>app=web"]
    S["Service<br/>selector: app=web"] -.->|"label로 선택"| P1
    S -.->|"label로 선택"| P2
    N["Annotation<br/>build=2026-09-03"] -.-> D
```

소유 관계와 선택 관계를 혼동하면 안 된다. Service는 Pod를 선택하지만 소유하지는 않는다. Service를 지워도 Pod는 계속 실행된다.

## 선언형 적용이 일어나는 순서

```mermaid
sequenceDiagram
    participant K as kubectl
    participant A as API server
    participant M as Admission
    participant E as etcd
    participant C as Controller
    K->>A: apply object.yaml
    A->>A: 인증과 인가
    A->>M: 기본값·검증·정책
    M-->>A: 허용 또는 거부
    A->>E: 새 리소스 버전 저장
    A-->>K: 생성 또는 변경 결과
    C->>A: 변경 감시
    C->>A: 실제 상태를 spec에 맞춤
```

`kubectl apply`가 성공했다는 것은 API 오브젝트가 받아들여졌다는 뜻이다. 애플리케이션이 준비됐다는 뜻은 아니다. 그 다음 `kubectl rollout status`, condition, event를 확인해야 한다.

## 실행 예제: 안전한 작성·검증·적용 루프

아래 파일을 `object.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: object-demo
  labels:
    app.kubernetes.io/name: object-demo
  annotations:
    study.example/purpose: api-object-practice
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: object-demo
  template:
    metadata:
      labels:
        app.kubernetes.io/name: object-demo
    spec:
      containers:
        - name: web
          image: nginx:1.27-alpine
          ports:
            - name: http
              containerPort: 80
```

서버에 쓰기 전에 현재 API 계약으로 검사하고 diff를 본다.

```bash
kubectl explain deployment.spec.strategy
kubectl apply --dry-run=server -f object.yaml
kubectl diff -f object.yaml
kubectl apply -f object.yaml
kubectl get deployment object-demo -o yaml
kubectl get pods -l app.kubernetes.io/name=object-demo --show-labels
kubectl rollout status deployment/object-demo
```

`--dry-run=server`는 현재 API server의 기본값·검증·admission을 통과하는지 확인한다. 반면 로컬 검사만으로는 클러스터에 설치된 CRD나 admission 정책까지 알 수 없다.

실습이 끝나면 소유 관계를 본 뒤 정리한다.

```bash
kubectl get rs,pods -l app.kubernetes.io/name=object-demo \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,OWNER:.metadata.ownerReferences[0].kind
kubectl delete -f object.yaml
```

## create, apply, patch, edit의 선택 기준

| 방법 | 알맞은 상황 | 주의점 |
|---|---|---|
| `create` | 새 오브젝트를 한 번 만들 때 | 이미 있으면 실패한다. |
| `apply` | 파일·Git을 원하는 상태의 정본으로 둘 때 | 여러 field manager가 같은 필드를 소유하면 충돌할 수 있다. |
| `patch` | 자동화가 일부 필드만 바꿀 때 | 패치 종류와 배열 병합 의미를 알아야 한다. |
| `edit` | 긴급 확인이나 일회성 수정 | 재현 가능한 파일과 쉽게 어긋난다. |

서버 측 적용은 API server가 필드별 관리 주체를 추적한다. 충돌 메시지는 방해물이 아니라 “같은 필드를 둘 이상의 주체가 소유하려 한다”는 중요한 신호다. 무조건 강제하기 전에 어느 자동화가 정본인지 결정한다.

## 실패를 증상에서 원인으로 좁히기

| 증상 | 먼저 확인 | 흔한 원인 |
|---|---|---|
| `no matches for kind` | `kubectl api-resources`, `apiVersion` | API 버전 오타, 필요한 CRD 미설치 |
| `unknown field` | `kubectl explain`, server dry-run | 다른 버전의 필드 사용 |
| selector 관련 거부 | selector와 Pod template label | 두 값 불일치 또는 변경 불가 필드 수정 |
| 적용 성공, Pod 없음 | Deployment condition과 event | controller·quota·admission 문제 |
| Service endpoint 없음 | Service selector와 Pod label | 선택 관계 불일치, Pod NotReady |
| 삭제가 끝나지 않음 | `deletionTimestamp`, finalizers | 외부 정리 컨트롤러가 완료하지 못함 |

오브젝트가 예상과 다를 때는 먼저 “내가 보낸 spec”, “서버가 저장한 spec”, “status”를 분리해 비교한다. 기본값 적용이나 다른 controller의 수정 때문에 로컬 YAML과 저장 결과가 다를 수 있다.

## 스스로 설명해 보기

1. `kubectl apply` 성공과 애플리케이션 준비 완료는 왜 다른가?
2. Service가 선택한 Pod는 왜 Service의 자식이 아닌가?
3. 같은 이름으로 삭제 후 재생성한 Pod를 UID가 구분해야 하는 이유는 무엇인가?
4. field conflict를 무조건 강제로 덮으면 어떤 자동화 문제가 숨어 있을 수 있는가?
5. Namespace를 하나 만들기만 해서는 팀 사이의 network·권한·자원 격리가 완성되지 않는 이유는 무엇인가?
6. namespaced 리소스와 클러스터 범위 리소스를 현재 클러스터에서 어떻게 구분할 수 있는가?

[← 첫 클러스터](01-why-and-first-cluster.md) · [클러스터 아키텍처와 제어 루프 →](03-cluster-architecture.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/overview/kubernetes-api/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/kubernetes-objects/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/object-management/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/labels/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/overview/working-with-objects/owners-dependents/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/ | checked: 2026-09-04 -->
<!-- source: https://kubernetes.io/docs/tasks/administer-cluster/namespaces/ | checked: 2026-09-04 -->
<!-- source: https://kubernetes.io/docs/tutorials/cluster-management/namespaces-walkthrough/ | checked: 2026-09-04 -->
<!-- source: https://kubernetes.io/docs/concepts/security/multi-tenancy/ | checked: 2026-09-04 -->
<!-- source: https://kubernetes.io/docs/concepts/policy/resource-quotas/ | checked: 2026-09-04 -->
<!-- source: https://kubernetes.io/docs/concepts/policy/limit-range/ | checked: 2026-09-04 -->
