# Project_Z 기술 면접 설명 가이드

## 1. 문서 목적

- 대상 프로젝트: `Project/Project_Z/Project_Z.uproject`
- 기준 엔진: Unreal Engine 5.7
- 목적: 기술 면접관에게 `Project_Z`의 오브젝트 및 기능 설계를 클래스와 변수 중심으로 설명한다.
- 분석 기준: 현재 C++ 소스의 실제 구현을 기준으로 하며, 구현되지 않은 계획은 구현 결과처럼 표현하지 않는다.

---

## 2. 1분 프로젝트 소개

`Project_Z`는 다수의 적을 상대하면서 무기와 능력치를 성장시키는 TPS 전투 프로젝트입니다. 설계 방향은 크게 세 가지입니다.

첫째, 게임 규칙과 실행 흐름은 C++로 구현하고 무기, 캐릭터, 몬스터 변형, 스테이지, 레벨업 밸런스는 DataAsset과 DataTable로 분리했습니다. 콘텐츠를 추가하거나 수치를 조정할 때 핵심 코드를 수정하는 범위를 줄이기 위해서입니다.

둘째, Unreal Framework의 책임에 맞춰 `GameMode`는 스테이지 규칙, `PlayerController`는 입력 모드와 UI, `Character`는 플레이어 행동, `WorldSubsystem`은 투사체 풀, `GameInstanceSubsystem`은 영구 성장 데이터를 담당하도록 구성했습니다.

셋째, 원본 무기 데이터와 현재 플레이의 강화 수치를 분리했습니다. 무기의 기본 능력치는 `UZWeaponDataAsset`에 두고, 레벨업으로 얻은 보너스는 `AZCharacterBase`의 런타임 변수에 누적합니다. 이 방식으로 공유 DataAsset이 플레이 중 수정되는 문제를 피했습니다.

---

## 3. 전체 아키텍처

```text
AProject_Z_GameMode
 ├─ 스테이지/웨이브 데이터 로드
 ├─ 적 생성 및 생존 수 관리
 └─ 스테이지 클리어와 게임오버 판정

AProject_Z_PlayerController
 ├─ UI 생성과 화면 전환
 ├─ TPS 입력 모드 관리
 └─ 선택 캐릭터 적용

AZCharacterBase
 ├─ 이동, 카메라, 조준, 엄폐
 ├─ GAS 초기화와 플레이어 Attribute
 ├─ 장비와 공격 실행
 └─ 경험치, 레벨업, 런타임 강화

UZWeaponDataAsset
 └─ 무기 종류, 공격 방식, 수치, 외형 데이터

AZProjectileBase ↔ UZActorPoolSubsystem
 ├─ 충돌, 피해, 관통, 헤드샷, 속성 효과
 └─ 투사체 획득과 반환

AZEnemyBase
 ├─ 추적, 공격, 피격, 사망
 ├─ 몬스터 타입/등급 및 상태이상
 └─ 경험치, 상자, 영구 재화 보상

UZMetaProgressionSubsystem
 └─ SaveGame 기반 영구 성장
```

면접에서는 클래스 목록을 순서대로 외우기보다 다음 실행 흐름을 먼저 설명하는 편이 좋습니다.

```text
입력
→ PlayerController/Character
→ Gameplay Ability 발동
→ 무기 데이터에 따라 공격 방식 선택
→ 투사체 또는 근접/오라 공격
→ Enemy 피해 및 상태 변화
→ 사망 시 GameMode 통지와 보상 생성
→ 경험치 획득 및 Character 런타임 성장
```

---

## 4. 플레이어 설계: AZCharacterBase

### 클래스 역할

`AZCharacterBase`는 `ACharacter`와 `IAbilitySystemInterface`를 기반으로 플레이어의 이동, 카메라, 전투, 장비, 성장 상태를 관리합니다.

### 주요 객체 변수

| 변수 | 역할 | 설계 의도 |
|---|---|---|
| `CameraBoom`, `FollowCamera` | 쿼터뷰/TPS 카메라 구성 | 카메라를 캐릭터 구성요소로 소유하고 모드별 설정을 교체한다. |
| `AbilitySystemComponent` | Gameplay Ability 실행 | 입력과 능력 발동의 공통 진입점을 제공한다. |
| `AttributeSet` | HP, MP, Stamina, MovementSpeed 등 | 전투 능력치를 GAS가 이해할 수 있는 형태로 관리한다. |
| `CharacterDataAsset` | 메시, 기본 능력치, 애니메이션, 시작 장비 | 캐릭터별 차이를 코드가 아닌 데이터로 정의한다. |
| `CurrentWeaponData` | 현재 일반 무기 | 공격 계산과 무기 외형의 기준 데이터다. |
| `AuraWeaponData` | 현재 오라 장비 | 일반 무기와 지속형 오라를 동시에 독립 관리한다. |
| `ActivePrimaryAura` | 현재 생성된 오라 액터 | 오라 중복 생성과 수명주기를 관리한다. |
| `EquippedWeaponMeshComponent` | 장착된 무기 표현 | 무기 데이터의 Skeletal Mesh를 캐릭터 소켓에 표현한다. |

### 성장 관련 변수

| 변수 | 의미 |
|---|---|
| `CurrentExperience` | 현재 경험치 |
| `CurrentLevel` | 현재 레벨 |
| `NextLevelUpExperience` | 다음 레벨에 필요한 경험치 |
| `MaxLevel` | 한 런의 최대 레벨 |
| `LevelUpChoiceStacks` | 선택한 강화별 중첩 횟수 |
| `RuntimeMoveSpeedBonus` | 현재 런에서 획득한 이동속도 보너스 |
| `RuntimeProjectileDamageBonus` | 투사체 공격력 보너스 |
| `RuntimeProjectileCooldownReduction` | 투사체 쿨다운 감소량 |
| `RuntimeAuraRadiusBonus` | 오라 반경 보너스 |
| `RuntimeAuraDamageBonus` | 오라 피해 보너스 |
| `RuntimeMeleeDamageBonus` | 근접 피해 보너스 |
| `RuntimeDamageTakenMultiplier` | 캐릭터 특성에 따른 받는 피해 배율 |

### 왜 원본 데이터와 런타임 보너스를 분리했는가

`UZWeaponDataAsset`은 여러 객체가 공유할 수 있는 에셋입니다. 플레이 중 DataAsset 자체의 값을 변경하면 같은 에셋을 참조하는 다른 객체와 다음 플레이에 의도하지 않은 영향을 줄 수 있습니다.

따라서 최종 전투 값은 개념적으로 다음처럼 계산합니다.

```text
최종 값 = 무기 기본값 + 캐릭터 고유 보너스 + 현재 런의 강화 보너스 + 영구 성장 보너스
```

이 설계의 효과는 다음과 같습니다.

- 공유 에셋의 런타임 오염을 방지한다.
- 기본 밸런스와 현재 런 상태를 구분할 수 있다.
- 캐릭터 특성, 레벨업, 메타 성장을 조합하기 쉽다.
- HUD가 Getter를 통해 최종 상태를 읽을 수 있다.

### 공격 호출 흐름

```text
Enhanced Input
→ AbilitySystemComponent 입력 처리
→ UZGA_PrimaryAttack::ActivateAbility()
→ AZCharacterBase::ActivatePrimaryWeapon()
→ CurrentWeaponData의 WeaponType/HitType 판정
   ├─ 원거리: FirePrimaryProjectile()
   ├─ 근접: ActivatePrimaryMelee()
   └─ 오라: ActivatePrimaryAura()
```

`UZGA_PrimaryAttack`은 실제 공격 계산을 직접 가지지 않고 캐릭터의 무기 실행 함수를 호출한 뒤 종료됩니다. 현재 구조에서 GAS는 Attribute와 능력 발동의 진입점 역할을 하며, 세부 전투 로직은 캐릭터·투사체·적 클래스가 담당합니다.

### 면접에서 정확히 말해야 할 점

현재 구조를 “GAS 기반 전투가 완전히 구축됐다”고 표현하면 과장입니다. GameplayEffect를 통한 피해 경로가 존재하지만 직접 함수 호출 피해 경로도 병존합니다. 정확한 표현은 다음과 같습니다.

> GAS를 Attribute 관리와 Ability 진입점에 적용했고, 기존 직접 전투 로직을 단계적으로 GAS로 통합하는 구조입니다.

---

## 5. 무기 데이터 설계: UZWeaponDataAsset

### 핵심 설계

무기마다 C++ 하위 클래스를 만드는 대신 `UZWeaponDataAsset` 하나가 무기 유형과 세부 동작을 데이터로 정의합니다.

### 분류 변수

| 변수 | 설명 |
|---|---|
| `WeaponType` | `Melee`, `Ranged`, `Aura` 등 상위 무기 분류 |
| `AnimationType` | Pistol, Rifle, Shotgun 등 애니메이션 세트 선택 |
| `HitType` | Projectile, Hitscan 계열 판정 방식 |
| `FirePattern` | 단발, 확산 발사 등 발사 패턴 |
| `WeaponElementType` | Fire, Cold, Lightning, Poison 등 속성 |

### 공통 전투 변수

- `BaseDamage`
- `Cooldown`
- `Range`
- `AttackAnimationPlayRate`

### 원거리 전용 변수

- `ProjectileClass`, `ProjectileRowName`
- `ProjectileSpeed`, `ProjectileCount`
- `SpreadAngleDegrees`
- `PierceCount`, `PierceDamageRetention`
- `DefultAmmo`, `MaxAmmo`

### 근접 전용 변수

- `MeleeRange`
- `MeleeHalfAngleDegrees`
- `MeleeKnockbackStrength`
- `MeleeHitReactDuration`

### 오라 전용 변수

- `AuraClass`
- `AuraRadius`
- `AuraTickInterval`
- `AuraDuration`
- `AuraElementType`
- `AuraNiagaraSystems`

### 설계 효과

- 새 무기를 추가할 때 기존 공격 코드를 재사용할 수 있다.
- 밸런스와 외형을 한 에셋에서 설정할 수 있다.
- `EditCondition`으로 무기 타입과 관계있는 속성만 에디터에 노출한다.
- 디자이너가 코드 컴파일 없이 무기 변형을 제작할 수 있다.

### 트레이드오프

원거리, 근접, 오라 필드가 하나의 DataAsset에 모여 있기 때문에 무기 유형이 증가하면 사용하지 않는 필드도 함께 늘어납니다. 프로젝트가 커지면 공통 데이터와 타입별 데이터를 Fragment 또는 별도 DataAsset으로 나누는 방향이 적합합니다.

---

## 6. 투사체 설계: AZProjectileBase

### 핵심 컴포넌트

| 변수 | 역할 |
|---|---|
| `CollisionComponent` | 충돌 및 Overlap 판정 |
| `MeshComponent` | 투사체 시각 표현 |
| `ProjectileMovement` | 투사체 이동 |
| `ProjectileDataTable` | 투사체 기본 데이터 테이블 |
| `ProjectileRowName` | 사용할 DataTable 행 |

### 런타임 상태

| 변수 | 역할 |
|---|---|
| `RuntimeDamageOverride` | 무기와 강화가 반영된 실제 피해량 |
| `RuntimeRemainingPierceCount` | 남은 관통 가능 횟수 |
| `RuntimePierceDamageRetention` | 관통 후 유지되는 피해 비율 |
| `RuntimeHitActors` | 동일 액터 중복 타격 방지 |
| `RuntimeElementType` | 적에게 전달할 속성 |
| `RuntimeElementEffectScale` | 상태이상 강도 |
| `HeadshotDamageMultiplier` | 헤드샷 피해 배율 |
| `HeadshotHeightRatio` | 액터 높이에 대한 헤드샷 판정 기준 |

투사체 기본 형태는 DataTable에서 가져오고, 발사 순간에 무기 및 캐릭터 강화가 반영된 값을 런타임 변수로 주입합니다. 기본 정의와 한 번의 발사에만 필요한 상태를 분리한 것입니다.

---

## 7. 오브젝트 풀 설계: UZActorPoolSubsystem

`UZActorPoolSubsystem`은 `UWorldSubsystem`으로 구현되어 현재 World 단위의 액터 풀을 관리합니다.

### 핵심 변수

| 변수 | 역할 |
|---|---|
| `Pools` | 클래스별 `AvailableActors`, `InUseActors` 보관 |
| `ActorToPoolClass` | 액터에서 원래 풀 클래스로 역추적 |

### 실행 흐름

```text
AcquireActor()
→ AvailableActors에 객체가 있으면 재사용
→ 없으면 SpawnPooledActor()
→ 위치, 충돌, 가시성 및 런타임 상태 초기화
→ InUseActors로 이동

ReleaseActor()
→ 충돌과 가시성 비활성화
→ 런타임 상태 초기화
→ AvailableActors로 반환
```

### 설계 이유

투사체를 매번 `SpawnActor()`/`Destroy()`하면 반복적인 메모리 할당과 GC 부하가 발생합니다. 특히 적과 발사체 수가 동시에 증가하는 게임에서 순간적인 프레임 저하 원인이 될 수 있습니다.

### 효과

- 반복 생성 및 삭제 비용 감소
- GC 대상 감소
- 다량 발사 시 프레임 안정성 향상
- Character는 풀의 내부 저장 구조를 알 필요가 없음

### 중요한 구현 조건

풀링 객체는 반환될 때 타이머, 충돌, 속도, 관통 횟수, 이미 맞은 액터 목록을 모두 초기화해야 합니다. `AZProjectileBase`가 `IZPoolableActorInterface`의 획득/반환 이벤트를 구현한 이유가 여기에 있습니다.

---

## 8. 적 설계: AZEnemyBase

### 클래스 역할

`AZEnemyBase`는 `ACharacter`, `IZDamageableInterface`, `IAbilitySystemInterface`를 기반으로 추적, 공격, 피해, 상태이상, 사망과 보상을 처리합니다.

### AI 및 상태 변수

| 변수 | 의미 |
|---|---|
| `TargetPlayer` | 현재 추적 대상 |
| `ChaseRange` | 추적을 시작할 거리 |
| `StopRange` | 이동을 멈출 거리 |
| `AttackRange` | 공격 가능 거리 |
| `AttackDamage` | 기본 공격 피해 |
| `AttackCooldown` | 공격 간격 |
| `bIsChasingTarget` | 추적 상태 |
| `bIsAttackingTarget` | 공격 상태 |
| `bIsInHitReactState` | 피격 반응 상태 |
| `bIsRunnerDashing` | Runner 대시 상태 |
| `bIsDead` | 사망 상태 및 중복 처리 방지 |

현재 AI는 Behavior Tree가 아니라 Tick과 상태 bool, 남은 시간 변수로 구현돼 있습니다. 행동 수가 제한된 프로토타입에서는 구조가 단순하고 디버깅이 빠르다는 장점이 있습니다.

행동 종류가 늘어나면 bool 조합이 모순된 상태를 만들 수 있으므로 명시적인 enum 상태 머신, StateTree 또는 Behavior Tree로 이전하는 편이 안전합니다.

### 몬스터 변형 변수

| 변수 | 의미 |
|---|---|
| `MonsterType` | Basic, Heavy, Runner 행동 유형 |
| `MonsterRank` | Normal, Elite, Boss 등급 |
| `MonsterActorScale` | 크기 차이 |
| `MonsterVisualTint` | 시각 구분 |
| `MonsterHitReactMultiplier` | 피격 반응 차이 |
| `MonsterKnockbackMultiplier` | 밀려나는 정도 |
| `MonsterAnimationPlayRateMultiplier` | 애니메이션 속도 |
| `MonsterRunnerDashLaunchSpeedMultiplier` | Runner 대시 속도 보정 |

`FZMonsterVariantDefinition`을 적용해 동일한 적 클래스를 여러 변형으로 사용합니다.

```text
최종 적 능력치
= 기본 적 수치
× 웨이브 배율
× 몬스터 변형 배율
```

이 구조는 Blueprint 복제를 줄이고 몬스터 밸런스를 DataTable에서 비교 가능하게 합니다.

### 속성 상태이상

- Fire: 일정 시간 주기 피해
- Cold: 이동속도 감소
- Lightning: 즉시 피해와 재적용 쿨다운
- Poison: 장시간 주기 피해

`ElementStatusBalanceTable`이 있으면 해당 데이터를 사용하고, 없으면 클래스 기본값을 fallback으로 사용합니다. 데이터 누락 때문에 상태이상 전체가 동작하지 않는 상황을 줄이기 위한 방어 설계입니다.

### 사망과 보상 흐름

```text
피해 수신
→ HP 반영
→ Die()
→ GameMode::NotifyEnemyDead()
→ 경험치 픽업 생성
→ 등급별 상자/메타 재화 지급
→ 사망 연출 후 제거
```

---

## 9. 스테이지 설계: AProject_Z_GameMode

### 주요 변수

| 변수 | 역할 |
|---|---|
| `StageDefinitionAsset` | 스테이지 설정과 웨이브 테이블 참조 |
| `MonsterVariantTable` | 생성할 몬스터 변형 정보 |
| `LoadedWaveDefinitions` | 로드한 웨이브 데이터의 런타임 복사본 |
| `CurrentStateIndex` | 현재 진행 중인 데이터 행 인덱스 |
| `AliveEnemyCount` | 현재 살아 있는 적 수 |
| `bStageClered` | 클리어 중복 처리 방지 |
| `bGameOver` | 게임오버 중복 처리 방지 |

### 실행 흐름

```text
BeginPlay()
→ LoadWaveDefinition()
→ StartTPSStage()
→ 현재 FZWaveDefinition 선택
→ MonsterVariantRowNames 순회
→ AZEnemyBase 생성 및 Variant 적용
→ AliveEnemyCount 증가
→ 적 사망 통지를 받을 때 감소
→ 0이 되면 HandleStageClear()
```

### GameMode에 둔 이유

스테이지 진행과 승패 판정은 특정 캐릭터나 UI가 아니라 현재 게임 세션 전체의 규칙입니다. Unreal Framework에서 이런 규칙은 GameMode의 책임에 해당합니다.

- Enemy는 자신의 사망만 통지한다.
- GameMode가 전체 적 수와 클리어 여부를 판단한다.
- PlayerController는 결과 UI를 표시한다.

이렇게 하면 적이나 UI가 스테이지 전체 상태를 직접 소유하지 않습니다.

### 현재 구조의 한계

현재 `LoadedWaveDefinitions`의 각 행은 사실상 순차 스테이지처럼 사용됩니다. `Stage`, `Wave`, `CurrentStateIndex` 용어가 일관되지 않으며, 한 스테이지 안에서 여러 웨이브를 운영하는 구조는 아닙니다.

면접에서는 다음과 같이 말하는 것이 정확합니다.

> 현재는 WaveDefinition 한 행을 한 진행 단위로 사용한 프로토타입입니다. 다중 웨이브 스테이지로 확장한다면 StageIndex와 WaveIndex를 분리하고, 생성 대기 수와 생존 수를 각각 추적하겠습니다.

---

## 10. PlayerController와 UI 설계

### AProject_Z_PlayerController 역할

- HUD, Crosshair, Interaction Marker 생성
- 메인 메뉴, 일시정지, 게임오버, 스테이지 클리어 화면 전환
- Game Only / UI 입력 모드 전환
- 캐릭터 선택 데이터 적용
- 발사, 재장전, 상호작용 입력 전달
- 재시작과 다음 스테이지 요청

### 주요 변수

| 변수 종류 | 역할 |
|---|---|
| `TSubclassOf<...Widget>` | 생성할 Widget Blueprint 클래스를 외부에서 지정 |
| `Active...Widget` | 생성된 Widget 인스턴스를 보관해 중복 생성 방지 |
| `PlayableCharacterTable` | 플레이 가능한 캐릭터 목록과 특성 데이터 |

PlayerController는 사용자의 입력 환경과 로컬 UI를 관리하기 적합합니다. Character는 메뉴 화면을 알 필요가 없고 GameMode는 직접 Widget의 생명주기를 소유하지 않습니다.

### UI의 현재 트레이드오프

일부 HUD와 HP Bar는 `NativeTick()`에서 상태를 조회합니다. 초기 구현은 단순하지만 Widget과 적 수가 늘면 매 프레임 조회 비용도 증가합니다. 확장 단계에서는 Attribute 변경 Delegate, 경험치 변경 Delegate, 탄약 변경 Event를 구독하는 이벤트 기반 UI가 적합합니다.

---

## 11. 경험치와 보상 오브젝트

### AZExperiencePickupActor

주요 상태 변수는 다음과 같습니다.

- `ExperienceAmount`: 지급 경험치
- `TargetCharacter`: 끌려갈 대상
- `bDropMotionActive`: 최초 낙하 연출 상태
- `bAttracting`: 플레이어에게 흡수되는 상태
- `bCollected`: 중복 지급 방지

```text
적 사망 위치에 생성
→ 포물선 낙하
→ Character의 PickupRadius 진입
→ Character 방향으로 이동
→ AddExperience()
```

픽업이 플레이어의 `PickupRadius`를 조회하기 때문에 흡수 범위 업그레이드를 픽업별로 수정할 필요가 없습니다.

### AZRewardChestActor

`ChestType`으로 Treasure Chest와 Lucky Box를 구분합니다.

- Treasure Chest: 정해진 보상 흐름
- Lucky Box: Heal, Shockwave, Upgrade 중 확률 선택

`bClaimed`는 Overlap이 여러 번 들어와도 보상이 한 번만 지급되게 합니다. 확률, 회복 비율, 충격파 범위는 변수로 노출되어 코드 수정 없이 조정할 수 있습니다.

---

## 12. 영구 성장: UZMetaProgressionSubsystem

### 사용한 Unreal 수명주기

`UZMetaProgressionSubsystem`은 `UGameInstanceSubsystem`입니다. 맵보다 긴 수명을 가지며, 현재 실행 전체에서 접근 가능한 영구 성장 관리자 역할을 합니다.

### 핵심 데이터

- `ActiveSaveGame`: 메모리에 로드된 저장 객체
- `SaveSlotName`: 저장 슬롯 식별자
- `Currency`: 획득한 영구 재화
- `UpgradeLevels`: 강화 타입별 레벨

### 책임

- 저장 데이터 로드와 저장
- 재화 획득
- 강화 비용 계산
- 구매 가능 여부 검사
- 강화 구매
- 초기화와 환불

Character나 UI가 직접 SaveGame API를 호출하지 않게 하여 저장 규칙의 중복과 불일치를 줄였습니다.

---

## 13. 기술 선택의 핵심 효과

### 데이터 중심 설계

코드 수정 없이 무기, 몬스터, 스테이지, 레벨업 수치를 조정할 수 있습니다. 동일한 C++ 로직을 여러 콘텐츠가 공유합니다.

### 원본과 런타임 상태 분리

공유 DataAsset에는 정의값을 두고 현재 플레이 상태는 Actor에 보관합니다. 데이터 오염과 세션 간 상태 누출을 막습니다.

### Unreal Framework 책임 활용

- GameMode: 현재 게임 규칙
- PlayerController: 로컬 입력과 화면
- Character: 플레이어의 월드 행동
- WorldSubsystem: World 단위 풀
- GameInstanceSubsystem: 맵을 넘어 유지되는 성장

### 다수 객체 대응

투사체 풀링과 데이터 기반 적 변형으로 많은 발사체와 적을 상대하는 장르의 요구사항에 대응했습니다.

---

## 14. 면접관 관점에서 보이는 기술 부채

### 14.1 AZCharacterBase의 과도한 책임

현재 Character가 입력, 카메라, 조준, 엄폐, 장비, 공격, 애니메이션, 성장과 픽업을 모두 담당합니다. 빠른 프로토타이핑에는 유리하지만 변경 이유가 너무 많은 클래스입니다.

개선 우선순위는 다음과 같습니다.

1. `CombatComponent`: 무기 장착, 공격, 재장전
2. `ProgressionComponent`: 경험치, 레벨업, 강화 중첩
3. `AimComponent`: 마우스 조준, 회전, 조준 표시
4. `InteractionComponent`: 엄폐와 아이템 상호작용

### 14.2 GAS와 수동 HP의 혼재

플레이어와 적이 `AttributeSet`을 가지지만 적은 `CurrentHP`, `MaxHP`도 따로 유지합니다. GameplayEffect 피해와 직접 함수 호출 피해가 병존하므로 동기화 누락 가능성이 있습니다.

개선 방향은 HP의 단일 원천을 `AttributeSet`으로 통일하고 피해, 회복, 사망 판정을 Attribute 변경 흐름에 연결하는 것입니다.

### 14.3 GameMode의 호환용 더미 API

생존 모드, 보스 정보, 남은 생성 수 관련 Getter 중 일부는 현재 고정된 `false`, `0`, `nullptr`을 반환합니다. 구현된 기능이 아니라 기존 UI 호출부를 유지하기 위한 호환 API이므로, 완성 기능처럼 설명하면 안 됩니다.

### 14.4 하드코딩된 에셋 경로

스테이지 DataAsset을 문자열 경로로 불러오는 fallback이 존재합니다. 에셋 이동이나 이름 변경에 취약합니다. 정상적인 설정 경로는 Blueprint, Soft Object Reference 또는 Asset Manager를 통해 주입하는 것입니다.

### 14.5 명명 불일치

- `CurrentStateIndex`: 실제로 Stage/Wave 진행 인덱스
- `bStageClered`: `bStageCleared` 오탈자
- `DefultAmmo`: `DefaultAmmo` 오탈자
- Stage와 Wave 용어 혼용

동작 문제는 아니지만, 팀 개발에서는 검색성과 의사소통 비용을 증가시킵니다.

---

## 15. 예상 기술 면접 질문과 답변

### Q1. 왜 무기를 상속 구조가 아니라 DataAsset으로 만들었나요?

무기별 차이의 대부분이 피해량, 쿨다운, 발사 수, 관통 수, 메시와 이펙트 같은 데이터였기 때문입니다. 공통 공격 흐름을 C++에 두고 차이를 DataAsset으로 표현하면 클래스 수와 Blueprint 복제를 줄일 수 있습니다. 다만 공격 규칙 자체가 완전히 다른 무기가 많아지면 전략 객체나 타입별 컴포넌트로 분리할 필요가 있습니다.

### Q2. 왜 투사체 풀을 WorldSubsystem으로 구현했나요?

투사체는 특정 Character가 아니라 현재 World에서 여러 발사 주체가 공유할 수 있는 자원입니다. WorldSubsystem을 사용하면 World의 수명과 함께 관리되고, Actor가 전역 Singleton의 수명이나 생성 순서를 직접 관리할 필요가 없습니다.

### Q3. 풀링에서 가장 조심한 부분은 무엇인가요?

재사용 객체의 이전 상태가 다음 사용에 남지 않도록 초기화하는 것입니다. 투사체의 타이머, 속도, 충돌, 관통 수, 피해 Override, 속성, 이미 타격한 Actor 집합을 획득과 반환 시점에 초기화해야 합니다.

### Q4. 왜 적 AI에 Behavior Tree를 사용하지 않았나요?

현재 행동이 추적, 공격, 피격, 대시 정도로 제한되어 있어 C++ Tick 상태 로직이 구현과 디버깅 면에서 단순했습니다. 행동 수와 전이 조건이 증가하면 bool 상태의 조합 복잡도가 커지므로 StateTree나 Behavior Tree로 전환하는 것이 더 적합합니다.

### Q5. GAS를 어디까지 사용했나요?

Character와 Enemy에 ASC와 AttributeSet을 두고 Ability 발동과 일부 GameplayEffect 피해에 사용했습니다. 그러나 모든 피해와 쿨다운이 GAS로 통일된 상태는 아닙니다. 현재는 기존 직접 로직과 GAS가 공존하는 전환 단계입니다.

### Q6. DataAsset을 런타임에 직접 수정하지 않은 이유는 무엇인가요?

DataAsset은 여러 인스턴스가 공유할 수 있는 정의 데이터입니다. 런타임 강화로 이를 변경하면 다른 객체에도 영향을 줄 수 있습니다. 따라서 원본은 읽기 전용 정의로 취급하고 현재 런의 변화는 Character 인스턴스 변수에 저장했습니다.

### Q7. 적 수로 클리어를 판정하면 생성 실패 시 문제가 없나요?

현재 구현에는 보완이 필요합니다. Spawn 함수가 성공 여부를 반환하지 않는데 호출 직후 `AliveEnemyCount`를 무조건 증가시키므로, Spawn 실패 시 죽을 수 없는 적이 카운트에 남아 스테이지가 종료되지 않을 수 있습니다. Spawn 성공 시에만 카운트를 증가시키고, 최종 생성 수가 0이면 실패 또는 빈 스테이지 정책을 명시적으로 처리해야 합니다.

### Q8. 가장 먼저 리팩터링할 부분은 무엇인가요?

첫 번째는 Enemy HP를 AttributeSet으로 단일화하는 것입니다. 상태의 원천이 두 개면 전투 안정성에 직접 영향을 줍니다. 두 번째는 Character의 전투와 성장 책임을 컴포넌트로 분리하는 것입니다. 그 다음으로 Stage/Wave 모델과 명명을 정리하겠습니다.

### Q9. UI를 왜 Tick으로 업데이트했나요?

초기 기능 검증에서 상태 연결을 빠르게 확인하기 위해 polling 방식을 사용했습니다. 규모가 커지면 불필요한 매 프레임 조회가 늘어나므로 ASC Attribute Delegate와 게임 상태 변경 Delegate를 사용하는 이벤트 기반 방식으로 변경하는 것이 목표입니다.

### Q10. 이 프로젝트에서 가장 의미 있는 설계 결정은 무엇인가요?

무기와 몬스터를 개별 클래스 복제로 늘리지 않고 공통 실행 코드와 데이터 정의로 분리한 점입니다. 이 결정 덕분에 콘텐츠 확장 속도를 확보했고, 런타임 강화는 별도 상태로 관리해 공유 데이터의 안정성도 유지할 수 있었습니다.

---

## 16. 면접용 3분 설명 예시

`Project_Z`는 다수의 적과 투사체가 등장하는 TPS 전투 프로젝트입니다. 저는 기능을 Unreal Framework의 수명과 책임에 맞춰 나누려고 했습니다. GameMode는 스테이지 데이터 로드, 적 생성, 생존 적 수와 클리어 판정을 담당합니다. PlayerController는 HUD와 메뉴, 입력 모드를 관리하고 Character는 이동과 실제 전투 행동을 담당합니다.

콘텐츠는 데이터 중심으로 구성했습니다. 캐릭터의 메시, 초기 능력치와 시작 장비는 Character DataAsset에 두고, 무기의 피해량, 쿨다운, 발사 패턴, 관통, 근접 범위, 오라 반경과 시각 효과는 Weapon DataAsset에 넣었습니다. 따라서 새 무기를 추가할 때 공통 공격 코드를 재사용하면서 데이터만 다르게 구성할 수 있습니다.

플레이 중 얻는 강화는 DataAsset을 수정하지 않고 Character의 `RuntimeProjectileDamageBonus`, `RuntimeAuraRadiusBonus` 같은 인스턴스 변수에 누적합니다. DataAsset은 공유 정의이므로 런타임에 변경할 경우 다른 인스턴스나 다음 플레이에 영향을 줄 가능성이 있기 때문입니다.

원거리 공격에서는 Character가 무기 데이터를 해석한 뒤 WorldSubsystem의 Actor Pool에서 투사체를 가져옵니다. 투사체에는 최종 피해량, 관통 수, 속성을 런타임 값으로 전달합니다. 투사체는 충돌 시 중복 타격을 방지하고, 수명이 끝나거나 사거리를 벗어나면 파괴되지 않고 풀로 반환됩니다. 이를 통해 반복적인 Spawn과 Destroy, GC 비용을 줄이려고 했습니다.

Enemy는 하나의 기본 클래스를 사용하고 DataTable의 몬스터 타입과 등급 배율을 적용합니다. 같은 코드로 Basic, Heavy, Runner와 Normal, Elite, Boss를 표현할 수 있습니다. 사망 시 GameMode에 통지하고 경험치 픽업과 등급별 보상을 생성합니다.

현재 한계도 있습니다. Character가 전투와 성장 등 너무 많은 책임을 가지고 있고, GAS Attribute와 직접 HP 관리가 일부 혼재합니다. 우선 Enemy HP를 AttributeSet으로 통일하고, Character의 전투와 성장 로직을 ActorComponent로 분리하는 것을 다음 리팩터링 우선순위로 보고 있습니다.

---

## 17. 설명할 때 피해야 할 표현

| 피해야 할 표현 | 더 정확한 표현 |
|---|---|
| “GAS로 모든 전투를 구현했습니다.” | “GAS를 Attribute와 Ability 진입점에 적용했고 직접 전투 경로를 통합 중입니다.” |
| “완전한 웨이브 시스템입니다.” | “현재 WaveDefinition 행을 순차 진행 단위로 사용하는 프로토타입입니다.” |
| “모든 UI가 최적화되어 있습니다.” | “현재 일부 UI는 polling 방식이며 이벤트 기반 전환이 개선 과제입니다.” |
| “어떤 무기도 데이터만으로 만들 수 있습니다.” | “현재 지원하는 원거리, 근접, 오라 공통 패턴은 데이터로 변형할 수 있습니다.” |
| “풀링으로 성능이 향상됐습니다.” | “Spawn/Destroy와 GC 부담을 줄이도록 설계했으며, 실제 개선 폭은 프로파일링으로 검증해야 합니다.” |

---

## 18. 검증 체크리스트

면접이나 발표 전 다음 항목을 실제 PIE에서 확인해야 합니다.

- Pistol, Rifle, Shotgun의 발사 패턴과 탄약 처리
- 투사체 반환 후 관통 수와 이미 맞은 대상 목록 초기화
- Projectile GameplayEffect 피해와 직접 피해 경로의 결과 일치
- Fire, Cold, Lightning, Poison 상태이상
- Normal, Elite, Boss 보상 차이
- 적 생성 실패 및 빈 Variant 목록에서 스테이지 진행 처리
- 플레이어 사망 처리의 중복 호출 방지
- 레벨업 선택지의 요구 조건과 최대 중첩
- 메타 강화 저장, 구매, 환불과 재실행 후 로드
- 다수 적 및 투사체 상황에서 `stat game`, `stat unit`, Unreal Insights 측정

성능에 대해서는 풀링을 사용했다는 사실만으로 개선을 단정하지 않고, 동일한 발사량에서 Spawn/Destroy 방식과 풀링 방식의 Game Thread 시간, 객체 생성 수, GC 시간을 비교하는 것이 기술적으로 타당합니다.

---

## 19. 분석 기준 주요 파일

- `Source/Project_Z/Public/Characters/ZCharacterBase.h`
- `Source/Project_Z/Private/Characters/ZCharacterBase.cpp`
- `Source/Project_Z/Public/Data/ZWeaponDataAsset.h`
- `Source/Project_Z/Public/Projectiles/ZProjectileBase.h`
- `Source/Project_Z/Private/Projectiles/ZProjectileBase.cpp`
- `Source/Project_Z/Public/Pooling/ZActorPoolSubsystem.h`
- `Source/Project_Z/Private/Pooling/ZActorPoolSubsystem.cpp`
- `Source/Project_Z/Public/Enemies/ZEnemyBase.h`
- `Source/Project_Z/Private/Enemies/ZEnemyBase.cpp`
- `Source/Project_Z/Public/GameModes/Project_Z_GameMode.h`
- `Source/Project_Z/Private/GameModes/Project_Z_GameMode.cpp`
- `Source/Project_Z/Public/Controllers/Project_Z_PlayerController.h`
- `Source/Project_Z/Public/MetaProgression/ZMetaProgressionSubsystem.h`
- `Source/Project_Z/Public/AttributeSets/UZAttributeSet.h`

## 20. 검증 상태

- 소스 기반 정적 분석: 완료
- 문서 작성: 완료
- C++ 빌드: 이번 문서 작업에서는 미실행
- PIE 기능 검증: 이번 문서 작업에서는 미실행
- 프로젝트 소스 및 에셋 변경: 없음
