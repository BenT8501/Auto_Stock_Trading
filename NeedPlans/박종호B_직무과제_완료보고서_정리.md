# 직무과제 완료보고서

> 원본 PPT 내용을 Markdown 형식으로 정리한 문서입니다.

## 2. 진행 결과 (계획했던 목표 대비 실제 달성 내용 작성)

1. 업무명

- Unreal Engine 기반 TPS 좀비 서바이벌 샘플 프로젝트 제작
개발 목표

Unreal Engine 에서 실시간 액션형 샘플 콘텐츠의 핵심 개발 요소 구현

C++ 과 Blueprint의 역할을 분리 하고, Editor Asset 기반 조정 구조 구성

TPS 조작, 엄폐, 총기 전투,  적  AI, UI, 데이터 기반 설정을 구현

GAS 기반의 데미지 처리 구조 구현

달성 내용

기본 플레이 흐름

Ready, Play, Stage Clear, Game Over 흐름 구현 (달성)

카메라 이동 및 Aim 구현

TPS 이동, 카메라, 조준 구현 (달성)

엄폐

적 AI 감지, 진입, 이동, 해제 및 애니메이션 구현 (달성)

적 생성

Wave 스폰과 AI 추적, 공격 구현 달성

총기 데이터

Pistol, Rifle, Shot Gun  및 주요 능력치 데이터화 (달성)

탄약 재 장전

탄약 소모, 재장전 Montage와 AnimationNotify 구현 (달성)

무기 파츠

조준경, 탄창, 총구등 독립적 장착 및 효과 – 미구현

공격, 충돌, 피격 처리

투자체 피격 처리 구현(달성)

---

## UI

UI

HUD, 상태, 진행 및 결과 화면 구성 구현(달성)

데이터 기반 설정

DataAsset 및 DataTable 적용 (달성)

추가 성과

적 변종, 보스, 성장 보상, GAS 데미지 처리 구현

핵심 플레이 요소 개발

플레이 흐름, 캐릭터 조작, 적 생성 및 AI, 몬스터 확장, 보스/특수 행동 구현 등 핵심 플레이 요소들을 개발 하였으며, 적 변종 및 보스 조건 등을 추가 하였습니다.

전투, UI,  데이터 구조 결과

무기 파츠는 제외 하였으나, 무기 능력치와 공격 구조를 데이터 기반으로 분리 하여 이후 확장 할 수 있는 구조로 만들었습니다.

GAS 데미지 처리 구현

좀비에  GAS(GAMEPLAY ABILITY SYSTEM)을 적용 하여 ASC(Ability System Component)와 AttributeSet을 적용 투사체 충돌시 Bone정보 또는 피격 높이로 Head Shot 여부 판정 GameplayEffect의 SetByCaller 값으로 데미지를 전달 Head Shot GameplayTag와 데미지 2배율을 적용 하였습니다.

ASC 미 적용 대상은 무기의 기본 데미지와 같게 처리 하였습니다.

---

## 3. 성과 (기대효과 대비 달성한 내용 작성)

계획에 포함된 핵심 플레이 루프, 조작, AI, 총기, 재장전, 공격, UI와 데이터 기반 설정을 대부분 달성 하였습니다.

무기 파츠는 미구현 상태이지만 과제의 핵심 목적인 Unreal Engine기반 실시간 액션 콘텐츠 제작 구조와  Unreal C++과 Blueprint간의 연계 작업을 파악 하여 프로젝트 작업 역량을 높였습니다.

4. 업무일정 (실제 업무 일정)

2026.07.14~07.20	투사체 전투 기반 구현 - 투사체 생성과 Object Pool 적용, 캐릭터 투사체 충돌 처리

2026.07.22~07.25	TPS 조준 및 발사 보완 – TPS Aim 방향과 투사체 발사 오류 수정

2026.07.27~07.31	데이터 및 게임 진행 구조 정리 – DataTable 적용, GameMode 구성, 시작 전 이동 오류 수정 등

2026.08.03~08.07	Stage UI Ai 통합 – Stage Clear, HUD, 적 생성 수와 Ai 동작 수정

2026.08.10~08.12 	아이템 드랍 및 엄폐 기반 구현 – 적 무기 드랍 및 업폐기능과 애니메이션 추가

2026.08.14~08.21	HUD 상호 작용 보완, TPS 애니메이션 및 아이템 보완 – HUD정보 갱신 엄폐가능 블록 상호 작용 작업

아이템 픽업 수정

2026.08.24~08.25 	재장전 및 엄폐 오류 수정, GAS 적용 – 재장전 AnimationNotify연동, 엄폐 이동 오류 수정 및 GAS 구현

2026.08.25~08.28	테스트 및 오류 수정

---

## 5. 업무결과 (결과물 첨부)

아키텍처

Unreal 엔진의 C++과 Blueprint를 병행 하는 구조로 구성 했습니다.

게임의 핵심 적인 처리와 반복적으로 사용 되는 로직은 C++로 구현 하였 고 Mesh, Animation, Widget, DataTable, DataAsset 등과 같은 컨텐츠는 Blueprint를 이용 하여 Unreal 엔진에서 관리 할 수 있게 만들었습니다.

전체 적인 컨텐츠 구성으로 캐릭터, 좀비,  좀비 Ai, 무기, 전투, 게임 진행, UI, 데이터 관리, GAS 데미지 처리 등이 있습니다.

핵심 GamePlay Blueprint

BP_Project_Z_GameMode

Aproject_Z_GameMode Class 연동

게임 진행, 적 스폰, Player, Controller Class 지정

BP_ZCharacter

AZCharacterBase Class 연동

Player 이동 및 카메라 처리

조준, 총기 발사 및 재장전, 엄폐

WeaponDataAsset , ABP_Zcharacter 등과 Blueprint로 연동

BP_Project_Z_PlayerController

AProject_Z_PlayerController Class 연동

Player 입력 모드 관리, HUD 생성 및 표시, 레벨업 UI, Stage Clear, Game Over UI 관리

BP_Enemy

AZEnemyBase  Class 연동

Player 추적 및 공격

GAS(Gameplay Ability System)을 이용한 피격 반응 및 사망 처리

경험치 구슬 및 총기 드랍

DT_MonsterVariants 와 연동 하여 좀비 등급 및  HP, 이동속도, 공격력, 외형 등 설정

---

## 5-1. 아키텍처 구현을 통한 역량 향상

C++ 클래스와 Blueprint Asset의 역할을 나누고, 각 시스템의 책임을 분리하는 경험을 확보했습니다.

수행한 내용

Character: 이동, 조준, 사격, 재장전, 엄폐 등 플레이어 동작 처리

PlayerController: 입력 모드, HUD 생성, UI 전환 관리

GameMode: Stage 진행, 적 생성, Stage Clear, Game Over 흐름 관리

Widget 계층: HUD, 상태 표시, Crosshair, 상호작용 표시로 역할 분리

향상된 실무 역량

Actor, Controller, GameMode, Widget의 구현 범위를 구분할 수 있게 되었습니다.

모든 기능을 Character에 몰아넣지 않고 시스템별 담당 클래스로 분산하는 기준을 익혔습니다.

C++에서 핵심 로직을 처리하고, Blueprint에서 Mesh, Animation, Widget, DataAsset을 연결하는 흐름을 이해했습니다.

`ACharacter`는 이동·전투 상태, `APlayerController`는 입력 모드와 HUD, `AGameModeBase`는 Stage·Wave 진행을 담당하도록 책임을 분리하고 클래스 간 호출 방향을 설계할 수 있게 되었습니다.

`UCLASS`, `UFUNCTION`, `UPROPERTY`를 이용해 C++ 기능과 설정값을 Blueprint에 노출하고, `TObjectPtr`, `TSubclassOf`, `TSoftObjectPtr`의 용도에 맞춰 UObject와 Asset 참조를 구성하는 경험을 확보했습니다.

Unreal의 객체 생성 시점과 수명주기를 고려하여 `BeginPlay`, 입력 바인딩, Widget 생성, Actor 사망 처리의 실행 순서를 추적하고 초기화 누락과 유효하지 않은 참조 문제를 점검할 수 있게 되었습니다.

C++ 컴파일, Blueprint 부모 클래스와 기본값 확인, PIE 실행 로그 검토를 단계별로 수행하여 코드 변경이 에셋과 런타임 동작에 미치는 영향을 검증하는 작업 방식을 익혔습니다.

향후 Unreal 프로젝트에서 기능 추가 시 “어느 클래스에 구현 해야 하는가,  Blueprint에서 담당해야 하는가”를 먼저 판단하고, 유지보수 가능한 구조로 설계할 수 있는 기반을 확보했습니다.

---

## BP_Projectile_GunBullet

BP_Projectile_GunBullet

AZProjectileBase Class 연동

총알 이동 및 충돌처리

HitResult를 이용 하여  일반 피격과 Head Shot 판정

GE_Damage_Bullet를 이용 GAS 데미지 적용

관통 횟수와 Projectile Pool 반환 처리

UI Blueprint

WBP_TPS_HUD

UZHUDWidget Class 연동

화면의 최상위 HUD

상태 HUD, Crosshair, Interaction UI 관리

하위에 여러 개의 Widget Blueprint를  가지고 있다.

WBP_StateHUD

UZStateHUDWidget Class 연동

Player HP, EXP, Ammo 등 표시

WBP_CrossHair

UZCrosshairWidget Class 연동

화면 중앙 조준점 표시

WBP_InteractionWidget

UZInteractionMarkerWidget Class 연동

획득 가능한 무기와 아이템 안내, 상호작용(엄폐 블록) 가능 상태 표시

WBP_ZStageClearWidget

UZStageClearWidget Class 연동

Staget Clear 상태 표시, 다음 Stage 진행 처리

PlayerController 및 GameMode 연동

---

## 5-2. 전투·투사체 구현을 통한 역량 향상

입력부터 조준, 발사, 충돌, 재장전, 엄폐까지 이어지는 TPS 전투 흐름을 직접 구성했습니다.

수행 한 내용

전투 기능

카메라 방향 기반 Aim 처리와 Projectile 발사 방향을 보정했습니다.

Pistol, Rifle, Shotgun의 발사 방식과 탄약 소모 구조를 구현했습니다.

Projectile 충돌, 관통 횟수, Object Pool 반환 처리를 연결했습니다.

재장전 Montage와 AnimationNotify를 이용해 애니메이션 완료 시점에 탄약을 갱신했습니다.

Animation

Layered Blend per Bone을 활용해 상체 조준/사격과 하체 이동을 분리했습니다.

엄폐 상태, 이동 방향, 조준 상태에 따라 Animation 상태를 전환했습니다.

코드에서 관리하는 공격/재장전 상태와 Animation Blueprint를 연동했습니다.

캐릭터 상태 변화와 애니메이션, 전투 결과를 함께 연결하는 경험을 통해 TPS 전투 기능을 독립적으로 설계·구현할 수 있는 능력이 향상되었습니다.

향상된 실무 역량

Enhanced Input의 입력 이벤트에서 카메라와 캐릭터의 Aim 방향을 계산하고, 무기 Muzzle 위치에서 Projectile을 생성하여 충돌 결과까지 연결하는 TPS 사격 흐름을 구현할 수 있게 되었습니다.

`FHitResult`의 Bone 이름과 피격 위치를 이용해 일반 피격과 Head Shot을 구분하고, Head Shot GameplayTag와 피해 배율을 이후 데미지 처리 단계로 전달하는 구조를 이해했습니다.

Projectile 생성과 반환을 Object Pool로 관리하고, 충돌 또는 관통 횟수 소진 시 Pool에 복귀시키는 방식으로 반복적인 Actor 생성·삭제 비용을 줄이는 경험을 확보했습니다.

Pistol·Rifle·Shotgun의 발사 방식, 탄환 수, 확산 각도, 사거리, 탄속과 탄약 값을 `UZWeaponDataAsset`으로 분리하여 동일한 C++ 발사 로직에서 서로 다른 무기 동작을 구성할 수 있게 되었습니다.

재장전 상태와 Montage 재생을 연결하고, `AnimationNotify`가 호출되는 정확한 시점에 탄약을 갱신하여 코드 상태와 애니메이션 타이밍을 동기화할 수 있게 되었습니다.

Animation Blueprint의 `Layered Blend per Bone`을 활용하여 하체 이동과 상체 조준·사격을 분리하고, 이동·조준·엄폐·재장전 상태에 따라 Animation State를 전환하는 구조를 구성했습니다.

---

## WBP_ZGameOverWidget

WBP_ZGameOverWidget

UZGameOverWidget Class 연동

Player 사망 및 Game Over 표시

게임 재 시작및 종료 입력 처리

Animation Blueprint

ABP_ZCharacter

PlayerCharacter의 Skeletal Mesh 연동

기본 이동, 정지 방향 전환등 Animation 처리

Character Movement 상태를 Animation State로 변환

ABP_ZCharcater_Pistol

BP_ZCharacter와 Blueprint연동

권총 장착 상태, 이동, 조준, 발사, 재장전 Montage 연동

C++ 의 공격 재장전 상태와 Blueprint연동

ABP_ZCharacter_Rifle

BP_ZCharacter와 Blueprint연동

소총 및 산탄총 장착 상태, 이동, 조준, 발사, 재장전 Montage 연동

C++ 의 공격 재장전 상태와 Blueprint연동

ABP_Zenemy

UZEnemyAnimInstance Class 연동

적 Idle, 이동, 추격, 공격 Animation 처리

피격 반응과 사망 상태 표시

BP_Enemy의 Skeletal Mesh에 적용

---

## 5-3. UI·상호작용 구현을 통한 역량 향상

플레이어 상태와 게임 진행 정보를 HUD와 결과 UI로 표시하는 구조를 구성했습니다.

수행 내용

UI / 상호 작용

HUD에 HP, EXP, Ammo, Crosshair, 상호작용 정보를 표시했습니다.

무기와 아이템 드랍, 획득 안내, 결과 UI를 PlayerController와 연동했습니다.

Stage Clear와 Game Over UI를 GameMode 진행 흐름과 연결했습니다.

UI가 보이지 않거나 값이 갱신되지 않는 문제를 구조 재정리로 해결했습니다.

적 생성 수, Stage 진행, HUD 갱신, Player 상태 변화가 서로 맞물리도록 수정했습니다.

향상된 실무 역량

`AProject_Z_PlayerController`에서 Widget 생성과 화면 전환을 관리하고, 최상위 `UZHUDWidget` 아래에 상태 HUD, Crosshair와 상호작용 Widget을 배치하는 계층 구조를 구성할 수 있게 되었습니다.

Character의 HP·EXP·Ammo·무기 상태와 GameMode의 Stage·Wave 상태를 각 Widget 갱신 함수로 전달하여 게임 데이터와 화면 표시를 동기화하는 경험을 확보했습니다.

Ready, 플레이, Stage Clear와 Game Over 상태에 따라 Widget의 `ESlateVisibility`, 마우스 커서, Game/UI Input Mode를 전환하고 중복 입력과 화면 충돌을 방지하는 흐름을 구현했습니다.

화면 중앙 Crosshair와 월드 상호작용 표시를 분리하고, 무기 획득 및 엄폐 가능 상태에 따라 안내 Widget을 표시하거나 숨기는 조건을 구성할 수 있게 되었습니다.

UI 오류 발생 시 Widget 생성 여부, Owning Player, Blueprint 지정 클래스, `BindWidget` 대상, Visibility와 데이터 갱신 호출 순서를 순차적으로 확인하는 디버깅 기준을 익혔습니다.

---

## GameplayEffect Blueprint

GameplayEffect Blueprint

GE_Damage_Bullet

UGameplayEffect Class 연동

Instant GameplayEffect로 총알 피해 적용

Data.Damage Tag를 이용 SetByCaller 값 사용

Character의 UZAttributeSet::Damage Attribute 값 변경

일반 피격과 Head Shot 태그 전달

Data Asset, Data Table

Character Data

DA_Character_Player

UZCharacterDataAsset  Class 연동

Player 기본 능력치 관리, 캐릭터 Mesh, Animation 설정

기본 무기Data Asset 연결

시작 Ability 및 GameplayEffect 설정

Weapon Data

DA_Weapon_Pistol

UZWeaponDataAsset Class 연동

권총 공격력, 사거리, 공격 속도, 탄약 수, Projectile Class와 탄환속도 관리

DA_Weapon_Rifle

UZWeaponDataAsset Class 연동

소총 공격력, 사거리, 공격 속도, 탄약 수, Projectile Class와 탄환속도 관리

DA_Weapont_Shotgun

UZWeaponDataAsset Class 연동

산탄총 공격력, 사거리, 공격 속도, 탄약 수, Projectile Class와 탄환속도

동시 발사되는 탄환 수, 탄환 확산 각도 관리

---

## 5-4. 데이터·GAS 구현을 통한 역량 향상

수행 내용

데이터 기반 설계

WeaponDataAsset으로 공격력, 탄약 수, 공격 속도, Projectile Class를 분리했습니다.

StageDefinition과 WaveDefinition으로 Stage 진행과 적 생성 정보를 분리했습니다.

MonsterVariants DataTable로 적 타입, 등급, HP, 이동 속도, 공격력, 외형 배율을 관리했습니다.

LevelUpBalance DataTable로 레벨업 요구 경험치와 성장 수치를 관리했습니다.

ASC, AttributeSet, GameplayEffect, GameplayTag, SetByCaller를 이용해 데미지 전달 구조를 구현했습니다.

HitResult의 Bone 정보 또는 피격 위치를 이용해 Head Shot 여부를 판정했습니다.

Head Shot 태그와 데미지 배율을 GameplayEffect 처리 흐름에 연결했습니다.

GAS 적용

데이터 기반 설계는 실무 활용 가능 수준의 기초를 확보했고,

GAS는 숙련 단계보다는 전투 로직에 적용 가능한 기본 구조를 이해한 수준입니다.

향상된 실무 역량

`UZWeaponDataAsset`에는 개별 무기의 능력치와 Projectile 설정을, DataTable에는 다수의 Wave·적 변종·밸런스 행을 저장하여 단일 에셋 데이터와 표 형식 데이터의 용도를 구분할 수 있게 되었습니다.

`TSoftObjectPtr`와 Editor 지정 참조를 사용해 코드와 에셋의 결합도를 낮추고, C++을 다시 컴파일하지 않고도 무기 능력치와 Stage·Wave 구성을 조정할 수 있는 구조를 설계했습니다.

GAS의 `UAbilitySystemComponent`, `UAttributeSet`, `UGameplayEffect`, `FGameplayEffectSpecHandle` 사이의 역할을 이해하고 공격자와 피격 대상의 ASC를 통해 GameplayEffect를 적용할 수 있게 되었습니다.

Projectile 충돌 시 계산한 최종 피해를 `SetByCaller`의 `Data.Damage` GameplayTag로 전달하고, `UZAttributeSet`에서 Damage 값을 HP 변화로 반영하는 데이터 흐름을 구현했습니다.

Head Shot 여부를 GameplayTag로 Effect Context에 전달하여 일반 피해와 Head Shot 피해를 구분하고, 동일 조건에서 Head Shot 배율이 2배로 적용되는지 검증할 수 있게 되었습니다.

ASC가 없는 대상에는 Interface 기반 직접 피해 경로를 제공하여 GAS 적용 대상과 미적용 대상이 동일한 무기 기본 피해 기준을 사용하도록 예외 경로를 구성했습니다.

---

## Game Data

Game Data

DA_ZStageDefinition

UZStageDefinitionAsset Class 연동

Stage 진행 정보 관리, Stage별 적 생성 설정, Boss 출현 및 완료 조건 관리

DT_ZWaveDefinition

FZWaveDefinition Struct  연동

Wave별 적 종류와 생성 수 관리, 난의도 설정

DT_MonsterVariants

FZMonsterVariantDefinition Struct 연동

Basic, Runner, Heavy  타입 설정

Normal, Elite, Boss 등급 설정

HP, 이동 속도, 공격력 및 외형 배율 관리

DT_LevelUpBalance

FZLevelUpBalanceRow Struct 연동

레벨업 요구 경험치 관리

총기 공격력과 이동 속도 등 레벨별 강화 수치 관리

최대 레벨 및 성장 벨런스 설정

---

## 5-5. AI·Game Flow 구현을 통한 역량 향상

수행 내용

적 AI와 Stage 진행을 GameMode 중심의 플레이 루프로 연결했습니다.

AI 구현

적 감지, 추적, 공격, 피격, 사망 처리를 구현했습니다.

Basic, Runner, Heavy 타입과 Normal, Elite, Boss 등급 구조를 구성했습니다.

적 사망 시 경험치 구슬과 무기 드랍이 발생하도록 연결했습니다.

엄폐 상태에 따라 적 인식 조건이 달라지는 구조를 적용했습니다.

Game Flow

Ready, Play, Stage Clear, Game Over 흐름을 구성했습니다.

Stage별 적 생성 수와 Boss 출현 조건을 데이터와 연동했습니다.

적 처치, 경험치 획득, 레벨업, 다음 Stage 진행 흐름을 연결했습니다.

향상된 실무 역량

Enemy Actor에서 Player 감지, 이동, 공격 가능 거리와 Cooldown을 판정하고, 피격·사망 상태에서는 추적과 공격을 중지하도록 AI 상태 전환을 구성하는 경험을 확보했습니다.

적 사망 시 경험치와 무기 드랍을 처리한 뒤 GameMode에 사망을 통지하고, 현재 Wave의 생존 적 수가 0이 되었을 때만 Stage Clear로 전환되는 흐름을 연결했습니다.

Actor의 사망 통지와 `Destroyed` 이벤트가 동시에 발생할 수 있음을 고려하여 적 사망 수, 보상과 Stage 완료가 중복 집계되지 않는지 확인하는 검증 기준을 익혔습니다.

`UZStageDefinitionAsset`, `FZWaveDefinition`, `FZMonsterVariantDefinition`을 통해 Stage별 Wave 수, 적 종류·수량, Basic·Runner·Heavy 타입과 Normal·Elite·Boss 등급을 데이터로 구성할 수 있게 되었습니다.

GameMode에서 Ready, Wave 시작, 적 생성, 전투, Stage Clear, 다음 Stage와 Game Over 상태를 관리하고 PlayerController의 결과 UI와 입력 상태를 함께 전환하는 전체 게임 흐름을 구현했습니다.

개별 기능만 확인하지 않고 적 생성 수, AI 활성화, 사망 집계, UI 전환과 재시작을 하나의 PIE 시나리오로 반복 검증하는 통합 테스트 방식을 익혔습니다.

---
