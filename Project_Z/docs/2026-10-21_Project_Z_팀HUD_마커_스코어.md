# Project_Z 팀 HUD·마커·스코어 구현 기록

작성일: 2026-10-21

## 구현 범위

- 전투 HUD 상단 중앙에 로컬 플레이어 팀과 A/B 팀 점수 표시
- 원격 플레이어 머리 위에 절대 팀명 `TEAM A` 또는 `TEAM B` 마커 표시
- 서버에서 적 팀 플레이어 처치 시 공격자 팀 점수 1 증가
- GameState의 A/B 팀 점수를 전체 클라이언트에 복제
- 자기 자신, 팀 미확정 대상은 마커를 표시하지 않음

## 표시 예시

```text
[TEAM A]  1 : 0  TEAM B
TEAM A
TEAM B
```

UI 레이아웃은 WBP가 담당하고 C++은 팀 판별, 점수 데이터 갱신, 표시 조건을 담당한다. C++에서 위젯 레이아웃을 생성하는 fallback은 사용하지 않는다.

## WBP 전환 규격

### WBP_TeamStatus

- 부모 클래스: `ZTeamStatusWidget`
- 필수 변수 이름:
  - `Border_Root` — Border, 선택 사항
  - `Text_TeamA` — TextBlock
  - `Text_Score` — TextBlock
  - `Text_TeamB` — TextBlock
- 세 TextBlock은 `Is Variable`을 활성화한다.
- 최상위 FPS HUD인 `WBP_FPS_HUD`에 `WBP_TeamStatus`를 자식으로 직접 배치한다.
- 자식 위젯 이름을 `TeamStatus`로 지정하고 `Is Variable`을 활성화한다.
- `UZHUDWidget`의 `BindWidgetOptional TeamStatus`와 자동 연결된다.
- 위치와 크기는 `WBP_FPS_HUD`에서 관리하며 권장값은 상단 중앙 `420 x 38`, Y=4다.

### WBP_PlayerTeamMarker

- 부모 클래스: `ZPlayerTeamMarkerWidget`
- 필수 변수 이름:
  - `Border_Team` — Border, 선택 사항
  - `Text_Team` — TextBlock
- `Text_Team`은 `Is Variable`을 활성화한다.
- `BP_ZCharacter_FPS` Class Defaults의 `Team Marker Widget Class`에 `WBP_PlayerTeamMarker`를 지정한다.
- 마커 위치는 `TeamMarkerHUDComponent`의 상대 Z=135에서 조정할 수 있다.

## 벽 가림 처리

- 마커는 Screen Space를 유지한다.
- 각 로컬 클라이언트에서 0.25초 간격으로 카메라와 대상 마커 사이를 검사한다.
- `WorldStatic` 또는 `WorldDynamic` 물체가 사이를 막으면 마커를 숨긴다.
- 벽을 벗어나 시야가 확보되면 같은 검사에서 다시 표시한다.

## 점수 규칙

- 적 팀 플레이어 처치: 공격자 팀 점수 +1
- 같은 팀 플레이어 처치: 점수 없음
- 공격자 확인 불가 또는 자살: 점수 없음
- 현재 아군 피해 자체는 차단하지 않는다.

## 주요 코드

- `Public/Multiplayer/ZTeamTypes.h`
- `Public/GameStates/Project_Z_MultiGameState.h`
- `Private/GameStates/Project_Z_MultiGameState.cpp`
- `Public/UI/ZTeamStatusWidget.h`
- `Private/UI/ZTeamStatusWidget.cpp`
- `Public/UI/ZPlayerTeamMarkerWidget.h`
- `Private/UI/ZPlayerTeamMarkerWidget.cpp`
- `Private/GameModes/Project_Z_MultiGameMode_Score.cpp`
- `Private/Characters/ZCharacter_FPS.cpp`
- `Private/Characters/ZCharacterBaseMulti.cpp`
- `Private/Projectiles/ZProjectileBase.cpp`

## 검증 상태

- UnrealHeaderTool: 성공
- Project_ZEditor Win64 Development 컴파일 및 링크: 성공
- `WBP_FPS_HUD`의 상단 팀 상태 HUD 표시: PIE 확인 완료
- 원격 플레이어 `TEAM A`/`TEAM B` 마커 표시 및 갱신: PIE 확인 완료
- 벽 뒤 마커 숨김 및 시야 확보 후 재표시: PIE 확인 완료
- 적 처치 점수의 호스트·게스트 동기화: 미검증
- 아군 처치 시 점수 제외: 미검증
- 사망·리스폰 후 팀 표시·마커·점수 유지: 미검증

### 런타임 연결 오류 및 해결

`WBP_FPS_HUD`에 `TeamStatus`를 정확히 배치했지만 실행 중 표시되지 않았다. 런타임 로그에서 실제 생성 클래스가 `WBP_TPS_HUD_C`임을 확인했다.

```text
[HUD] ... HUDClass = WBP_TPS_HUD_C
[TeamHUD] RootHUD=WBP_TPS_HUD_C_0 TeamStatus=None
```

`BP_Project_Z_MultiPlayerController`의 `HUDWidgetClass`를 `WBP_FPS_HUD`로 변경하여 해결했다. 위젯 이름이나 `Is Variable` 설정 문제는 아니었다.

## PIE 검증 순서

1. ~~에디터를 재실행하고 Listen Server 2인으로 실행한다.~~ 완료
2. ~~호스트와 게스트가 서로 다른 팀을 선택한다.~~ 완료
3. ~~각 화면 상단 정중앙에서 자기 팀과 `TEAM A 0 : 0 TEAM B`를 확인한다.~~ 완료
4. ~~상대 캐릭터 머리 위에 실제 소속에 맞는 `TEAM A` 또는 `TEAM B`가 표시되는지 확인한다.~~ 완료
5. 같은 팀 2인 테스트에서도 상대의 실제 팀명이 동일하게 표시되는지 확인한다.
6. 상대 팀을 처치하고 양쪽 화면의 점수가 동일하게 1 증가하는지 확인한다.
7. 같은 팀을 처치해도 점수가 증가하지 않는지 확인한다.
8. 사망·리스폰 후 팀 표시, 마커, 점수가 유지되는지 확인한다.
9. ~~상대가 벽 뒤로 이동하면 팀 마커가 숨고 다시 나오면 표시되는지 확인한다.~~ 완료

## 잔여 결정

- 아군 피해 허용 여부
- 마커 상시 표시 또는 거리·시야 조건 적용 여부
- 목표 점수와 승리/라운드 종료 조건
- C++ 임시 UI의 최종 WBP 디자인 교체
