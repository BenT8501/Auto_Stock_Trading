# Project_Z 공통 캐릭터 분리 수정 가이드

- 갱신일: 2026-10-07
- 최신 확인: C:/WorkSpace/WorkSpace/Project/Project_Z/Source/Project_Z, HEAD 32254b5.
- 확인 파일: ZCharacterBase, ZCharacterBaseMulti, ZCharacter_TPS, ZCharacter_FPS 각각의 .h/.cpp.
- 이전 멤버 목록 대조 기준: d355bf2. 최신 파일에서 주석 처리된 원본은 이관 재료이며 실행되는 구현으로 세지 않는다.
- 작업 방식: 사용자가 직접 수정·빌드·테스트한다. 이 문서는 코드 본문 없이 파일명·함수명·변수명·처리 방향과 단계만 제공한다.
- 이번 작업은 소스 분석과 문서 갱신이다. 빌드·PIE·BP 연결을 실행하여 검증한 결과는 아니다.
- 이 문서는 이전의 “Aura·Melee·LevelUpChoice까지 TPS로 모두 보존”하는 안내를 대체한다.

## 1. 이번에 확정한 기능 범위

| 기능 | 플레이어 TPS/FPS | Enemy·공용 데이터 |
|---|---|---|
| Aura 능력·Aura 무기 | 사용하지 않음. 캐릭터와 무기 실행 경로에서 제외 | Enemy Aura는 유지 |
| Melee 무기·근접 공격 타입 | 두 시점 모두 사용하지 않음 | Enemy 공격이나 피격 반응까지 삭제하라는 요청은 아님 |
| Level/Experience | 유지. 경험치 누적·레벨 증가·최대 레벨·다음 경험치 필요 | 경험치 지급 경로 유지 |
| LevelUpChoice | 사용하지 않음. 선택 카드·선택 보상·선택 스택 제외 | 플레이어 연결을 끊되 공용 정의의 다른 사용자는 확인 |
| 원거리 무기·탄약·재장전 | 유지 | 기존 무기 데이터 재사용 |
| 원소 피해·무기 이펙트 | 별도 제거 지시가 없으므로 Aura 능력과 구분해 유지 검토 | EAuraElementType은 Enemy와 일반 원소 처리에도 사용 |
| 보물상자의 경험치·직접 회복 | 이번 지시만으로 제거하지 않음 | 선택창을 여는 경로만 제외. 대체 보상은 임의로 만들지 않음 |

LevelUpChoice를 없애는 것은 레벨업 자체를 없애는 일이 아니다. 레벨업 시 자동 능력치 상승은 아직 지정되지 않았다. 이번에는 기존의 경험치 차감·레벨 증가·다음 임계치 갱신만 보존하고 임의의 자동 업그레이드를 넣지 않는다.

EAuraElementType, E_AttachWeaponType의 Aura/Melee 항목, UZWeaponDataAsset의 공용 필드, AZAuraBase 클래스, Enemy의 Aura 에셋을 프로젝트 전체에서 삭제하지 않는다. 이번 범위는 플레이어의 사용 경로 제거다. 기존 BP/DataAsset이 참조할 수 있으므로 enum 항목을 삭제하거나 순서를 바꾸지 않는다.

## 2. 현재 소스에서 확인한 진행 상태

### 2-1. 현재 구조와 목표를 구분

| 클래스 | 실제 현재 부모 | 확인 내용 |
|---|---|---|
| AZCharacterBase | ACharacter, IAbilitySystemInterface | GAS 변수와 조회 선언을 남기는 정리 진행 |
| AZCharacterBaseMulti | ACharacter | 아직 Base를 상속하지 않음. FPS 입력·카메라와 테스트 RPC가 혼재 |
| AZCharacter_TPS | AZCharacterBaseMulti | 일부 변수·함수 선언만 이관 |
| AZCharacter_FPS | AZCharacterBaseMulti | 빈 생성자 외 별도 기능 없음 |

이 저장소에는 AZCharacterMulti라는 이름의 파일이 없다. 이전 문서의 AZCharacterMulti는 목표 이름이었다. 이번 단계별 명세는 실제 작업 파일인 AZCharacterBaseMulti를 중간 계층으로 표기한다. 먼저 AZCharacterBaseMulti의 부모를 AZCharacterBase로 연결한다. 클래스 이름까지 바꾸려면 별도의 리네임 단계로 진행하며, 여기서는 새 클래스를 하나 더 만들거나 리네임 완료로 간주하지 않는다.

이번 문서의 작업 관계: ACharacter → AZCharacterBase → AZCharacterBaseMulti → AZCharacter_TPS / AZCharacter_FPS.

### 2-2. 확인된 것과 미완료인 것

| 항목 | 상태 | 근거 |
|---|---|---|
| Base.h의 include 축소 | 부분 완료 | 활성 include는 CoreMinimal.h, GameFramework/Character.h, AbilitySystemInterface.h, ZCharacterBase.generated.h |
| Base의 전방 선언 | 반영 | UAbilitySystemComponent, UZAttributeSet |
| HP·Stamina getter 4개 cpp 이동 | 반영, 보완 필요 | GetCurrentHPValue, GetMaxHPValue, GetCurrentStaminaValue, GetMaxStaminaValue 정의 있음 |
| Base 생성·초기화 | 미완료 | 기존 Base.cpp의 44~3900행이 블록 주석. 생성자·BeginPlay 등 활성 정의 없음 |
| Base의 GAS 조회 계약 | 미완료 | GetAbilitySystemComponent, InitAbilityActorInfo 선언·구현이 주석 상태 |
| Base의 reflection 메타데이터 | 복원 필요 | 새 AbilitySystemComponent·AttributeSet 선언에 UPROPERTY 없음. getter 4개의 기존 UFUNCTION도 사라짐 |
| TPS 선언 분류 | 부분 완료 | 카메라·입력·원거리 무기·조준 변수와 일부 함수 선언 있음 |
| TPS 기능 구현 | 미완료 | TPS.cpp에는 빈 생성자만 있음 |
| FPS 기능 이관 | 미완료 | FPS.h/.cpp에는 생성자만 있고 입력·카메라는 부모에 남음 |
| RPC·TestValue | 기존 BaseMulti에 유지 | 현재 시점 전용 코드와 분리가 안 됨 |
| PrintTESTLog | 출력 복원 필요 | 값을 준비하지만 UE_LOG 호출이 없음 |
| 새 구조의 빌드·PIE | 미검증 | 이번 검토는 정적 소스 확인 |

이전 대화에서 성공한 2인 테스트와 TestValue 로그는 이전 구현 기준이다. 현재 주석 처리한 코드 상태까지 동작한다고 해석하면 안 된다. 코드상 선언·정의 불일치와 외부 호출 의존성이 있어 현재 상태를 빌드 완료로 표시할 수 없다.

### 2-3. 먼저 해결할 구체 항목

| 위치 | 이름 | 필요한 작업 |
|---|---|---|
| Base.h/.cpp | AZCharacterBase, BeginPlay | 선언과 활성 정의 일치, GAS 생성·연결 복원 |
| Base.h/.cpp | Tick, SetupPlayerInputComponent | 공통 구현이 없으면 선언 제거, 시점별 작업은 자식으로 |
| Base.h/.cpp | GetAbilitySystemComponent, InitAbilityActorInfo | 공통 계약 복원. 기존 TPS 능력 부여를 통째로 복원하지 않음 |
| Base.h | AbilitySystemComponent, AttributeSet | UPROPERTY 복원, 필요한 접근 범위 정리 |
| Base.cpp | HP·Stamina getter 4개 | 현재 무조건 역참조하므로 초기화 전 null 처리 복원 |
| BaseMulti.h | 직접 부모·부모 헤더 | AZCharacterBase와 Characters/ZCharacterBase.h로 연결 |
| TPS.h | UIInputAction, UIInputMappingCont1t | 잘못된 전방 선언 이름. UInputAction, UInputMappingContext로 정리 |
| TPS.h | FPlayableCharacterRow | 기존 실제 타입은 FZPlayableCharacterRow. 아직 안 쓰면 전방 선언 제거 |
| TPS.h/.cpp | RefreshCharacterAnimation | 현재 선언에는 const, 원본 정의에는 없음. 원본이 몽타주·무기 상태를 변경하므로 원본의 비const 계약 유지 |
| TPS.h | Reload, FinishReload 등 외부 호출 함수 | 현재 protected 구역에 있음. C++ Controller·AnimNotify가 호출하는 함수는 public 계약 필요 |
| TPS.h | FTimerHandle | 정의 헤더를 직접 포함. TimerManager.h 의존성 확인 |
| TPS.h | bCameraRotateHeld, MoveByInput, OnAbilityInputPressed 등 | 원본 유지 기능인데 아직 누락. 전체 목록 기준으로 선언·멤버 보충 |
| BaseMulti.cpp | PrintTESTLog | 실제 로그 출력 복원. 과거 Ow nerController 오타는 현재 출력 블록 제거로 존재하지 않음 |
| BaseMulti.cpp | DeficatedServer | 로그 문자열 DedicatedServer로 정리 |

TObjectPtr라는 타입만으로 UPROPERTY 역할이 대신되는 것은 아니다. 이 문서에서는 원래 GAS 멤버의 reflection 선언을 복원하고, 생성·참조 경로를 하나로 유지하는 방향이다.

## 3. 앞으로의 목적지 기준

| 책임 | 목적지 | 이번 결정 |
|---|---|---|
| 공통 GAS/Attribute 조회 | AZCharacterBase | 시점·무기·성장 선택 UI를 모르는 최소 부모 |
| 네트워크 설정, TestValue/RPC | AZCharacterBaseMulti | 카메라·Input Action을 제거한 공통 계층 |
| 공통 Level/Experience·상태 | AZCharacterBaseMulti | TPS/FPS가 같은 상태를 사용. 서버에서 변경하고 필요한 상태 복제 |
| 사망 여부·HP 변경 진입 | AZCharacterBaseMulti | 연출·TPS 피해 배율·GameMode 정책을 분리해서 이관 |
| TPS 카메라·조준·입력·커버 | AZCharacter_TPS | 원본에서 필요한 부분만 복원 |
| FPS 카메라·입력·팔 | AZCharacter_FPS와 BP | 기존 BaseMulti에서 이동 |
| 기존 원거리 무기 구현 | 우선 AZCharacter_TPS | Aura/Melee 분기 제거 후 복원. 후속 단계에서 FPS와 공유할 무기 규칙 추출 |
| Attribute 값·OnRep | UZAttributeSet | 원래 소유자에 유지 |
| Enemy Aura | AZEnemyBase 및 기존 지원 클래스 | 유지, 플레이어 기능 제거와 함께 삭제하지 않음 |
| 선택 UI·선택 스택·선택 보상 | 플레이어 이관 제외 | 호출자도 함께 해제 |

BaseMulti가 서버에서만 존재하는 것은 아니다. 서버와 클라이언트에서 같은 상속 계층을 사용한다. 서버 판정과 로컬 입력·표현을 분리한다.

레벨은 우선 캐릭터 생애 동안의 상태로 분류한다. 리스폰 후에도 유지해야 한다면 최종 저장소는 PlayerState로 옮기고 캐릭터는 조회·전달 역할로 줄여야 한다. 이 정책은 아직 확인되지 않았으므로 영속 레벨이라고 가정하지 않는다.

## 4. 이번 범위로 바꾸는 헤더·include

### 4-1. 플레이어 헤더에서 남기거나 내려보낼 이름

| 파일·타입 | 목적지·처리 |
|---|---|
| CoreMinimal.h, GameFramework/Character.h, AbilitySystemInterface.h, ZCharacterBase.generated.h | Base.h 유지 |
| UAbilitySystemComponent, UZAttributeSet | Base.h 전방 선언 유지 |
| AbilitySystemComponent.h, AttributeSets/UZAttributeSet.h | 실제 멤버 접근하는 cpp에 포함 |
| Characters/ZCharacterBase.h, ZCharacterBaseMulti.generated.h | BaseMulti.h의 직접 부모·자기 generated 헤더 |
| Characters/ZCharacterBaseMulti.h | TPS.h와 FPS.h의 직접 부모 |
| ZCharacter_TPS.generated.h, ZCharacter_FPS.generated.h | 각각 자기 헤더의 마지막 include |
| Data/ZCharacterData.h | TPS 데이터·무기 enum 사용처에 유지. 공용 enum 정의는 삭제하지 않음 |
| Data/ZCharacterDataAsset.h | TPS.cpp의 실제 데이터 접근 |
| Data/ZPlayableCharacterData.h | TPS.cpp, 헤더는 필요한 일반 참조 선언에 FZPlayableCharacterRow |
| Data/ZLevelUpBalanceData.h | BaseMulti.cpp의 레벨 밸런스 접근. FZLevelUpBalanceRow 일반 선언은 전방 선언 검토 |
| Abilities/Project_Z_AbilityInputID.h | TPS 능력 입력. Base에는 불필요 |
| UI/ZLevelUpChoice.h | 플레이어 캐릭터 헤더에서 이관 제외. 기존 Controller·UI 잔여 참조는 따로 정리 |
| Containers/Map.h | LevelUpChoiceStacks를 없애면 현재 TPS.h의 직접 사용 없음. 다른 TMap이 추가되지 않았다면 제거 |
| InputActionValue.h, InputAction.h, InputMappingContext.h | TPS/FPS.cpp. 헤더는 FInputActionValue, UInputAction, UInputMappingContext 전방 선언 |
| EnhancedInputComponent.h, EnhancedInputSubsystems.h, Engine/LocalPlayer.h | TPS/FPS.cpp |
| Engine/DataTable.h | TPS.cpp 또는 BaseMulti.cpp의 실제 테이블 접근. UDataTable 포인터 선언은 전방 선언 |
| Abilities/GameplayAbility.h, GameplayEffect.h | 초기 능력·효과 구현 cpp. 선언에는 UGameplayAbility, UGameplayEffect |
| TimerManager.h | TPS의 SecondaryFireTimerHandle과 반복 발사에 필요한 정의 |
| Net/UnrealNetwork.h | BaseMulti.cpp의 직접 복제 등록 |
| Auras/ZAuraBase.h, AZAuraBase 전방 선언 | 플레이어에서 제외. Enemy·기존 공용 구현의 include는 유지 |
| UTexture2D, Engine/Texture2D.h | 선택 카드·Aura 아이콘 제거 후 플레이어의 잔여 사용이 없으면 제외 |
| Data/ZElementStatusBalanceData.h | 선택 설명 함수만을 위해서는 제외. GetZElementColor 등 일반 원소 처리가 남으면 해당 cpp에 유지 |
| NiagaraComponent.h, NiagaraSystem.h | Enemy와 일반 원거리 이펙트에 필요할 수 있어 일괄 제거 금지 |
| Engine/OverlapResult.h, CollisionShape.h, Combat/ZDamageableInterface.h | Melee 구현을 빼고 남은 직접 사용 여부로 판단. 단어만 보고 프로젝트 전체 제거 금지 |

### 4-2. 시점별 cpp와 공용 파일의 나머지 include

- TPS.cpp: 자기 헤더, Camera/CameraComponent.h, GameFramework/SpringArmComponent.h, Components/DecalComponent.h, Animation/AnimInstance.h, Components/SkeletalMeshComponent.h, Components/StaticMeshComponent.h.
- FPS.cpp: 자기 헤더, Camera/CameraComponent.h, Math/RotationMatrix.h, GameFramework/Controller.h, GameFramework/PlayerController.h, 로컬 입력 관련 헤더.
- BaseMulti.cpp: 자기 헤더, AbilitySystemComponent.h, AttributeSets/UZAttributeSet.h, Net/UnrealNetwork.h, 레벨 밸런스·DataTable 정의.
- TPS 원거리 구현 cpp: Data/ZWeaponDataAsset.h, Projectiles/ZProjectileBase.h, Pooling/ZActorPoolSubsystem.h, Pickups/ItemWeapon.h, 필요한 Engine/World.h·Engine/EngineTypes.h.
- TPS 표현·정책 cpp: Controllers/Project_Z_PlayerController.h, Feedback/ZFloatingTextActor.h, GameModes/Project_Z_GameMode.h는 그 책임을 분리한 위치에 둔다. Base에 올리지 않는다.
- 이동 설정을 직접 다루는 cpp: GameFramework/CharacterMovementComponent.h.
- 자동 타깃을 유지하는 TPS.cpp: Enemies/ZEnemyBase.h, EngineUtils.h. 자동 공격까지 제외하라는 요청은 아직 없음.
- 메타 성장을 유지하는 TPS.cpp: MetaProgression/ZMetaProgressionSubsystem.h. 일반 레벨업과 선택 보상과 구분.
- DrawDebugHelpers.h는 실제 디버그 호출이 없으면 제거 후보.
- 원소 색상·Niagara 에셋 경로에 Aura라는 문자열이 있어도 공격 Aura 기능과 동일하다고 간주하지 않는다.

include 제거는 그 타입을 사용하는 선언·구현을 이동한 뒤 진행한다. Blueprint에 노출된 타입과 값 멤버에는 정의가 필요할 수 있다. 원래 공유된 DataAsset·Struct를 새 클래스에 복사하지 않는다.

## 5. 함수·변수별 전체 작업 목록

현재 상태 표기: Base, BaseMulti, _TPS, _FPS는 각 ZCharacter 클래스의 약칭이다. “선언만”은 구현 완료가 아니며, “이전 Base에 주석/미이관”은 활성 구현으로 복원되지 않았다는 뜻이다.
### 5-1. 기존 Base 함수 전체 판정

원본은 d355bf2의 활성 멤버 목록, 진행 표시는 32254b5의 주석을 제외한 선언·정의 비교다. 아래의 TPS 목적지는 1차 원거리 구현 복구 위치이며, FPS 무기 구현 완료를 뜻하지 않는다.

| 함수명 | 현재 상태 | 이번 목적지·처리 |
|---|---|---|
| AZCharacterBase | Base 선언만 | Base — 공통 GAS/조회 복원 |
| GetCurrentLevelValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetMaxLevelValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetCurrentExperienceValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetNextLevelUpExperienceValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetPickupRadiusValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetMetaExperienceGainMultiplierValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetMoveSpeedBonusValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetProjectileDamageBonusValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetProjectileCooldownReductionValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetAuraRadiusBonusValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetAuraDamageBonusValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetAuraTickIntervalReductionValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetRuntimeAuraElementType | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetRuntimeWeaponElementType | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetMeleeDamageBonusValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외. 관련 호출도 제거 |
| GetMeleeRangeBonusValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외. 관련 호출도 제거 |
| GetLevelUpChoiceOfferCountValue | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetDamageTakenMultiplierValue | 이전 Base에 주석/미이관 | BaseMulti — 공통 피해 배율 조회 |
| GetCurrentHPValue | Base 선언·정의 | Base — 공통 GAS/조회 복원 |
| GetMaxHPValue | Base 선언·정의 | Base — 공통 GAS/조회 복원 |
| GetCurrentStaminaValue | Base 선언·정의 | Base — 공통 GAS/조회 복원 |
| GetMaxStaminaValue | Base 선언·정의 | Base — 공통 GAS/조회 복원 |
| IsPlayerDead | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태 |
| GetChoiceStackCount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetActiveWeaponType | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponBaseDamageValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponCooldownValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponRangeValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponProjectileSpeedValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponProjectileCountValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponPierceCountValue | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveWeaponMeleeRangeValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외. 관련 호출도 제거 |
| GetActiveWeaponAuraRadiusValue | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetActiveWeaponAnimationType | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| IsAuraEquipped | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetAimYawOffsetValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetMaxAimYawOffsetValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetAimPitchOffsetValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetMaxAimPitchOffsetValue | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetIsInCover | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| SetCanCover | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| SetCoverMoveDirection | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetCanCover | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| SetCanPickUp | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetCanPickUp | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| SetPickupItemData | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetMaxAmmo | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetDefultAmmo | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetCurrentAmmo | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| SetCurrentAmmo | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| ItemPickUp | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| Reload | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| FinishReload | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| BeginPlay | Base 선언만, BaseMulti 선언·정의 | 분할 — GAS는 Base, 입력·시점은 TPS/FPS; Aura·Melee 처리 제외 |
| Tick | Base 선언만, BaseMulti 선언·정의 | 분할 — GAS는 Base, 입력·시점은 TPS/FPS; Aura·Melee 처리 제외 |
| SetupPlayerInputComponent | Base 선언만, BaseMulti 선언·정의 | 분할 — GAS는 Base, 입력·시점은 TPS/FPS; Aura·Melee 처리 제외 |
| EnterCover | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| ExitCover | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| GetCoverMoveAxis | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| ApplyCharacterData | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| ApplyCharacterDataAsset | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ActivatePrimaryWeapon | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| FirePrimaryProjectile | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| FireSecondaryProjectile | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| ActivatePrimaryMelee | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외. 관련 호출도 제거 |
| ActivatePrimaryAura | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| AddExperience | _TPS 선언만 | BaseMulti — 공통 레벨/상태 |
| RestoreHPPercent | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경과 자식 표현·GameMode 분리 |
| OpenTreasureRewardSelection | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| ReceiveEnemyDamage | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경과 자식 표현·GameMode 분리 |
| ApplyLevelUpChoice | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| ReapplyMetaProgressionBonuses | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ApplyPlayableCharacterSelection | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ApplyLevelUpChoiceData | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| ConfigureTPSCameraMode | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| MoveByInput | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| EquipWeaponFromPickup | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ToggleRunningMove | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetAbilitySystemComponent | 이전 Base에 주석/미이관 | Base — 공통 GAS/조회 복원 |
| InitAbilityActorInfo | 이전 Base에 주석/미이관 | Base — 공통 GAS/조회 복원; TPS 능력 부여는 분리 |
| ApplyResolvedCharacterData | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ApplyMetaProgressionBonuses | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| ApplyLevelUpBalanceData | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 레벨 필드만 사용 |
| GetLevelUpBalanceRow | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 레벨 필드만 사용 |
| ResolveAnimationSetForWeapon | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| RefreshCharacterAnimation | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| PlayEquipAnimation | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| PlayDeathAnimation | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| PlayReloadAnimation | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| ConfigureQuarterViewCamera | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| SyncCameraRotationToCharacter | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| Move | BaseMulti 선언·정의, _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| Look | BaseMulti 선언·정의, _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| StartCameraRotate | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| StopCameraRotate | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| OnAbilityInputPressed | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| StartSecondaryFire | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| StopSecondaryFire | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| HandleSecondaryAutoFire | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| UpdateAutoPrimaryAttack | 이전 Base에 주석/미이관 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| FindNearestAutoAttackTarget | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| FaceAutoAttackTarget | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| UpdateMouseAim | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetMouseAimWorldPoint | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| RefreshMouseAimIndicator | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| RefreshWeaponState | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| RefreshCrosshairVisibility | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| EquipWeaponVisual | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| UnequipWeaponVisual | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| RefreshWeaponElementEffect | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| PlayAttackAnimation | _TPS 선언만 | TPS — 제외 기능 분기를 제거한 뒤 구현 이관 |
| UpdateCharacterFacingFromAim | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetProjectileAimPoint | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetAimDirection | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetProjectileSpawnLocation | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| HandleLevelUpIfNeeded | _TPS 선언만 | BaseMulti — 공통 레벨/상태; 선택 UI 없이 증가 처리 |
| BuildLevelUpChoices | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| BuildTreasureRewardChoices | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| BuildLevelUpChoicesFromTable | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| DoesLevelUpChoiceRowPass | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| BuildChoiceDataFromRow | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| SelectLevelUpChoiceOffer | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetLevelUpChoiceOfferCount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetEffectiveWeaponCooldown | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| BuildChoiceData | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| BuildWeaponChoiceData | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| AddWeaponChoiceIfNotCurrent | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetActiveWeaponData | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| GetActiveAuraData | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| LoadWeaponDataByPath | _TPS 선언만 | TPS — 선언·구현 함께 이관 |
| ApplyAuraElementChoice | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| ApplyWeaponElementChoice | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |
| GetActiveAuraElementType | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetActiveWeaponElementType | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| ResolveWeaponElementEffect | 이전 Base에 주석/미이관 | TPS — 선언·구현 함께 이관 |
| ResolveAuraNiagaraSystem | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| ResolveAuraNiagaraSystems | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| ResolveAuraSymbolTexture | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetDefaultAuraNiagaraSystemPath | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetDefaultAuraSymbolTexturePath | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외. 관련 호출도 제거 |
| GetDefaultAuraElementColor | 이전 Base에 주석/미이관 | TPS 원거리 원소 색상 보조 유지 — Aura라는 이름으로 삭제 금지; 이후 중립 이름 검토 |
| AddChoiceStack | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외. 관련 호출도 제거 |

### 5-2. 기존 Base 변수 전체 판정

| 변수명 | 현재 상태 | 이번 목적지·처리 |
|---|---|---|
| CameraBoom | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| FollowCamera | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimIndicatorComponent | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| DefaultIMC | BaseMulti 활성 | TPS — 전용 IMC; BaseMulti의 동명 FPS IMC는 FPS로 이동 |
| IA_Move | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| IA_Look | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| IA_CameraRotate | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| IA_Jump | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| IA_Ability_Primary | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| IA_Ability_Secondary | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| CharacterDataTable | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| CharacterDataAsset | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| CurrentData | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| bIsInCover | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| CoverMoveAxis | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| CoverMoveDirection | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AbilitySystemComponent | Base 활성 | Base — UPROPERTY·생성 경로 복원 |
| AttributeSet | Base 활성 | Base — UPROPERTY·생성 경로 복원 |
| bIsPlayerDead | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| DefaultAbilities | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| DefaultEffects | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| DeathMontage | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| ActivePrimaryAura | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| EquippedWeaponMeshComponent | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| EquippedStaticWeaponMeshComponent | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectComponent | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectAsset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementTypeParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementColorParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementIntensityParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectScaleParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementSynergyActiveParameterName | _TPS 활성 | 이관 제외 — 플레이어 Aura 시너지 제외; 잔여 참조 제거 |
| WeaponElementLengthParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementRadiusParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementBoxSizeParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementAxisParameterName | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementVisualIntensity | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectLocationOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectRotationOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| WeaponElementEffectScale | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| CurrentExperience | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| CurrentLevel | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| MaxLevel | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| NextLevelUpExperience | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| LevelUpExperienceStep | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| PickupRadius | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| MetaExperienceGainMultiplier | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| MoveSpeedUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 업그레이드 수치 제외; 잔여 참조 제거 |
| ProjectileDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 업그레이드 수치 제외; 잔여 참조 제거 |
| ProjectileCooldownReductionUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 업그레이드 수치 제외; 잔여 참조 제거 |
| MinProjectileCooldown | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| AuraRadiusUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| AuraDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| AuraTickIntervalReductionUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| MinAuraTickInterval | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| MeleeDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| MeleeRangeUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| TreasureProjectileDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| TreasureProjectileSpeedUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| TreasureMeleeDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| TreasureMeleeRangeUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| TreasureAuraDamageUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| TreasureAuraRadiusUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| TreasureMoveSpeedUpgradeAmount | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| TreasureHealPercent | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| TreasureDamageTakenReduction | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| LevelUpBalanceTable | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| LevelUpChoiceTable | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| LevelUpBalanceRowName | 이전 Base에 주석/미이관 | BaseMulti — 공통 레벨/상태; 서버 변경·필요 상태 복제 |
| CurrentWeaponData | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AuraWeaponData | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| bPrimaryWeaponChoiceApplied | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| bAuraEquipped | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| RuntimeMoveSpeedBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| RuntimeProjectileSpeedBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| RuntimeProjectileDamageBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| RuntimeProjectileCooldownReduction | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| RuntimeAuraRadiusBonus | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| RuntimeAuraDamageBonus | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| RuntimeAuraTickIntervalReduction | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| RuntimeAuraElementType | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Aura 제외; 잔여 참조 제거 |
| RuntimeWeaponElementType | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| RuntimeMeleeDamageBonus | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| RuntimeMeleeRangeBonus | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| RuntimeLevelUpChoiceOfferBonus | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| RuntimeDamageTakenMultiplier | 이전 Base에 주석/미이관 | BaseMulti — 공통 피해 배율; 서버만 변경 |
| AppliedMetaMaxHPBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| AppliedMetaMoveSpeedBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| AppliedMetaDamageBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| AppliedMetaPickupRadiusBonus | 이전 Base에 주석/미이관 | TPS — 선택 제거 후에도 원거리·메타 의존성이 있어 우선 보존 |
| PrimaryMeleeCooldownRemaining | 이전 Base에 주석/미이관 | 이관 제외 — 플레이어 Melee 제외; 잔여 참조 제거 |
| bUseAutoPrimaryAttack | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| AutoAttackSearchRadius | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| AutoPrimaryAttackCooldownRemaining | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| CurrentEquipMontage | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| CurrentReloadMontage | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| LastAppliedWeaponType | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| LastAppliedWeaponAnimationType | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bWeaponStateInitialized | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| SecondaryFireTimerHandle | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bSecondaryFireHeld | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bCameraRotateHeld | 이전 Base에 주석/미이관 | TPS — 관련 기능과 함께 이관 |
| bUseTPSCameraMode | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bUseManualAim | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bUseMouseAim | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bShowMouseAimIndicator | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimIndicatorMaterial | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimIndicatorRadius | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimGroundOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimTraceDistance | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimTurnSpeed | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bHasMouseAimPoint | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MouseAimWorldPoint | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AimYawOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MaxAimYawOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AimYawStepPerInput | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AimPitchOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| MaxAimPitchOffset | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AimPitchStepPerInput | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| AimFollowTurnSpeed | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| LevelUpChoiceStacks | 이전 Base에 주석/미이관 | 이관 제외 — 선택 보상 제외; 잔여 참조 제거 |
| bIsRunning | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bIsCanCover | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| bISCanPickup | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| pickupItem | _TPS 활성 | TPS — 관련 기능과 함께 이관 |
| currentAmmo | _TPS 활성 | TPS — 관련 기능과 함께 이관 |

### 5-3. 기존 BaseMulti에서 FPS로 옮길 목록

| 종류 | 이름 | 현재 상태 → 처리 |
|---|---|---|
| 변수 | CameraComponent, DefaultIMC, MoveAction, LookAction, JumpAction, TestAction | BaseMulti 활성 → FPS로 이동 |
| 함수 | Move, Look, StartJump, StopJump, RequestValue | BaseMulti 활성 → FPS로 이동 |
| 함수 | BeginPlay | 카메라 참조 확보 부분은 FPS, 공통 초기화는 부모 유지 |
| 함수 | SetupPlayerInputComponent | FPS 입력 바인딩 부분은 FPS, TPS에는 TPS 전용 바인딩 |
| 함수 | Tick | Super 호출뿐. 실제 공통 작업 없으면 override 생략 |
| 변수 | TestValue | BaseMulti 유지 |
| 함수 | ServerIncreaseTestValue, ServerIncreaseTestValue_Implementation, OnRep_TestValue, GetLifetimeReplicatedProps | BaseMulti 유지, TestValue 중복 선언·등록 금지 |
| 함수 | PrintTESTLog | BaseMulti 유지, 실제 출력 복원 |
| 생성자 | AZCharacterBaseMulti | 부모 연결 후 공통 복제 설정 담당. FPS 입력·카메라 생성 책임 없음 |
| 생성자 | AZCharacter_TPS, AZCharacter_FPS | 현재 빈 생성자. 실제 시점별 설정을 이관해야 함 |

TPS에서 AddExperience, HandleLevelUpIfNeeded를 이미 선언했지만 이번에는 공통 레벨 기능으로 BaseMulti에 올린다. 자식에 동일 선언을 남겨 다른 구현으로 갈라지게 하지 않는다.

### 5-4. 이름 목록 이외에 반드시 잘라낼 내부 의존성

| 함수 | 유지할 부분 | 제거·변경할 부분 |
|---|---|---|
| ActivatePrimaryWeapon | Ranged 무기 판별·발사 진입 | ActivatePrimaryAura, ActivatePrimaryMelee 호출 제외. 미지원 타입을 원거리로 묵인하지 않음 |
| ApplyCharacterDataAsset, ApplyPlayableCharacterSelection, EquipWeaponFromPickup | 플레이어 데이터·원거리 장비 | AuraWeaponData·bAuraEquipped 설정, Melee 장비 경로 제외. 기본 무기·픽업에서도 미지원 타입 차단 |
| FirePrimaryProjectile | 발사체·원거리 피해·조준 | GetActiveAuraData·GetActiveAuraElementType 등 Aura 시너지 참조가 있으면 제거 |
| RefreshWeaponState | 장비 변경·애니메이션 갱신 | Aura 상태/자동 활성화 경로 제외 |
| RefreshWeaponElementEffect | 일반 원소 색·원거리 이펙트 | Active Aura와 비교한 시너지 배율 제거. Niagara의 시너지 출력도 비활성으로 일치시킴 |
| GetDefaultAuraElementColor | GetZElementColor를 이용한 일반 원소 색 조회 | 이름에 Aura가 있어도 역할은 일반 색상 보조. 삭제하지 말고 중립 이름 변경은 별도 작업 |
| ApplyWeaponElementChoice | 선택 보상 진입은 제외 | 일반 원소 무기는 WeaponData의 WeaponElementType 등 유지 경로를 사용 |
| ApplyLevelUpBalanceData, GetLevelUpBalanceRow | MaxLevel, NextLevelUpExperience, LevelUpExperienceStep 및 테이블 조회 | 선택 업그레이드·Aura·Melee 필드 읽기/폴백 설정 제외 |
| AddExperience | 경험치 지급·HandleLevelUpIfNeeded 연결 | 클라이언트가 임의 경험치 양을 확정하지 않음. 서버의 보상 근거에서 호출 |
| HandleLevelUpIfNeeded | 경험치 차감·레벨 상한·다음 임계치 갱신 | 선택창·선택 카드 호출을 추가하지 않음. 확인한 원본 함수 자체에는 선택 UI 호출 없음 |
| ApplyMetaProgressionBonuses, ReapplyMetaProgressionBonuses | 선택 UI와 무관한 실제 메타 보너스 | 제외 변수 참조만 정리. 메타 성장 전체를 자동 삭제하지 않음 |
| ReceiveEnemyDamage, RestoreHPPercent | 서버 HP 변경·사망 중복 방지 | FloatingText·DeathMontage·StopSecondaryFire·TPS GameMode 호출을 자식 표현/모드 정책으로 분리 |
| Tick | 필요한 조준·회전·원거리 상태 | PrimaryMeleeCooldownRemaining, 플레이어 Aura 처리 제외. 스태미나 권한과 시간 기준은 별도 검증 |
| InitAbilityActorInfo | ASC 연결·기존 AttributeSet 사용 | DefaultAbilities·DefaultEffects·CharacterDataAsset 의존 부여는 별도 초기화. 반복 연결 때 능력 중복 부여 금지 |

RuntimeDamageTakenMultiplier와 GetDamageTakenMultiplierValue는 공통 피해 처리와 함께 BaseMulti로 이동한다. BaseMulti의 ReceiveEnemyDamage가 TPS에만 있는 멤버를 읽도록 만들지 않는다.

원거리 업그레이드의 기본 증가량과 Runtime 보너스를 구분한다. MoveSpeedUpgradeAmount, ProjectileDamageUpgradeAmount, ProjectileCooldownReductionUpgradeAmount는 선택 적용·선택 설명·밸런스 복원의 관련 경로를 끊고 제외한다. RuntimeMoveSpeedBonus, RuntimeProjectileDamageBonus 등은 원거리/메타 계산이 여전히 참조하므로 우선 유지하며 실제 사용자가 없어졌을 때만 정리한다.

기존 cpp 익명 namespace의 GetElementStatusBalanceRowNameForUI, BuildElementStatusDetailTextForUI는 선택 설명용이므로 플레이어 이관 제외다. 선택 데이터용 BuildChoiceData 계열을 복원하지 않는다.

## 6. Enemy·UI·보상·호출자를 함께 점검

### 6-1. Enemy Aura를 보호할 목록

- AZEnemyBase: MonsterVariantAuraComponent, MonsterAuraScaleMultiplier, MonsterAuraIntensityMultiplier, ResolveMonsterVariantAuraEffect.
- Enemy 상태 효과: ApplyAuraStatusEffect, ApplyElementStatusEffect, TickAuraStatusEffects, GetElementStatusBalance, GetElementStatusBalanceRowName.
- EAuraElementType, FZElementStatusBalanceRow 등 공용 원소 타입.
- Enemy의 기존 Aura Niagara 및 몬스터 변형 데이터.
- AZEnemyBase의 ApplyMeleeHitReaction은 플레이어 Melee 타입 제외만으로 삭제할 대상이 아니다. 다른 호출자가 있으면 유지한다.

확인한 Enemy Aura에는 Niagara 표현과 상태 효과 처리가 있다. 플레이어의 AZAuraBase 공격 기능과 같은 구현이라고 가정하지 않는다. 플레이어의 ActivePrimaryAura를 Enemy로 그대로 옮기는 작업도 이번 요구가 아니다.

### 6-2. 다른 파일에서 수정할 실제 연결

| 파일/클래스 | 확인 이름 | 처리 |
|---|---|---|
| ZGA_PrimaryAttack.cpp | ActivatePrimaryWeapon | 현재 Base 호출을 TPS의 공개 계약 또는 이후 공통 원거리 계약으로 변경 |
| ZAnimNotify_ReloadAmmo.cpp | FinishReload | TPS 공개 접근·호출 타입 일치 |
| Project_Z_PlayerController.cpp | ConfigureTPSCameraMode, ToggleRunningMove, EnterCover, ExitCover, ItemPickUp, Reload, ApplyPlayableCharacterSelection, ActivatePrimaryWeapon | TPS 기능의 캐스팅·include·접근 범위 수정 |
| Project_Z_PlayerController.h/.cpp | UI/ZLevelUpChoice.h, UZLevelUpWidget, LevelUpWidgetClass, StartupLevelUpRetryCount, bStartupLevelUpPending | 선택 UI의 잔여 선언·시작 처리 제거 대상. 일반 PauseMenu까지 일괄 제거하지 않음 |
| ZLevelUpWidget.h/.cpp | SetupLevelUpWidget, ApplyChoiceByIndex, ApplyLevelUpChoiceData, OwningCharacter | 플레이어 선택 기능의 실제 호출 연결 해제. 미사용 UI도 모듈에 컴파일되면 사라진 함수 호출을 반드시 정리 |
| ZLevelUpChoiceCardWidget 및 관련 BP | 선택 카드 이벤트 | 플레이어 생성·표시 경로 제외. 공용 에셋 자체 삭제는 별도 참조 확인 후 |
| ZRewardChestActor.h/.cpp | OpenTreasureRewardSelection, AddExperience, RestoreHPPercent | 선택창 호출 제거. 경험치·직접 회복은 공통 상태 계약으로 연결. 보상 교체는 별도 정책 |
| ZExperiencePickupActor.h/.cpp | AddExperience, GetPickupRadiusValue, IsPlayerDead, TargetCharacter | 공통 BaseMulti 계약으로 연결하면 TPS/FPS 모두 수집 가능. 서버만 실제 지급, 기존 플레이어 0 타깃 검색의 멀티 대응은 별도 보완 |
| ZEnemyBase.cpp | AddExperience, ReceiveEnemyDamage, GetIsInCover | 레벨·피해는 공통 계층, 커버는 TPS에만 있는 선택적 기능으로 구분. Enemy Aura 유지 |
| ZInteractableBlock.cpp | SetCanCover, SetCoverMoveDirection, GetIsInCover, ExitCover | TPS 대상 연결 |
| ItemWeapon.h/.cpp | SetCanPickUp, SetPickupItemData, EquipWeaponFromPickup | TPS 복구 경로 연결, 미지원 무기 타입이 플레이어에게 장착되지 않게 확인 |
| ZCrosshairWidget.cpp | GetAimYawOffsetValue, GetMaxAimYawOffsetValue, GetAimPitchOffsetValue, GetMaxAimPitchOffsetValue | TPS 조회 계약 |
| ZGameFlowWidget.cpp | GetCurrentLevelValue | 공통 BaseMulti의 레벨 조회 |
| ZStateHUDWidget.cpp | HP, Stamina, Level, Experience, Ammo, WeaponAnimationType | HP·Stamina는 Base, 레벨은 BaseMulti, 기존 무기 표시는 TPS. 레벨 표시까지 삭제하지 않음 |
| UZWeaponDataAsset, UZCharacterDataAsset 및 BP/DataAsset | DefaultWeaponData, WeaponType, StartupAbilities, StartupEffects | 플레이어 기본 장비·능력에서 Aura/Melee 제외. 공용 필드·enum은 유지 |

게임에서 선택 UI를 열지 않는 것만으로 컴파일 의존성이 사라지지는 않는다. 제거할 캐릭터 함수에 대한 C++ 호출과 BP 노드를 함께 정리한다. 전체 AZCharacterBase 캐스팅을 한꺼번에 TPS로 바꾸지 않는다.

## 7. 앞으로 진행할 스텝과 확인 기준

웹 AI는 한 번에 아래 한 단계만 안내한다. 코드 본문은 사용자가 따로 요청할 때만 제공하고, 기본 안내는 이름·위치·작업 이유·검증 사항이다.

### Step 0. 최신 상태와 중간 클래스 이름 맞추기

- 현재 작업 파일은 Base, BaseMulti, TPS, FPS다.
- BaseMulti는 아직 ACharacter 직속이며, 목표는 Base를 상속하도록 연결하는 것이다.
- AZCharacterMulti로 리네임은 별도 결정 사항이다. 없는 파일에 이관하라고 안내하지 않는다.
- 이전 테스트 성공과 최신 소스의 미완료 상태를 구분한다.

### Step 1. Base의 최소 GAS 계약 복원

- 대상: AZCharacterBase 생성자, BeginPlay, GetAbilitySystemComponent, InitAbilityActorInfo, AbilitySystemComponent, AttributeSet.
- 유지·보완: GetCurrentHPValue, GetMaxHPValue, GetCurrentStaminaValue, GetMaxStaminaValue.
- 공통에 필요 없는 Tick, SetupPlayerInputComponent 선언을 정리한다.
- UPROPERTY, 기존 BP용 UFUNCTION, null 검사, 실제 GAS 생성·연결을 확인한다.
- TPS 원본 전체의 블록 주석을 한 번에 해제하지 않는다.
- 완료 판단: Base의 활성 선언과 정의가 일치한다. 프로젝트 전체 빌드 성공과는 별개의 중간 확인이다.

### Step 2. 상속·헤더·접근 범위 정리

- BaseMulti 부모를 Base로 연결한다. TPS/FPS는 실제 BaseMulti를 계속 상속한다.
- TPS의 UIInputAction, UIInputMappingCont1t, FPlayableCharacterRow 오타를 정리한다.
- RefreshCharacterAnimation의 const를 원본 비const 계약과 맞춘다.
- 외부 C++ 호출 함수는 public으로 배치하고 필요한 멤버는 protected 등으로 제한한다.
- Containers/Map.h, 선택 UI 타입, Aura/Melee 전용 전방 선언을 제외한다.
- 완료 판단: 헤더 구조와 include/전방 선언 방향이 맞는다.

### Step 3. 플레이어 제외 기능과 외부 호출 정리

- 5절의 “이관 제외” 이름을 TPS/FPS로 옮기지 않는다.
- 이미 TPS에 있는 WeaponElementSynergyActiveParameterName 등은 처리 방향을 적용한다.
- 선택 UI의 Controller·Widget·Chest 호출을 6절 기준으로 해제한다.
- DataAsset의 기본 장비·능력에서 Aura/Melee가 플레이어에게 활성화되지 않게 확인한다.
- Enemy Aura·공유 enum·공용 DataAsset 정의는 보존한다.
- 완료 판단: 제거한 이름을 호출하는 플레이어 경로가 남지 않으며, 레벨·경험치 경로는 남는다.

### Step 4. 레벨업만 공통 계층에 복원

- 함수: AddExperience, HandleLevelUpIfNeeded, GetCurrentLevelValue, GetMaxLevelValue, GetCurrentExperienceValue, GetNextLevelUpExperienceValue, ApplyLevelUpBalanceData, GetLevelUpBalanceRow.
- 변수: CurrentExperience, CurrentLevel, MaxLevel, NextLevelUpExperience, LevelUpExperienceStep, LevelUpBalanceTable, LevelUpBalanceRowName.
- 관련 상태: PickupRadius, GetPickupRadiusValue, MetaExperienceGainMultiplier, GetMetaExperienceGainMultiplierValue.
- TPS에 먼저 추가한 AddExperience, HandleLevelUpIfNeeded 선언을 공통 계층으로 이동한다.
- 서버 지급, 양수 임계치·상한·한 번에 여러 레벨 상승을 확인한다. 선택 UI나 자동 능력치 보상을 추가하지 않는다.
- 클라이언트 표시용 레벨·경험치의 복제 및 갱신은 새 작업이며, 아직 원본 구현 완료로 간주하지 않는다.
- 완료 판단: 경험치와 레벨이 증가하되 선택창·선택 스택이 없다.

### Step 5. TPS 입력·카메라 복원

- 5절의 TPS 카메라·조준·커버 함수와 멤버를 선언·정의 한 묶음으로 이관한다.
- BeginPlay, Tick, SetupPlayerInputComponent에서 제외 기능의 호출을 뺀다.
- bCameraRotateHeld, MoveByInput, OnAbilityInputPressed 등 빠진 이름을 보충한다.
- DefaultIMC는 TPS 전용으로 준비한다. 기존 부모의 FPS IMC를 우연히 쓰지 않는다.
- 완료 판단: TPS 전용 입력이 FPS 입력과 중복 실행되지 않는다.

### Step 6. 원거리 무기와 공통 상태 복원

- 원거리·장착·탄약·재장전·표현 함수는 5절의 TPS 이관 목록대로 복원한다.
- ActivatePrimaryWeapon과 데이터·픽업 경로 모두에서 Aura/Melee를 제외한다.
- ReceiveEnemyDamage, RestoreHPPercent, IsPlayerDead, bIsPlayerDead, RuntimeDamageTakenMultiplier는 공통 상태 책임으로 분리한다.
- TPS의 StopSecondaryFire, PlayDeathAnimation, FloatingText와 게임오버 처리를 공통 상태 변경에서 분리한다.
- 보상 선택 때문에 있던 bPrimaryWeaponChoiceApplied를 제거하면서 장착한 원거리 무기를 기본 무기가 다시 덮어쓰지 않게 확인한다.
- 완료 판단: TPS에서 원거리 장비·발사·재장전과 HP 상태 처리가 연결된다. 아직 FPS 무기 완료는 아니다.

### Step 7. BaseMulti의 FPS 입력을 FPS로 이동

- 5-3절의 CameraComponent, IMC/IA, Move, Look, Jump, RequestValue를 FPS에 이관한다.
- BaseMulti에는 네트워크 설정·공통 상태·RPC만 남긴다.
- BP 카메라 참조 방식, 기존 Look의 부호, 입력 에셋 기본값은 확인된 설정을 유지한다.
- PrintTESTLog의 실제 UE_LOG 출력도 복원한다.
- 완료 판단: FPS의 입력·카메라가 자식에서 실행되고 TestValue 요청만 부모로 전달된다.

### Step 8. 빌드와 BP 참조 연결

- 선언 이동, cpp 정의, 외부 호출자 변경이 한 묶음으로 끝난 뒤 Editor 타깃을 빌드한다.
- 현재 TPS에는 선언만 있는 UFUNCTION이 많다. 해당 본문이 없는 상태에서 빌드 성공을 기대하지 않는다.
- Base의 사라진 함수에 의존하는 기존 UI·Controller도 모두 일치해야 전체 빌드가 가능하다.
- 첫 컴파일 오류부터 분류하며, 빌드를 통과시키려고 제외 기능을 전부 복원하지 않는다.
- TPS/FPS BP 부모·기본값·네이티브 컴포넌트·IMC/IA·GameMode Pawn을 확인한다.
- 완료 판단: C++와 관련 BP Compile 성공. 아직 런타임 완료 체크는 하지 않는다.

### Step 9. 2인·기능 검증

| 시험 | 기대 결과 |
|---|---|
| 두 시점 기본 조작 | 각자 카메라·이동·회전·점프 정상 |
| 호스트·게스트 TestValue | 서버 변경·클라이언트 반영·로그 확인 |
| 경험치 경계 | 한 레벨·여러 레벨 증가·최대 레벨 정상 |
| 선택 기능 제외 | 레벨업해도 카드·선택 UI·선택용 일시정지 없음 |
| 플레이어 무기 타입 | Aura/Melee가 기본 장비·픽업·발사 경로에서 실행되지 않음 |
| 일반 원거리·원소 | 유지하기로 한 투사체·색상·이펙트가 정상 |
| Enemy Aura | 기존 몬스터 Aura 표현·상태 효과 유지 |
| HP·사망 | 서버만 확정, 필요한 클라이언트 표현 갱신 |
| 반복 초기화 | 능력·효과·AttributeSet 중복 없이 유지 |

### Step 10. FPS 원거리 기능 공유와 원본 정리

- TPS에 복원한 무기 중 탄약·쿨다운·장비 유효성·서버 발사는 공통 BaseMulti 또는 별도 무기 기능으로 추출한다.
- 조준 원점·총구·카메라·팔/몸 메시·애니메이션은 TPS/FPS의 다른 구현으로 둔다.
- GetAimDirection, GetProjectileAimPoint, GetProjectileSpawnLocation은 이름이 같아도 TPS 본문을 FPS로 그대로 복사하지 않는다.
- 공유 계약을 정한 다음 FPS에서도 발사·재장전·피해를 검증한다. 이 단계 이전에는 FPS 원거리 기능 완료로 표시하지 않는다.
- 사용하지 않는 주석 원본과 잔여 참조는 검증 뒤 정리한다.
- 리스폰 후 레벨 유지 정책이 필요하면 PlayerState 저장과 함께 별도 확정한다.

## 8. 작업 완료 체크

- [x] 32254b5 기준 네 클래스의 .h/.cpp 확인
- [x] 플레이어 Aura·Melee·LevelUpChoice 제외 범위 반영
- [x] Enemy Aura·일반 레벨업 유지 범위 반영
- [x] Base 헤더 include 축소 확인
- [x] HP·Stamina getter 4개 cpp 이동 확인
- [x] TPS 일부 선언 이관 및 TPS/FPS 파일 생성 확인
- [ ] Base GAS 생성·조회 계약·reflection·null 처리 복원
- [ ] BaseMulti가 Base를 상속하도록 연결
- [ ] TPS 선언 오타·const·접근 범위·누락 멤버 수정
- [ ] 선택 UI·보상 호출자와 Aura/Melee 실행 분기 제거
- [ ] 공통 경험치·레벨 증가 및 복제
- [ ] TPS 입력·카메라·원거리 구현
- [ ] 공통 HP·사망 판정과 시점별 표현 분리
- [ ] FPS 입력·카메라 이관, PrintTESTLog 출력 복원
- [ ] C++ 빌드와 BP 연결 확인
- [ ] 2인 및 레벨·Enemy Aura 회귀 검증
- [ ] FPS 원거리 공유 구현 및 검증
- [ ] 원본 주석·잔여 참조 정리

## 9. 웹 ChatGPT 전달용 컨텍스트

이 절과 위 이관표를 함께 전달하면 된다. 최초 안내를 위해 cpp 전체를 다시 요구하지 않는다.

### 확정 맥락

- 사용자는 직접 수정·빌드·테스트한다. 응답은 파일명·클래스명·함수명·변수명·이동 위치·이유 중심이다. 전체 구현 코드나 함수 본문을 먼저 출력하지 않는다.
- 최신 소스는 2026-10-07 확인한 32254b5다. d355bf2는 옛 멤버 목록 비교에만 사용했다.
- 현재 클래스는 AZCharacterBase, AZCharacterBaseMulti, AZCharacter_TPS, AZCharacter_FPS다. AZCharacterMulti 파일은 없다.
- 실제 BaseMulti는 아직 ACharacter 직속이다. 우선 Base 상속으로 연결하는 것이 필요하다. 임의로 다섯 번째 클래스를 만들지 않는다.
- Base.h는 축소됐지만 Base.cpp는 getter 4개 외 옛 구현이 블록 주석이다. TPS/FPS.cpp에는 빈 생성자만 있다. 선언 이동과 구현 완료를 구분한다.
- 플레이어의 Aura 능력·Aura 무기·Melee는 모두 제외한다. Enemy Aura는 유지한다.
- 레벨업은 유지하고 LevelUpChoice·선택 카드·선택 스택은 제외한다. 자동 능력치 상승은 새로 만들지 않는다.
- EAuraElementType은 원소 피해에도 쓰인다. 이름만 보고 공용 enum·Enemy 타입을 삭제하지 않는다.
- 카메라·팔은 BP 생성·부착, C++ 참조와 기능 구현 원칙을 유지한다. ASC/AttributeSet은 단일 생성 경로로 복원한다.
- 기존 BaseMulti의 PrintTESTLog에는 현재 실제 출력이 없다. 과거 로그 성공을 최신 구현 성공으로 표시하지 않는다.
- 이 문서의 5절은 전체 심볼의 처리 명세, 6절은 외부 의존성, 7절은 순서, 8절은 실제 확인 상태다.
- 첫 안내는 Step 0의 현재 구조 확인 후 Step 1의 Base 최소 계약 복원이다. getter cpp 이동을 처음부터 다시 시키지 말고 현재 부족한 부분만 보완한다.
- 분석본과 달라졌거나 오류가 나면 해당 선언·문제 함수 주변만 추가로 요청한다.

### 한 번에 안내할 응답 형식

| 항목 | 내용 |
|---|---|
| 현재 Step | 이번에 처리할 작은 작업 단위 |
| 열 파일 | 실제 존재하는 .h/.cpp 이름 |
| 유지 | 남겨야 하는 include·전방 선언·함수·변수 이름 |
| 이동 | 원본 이름 → 목적지 클래스·파일 |
| 제외 | 플레이어 이관 제외 이름과 함께 끊을 호출자 |
| 수정 | 오타·접근 범위·const·초기화 순서 등 |
| 확인 | 현재 가능한 정적 점검/빌드/PIE와 기대 결과 |
| 다음 | 사용자가 완료를 확인한 뒤 넘어갈 Step |

한 번의 응답에 전체 이관을 요구하지 않는다. 단, 선언·구현·호출자가 아직 불일치하는 중간 단계는 전체 빌드가 실패할 수 있음을 정확히 설명한다. 소스 확인, 빌드 성공, 런타임 검증을 서로 다른 완료 상태로 기록한다.
