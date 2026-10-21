# Project_Z 팀 선택 UI 작업 기록 및 다음 작업

작성일: 2026-10-20

대상 저장소: BenT8501/WorkSpace

최종 코드 확인 기준: `e8fda3b` (팀 선택 작업 중). 문서 작성 도중 추가된 원격 커밋까지 반영했다.

## 1. 이 기록을 읽는 기준

- 사용자가 코드를 직접 작성하며, 에이전트는 가이드와 검토를 담당한다.
- 이 기록 작성 시 소스, Blueprint, 맵을 수정하지 않았고 빌드·PIE 테스트도 실행하지 않았다.
- 최신 원격 코드에 UI 함수 본문이 추가됐지만, 마지막 안내와 다른 부분 및 미연결 항목이 남아 있다.
- **코드 확인**, **사용자 실행 확인**, **구현 안내 완료**를 구분한다. 안내 완료를 구현·검증 완료로 간주하지 않는다.
- 다음 작업자는 최신 사용자 코드부터 확인하고 이미 작성한 함수를 다시 만들지 않는다.

이 문서는 [10/19 팀 선택 가이드](2026-10-19_Project_Z_접속시_팀선택_작업가이드.md) 이후 변경된 결정과 진행 상황을 기록한다. 이전 가이드의 “A/B 클릭 즉시 요청”, “Blueprint 이벤트로 UI 동작 구현”, “팀 선택 전에도 무조건 팀별 시작점 검색”은 아래 결정으로 대체한다.

## 2. 확정한 UI 및 역할 분담

### 선택 흐름

1. 접속 시 팀 선택 화면을 연다.
2. A/B 버튼은 Widget의 임시 선택만 변경한다. 이때 서버에 요청하지 않는다.
3. 사용자는 입장 확정 전까지 A/B 선택을 변경할 수 있다.
4. 입장 버튼 클릭 시 Controller에 선택한 팀을 전달한다.
5. 서버가 승인하면 해당 접속 동안 팀을 유지한다. 사망·리스폰 후에도 변경하지 않는다.
6. 승인 후 스폰에 실패하면 팀은 유지하고 입장 재시도만 제공한다.
7. 로컬 PlayerState 팀과 FPS Pawn 준비를 확인한 뒤 전투 HUD로 전환한다.

### 클래스 책임

| 대상 | 책임 |
|---|---|
| WBP_TeamSelectionWidget | 배치, 크기, 스타일. 동작용 BP 변수·이벤트 그래프는 만들지 않는 방향 |
| UZTeamSelectionWidget | 임시 팀 선택, 버튼 바인딩, 색상, 활성화, 상태 메시지 |
| AProject_Z_MultiPlayerController | Widget 생성, 서버 RPC 요청, 결과 수신, 입장 준비 검사 및 HUD 전환 |
| AProject_Z_MultiGameMode | 팀 선택 검증·확정 및 팀별 스폰 |
| AProject_Z_MultiPlayerState | 확정 팀 저장·복제 |

## 3. 화면 구성 및 배치 기준

1920×1080 Designer 미리보기 기준이며 수치는 UMG 레이아웃 단위다.

```text
Canvas Panel
├─ Border_Background
└─ SizeBox_Main
   └─ VerticalBox_Main
      ├─ Text_Title
      ├─ Text_Description
      ├─ Spacer_Top
      ├─ HorizontalBox_Teams
      │  ├─ SizeBox_TeamA → Button_TeamA → 팀 A
      │  ├─ Spacer_Center
      │  └─ SizeBox_TeamB → Button_TeamB → 팀 B
      ├─ Spacer_Bottom
      ├─ SizeBox_Enter → Button_Enter → 입장
      ├─ Text_Status
      └─ SizeBox_Retry → Button_RetrySpawn → 입장 재시도
```

| 요소 | 설정 |
|---|---|
| 배경 | Anchors Min (0,0), Max (1,1), 네 Offset 0, ZOrder 0 |
| 중앙 SizeBox | Anchors Min/Max (0.5,0.5), Alignment (0.5,0.5), Position (0,0), Auto Size, Width Override 720, 높이 자동, ZOrder 1 |
| 제목/설명 | Font Size 36/18, 가운데 정렬, 설명 위 Padding 12 |
| 팀 영역 위 Spacer | 높이 32 |
| 팀 버튼 SizeBox | 각각 320×180, 가운데 간격 24 |
| 팀 버튼 텍스트 | Font Size 28, 가로·세로 가운데 |
| 입장 영역 위 Spacer | 높이 28 |
| 입장 버튼 SizeBox | 240×56, 가운데 정렬 |
| 상태 문구 | Font Size 16, 가운데 정렬, 위 Padding 16 |
| 재시도 버튼 SizeBox | 240×48, 가운데 정렬, 위 Padding 12 |
| 재시도 버튼 | 기본 Visibility Collapsed, 텍스트 크기 20 |

Anchors는 Canvas의 직접 자식에 설정한다. 그 아래는 각 부모 Slot의 Auto/Fill 및 정렬로 배치한다.

버튼과 Text_Status는 Is Variable을 체크하고 아래 BindWidget 이름과 일치시킨다. 버튼만 Collapsed로 두면 고정 높이 SizeBox의 공간은 남을 수 있으며, 이 여백 정리는 후속 UI 조정 사항이다.

## 4. Widget에서 안내한 작업

파일:

- `Source/Project_Z/Public/UI/ZTeamSelectionWidget.h`
- `Source/Project_Z/Private/UI/ZTeamSelectionWidget.cpp`

### 필요한 멤버와 함수

| 항목 | 준비/구현 방법 |
|---|---|
| Button_TeamA, Button_TeamB, Button_Enter, Button_RetrySpawn | `UPROPERTY(meta=(BindWidget)) TObjectPtr<UButton>` |
| Text_Status | `UPROPERTY(meta=(BindWidget)) TObjectPtr<UTextBlock>` |
| SelectedTeam | `EZPlayerTeam`, 기본값 None. Widget 로컬 임시 선택 |
| NativeOnInitialized | override. Super 호출 후 위젯 유효성 검사, 버튼 AddDynamic 바인딩 |
| HandleTeamAClicked / HandleTeamBClicked | UFUNCTION. SelectedTeam을 A/B로 변경한 뒤 표시 갱신 |
| HandleEnterClicked | UFUNCTION. 유효한 A/B 선택을 소유 MultiPlayerController의 RequestTeamSelection에 전달 |
| HandleRetrySpawnClicked | UFUNCTION. 소유 Controller의 RequestInitalSpawnRetry 호출 |
| UpdateTeamSelectionVisual | 일반 C++ 함수. 선택 색상 및 입장 버튼 활성화 갱신 |
| ApplySelectionState | 일반 C++ 함수. 메시지, 선택 가능 여부, 재시도 표시 갱신 |

`ApplySelectionState`의 기존 BlueprintImplementableEvent 지정은 제거하고 CPP에 본문을 작성하도록 안내했다. `_Implementation`을 붙이는 함수가 아니다.

```cpp
void ApplySelectionState(
    const FText& Message,
    bool bCanSelectTeam,
    bool bCanRetrySpawn);
```

NativeOnInitialized에서 SelectedTeam을 None으로 초기화하고 UpdateTeamSelectionVisual을 호출한다. 입장 버튼은 선택 전 비활성화하고 재시도 버튼은 Collapsed로 시작한다.

UpdateTeamSelectionVisual은 선택된 팀을 밝게 표시한다. SetBackgroundColor와 곱해지는 Button Style의 Normal/Hovered/Pressed Tint는 우선 흰색으로 통일하도록 안내했다.

### UI 상태 적용 규칙

| 상태 | bCanSelectTeam | bCanRetrySpawn |
|---|---|---|
| PlayerState 준비 중 | false | false |
| 선택 가능 | true | false |
| 요청 중/승인 후 입장 준비 중 | false | false |
| 승인 후 스폰 실패 | false | true |

ApplySelectionState에서는:

- Text_Status에 Message를 표시한다.
- A/B 버튼 활성 조건은 `bCanSelectTeam && !bCanRetrySpawn`이다.
- 입장 버튼은 위 조건에 더해 SelectedTeam이 유효한 A/B일 때 활성화한다.
- 재시도 버튼은 bCanRetrySpawn일 때만 Visible 및 활성화한다.
- 재시도 중에는 Controller가 false/false를 전달하여 중복 입력을 막아야 한다.

## 5. Controller에서 안내한 작업

파일:

- `Source/Project_Z/Public/Controllers/Project_Z_MultiPlayerController.h`
- `Source/Project_Z/Private/Controllers/Project_Z_MultiPlayerController.cpp`

### ShowTeamSelectionUI

1. IsLocalController 검사.
2. Widget이 없으면 TeamSelectionWidgetClass를 검사하고 CreateWidget 호출. Owning Player는 `this`.
3. 최초 생성 후 ApplySelectionState에 준비 메시지와 false/false 전달.
4. 이미 IsInViewport이면 재추가·입력 재설정 없이 종료.
5. AddToViewport(10), FInputModeUIOnly, Widget 포커스, 마우스 커서 표시.

Controller BP의 Class Defaults에서 TeamSelectionWidgetClass를 WBP_TeamSelectionWidget으로 지정한다.

**사용자 실행 확인:** 팀 선택 UI가 표시된다고 보고했다.

### 버튼이 작동하지 않았던 이유

초기 화면에 false/false를 적용했지만 PlayerState 준비 후 버튼을 활성화하는 RefreshInitialEntryState가 연결되지 않은 단계였다. 이 상태에서는 버튼 비활성화가 의도된 결과다.

### 마지막으로 안내한 작업: RefreshInitialEntryState / EnterGamePlayUI / BeginPlay / Tick

**상태: 구현 안내 완료. 최신 e8fda3b에서 함수 본문 추가를 확인했지만 조건 오류와 BeginPlay/Tick 미연결이 남아 있다. 7절을 먼저 확인한다.**

RefreshInitialEntryState 순서:

```text
로컬 Controller가 아니거나 최초 입장 완료 → 종료
ShowTeamSelectionUI 호출
Widget 생성 실패 → 종료
MultiPlayerState 없음 → 준비 메시지, false/false
팀 확정 + 소유 FPS Pawn 유효 + HasActorBegunPlay → EnterGamePlayUI
요청 중 → 요청 처리 메시지, false/false
팀 확정 또는 승인 응답 수신 → 저장된 메시지, false/재시도 허용 상태
그 외 → 선택 안내 또는 거절 메시지, true/false
```

준비 검사에서 Widget의 SelectedTeam을 초기화하지 않는다. Tick마다 위젯을 재생성하거나 포커스를 반복 설정하지 않는다.

EnterGamePlayUI 순서:

```text
로컬 여부/중복 진입 검사
bInitialEntryCompleted = true
요청 중 상태 및 재시도 허용 상태 해제
선택 Widget RemoveFromParent 후 참조 nullptr
FInputModeGameOnly / bShowMouseCursor = false
기존 CreateHUDWidget 호출
HUDWidget 유효하면 Visible
```

BeginPlay는 Super 호출 후 RefreshInitialEntryState를 호출하도록 안내했다. 기존 무조건 CreateHUDWidget 호출은 제거한다.

Tick은 Super 호출 후 로컬이고 최초 입장 완료 전인 동안만 RefreshInitialEntryState를 실행한다. 실제 Controller Tick 활성 상태를 확인해야 한다.

### 현재 코드 이름 주의

확인한 소스와 맞추기 위해 다음 이름을 사용했다. 후속 작업자는 이름을 추정해서 다른 변수를 추가하지 않는다.

| 현재 이름 | 의미 |
|---|---|
| RequestInitalSpawnRetry | 로컬 재시도 요청. Initial 철자와 다르지만 실제 선언 확인 필요 |
| EnterGamePlayUI | 전투 UI 전환 |
| bRequestPeding | 로컬 요청 처리 중 상태 |
| bInitialSpawnPedding | 서버 최초 스폰 대기 상태 |

기존 bIsReadySelectTeam/bIsReadyRequestTeamSelect/bIsFirstRequest와 새 상태가 함께 존재한다. 기존 요청 함수가 이전 변수만 검사하므로 이후 RPC 작업 시 상태 체계를 정리해야 한다. 단순히 변수만 추가하면 중복 요청 방지가 완성되지 않는다.

## 6. 팀 선택 전 시작점 오류와 안내한 수정

사용자가 보고한 메시지:

```text
Couldn't spawn player: Could not find a starting spot
```

발생 시점은 팀 선택 이전이었다. 접속 초기화에서도 시작점 조회가 필요하지만 기존 FindPlayerStart는 무조건 팀별 ChoosePlayerStart로 전달하여 팀 None에서 실패할 수 있었다.

안내한 수정 방향:

1. FindPlayerStart에서 팀 미확정 상태는 `Super::ChoosePlayerStart_Implementation(Player)`로 기본 시작점을 제공한다.
2. 팀이 확정되면 사용자 정의 `ChoosePlayerStart(Player)`로 팀별 검색을 수행한다.
3. HandleStartingNewPlayer와 RestartPlayer에서 팀 미선택 상태의 전투 Pawn 생성 차단은 유지한다.
4. RestartPlayer는 시작점을 직접 조회·검사하고 성공 시 RestartPlayerAtPlayerStart를 호출한다.
5. 검색 실패 시 기본 RestartPlayer가 이전 StartSpot으로 대신 스폰하는 경로를 사용하지 않는다.

시작점을 반환하는 것과 Pawn을 생성하는 것은 별개다. 초기화용 시작점을 제공하더라도 선택 전 전투 Pawn을 만들지 않는 정책은 유지한다.

**사용자 실행 확인:** 이 안내 이후 팀 선택 UI가 표시된다고 보고했다. 팀별 최초 스폰·리스폰 전체 검증까지 완료한 것은 아니다.

## 7. 최신 원격 코드에서 확인한 상태와 우선 수정 항목

문서 작성 시작 시 확인한 `9883cfd`에는 함수 골격만 있었지만, 업로드 도중 추가된 `e8fda3b`에서 다음 변경을 확인했다.

- Widget BindWidget, 클릭 바인딩, 선택·입장·재시도 및 표시 함수 본문이 추가됐다.
- ApplySelectionState가 일반 C++ 함수로 변경됐다.
- Controller의 ShowTeamSelectionUI, RefreshInitialEntryState, EnterGamePlayUI 본문이 추가됐다.
- BeginPlay는 ShowTeamSelectionUI를 호출한다. RefreshInitialEntryState 호출은 아직 없다.
- Tick은 Super 호출만 있으며 준비 검사 연결이 없다.
- FindPlayerStart에 팀 미선택 시 부모 기본 시작점 선택 경로가 추가됐다.
- 서버 선택·재시도 RPC 및 클라이언트 결과 RPC 본문이 비어 있다.

**다음 작업은 아래 오류 수정부터 진행한다. 소스는 이 문서 작업에서 수정하지 않았다.**

1. **RefreshInitialEntryState의 PlayerState 검사 반전:** 현재 `if (IsValid(PlayerState))`에서 준비 메시지를 띄우고 return한다. `if (!IsValid(PlayerState))`여야 한다. 현재 상태는 정상 PlayerState에서 계속 대기하고, 유효하지 않으면 아래 HasAssignedTeam 호출로 진행하여 잘못된 포인터 접근 위험이 있다. Tick 연결 전에 수정한다.
2. **UpdateTeamSelectionVisual의 B팀 색상 대상 오류:** 두 번째 SetBackgroundColor도 Button_TeamA와 bSelectedTeamA를 사용한다. 두 번째 줄은 Button_TeamB와 bSelectedTeamB를 사용해야 한다.
3. **준비 검사 호출 미연결:** 위 조건 오류 수정 후 BeginPlay와 Tick을 5절의 마지막 안내대로 연결한다.
4. **팀 승인 후 대기 분기 누락:** RefreshInitialEntryState에서 요청 중 검사 다음에 `bHasAssignedTeam || bTeamSelectionAccepted` 분기를 추가한다. 미추가 상태에서는 팀 승인 후 Pawn을 기다리는 동안 선택을 다시 허용할 수 있다. 해당 분기에서 선택 잠금 및 재시도 상태를 적용한다.
5. **RestartPlayer 경로:** 여전히 Super::RestartPlayer를 호출한다. 6절에서 안내한 직접 시작점 확인 후 RestartPlayerAtPlayerStart 경로는 아직 반영되지 않았다.

후속 코드 확인 시 다음도 점검한다.

1. TrySelectPlayerTeam의 Pawn 검사: `IsValid(Player->GetPawn())`일 때 거절해야 한다. 마지막 원격은 `!IsValid`라 정상적인 선택 대기를 거절한다.
2. ClientTeamSelectionResult는 Client RPC이고 CPP 본문은 `_Implementation`으로 작성한다. 일반 이름 본문과 중복 정의하지 않는다. 이전 LNK2005 해결 여부는 빌드 결과 미확인이다.
3. 서버가 승인한 후 스폰 실패 시 팀을 None으로 되돌리지 않는다.
4. 최초 입장 재시도와 사망 후 지연 리스폰을 구분한다.
5. ChoosePlayerStart의 잘못된 팀 값은 팀별 스폰 경로에서 명확히 실패 처리한다.
6. 기본 시작점 검색과 팀별 검색을 구분하는 6절 수정이 실제 반영됐는지 확인한다.

## 8. 현재 완료 판정

| 항목 | 상태 |
|---|---|
| C++ 동작 / BP 배치·스타일 분담 | 결정 완료 |
| A/B 임시 선택 후 입장 확정 방식 | 결정 완료 |
| UI 배치 수치 및 위젯 구조 | 안내 완료 |
| Widget BindWidget/바인딩/선택/입장/재시도/표시 함수 | 최신 코드에서 본문 확인. B팀 색상 대상 오류 수정 필요 |
| 팀 선택 화면 표시 | 사용자 확인 |
| 시작점 초기화 오류 대응 | 수정 안내 후 UI 표시 확인, 전체 스폰 검증 미완료 |
| 준비 상태 검사 및 버튼 활성화 | 본문 추가 확인. PlayerState 조건 반전, 승인 대기 분기 및 BeginPlay/Tick 연결 수정 필요 |
| 서버 팀 선택 승인·스폰 연결 | 다음 작업 |
| 서버 최초 스폰 재시도 연결 | 미완료 |
| 클라이언트 결과 처리 | 미완료 |
| 실제 입장 후 전투 HUD 전환 | EnterGamePlayUI 본문 확인, 실행 미확인 |
| 호스트/게스트 팀별 입장·리스폰 | 미검증 |

## 9. 다음 시작 지점

1. 7절의 최신 코드 오류를 먼저 수정한다. 특히 PlayerState 검사 반전 수정 전에 Tick에 준비 검사를 연결하지 않는다.
2. 준비 메시지가 “참여할 팀을 선택해 주세요.”로 바뀌고 A/B가 활성화되는지 확인한다.
3. A/B 선택 강조, 입장 버튼 활성화, 입장 전 선택 변경을 확인한다.
4. RequestTeamSelection에서 실제 사용 중인 요청 상태를 정리하고 중복 클릭을 차단한다.
5. ServerRequestTeamSelection에서 GameMode의 TrySelectPlayerTeam → 승인 후 RestartPlayer → 실제 Pawn 성공 여부 → ClientTeamSelectionResult를 연결한다.
6. ClientTeamSelectionResult에서 요청 상태 해제, 메시지, 승인 상태, 재시도 허용 여부를 갱신한다.
7. ServerRetryInitialSpawn과 로컬 재시도 흐름을 연결한다. 서버 최초 입장 대기 상태 및 간격 검사 필수.
8. 호스트/게스트 양쪽 입장, 거절, 실패 재시도, 사망 후 팀 유지 및 HUD 복귀를 검증한다.

UI가 보이는 것만으로 팀 선택 기능 전체가 완료된 것은 아니다. 다음 실제 작업은 **7절 오류 수정 → 준비 검사 연결 및 버튼 동작 확인 → 서버 요청 연결**이다.
