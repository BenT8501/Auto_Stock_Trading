# Project_Z FPS HP HUD Blueprint 연결 가이드

- 갱신일: 2026-10-08
- 목표: TPS HUD의 디자인을 복제하여 내 HP를 화면 하단 중앙에, Enemy HP Bar의 디자인을 복제하여 상대 플레이어 HP를 머리 위에 표시한다.
- 구현 방식: 새 FPS 위젯의 HP 조회·표시와 생성은 Blueprint에서 연결한다. 이 HUD 기능을 위해 C++ 클래스를 추가 수정할 필요는 없다.
- 현재 확인: 사용자가 새 구조의 2인 이동·점프와 TestValue 로그를 확인했다. FPS HP HUD의 BP 연결·빌드·2인 HP 변화는 아직 검증하지 않았다.
- 에셋 주의: 작업 공간에서 기존 `WBP_TPS_HUD`와 Enemy HP Bar `.uasset`의 실제 계층·그래프는 확인할 수 없었다. 아래 이름은 에디터의 실제 에셋 이름에 맞춰 적용한다.
- 소스 상태: 앞선 작업에서 수정된 HUD 관련 C++ 파일은 사용자의 요청대로 그대로 두었다. BP 방식에서는 해당 C++의 새 HUD 자동 생성 기능을 사용하지 않는다.

## 1. 먼저 구분할 것

| 화면 요소 | 표시할 캐릭터 | 생성 위치 | HP 읽는 곳 |
|---|---|---|---|
| `WBP_FPS_HUD` | 내 캐릭터 | 각 로컬 FPS PlayerController | `Get Owning Player Pawn` → `GetCurrentHPValue` / `GetMaxHPValue` |
| `WBP_FPS_PlayerHPBar` | 위젯이 붙은 캐릭터 | 각 `BP_ZCharacter_FPS`의 Widget Component | 명시적으로 전달한 `ObservedCharacter` → 같은 두 getter |

캐릭터의 HP 원본은 `UZAttributeSet::HP/MaxHP`다. 두 위젯은 그 값을 **읽기만** 한다. 위젯에 복제용 HP 변수를 새로 만들거나, 클라이언트 BP에서 HP 값을 확정하지 않는다.

## 2. TPS HUD의 디자인을 FPS용으로 복제

1. Content Browser에서 실제 TPS HUD Widget Blueprint를 **Duplicate**하여 `WBP_FPS_HUD`를 만든다. 원본은 편집하지 않는다.
2. `WBP_FPS_HUD`의 **Class Settings → Parent Class**를 확인한다. 기존 TPS C++ 위젯 클래스(`UZHUDWidget`)에 묶여 있으면 FPS 복제본은 기본 `UserWidget`으로 부모를 변경해 BP에서 독립적으로 연결한다. 변경 후 Compile 오류가 나는 TPS 전용 부모 함수 호출은 복제본에서 정리한다.
3. 내부의 `StateHUD`가 별도 Widget Blueprint라면 **그 내부 위젯도 복제**하고 FPS용 복제본을 바깥 HUD에 넣는다. 바깥 HUD만 복제하고 원본 내부 위젯을 편집하면 TPS HUD도 함께 바뀔 수 있다.
4. FPS용 내부 상태 위젯도 TPS 전용 C++ 부모(`UZStateHUDWidget`)가 자동으로 상태를 갱신하는 구조라면, 기본 `UserWidget`으로 부모를 바꾼 뒤 아래 HP 조회를 BP에서 연결한다. 이름 `StateHUD`가 C++의 `BindWidgetOptional` 대상으로 남아 타입 충돌이 발생하면 FPS 복제본에서는 `FPSStateHUD`처럼 별도 이름으로 바꾼다.
5. 현재 필요한 HP 바와 텍스트만 남긴다. 탄약·무기 아이콘 등 TPS 전용 영역은 FPS 복제본에서 숨기거나 정리한다.
6. Canvas Slot의 **Anchor=하단 중앙**, **Alignment X=0.5**를 기준으로 HP 영역을 화면 중앙 하단에 놓는다. 정확한 간격과 폭은 2인 PIE 창 크기에서 조정한다.

### 화면 HUD의 HP 연결

FPS HUD 또는 복제한 FPS 상태 위젯에 `RefreshHP` 함수를 만든다.

| 순서 | BP 처리 |
|---|---|
| 1 | `Get Owning Player Pawn`을 `ZCharacterBase` 또는 `ZCharacterBaseMulti`로 Cast한다. |
| 2 | 유효하면 `GetCurrentHPValue`와 `GetMaxHPValue`를 읽는다. |
| 3 | `MaxHP > 0`일 때 `CurrentHP / MaxHP`를 계산하고 0~1로 제한하여 Progress Bar의 Percent에 넣는다. 그렇지 않으면 0을 넣는다. |
| 4 | 텍스트가 있으면 `현재 HP / 최대 HP`로 표시한다. Pawn을 아직 찾지 못했을 때는 값 변경을 건너뛴다. |

Widget이 생성된 첫 순간에는 Pawn이 없을 수 있다. 첫 조회만 하고 끝내지 말고, 초기 연결을 재시도하고 HP가 바뀔 때 갱신되도록 구성한다. 먼저 작동을 확인할 때는 위젯의 Tick 또는 짧은 갱신 타이머로 읽어도 된다. 이후 상태 변경 이벤트를 연결하면 반복 조회를 줄일 수 있다.

## 3. FPS PlayerController BP에서 화면 HUD 생성

1. 현재 FPS GameMode의 **Player Controller Class**가 가리키는 BP를 연다.
2. 그 Controller BP의 `Event BeginPlay`에서 `Parent: BeginPlay` 다음 **Is Local Controller**가 true일 때만 `Create Widget`을 호출한다.
3. **Class=`WBP_FPS_HUD`, Owning Player=Self**로 지정하고 반환된 위젯을 변수로 저장한 뒤 `Add to Viewport` 한다. 다시 BeginPlay가 불릴 가능성에 대비해 이미 만든 위젯이 있으면 중복 생성하지 않는다.
4. 앞서 추가된 C++ `FPS HUD Widget Class` 속성은 **비워 둔다**. 여기에 같은 BP를 지정하고 Event Graph에서도 생성하면 HUD가 두 개 표시된다.
5. Controller BP와 두 FPS HUD BP를 **Compile → Save**한다.

이 위젯은 로컬 화면마다 별도로 만들어진다. 상대 화면의 HUD는 상대 Controller가 생성한다.

## 4. Enemy HP Bar의 디자인을 플레이어용으로 복제

1. 기존 Enemy HP Bar Widget Blueprint를 **Duplicate**하여 `WBP_FPS_PlayerHPBar`를 만든다. Enemy 원본은 유지한다.
2. 복제본의 부모가 Enemy만 읽는 C++ 클래스 `UZEnemyHPBarWidget`이라면 **기본 `UserWidget`으로 부모를 변경**한다. 복제본에 남은 Enemy Cast, `SetObservedEnemy`, 부모 위젯의 이름 바인딩 등은 FPS용 HP 조회 흐름으로 교체한다.
3. 복제본에 `ObservedCharacter` 변수를 추가한다. 타입은 `ZCharacterBase` 또는 `ZCharacterBaseMulti` **Object Reference**로 지정한다.
4. HP 바와 텍스트의 모양은 기존 Enemy 디자인을 활용한다. 표시 값은 `ObservedCharacter`의 `GetCurrentHPValue` / `GetMaxHPValue`를 읽어 갱신한다. 비율 계산은 화면 HUD와 동일하다.
5. `ObservedCharacter`가 유효하지 않을 때는 `-- / --` 등 임시 표시로 두고, 참조가 연결된 뒤 값을 다시 갱신한다.
6. `ObservedCharacter → Is Locally Controlled`가 true라면 이 위젯의 Render Opacity를 0으로, false라면 1로 둔다. 자기 화면에서 자기 머리 위 HP를 숨기기 위한 로컬 표시 처리다. 최초 생성 시점에는 빙의가 늦을 수 있으므로 갱신 때마다 조건을 다시 확인한다.

## 5. `BP_ZCharacter_FPS`의 머리 위 Widget Component 연결

1. `BP_ZCharacter_FPS`의 **Components → Add → Widget**으로 `OverheadHP`를 만든다. Capsule Component 아래에 붙이고 Relative Z를 실제 모델의 머리보다 약간 높게 맞춘다.
2. **Widget Class=`WBP_FPS_PlayerHPBar`**, **Space=Screen**, **Draw at Desired Size=켜짐**, **Collision Enabled=No Collision**로 시작한다.
3. FPS 캐릭터 BP의 BeginPlay에서 `OverheadHP → Init Widget → Get User Widget Object`를 사용한다. 이를 `WBP_FPS_PlayerHPBar`로 Cast해 `ObservedCharacter=Self`를 전달한다. 위젯 생성이 아직 끝나지 않았다면 유효한 위젯을 얻을 때까지 초기 연결을 재시도한다.
4. FPS 캐릭터 BP와 플레이어 HP Bar BP를 **Compile → Save**한다.

`Screen` 공간의 머리 위 위젯은 벽 뒤에서도 보일 수 있다. 이번 단계는 위치와 HP 동기화를 확인하고, 벽 가림·최대 표시 거리·팀별 표시 여부는 전투 UI 정책을 정할 때 추가한다.

## 6. 2인 PIE에서 확인

| 시험 | 호스트 화면 | 게스트 화면 |
|---|---|---|
| 시작 | 하단에는 호스트 HP, 머리 위에는 게스트 HP | 하단에는 게스트 HP, 머리 위에는 호스트 HP |
| 자기 머리 위 표시 | 숨김 | 숨김 |
| 서버에서 호스트 HP 감소 | 하단 호스트 HP 감소 | 호스트 머리 위 HP 감소 |
| 서버에서 게스트 HP 감소 | 게스트 머리 위 HP 감소 | 하단 게스트 HP 감소 |

`TestValue` 테스트 키는 HP를 변경하지 않는다. HP 변화는 서버의 기존 피해 처리로 시험한다. `ReceiveEnemyDamage`는 BP에서 호출할 수 있지만 함수 내부에서 서버 권한을 확인하므로, 클라이언트가 직접 호출한 결과만으로 복제를 판단하지 않는다.

| 증상 | 확인할 위치 |
|---|---|
| HUD가 아예 없음 | 실제 GameMode의 PlayerController Class, 로컬 Controller의 BeginPlay, Create Widget의 Class·Owning Player |
| HUD가 두 개임 | `FPS HUD Widget Class` 지정과 BP `Create Widget` 중복 여부 |
| 내 HP가 비어 있음 | Owning Player Pawn 연결, FPS HUD 내부 BP의 부모 클래스·HP getter 연결 |
| 상대 머리 위에 `-- / --` | `ObservedCharacter=Self` 전달과 Widget Component의 Widget Class |
| 자기 머리 위 HP가 보임 | `ObservedCharacter`의 Is Locally Controlled 판정이 빙의 이후 다시 갱신되는지 |
| 한쪽 화면만 HP가 변경됨 | 서버 HP 변경 경로, AttributeSet의 HP·MaxHP 복제, 각 위젯이 서로 다른 캐릭터를 읽는지 |

## 7. 현재 완료 상태

- [x] 사용자 확인: 2인 이동·점프와 TestValue 로그
- [x] 소스 확인: HP getter와 `UZAttributeSet::HP/MaxHP` 복제 선언
- [ ] FPS HUD와 내부 상태 위젯 복제·BP 부모·HP 조회 연결
- [ ] FPS Controller BP의 로컬 HUD 생성
- [ ] 플레이어용 HP Bar 복제·BP 부모·관찰 캐릭터 연결
- [ ] FPS 캐릭터 Widget Component 연결
- [ ] BP Compile과 2인 시작 화면 확인
- [ ] 서버 피해 후 두 화면의 HP 숫자·바 일치 확인

이 단계가 끝나면 직무 과제 계획서의 실제 상태 동기화 확인을 마친 뒤 서버 발사·피격 연결로 진행한다.
