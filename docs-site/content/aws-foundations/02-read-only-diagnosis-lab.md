# Read-only AWS 진단 실습

> 실습 등급: **Plan only에 준하는 read-only 조회**. AWS resource를 생성·변경하지 않지만 API 호출 권한과 credential이 필요하다. 출력의 account ID와 ARN은 공개 저장소에 복사하지 않는다.

## 준비

- AWS CLI가 설치되어 있다.
- root user가 아닌 학습용 role 또는 federated profile을 사용한다.
- profile과 region은 자신의 환경에 맞게 정한다.

```bash
export AWS_PROFILE="study-readonly"
export AWS_REGION="ap-northeast-2"
```

문서나 shell history에 access key를 직접 넣지 않는다. profile이 SSO나 temporary role session을 사용하도록 구성한다.

## 1. 현재 principal 확인

```bash
aws sts get-caller-identity
aws configure list
```

성공 기준은 기대한 account와 assumed role identity가 출력되는 것이다. 이 단계가 어긋나면 뒤의 resource 조회를 진행하지 않는다.

## 2. VPC와 route를 inventory로 만들기

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock,Default:IsDefault}' \
  --output table

aws ec2 describe-subnets \
  --query 'Subnets[].{SubnetId:SubnetId,VpcId:VpcId,AZ:AvailabilityZone,Cidr:CidrBlock,PublicIp:MapPublicIpOnLaunch}' \
  --output table

aws ec2 describe-route-tables \
  --query 'RouteTables[].{RouteTableId:RouteTableId,VpcId:VpcId,Associations:Associations[].SubnetId,Routes:Routes[].{Destination:DestinationCidrBlock,Gateway:GatewayId,Nat:NatGatewayId,State:State}}' \
  --output json
```

`MapPublicIpOnLaunch=true` 하나로 public reachability를 판정하지 않는다. subnet association, default route의 target, instance address, security group과 실제 listener가 추가로 필요하다.

```mermaid
flowchart TD
    A[caller identity 확인] --> B[VPC와 CIDR]
    B --> C[subnet과 AZ]
    C --> D[연결된 route table]
    D --> E[gateway·NAT·endpoint target]
    E --> F[security policy]
    F --> G[실제 reachability 관찰]
```

## 3. `AccessDenied`를 읽는 순서

권한이 없는 read-only profile이라면 일부 명령이 실패할 수 있다. 권한을 무작정 넓히지 말고 다음을 기록한다.

1. caller ARN과 account
2. 거부된 API action
3. 대상 resource 또는 scope
4. explicit deny 여부를 확인할 policy 계층
5. 실습에 필요한 최소 read action

IAM 변경이 필요하면 이 read-only 실습 범위를 벗어난다. 관리자에게 최소 action과 resource scope를 제안하고 별도 승인 흐름을 따른다.

## 4. 결과 표 만들기

| Subnet | AZ | CIDR | Default route | 분류가 아니라 근거 |
|---|---|---|---|---|
| 예시 값 | 예시 값 | 예시 값 | IGW/NAT/없음 | address·route·policy·listener 추가 확인 필요 |

account ID, 실제 resource ID와 내부 CIDR은 조직 정책에 따라 민감할 수 있으므로 공개 학습 기록에는 비식별화한다.

## 비용과 정리

이 장의 `sts`·`describe` 명령은 resource를 만들지 않는다. 다만 API 호출 기록은 CloudTrail 등 조직의 audit 경로에 남을 수 있다. export한 shell 변수는 terminal 종료 시 사라지며 별도 cloud cleanup은 없다.

## 스스로 설명해 보기

1. `get-caller-identity`를 첫 명령으로 두는 이유는 무엇인가?
2. subnet을 public 또는 private이라고 부르기 전에 어떤 증거를 모아야 하는가?
3. `AccessDenied` 해결을 위해 wildcard admin policy를 붙이지 않고 요청할 최소 정보는 무엇인가?

<!-- source: https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-route-tables.html | checked: 2026-09-03 -->
<!-- source: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html | checked: 2026-09-03 -->
