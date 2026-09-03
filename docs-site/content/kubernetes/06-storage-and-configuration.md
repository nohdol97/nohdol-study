# 06. 스토리지와 애플리케이션 구성

> **목차 단계** — 컨테이너 이미지 밖의 설정과 데이터가 어떤 수명주기를 가져야 하는지 구분하는 장이다.

## 이 장을 마치면

- ephemeral volume과 persistent volume의 수명 차이를 설명한다.
- PV, PVC, StorageClass와 CSI가 동적 프로비저닝에서 맡는 역할을 연결한다.
- ConfigMap과 Secret을 환경 변수나 파일로 주입할 때의 갱신 차이를 안다.
- StatefulSet과 영속 스토리지를 함께 설계할 때 삭제·복구 경계를 판단한다.

## 목차

1. 컨테이너 파일시스템의 수명
2. Pod Volume과 emptyDir
3. PersistentVolume과 PersistentVolumeClaim
4. access mode, volume mode와 reclaim policy
5. StorageClass와 동적 프로비저닝
6. CSI와 스토리지 드라이버
7. volume snapshot, expansion과 cloning
8. ConfigMap: 비민감 구성 분리
9. Secret: 민감 데이터의 전달과 한계
10. 환경 변수와 volume mount의 갱신 방식
11. StatefulSet의 volumeClaimTemplates
12. 백업·복원과 애플리케이션 일관성

## 예정 실습

- emptyDir와 PVC의 Pod 재생성 후 데이터 차이 확인
- ConfigMap 변경이 환경 변수와 마운트 파일에 반영되는 방식 비교
- PVC 삭제와 PV reclaim policy 조합 실험
- Secret이 출력·로그·환경 변수로 노출되는 경로 점검

[전체 로드맵으로 돌아가기](00-roadmap.md)

<!-- source: https://kubernetes.io/ko/docs/concepts/storage/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/storage/volumes/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/storage/persistent-volumes/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/storage/storage-classes/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/configuration/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/configuration/configmap/ | checked: 2026-09-03 -->
<!-- source: https://kubernetes.io/ko/docs/concepts/configuration/secret/ | checked: 2026-09-03 -->
