# 인프라 보안 로드맵

## 처음 보는 사람을 위한 출발점

프로그램이 데이터베이스에 접속할 수 있다고 해서 모든 데이터를 삭제할 권한까지 필요한 것은 아니다. 보안의 첫 질문은 “누구인가?”이고 두 번째 질문은 “무엇을 해도 되는가?”다. 여기에 비밀번호 같은 비밀 정보와 배포 파일이 바뀌지 않았다는 증거를 관리하는 일이 이어진다.

| 처음 만나는 말 | 학습용 쉬운 뜻 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| 신원(identity) | 요청을 보낸 사람이나 프로그램이 누구인지 나타내는 정보 | 권한을 적용하기 전에 요청한 사람·워크로드에 행위를 연결할 때 쓴다. **구체적인 상황(가상 예시):** 감사 기록에서 백그라운드 작업 두 개를 구분하지 못한다. → 각 워크로드에 추적 가능한 신원을 준다. → 기록이 실제 요청자를 식별하는지 확인한다. |
| 인증(authentication) | 주장한 신원이 맞는지 확인하는 과정 | 주장한 신원을 확정된 것으로 취급하기 전에 사칭을 걸러내기 위해 쓴다. **구체적인 상황(가상 예시):** 요청이 관리자라고 주장한다. → 신뢰하는 인증 절차로 자격 증명을 검증한다. → 권한 평가 전에 검증되지 않은 주장을 거부한다. |
| 인가(authorization) | 확인된 신원이 특정 작업을 해도 되는지 판단하는 과정 | 인증된 신원이라도 허용 범위를 벗어난 작업을 수행하지 못하게 한다. **구체적인 상황(가상 예시):** 로그인한 사용자가 다른 테넌트의 보고서를 요청한다. → 자원 범위의 권한을 평가한다. → 로그인 성공과 별개로 요청이 거부되는지 확인한다. |
| 정책(policy) | 어떤 조건에서 어떤 작업을 허용하거나 거부할지 적은 규칙 | 임시 예외에 의존하지 않고 접근 결정을 반복·검토할 수 있게 한다. **구체적인 상황(가상 예시):** 보고서를 소유 팀만 읽어야 한다. → 소유권과 허용 작업을 정책으로 표현한다. → 허용·금지 호출자를 모두 시험한다. |
| 비밀 정보(secret) | 노출되면 다른 사람이 권한을 사용할 수 있는 값 | 값을 가진 것만으로 특권 작업이 가능할 수 있어 접근을 제한해야 할 정보를 구분한다. **구체적인 상황(가상 예시):** 빌드 로그에 자격 증명이 실수로 담겼다. → 노출을 제한하고 승인된 절차로 해당 비밀을 교체한다. → 이전 자격 증명이 더 이상 작동하지 않는지 확인한다. |
| 산출물(artifact) | 배포할 container image나 package처럼 빌드 결과로 나온 파일 | 모호한 소스나 바뀔 수 있는 태그 대신 특정 빌드 결과를 배포·검증할 때 쓴다. **구체적인 상황(가상 예시):** 시험은 통과했는데 운영에는 다른 패키지가 전달됐다. → 승격 단계별 아티팩트 식별자를 비교한다. → 검토한 빌드를 배포하고 식별자를 확인한다. |

처음에는 읽기 한 작업만 허용하고 다른 작업은 실제로 거부되는지 확인한다. 이후 secret 교체와 image 검증을 같은 “누가 만들고, 누가 사용하며, 언제 폐기하는가”의 수명주기로 확장한다.

## 무엇을 해결하는가

보안은 배포 마지막의 scan 한 번이 아니다. identity가 어떤 권한으로 artifact와 secret을 받아 workload를 실행하고, 그 행위가 어떤 audit evidence로 남는지 수명주기 전체를 연결해야 한다.

```mermaid
flowchart LR
    I[human·workload identity] --> P[policy decision]
    P --> S[secret·key access]
    P --> A[artifact pull]
    A --> V[scan·signature verify]
    V --> D[deployment]
    S --> D
    D --> L[audit trail]
    P --> L
```

## 선수 지식

- AWS account·IAM·STS와 VPC boundary
- Kubernetes ServiceAccount·RBAC·Secret
- image registry와 CI/CD의 기본 흐름

## 학습 순서

1. **Identity·secret·artifact model**: least privilege와 trust boundary를 설계한다.
2. **Allow/deny 검증 실습**: 허용 동작과 명시적 거부를 모두 관찰하고 credential 수명주기를 추적한다.

## 완료

이 주제는 한 번 읽고 끝내지 않는다. 먼저 용어 표를 자신의 말로 바꾸고, 개념 장에서 한 요청의 흐름을 따라간다. 실습에서는 정상 상태를 먼저 기록한 뒤 조건 하나만 바꿔 실패를 만들고, 증거로 원인을 설명한 뒤 복구한다. 마지막으로 아래 운영 판단 질문에 답하면서 더 복잡한 환경으로 확장한다.

- human, CI와 workload identity를 분리한다.
- policy의 resource·action·condition을 설명하고 deny를 재현한다.
- secret rotation과 signed artifact 검증 실패 시의 차단 지점을 지정한다.

## 범위 밖

독립 Vault 운영, 모든 compliance framework와 penetration testing 과정은 포함하지 않는다.

## 처음 이해했는지 확인

1. authentication과 authorization은 각각 무엇을 확인하는가?
2. read 작업이 성공하는 것뿐 아니라 write가 거부되는 것도 시험해야 하는 이유는 무엇인가?

**확인 기준:** 인증은 누구인지, 인가는 그 신원이 무엇을 해도 되는지 확인한다. 허용과 거부를 함께 봐야 권한 경계가 예상보다 넓지 않음을 알 수 있다.

## 운영 판단으로 확장하기

1. private subnet만으로 workload가 안전하다고 결론 낼 수 없는 이유는 무엇인가?
2. image scan과 signature verification이 서로 대체되지 않는 이유는 무엇인가?
3. 짧은 수명의 credential도 과도한 권한이면 위험한 이유는 무엇인가?

<!-- source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html | checked: 2026-09-03 -->
<!-- source: https://slsa.dev/spec/v1.2/ | checked: 2026-09-03 | version: SLSA 1.2 -->
