# Unreal FPS 멀티플레이 과제 상담 컨텍스트

## 상담 목적

Unreal Engine 멀티플레이 FPS 과제가 실제 직무 역량 향상과 파견 업무 적응에 얼마나 도움이 되는지 검토하고, 구현 범위와 학습 우선순위를 점검한다.

## 현재 과제 목표

Unreal Engine Replication을 활용해 최대 6명이 접속하는 2팀 FPS 팀전 프로토타입을 구현한다.

핵심 플레이 흐름:

```text
서버 실행
-> 최대 6명 접속
-> 2개 팀 배정
-> 이동 및 조준 동기화
-> 무기 발사
-> 서버 피격 판정 및 데미지 적용
-> 체력 동기화
-> 사망 및 팀 점수 반영
-> 팀별 리스폰
-> 회복 아이템 사용
```

## 확정된 범위

- 최대 6명, 2개 팀
- 캐릭터 1종
- 테스트 맵 1개
- Hitscan 총기 1종
- 서버 권한 기반 발사·피격·데미지
- 탄약 및 재장전 동기화
- 사망, Kill/Death, 팀 점수, 팀별 리스폰
- 머리·상체·팔·다리 부위별 데미지
- 회복 아이템 1종
- Collision Profile 및 Collision Channel
- Physics Asset 기반 피격 영역
- Physical Material
- 사망 시 제한적 Ragdoll
- GameMode, GameState, PlayerState, Character, Weapon, Component 역할 분리

## 제거 또는 후속 범위

- 플레이어 스킬 3종은 제거하고 회복 아이템으로 대체
- 경기 종료 UI, 점수판, Kill Feed
- Ping 및 Packet Loss 환경 테스트
- 재접속 예외 처리
- 방어구 및 무기 파츠
- 물리 기반 Projectile, 폭발 충격량, 이동식 물리 오브젝트
- Dedicated Server, 매치메이킹, 외부 백엔드
- Lag Compensation 및 치팅 방지

## 8주 일정

1. 멀티플레이 프로젝트, 최대 6명 접속, 2팀 배정, 팀별 Spawn Point
2. 1인칭 카메라, 로컬 팔 Mesh, 원격 전신 Mesh, 이동·회전, Collision과 Physics Asset
3. 체력 Replication, 이동 상태, 팀 정보, 접속·퇴장 상태
4. Hitscan 무기, Server RPC, Line Trace, Physics Asset·Physical Material 피격 검증
5. 데미지, 탄약, 발사 간격, 재장전, 발사 이펙트
6. 사망, Kill/Death, 팀 점수, 제한적 Ragdoll, 팀별 리스폰
7. 부위별 데미지와 배율 데이터
8. 회복 아이템, 사용 취소, 수량 동기화, 6인 팀전 통합 검증

## 직무 연결

이 과제를 통해 다음 업무를 연습할 수 있다.

- Unreal 클라이언트·게임플레이 프로그래밍
- Replication과 RPC 기반 멀티플레이 기능 구현
- 서버 권한 전투 및 상태 동기화
- 무기, 체력, 사망, 리스폰, 회복 아이템 구현
- Collision, Physics Asset, Ragdoll 설정
- 멀티플레이 버그 재현과 로그 분석
- 기존 Unreal 프로젝트의 특정 기능 수정 및 유지보수

## 현재 고민

1. 최대 6명 팀전, 물리, 부위별 데미지, 회복 아이템까지 8주 범위가 현실적인가?
2. 8주 안에 반드시 남겨야 할 핵심 기능과 줄여야 할 기능은 무엇인가?
3. 파견 업무에 가장 직접적으로 도움이 되는 구현 우선순위는 무엇인가?
4. 이 과제를 포트폴리오와 면접에서 어떻게 설명하면 좋은가?
5. 현재 구조에서 빠진 Unreal 멀티플레이 핵심 개념이나 위험 요소는 무엇인가?
6. 회복 아이템과 Ragdoll을 구현할 때 네트워크 처리상 주의할 점은 무엇인가?

## 다른 에이전트에게 요청할 답변 형식

- 먼저 가장 큰 위험 요소 3개
- 8주 일정의 현실성 평가
- 우선순위 조정안
- 직무 관점에서 얻는 역량
- 반드시 추가해야 할 검증 항목
- 범위를 줄여야 한다면 무엇을 제외할지
