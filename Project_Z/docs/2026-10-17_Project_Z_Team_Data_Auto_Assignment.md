# Project_Z 팀 데이터 및 자동 배정 구현 기록

## 목적

Listen Server에서 서버가 팀을 자동 배정하고, 해당 팀 정보가 모든 클라이언트에 복제되는 최소 기반을 구성한다.

## 이번 작업 범위

- `EZPlayerTeam`: `None`, `TeamA`, `TeamB` 정의
- `AProject_Z_MultiPlayerState`: 플레이어별 팀의 저장 및 복제
- `AProject_Z_MultiGameState`: 복제된 `PlayerArray`를 기준으로 팀 인원 조회
- `AProject_Z_MultiGameMode`: 접속 시 인원이 적은 팀으로 서버 자동 배정

이번 단계에는 팀 UI, 진영별 외형, 아군 피해 차단, 팀별 PlayerStart 선택, 최대 6인 제한을 포함하지 않는다.

## 클래스 책임

| 클래스 | 책임 | 수명/접근 범위 |
|---|---|---|
| `AProject_Z_MultiGameMode` | 접속한 플레이어의 팀 결정 | 서버에만 존재 |
| `AProject_Z_MultiPlayerState` | 개별 플레이어의 팀 저장 및 복제 | Pawn 사망·리스폰 이후에도 유지 |
| `AProject_Z_MultiGameState` | 전체 `PlayerArray`에서 팀별 인원 조회 | 서버와 모든 클라이언트에 복제 |
| Pawn/Character | 팀 상태를 소유하지 않음 | 리스폰 시 교체되므로 저장소로 부적합 |

## 자동 배정 규칙

1. `PostLogin`은 서버에서 실행된다.
2. 현재 `TeamA`, `TeamB` 인원을 `GameState.PlayerArray`에서 계산한다.
3. 인원이 적은 팀에 신규 플레이어를 배정한다.
4. 인원이 같으면 `TeamA`에 배정한다.
5. 배정 결과는 `PlayerState.PlayerTeam`의 RepNotify를 통해 클라이언트에 전달된다.

예상 순서: 첫 번째 플레이어 A, 두 번째 B, 세 번째 A, 네 번째 B.

## 변경 파일

- `Source/Project_Z/Public/Multiplayer/ZTeamTypes.h`
- `Source/Project_Z/Public/PlayerStates/Project_Z_MultiPlayerState.h`
- `Source/Project_Z/Private/PlayerStates/Project_Z_MultiPlayerState.cpp`
- `Source/Project_Z/Public/GameStates/Project_Z_MultiGameState.h`
- `Source/Project_Z/Private/GameStates/Project_Z_MultiGameState.cpp`
- `Source/Project_Z/Public/GameModes/Project_Z_MultiGameMode.h`
- `Source/Project_Z/Private/GameModes/Project_Z_MultiGameMode.cpp`

## 검증 상태

- UnrealHeaderTool: 성공
- `Project_ZEditor Win64 Development` 컴파일 및 링크: 성공
- PIE 네트워크 런타임 검증: 미실시

## PIE 검증 절차

1. Unreal Editor를 재실행하거나 새 모듈이 로드된 상태인지 확인한다.
2. `BP_Project_Z_GameMode_MultiPlay`의 부모가 `Project_Z_MultiGameMode`인지 확인한다.
3. GameMode의 `Game State Class`와 `Player State Class`가 각각 새 멀티 클래스인지 확인한다.
4. Listen Server, 플레이어 2명으로 실행한다.
5. 서버 Output Log에서 `[Team] Assigned` 로그가 두 번 출력되고 Team A/B가 각각 한 명인지 확인한다.
6. 클라이언트 로그에서 각 PlayerState의 `[Team] Replicated` 로그와 A/B 값이 확인되는지 검사한다.
7. 플레이어 수를 3명으로 늘려 A/B/A 순서와 최종 인원 A=2, B=1을 확인한다.
8. 각 클라이언트에서 자신의 `PlayerState.GetPlayerTeam()` 값과 다른 플레이어의 값이 동일하게 보이는지 확인한다.

## 다음 작업

런타임 팀 복제를 확인한 뒤 팀 UI·최소 진영 표시를 연결한다. 그다음 `PlayerStart` 태그를 이용해 최초 스폰과 리스폰을 팀별로 분리한다.
