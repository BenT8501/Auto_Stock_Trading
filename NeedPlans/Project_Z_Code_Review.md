# Project_Z C++ 코드 리뷰

## 리뷰 범위와 기준

- 대상: `Project/Project_Z/Source/Project_Z`
- 방식: C++ 소스 정적 리뷰
- 우선순위: 게임 진행 불가, 상태 불일치, 데이터 설정 무시, 객체 수명주기, 성능, 유지보수성
- 제외: Blueprint 그래프, `.uasset` 내부 설정, PIE 재현, 패키징 및 멀티플레이 실행 검증

심각도는 다음 기준으로 구분합니다.

- **치명적**: 게임 진행 불가, 크래시, 핵심 상태 손상 가능성
- **중요**: 잘못된 결과, 기능 설정 무시, 확장 시 높은 장애 가능성
- **참고**: 구조, 성능, 명명과 유지보수 개선

---

## 결론 요약

현재 코드는 데이터 중심 구성, 투사체 풀링, Unreal Subsystem 활용처럼 확장성을 고려한 방향이 보입니다. 그러나 전투와 스테이지 핵심 상태에 복수의 원천이 존재하고, 데이터 구조에 선언된 값과 실제 실행 코드 사이에 차이가 있습니다.

수정 우선순위는 다음 순서가 타당합니다.

1. 적 HP의 단일 원천 확립
2. 적 Spawn 성공 여부와 `AliveEnemyCount` 일치
3. 0마리 생성 시 스테이지 종료 정책 추가
4. Wave/Stage 데이터 필드의 실제 적용 또는 제거
5. 풀의 중복 반환 방어
6. Character 책임 분리와 UI 이벤트화

---

# 발견 사항

## [치명적] CR-01: Enemy HP가 두 곳에 저장되어 피해 순서에 따라 체력이 되돌아갈 수 있음

### 근거

- `AZEnemyBase::ReceiveDamage_Implementation()`은 `CurrentHP`만 감소시킵니다.
- 속성 지속 피해도 `CurrentHP`를 직접 감소시킵니다.
- 투사체의 GAS 피해는 `AttributeSet::HP`를 감소시킨 뒤 `SyncHealthFromAttributeSet()`으로 `CurrentHP`를 덮어씁니다.
- Enemy는 `CurrentHP`, `MaxHP`, `AttributeSet`을 모두 보유합니다.

관련 위치:

- `Private/Enemies/ZEnemyBase.cpp:171`
- `Private/Enemies/ZEnemyBase.cpp:921`
- `Private/Enemies/ZEnemyBase.cpp:1141`
- `Private/Projectiles/ZProjectileBase.cpp:371`

### 실패 시나리오

```text
초기 상태
CurrentHP = 30
AttributeSet.HP = 30

근접 공격 20 피해
CurrentHP = 10
AttributeSet.HP = 30

GAS 투사체 5 피해
AttributeSet.HP = 25
SyncHealthFromAttributeSet()
CurrentHP = 25
```

근접 공격으로 감소했던 체력 일부가 사실상 복구됩니다. 반대 순서에서도 두 값이 다시 어긋날 수 있습니다.

### 영향

- 무기 종류와 공격 순서에 따라 적의 실질 체력이 달라집니다.
- HP Bar와 사망 판정이 서로 다른 값을 표시하거나 사용할 수 있습니다.
- 상태이상 피해 후 일반 투사체를 맞았을 때 적이 살아나는 것처럼 보일 수 있습니다.

### 수정 방향

`AttributeSet::HP`를 유일한 체력 원천으로 사용하는 것이 가장 안전합니다.

- 직접 피해, 근접 피해, 상태이상 피해를 GameplayEffect 또는 공통 Damage 함수로 통합합니다.
- `CurrentHP`, `MaxHP` 멤버를 제거하거나 읽기 전용 캐시로 제한합니다.
- 사망 판정은 HP Attribute 변경 Delegate 한 곳에서 수행합니다.
- 임시 수정이라면 모든 직접 피해 경로에서 두 HP를 동시에 갱신해야 하지만, 장기 해법으로는 권장하지 않습니다.

---

## [치명적] CR-02: Enemy Spawn 실패에도 AliveEnemyCount가 증가하여 스테이지가 끝나지 않을 수 있음

### 근거

`SpawnEnemyWithVariant` 람다는 Spawn에 실패하면 내부에서 반환하지만 성공 여부를 호출자에게 전달하지 않습니다. 이후 호출부는 결과와 관계없이 `AliveEnemyCount++`를 실행합니다.

관련 위치:

- `Private/GameModes/Project_Z_GameMode.cpp:169`
- `Private/GameModes/Project_Z_GameMode.cpp:174`
- `Private/GameModes/Project_Z_GameMode.cpp:182`
- `Private/GameModes/Project_Z_GameMode.cpp:226`
- `Private/GameModes/Project_Z_GameMode.cpp:229`

### 영향

충돌 위치, 잘못된 Enemy Class, World Spawn 실패 등으로 실제 적이 생성되지 않아도 생존 수에는 포함됩니다. 해당 카운트는 사망 통지를 보낼 Actor가 없으므로 0이 되지 않고 스테이지가 교착됩니다.

### 수정 방향

Spawn 람다가 `AZEnemyBase*` 또는 `bool`을 반환하게 변경하고 성공했을 때만 증가시켜야 합니다.

```cpp
if (AZEnemyBase* SpawnedEnemy = SpawnEnemyWithVariant(*EnemyVariant))
{
    ++AliveEnemyCount;
}
```

모든 생성 시도가 끝난 뒤 `AliveEnemyCount == 0`인 경우도 명시적으로 처리해야 합니다.

---

## [중요] CR-03: 생성 가능한 적이 0명일 때 스테이지 상태가 진행되지 않음

### 근거

다음 조건은 모두 함수에서 바로 반환합니다.

- `EnemyClass`가 없음
- `MonsterVariantRowNames`가 비어 있음
- `MonsterVariantTable`이 없음
- 모든 RowName이 비어 있거나 조회에 실패함

하지만 이 경로들은 `HandleStageClear()` 또는 실패 화면으로 전환하지 않습니다. `StartTPSStage()`에서 이미 `bStageClered = false`로 바꾼 상태라면 진행 가능한 적도 없고 다음 스테이지로 넘어갈 수도 없습니다.

관련 위치:

- `Private/GameModes/Project_Z_GameMode.cpp:22`
- `Private/GameModes/Project_Z_GameMode.cpp:147`

### 수정 방향

Spawn 결과를 `SpawnedCount`, `FailedCount`로 집계하고 정책을 정해야 합니다.

- 데이터 오류를 게임오버/오류 화면으로 처리
- 빈 스테이지를 즉시 클리어 처리
- 또는 개발 빌드에서 `ensureMsgf`로 설정 오류를 강하게 노출

로그만 남기고 진행 상태를 유지하는 현재 방식은 피해야 합니다.

---

## [중요] CR-04: FZWaveDefinition의 주요 필드가 실행 코드에서 사용되지 않음

### 근거

`FZWaveDefinition`에는 다음 값이 선언되어 있습니다.

- `EnemyCount`
- `SpawnInterval`
- `SpawnDistance`
- `HPMultiplier`
- `MoveSpeedMultiplier`
- `ExperienceMultiplier`

하지만 GameMode는 `MonsterVariantRowNames`의 원소당 적 한 명을 즉시 생성합니다. `ApplyWaveScaling()`도 호출되지 않으며, Spawn 거리는 GameMode의 `SpawnRadiusMin`, `SpawnRadiusMax`를 사용합니다.

관련 위치:

- `Public/Data/FZWaveDefinition.h:30`
- `Private/GameModes/Project_Z_GameMode.cpp:147`
- `Private/Enemies/ZEnemyBase.cpp:194`

### 영향

- 에디터에서 `EnemyCount`를 변경해도 실제 생성 수가 변하지 않습니다.
- `SpawnInterval`을 설정해도 모든 적이 한 프레임에 생성됩니다.
- 웨이브 HP, 속도, 경험치 배율이 적용되지 않습니다.
- 데이터 작성자는 값이 적용된다고 오해하기 쉽습니다.

### 수정 방향

사용할 필드는 실제 생성 흐름에 연결하고, 사용하지 않을 계획이라면 데이터 구조에서 제거하거나 Deprecated로 표시해야 합니다. 특히 `EnemyCount`와 `MonsterVariantRowNames` 사이의 관계를 먼저 정의해야 합니다.

예시 정책:

- Variant 목록에서 가중치로 `EnemyCount`회 선택
- Variant 배열 원소 하나를 적 한 명으로 간주하고 `EnemyCount` 제거

두 의미를 동시에 유지하면 데이터가 모순될 수 있습니다.

---

## [중요] CR-05: UZStageDefinitionAsset의 Stage 설정값이 사용되지 않음

### 근거

Stage Asset에는 다음 값이 있지만 현재 C++ 참조가 없습니다.

- `StageDuration`
- `StageHPMultiplier`
- `StageDamageMultiplier`
- `StageXPRewardMultiplier`

관련 위치:

- `Public/Data/UZStageDefinitionAsset.h:25`

### 영향

DataAsset에서 조정한 값이 플레이에 반영되지 않습니다. 특히 시간제 스테이지나 단계별 난이도 배율이 구현된 것처럼 보이지만 실제 동작하지 않습니다.

### 수정 방향

Stage 시작 시 Wave 배율과 결합해 Enemy에 적용하고, 시간제 진행이 요구사항이 아니라면 `StageDuration`을 제거해야 합니다. 데이터 필드는 “향후 사용할 예정”이라는 이유만으로 활성 스키마에 두지 않는 편이 검증과 유지보수에 안전합니다.

---

## [중요] CR-06: Actor Pool이 동일 Actor의 중복 반환을 허용함

### 근거

`ReleaseActor()`는 Actor가 실제로 `InUseActors`에 있었는지 확인하지 않고 다음 작업을 수행합니다.

1. `InUseActors.Remove(Actor)`
2. 반환 준비
3. `AvailableActors.Add(Actor)`

관련 위치:

- `Private/Pooling/ZActorPoolSubsystem.cpp:82`

같은 Actor에 `ReleaseActor()`가 두 번 호출되면 `AvailableActors`에 동일 포인터가 중복으로 들어갑니다. 이후 두 번의 Acquire가 동일 Actor를 동시에 사용 중인 것으로 반환할 수 있습니다.

### 수정 방향

- `InUseActors.RemoveSingleSwap(Actor) == 0`이면 중복 반환으로 판단하고 종료합니다.
- `AvailableActors.Contains(Actor)` 검사를 추가합니다.
- Pool 상태 위반에는 `ensureMsgf`를 사용해 개발 중 즉시 발견할 수 있게 합니다.

---

## [중요] CR-07: Attribute 복제 선언이 불완전함

### 근거

`GetLifetimeReplicatedProps()`에서 HP, MP, Stamina, MovementSpeed 등을 `DOREPLIFETIME_CONDITION_NOTIFY`로 등록하지만 헤더의 각 `UPROPERTY`에는 `Replicated` 또는 `ReplicatedUsing` 지정과 `OnRep` 함수가 없습니다.

관련 위치:

- `Public/AttributeSets/UZAttributeSet.h:28`
- `Private/AttributeSets/UZAttributeSet.cpp:113`

Enemy ASC는 명시적으로 복제를 끈 상태이므로 현재 싱글플레이에서는 노출되지 않을 수 있습니다. 하지만 멀티플레이 지원 의도를 가진 코드로 보기에는 불완전합니다.

### 수정 방향

- 멀티플레이가 범위라면 `ReplicatedUsing=OnRep_HP`와 `GAMEPLAYATTRIBUTE_REPNOTIFY` 패턴을 적용합니다.
- 싱글플레이 전용이라면 사용되지 않는 복제 코드를 제거해 의도를 명확히 합니다.

---

## [중요] CR-08: Primary Ability의 이름과 실제 지원 범위가 불일치함

### 근거

`UZGA_PrimaryAttack`은 `AZCharacterBase::ActivatePrimaryWeapon()`을 호출합니다. 그러나 해당 함수는 `IsSupportedFirearm()` 검사를 통과한 총기만 처리하고 근접 및 오라 분기는 실행하지 않습니다.

관련 위치:

- `Private/Abilities/ZGA_PrimaryAttack.cpp:10`
- `Private/Characters/ZCharacterBase.cpp:1396`

프로젝트가 총기 전용으로 범위를 축소한 것이 현재 의도라면 기능 오류는 아닙니다. 다만 `WeaponType`에는 여전히 Melee와 Aura가 있고 관련 실행 함수도 남아 있어 API 이름만 보면 모든 Primary Weapon을 처리할 것으로 오해할 수 있습니다.

### 수정 방향

- 총기 전용이 최종 요구사항이면 `ActivatePrimaryFirearm()`처럼 이름과 데이터 범위를 일치시킵니다.
- 근접/오라를 유지할 계획이면 `WeaponType`에 따른 명시적 dispatch를 구현합니다.

---

## [참고] CR-09: AZCharacterBase가 너무 많은 변경 이유를 가짐

### 근거

`AZCharacterBase`가 다음 책임을 모두 가집니다.

- Enhanced Input
- 카메라 모드
- 조준과 회전
- 엄폐
- 장비와 탄약
- 투사체, 근접, 오라 공격
- 애니메이션 선택
- 경험치와 레벨업 선택지 생성
- 캐릭터 특성 및 메타 성장 반영
- VFX 경로 fallback

구현 파일은 약 3,600줄이며 기능 간 결합이 높습니다.

### 영향

- 한 기능 변경이 다른 기능에 영향을 줄 가능성이 커집니다.
- 단위 테스트 대상을 분리하기 어렵습니다.
- 여러 개발자가 동시에 수정할 때 충돌이 증가합니다.

### 수정 방향

한 번에 대규모 분해하지 말고 다음 순서로 이동하는 것이 안전합니다.

1. `UZCombatComponent`: 장비, 탄약, 공격 dispatch
2. `UZProgressionComponent`: 경험치, 레벨, 강화 Stack
3. `UZAimComponent`: 조준점, 캐릭터 회전, Aim Offset
4. `UZInteractionComponent`: 엄폐와 픽업 상호작용

ActorComponent로 옮기더라도 GAS Attribute의 소유권은 ASC와 Avatar 관계를 고려해 Character에 유지하는 것이 자연스럽습니다.

---

## [참고] CR-10: UI가 매 프레임 전체 상태를 polling함

### 근거

`UZStateHUDWidget::NativeTick()`이 매 프레임 `RefreshCurrentStatus()`를 호출합니다. `TickUpdate()`에도 동일 호출이 존재합니다.

관련 위치:

- `Private/UI/ZStateHUDWidget.cpp:93`
- `Private/UI/ZStateHUDWidget.cpp:99`

### 영향

HUD 하나에서는 영향이 작지만 Enemy HP Bar나 추가 UI가 같은 패턴을 사용하면 매 프레임 Cast, Getter, Widget 갱신이 누적됩니다. 값이 변하지 않았는데도 Slate 속성을 다시 설정할 수 있습니다.

### 수정 방향

- HP, Stamina: ASC Attribute 변경 Delegate
- 경험치, 레벨, 탄약: Character 또는 Component의 multicast delegate
- 무기 교체: 장착 완료 이벤트
- Tick은 조준점처럼 실제로 프레임 단위 갱신이 필요한 UI에만 사용

---

## [참고] CR-11: 동기 로드와 하드코딩된 에셋 경로가 전투 클래스에 분산됨

### 근거

`StaticLoadObject()`와 `LoadSynchronous()`가 Character, Enemy, GameMode의 실행 코드 여러 곳에 있습니다.

예시 위치:

- `Private/GameModes/Project_Z_GameMode.cpp:95`
- `Private/Characters/ZCharacterBase.cpp:1819`
- `Private/Characters/ZCharacterBase.cpp:3321`
- `Private/Enemies/ZEnemyBase.cpp:558`

### 영향

- 에셋 이동이나 이름 변경에 취약합니다.
- 로드되지 않은 에셋을 전투 중 동기 로드하면 순간 정지가 발생할 수 있습니다.
- 콘텐츠 의존성을 코드 검색으로 찾아야 합니다.

### 수정 방향

- 필수 에셋은 DataAsset 또는 Blueprint 기본값으로 주입합니다.
- 선택 콘텐츠는 `TSoftObjectPtr`와 Streamable Manager로 미리 비동기 로드합니다.
- Asset Manager의 Primary Asset 체계를 일관되게 사용합니다.
- 문자열 경로 fallback은 개발용 보정 경로로만 제한하고 경고를 남깁니다.

---

## [참고] CR-12: Stage/Wave 명명과 호환 API가 현재 기능 범위를 흐림

### 근거

- `CurrentStateIndex`가 Stage/Wave 인덱스처럼 사용됩니다.
- `bStageClered`에 오탈자가 있습니다.
- 생존 모드와 Boss Getter 일부가 고정값을 반환합니다.
- 헤더 주석에 임시 호환 API라고 명시되어 있습니다.

관련 위치:

- `Public/GameModes/Project_Z_GameMode.h:29`
- `Public/GameModes/Project_Z_GameMode.h:119`

### 영향

호출자는 API가 실제 기능을 제공한다고 오해할 수 있고, Blueprint 참조가 남은 상태에서는 제거도 어려워집니다.

### 수정 방향

- Stage와 Wave의 도메인 모델을 먼저 확정합니다.
- `CurrentStageIndex`, `CurrentWaveIndex`를 분리합니다.
- Blueprint 참조를 교체한 뒤 호환 API를 제거합니다.
- 고정값 Getter에는 `DeprecatedFunction` 메타를 적용해 신규 사용을 차단합니다.

---

# 긍정적인 구현 사항

## 데이터 원본과 런타임 상태 분리

Weapon DataAsset의 기본값을 직접 수정하지 않고 Character와 Projectile에 런타임 Override를 둔 방향은 적절합니다. 공유 에셋 오염을 막고 현재 런의 강화 상태를 분리할 수 있습니다.

## 풀링 객체의 투사체 상태 초기화

`AZProjectileBase::OnAcquiredFromPool_Implementation()`과 `OnReleasedToPool_Implementation()`에서 피해 Override, 관통, 타격 목록, 속성, 이동과 타이머를 초기화합니다. 풀링에서 가장 흔한 이전 상태 누수를 의식한 구현입니다.

## 중복 피해와 중복 사망 방어

- Projectile의 `RuntimeHitActors`
- Enemy의 `bIsDead`
- Pickup의 `bCollected`
- Reward Chest의 `bClaimed`

여러 Overlap이나 재진입으로 동일 효과가 반복 적용되는 문제를 방어합니다.

## 데이터 입력값 방어

다수의 `ClampMin`, `ClampMax`, `FMath::Clamp()`를 사용해 음수 체력, 잘못된 배율, 0 이하 Tick Interval 같은 위험 값을 제한합니다.

## Unreal 수명주기에 맞는 Subsystem 선택

- 투사체 풀: `UWorldSubsystem`
- 영구 성장: `UGameInstanceSubsystem`

관리 대상의 수명에 맞춰 Subsystem 종류를 선택한 점은 타당합니다.

---

# 권장 수정 계획

## 1단계: 게임 진행과 전투 정합성

- Enemy HP를 AttributeSet으로 단일화
- Spawn 함수가 성공 Actor를 반환하도록 변경
- 생성 결과가 0일 때 명시적 실패/클리어 처리
- 관련 자동화 테스트 또는 재현용 테스트 맵 작성

## 2단계: 데이터 계약 정리

- `EnemyCount`와 Variant 목록의 의미 확정
- Spawn Interval 및 Wave 배율 적용
- Stage 배율과 Duration의 사용 여부 확정
- 사용하지 않는 필드는 제거 또는 Deprecated 처리

## 3단계: 객체 수명 및 성능

- Pool 중복 반환 방어
- 동기 에셋 로드를 사전 로드로 이전
- UI Attribute Delegate 적용
- Unreal Insights로 투사체 풀 전후 비교

## 4단계: 구조 리팩터링

- Character에서 Combat과 Progression 컴포넌트 분리
- Enemy AI 상태를 enum/StateTree/Behavior Tree 중 요구 규모에 맞게 이전
- Stage/Wave 모델과 API 명명 정리

---

# 필수 검증 시나리오

| 테스트 | 기대 결과 |
|---|---|
| 근접 피해 후 GAS 투사체 피해 | 이전 피해가 복구되지 않고 누적되어야 함 |
| 상태이상 피해 후 GAS 투사체 피해 | HP Bar와 사망 판정이 동일 HP를 사용해야 함 |
| Enemy Spawn을 의도적으로 실패시킴 | AliveEnemyCount에 실패 Actor가 포함되지 않아야 함 |
| 모든 Variant Row를 잘못 지정 | 명시적 오류 상태 또는 정책대로 즉시 종료되어야 함 |
| Pool Actor를 두 번 반환 | 두 번째 반환이 거부되어야 함 |
| 같은 Projectile을 연속 재사용 | 이전 관통 수, 속성, HitActors, Timer가 남지 않아야 함 |
| EnemyCount와 SpawnInterval 변경 | 실제 생성 수와 간격에 반영되어야 함 |
| Stage 배율 변경 | HP, Damage, XP 결과에 반영되어야 함 |
| 다수 적과 투사체 프로파일링 | 풀 적용 전후 Game Thread 및 GC 수치 비교 |

---

# 리뷰 상태

- 정적 코드 리뷰: 완료
- Blueprint 및 에셋 참조 검증: 미실행
- C++ 빌드: 미실행
- PIE 재현 테스트: 미실행
- 수정 코드 적용: 없음

이 문서의 발견 사항은 정적 분석 결과입니다. 치명적 항목은 코드 경로상 발생 가능성이 명확하지만, 최종 수정 전에는 최소 재현 테스트와 현재 Blueprint 설정 확인이 필요합니다.
