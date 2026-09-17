# Project_Z 코드 리뷰 연습 워크북

## 1. 연습 목적

이 문서는 `Project_Z`의 실제 코드를 대상으로 코드 리뷰를 연습하기 위한 자료다.

목표는 버그를 많이 찾는 것이 아니다. 다음 능력을 훈련하는 것이 핵심이다.

1. 코드의 의도를 먼저 파악한다.
2. 정상 흐름과 실패 흐름을 분리한다.
3. 상태의 소유자와 변경 경로를 추적한다.
4. 추측이 아니라 코드 근거로 위험을 설명한다.
5. 문제의 심각도와 수정 우선순위를 판단한다.
6. 최소 수정안과 장기 개선안을 구분한다.
7. 수정 후 무엇을 검증해야 하는지 제시한다.

분석 대상:

- `Project/Project_Z/Source/Project_Z`
- `Plans/박종호B_직무과제_완료보고서_정리.md`
- `_workspace/Project_Z/docs/Project_Z_Code_Review.md`

기존 코드 리뷰 문서는 정답지로 사용한다. 먼저 이 워크북으로 직접 답한 뒤 비교하는 것을 권장한다.

---

## 2. 코드 리뷰의 기본 사고 순서

코드를 보자마자 스타일이나 함수 길이부터 지적하지 않는다. 다음 순서로 검토한다.

```text
요구사항과 의도
→ 상태 소유자
→ 상태 변경 경로
→ 정상 실행 흐름
→ 실패·중복·취소 흐름
→ 객체 수명
→ 데이터 유효성
→ 성능과 확장성
→ 테스트 가능성
```

### 2.1 요구사항

- 이 함수가 보장해야 하는 결과는 무엇인가?
- 성공과 실패를 호출자가 구분할 수 있는가?
- 데이터가 없을 때 중단, 대체, 즉시 완료 중 어떤 정책을 사용하는가?

### 2.2 상태 소유권

- 이 값의 유일한 원천은 어디인가?
- 같은 의미의 값이 다른 클래스에도 있는가?
- 누가 쓸 수 있고 누가 읽기만 하는가?
- 모든 변경 경로가 동일한 규칙을 통과하는가?

### 2.3 불변조건

불변조건은 정상 실행 중 항상 지켜져야 하는 규칙이다.

예:

```text
HP는 0 이상 MaxHP 이하이다.
Pool Actor는 Available과 InUse 중 한 곳에만 존재한다.
AliveEnemyCount는 실제 살아 있는 적 수와 같다.
사망 보상은 적 한 명당 한 번만 지급된다.
탄약은 0 이상 MaxAmmo 이하이다.
```

리뷰에서는 “어떤 코드가 이 불변조건을 깨뜨릴 수 있는가?”를 찾는다.

### 2.4 실패와 재진입

- 함수가 중간에 `return`하면 상태는 일관적인가?
- 동일 이벤트가 두 번 발생하면 안전한가?
- Timer와 Overlap이 같은 프레임에 실행되면 안전한가?
- Actor가 이미 파괴 중이거나 반환된 상태면 어떻게 되는가?
- 일부만 성공하면 전체 결과는 어떻게 처리되는가?

### 2.5 수명주기

- Actor와 Subsystem의 World가 같은가?
- Delegate를 등록한 객체가 먼저 파괴될 수 있는가?
- Timer가 객체 재사용 뒤에도 남는가?
- UObject 참조를 GC가 추적하는가?
- Soft Reference를 언제 로드하는가?

### 2.6 검증

- 이 문제를 가장 작은 조건으로 어떻게 재현하는가?
- 수정 전 실패하고 수정 후 통과하는 테스트를 만들 수 있는가?
- 성능 주장은 어떤 수치로 확인하는가?

---

## 3. 좋은 리뷰 코멘트 작성법

리뷰 코멘트는 다음 구조를 사용한다.

```text
[심각도] 제목

현재 동작:
발생 조건:
영향:
코드 근거:
최소 수정안:
장기 개선안:
검증 방법:
```

### 나쁜 예

> 이 코드는 위험해 보입니다. 풀링 처리를 개선해야 합니다.

문제점:

- 어떤 조건에서 위험한지 없다.
- 실제 영향이 없다.
- 수정 완료 기준이 없다.

### 좋은 예

> **[중요] 동일 Actor가 Available 목록에 중복 등록될 수 있습니다.**
>
> `ReleaseActor()`는 `InUseActors.Remove()`의 결과를 확인하지 않고 항상 `AvailableActors.Add()`를 실행합니다. 같은 Actor가 Timer와 Overlap 경로에서 두 번 반환되면 Available 목록에 동일 포인터가 두 번 들어갈 수 있습니다. 이후 두 번의 Acquire가 같은 Actor를 반환해 위치, Owner와 피해 값을 서로 덮어쓸 수 있습니다.
>
> `RemoveSingleSwap()`의 제거 결과가 0이면 중복 반환으로 판단해 종료하고, 이 경우를 검증하는 자동화 테스트를 추가하는 것을 권장합니다.

---

## 4. 심각도 판단 기준

### 치명적

- 게임 진행 불가
- 크래시 또는 Use-After-Free 가능성
- 저장 데이터 손상
- 핵심 전투 결과 왜곡

예: 죽을 수 없는 가짜 적 카운트가 남아 Stage가 끝나지 않음.

### 중요

- 특정 조건에서 잘못된 기능 결과
- 데이터 설정이 실제로 적용되지 않음
- 상태가 누적되며 장시간 플레이에서 오류 발생
- 확장 시 높은 장애 가능성

예: Wave DataTable의 `SpawnInterval`을 수정해도 모두 즉시 생성됨.

### 참고

- 가독성, 명명과 구조 개선
- 아직 측정되지 않은 성능 가능성
- 현재 요구사항에서는 동작하지만 확장 비용이 큰 구조

예: Character 클래스가 여러 변경 이유를 가짐.

심각도는 코드가 보기 불편한 정도가 아니라 사용자 영향과 발생 가능성으로 정한다.

---

# 5. 실전 리뷰 시나리오

각 시나리오는 먼저 `문제 코드 위치`만 보고 스스로 리뷰한다. 이후 힌트와 모범 답변을 확인한다.

## 시나리오 1: Enemy HP

### 문제 코드 위치

- `Private/Enemies/ZEnemyBase.cpp:171`
- `Private/Enemies/ZEnemyBase.cpp:921`
- `Private/Enemies/ZEnemyBase.cpp:1141`
- `Private/Projectiles/ZProjectileBase.cpp:371`
- `Private/AttributeSets/UZAttributeSet.cpp:47`

### 연습 질문

1. Enemy의 실제 체력은 어느 변수가 소유하는가?
2. 직접 피해와 GAS 피해가 각각 어떤 값을 변경하는가?
3. 두 경로를 순서대로 실행하면 어떤 상태가 되는가?
4. 심각도는 무엇인가?
5. 최소 수정과 장기 수정은 무엇인가?
6. 어떤 테스트로 재현할 수 있는가?

### 1단계 힌트

`CurrentHP`와 `AttributeSet->GetHP()`를 모두 검색한다.

### 2단계 힌트

근접 피해 20을 먼저 적용하고 GAS 피해 5를 나중에 적용한다고 가정한다.

### 모범 리뷰

> **[치명적] Enemy 체력이 `CurrentHP`와 `AttributeSet::HP`에 이중 저장됩니다.**
>
> Interface 기반 직접 피해와 상태이상은 `CurrentHP`를 감소시키지만, Projectile의 GAS 경로는 `AttributeSet::HP`를 감소시킨 뒤 `SyncHealthFromAttributeSet()`으로 `CurrentHP`를 덮어씁니다. 초기 HP가 모두 30일 때 직접 피해 20 후 GAS 피해 5가 들어오면 `CurrentHP`가 10에서 25로 증가할 수 있습니다.
>
> 이는 무기 순서에 따라 전투 결과와 사망 판정이 달라지는 핵심 상태 손상입니다. `AttributeSet::HP`를 유일한 체력 원천으로 만들고 직접 피해와 상태이상도 공통 피해 파이프라인을 사용해야 합니다.
>
> 테스트는 동일 Enemy에 직접 피해와 GAS 피해를 서로 다른 순서로 적용한 뒤 최종 HP와 사망 여부가 같은지 확인해야 합니다.

### 예상 반박과 답변

**반박:** `SyncHealthFromAttributeSet()`이 있으니 항상 동기화되지 않나요?

**답변:** GAS 피해 뒤에는 동기화되지만 직접 피해 뒤에는 AttributeSet이 갱신되지 않는다. 동기화가 특정 경로에만 있으므로 단일 원천이 아니다.

**반박:** 직접 피해 때 두 값을 모두 감소시키면 되지 않나요?

**답변:** 단기 패치로는 가능하지만 새로운 피해와 회복 경로마다 두 값을 갱신해야 한다. 장기적으로 누락 가능성이 계속 남으므로 AttributeSet 하나로 통합하는 것이 안전하다.

---

## 시나리오 2: Enemy Spawn과 Stage Clear

### 문제 코드 위치

- `Private/GameModes/Project_Z_GameMode.cpp:147`
- `Private/GameModes/Project_Z_GameMode.cpp:169`
- `Private/GameModes/Project_Z_GameMode.cpp:226`
- `Private/GameModes/Project_Z_GameMode.cpp:229`

### 연습 질문

1. Spawn 함수는 성공 여부를 호출자에게 전달하는가?
2. `AliveEnemyCount`는 언제 증가하는가?
3. Spawn 실패 시 누가 Count를 감소시킬 수 있는가?
4. 유효한 Variant가 0개면 Stage 상태는 어떻게 되는가?
5. 정수 Count 대신 다른 관리 방식도 가능한가?

### 모범 리뷰

> **[치명적] Spawn 실패한 Enemy도 `AliveEnemyCount`에 포함됩니다.**
>
> Spawn 람다는 `SpawnActor()` 실패 시 내부에서 반환하지만 호출자에게 결과를 전달하지 않습니다. 호출부는 람다 실행 후 `AliveEnemyCount++`를 무조건 수행합니다. 실제 Actor가 없기 때문에 해당 Count를 감소시킬 사망 통지도 발생하지 않아 Stage가 영구히 종료되지 않을 수 있습니다.
>
> Spawn 함수가 `AZEnemyBase*`를 반환하게 하고 성공한 Actor만 Count에 포함해야 합니다. 모든 시도가 끝난 뒤 실제 생성 수가 0이면 오류 또는 빈 Stage 처리 정책도 실행해야 합니다.

### 예상 반박과 답변

**반박:** `SpawnActor()`는 `AlwaysSpawn`을 쓰면 실패하지 않지 않나요?

**답변:** 현재 GameMode Spawn에는 `AlwaysSpawn` 설정도 없으며, Class와 World, 생성 과정의 실패 가능성을 API가 `nullptr` 반환으로 표현한다. 실패 가능성이 낮더라도 Count 불변조건은 반환 결과와 결합해야 한다.

**반박:** Count를 Variant 배열 크기로 미리 설정하면 단순하지 않나요?

**답변:** 잘못된 Row, Spawn 실패와 비활성 항목이 있으면 실제 Actor 수와 다를 수 있다. 요청 수와 실제 생성 수를 구분해야 한다.

---

## 시나리오 3: Actor Pool 중복 반환

### 문제 코드 위치

- `Private/Pooling/ZActorPoolSubsystem.cpp:31`
- `Private/Pooling/ZActorPoolSubsystem.cpp:82`
- `Private/Projectiles/ZProjectileBase.cpp:219`
- `Private/Projectiles/ZProjectileBase.cpp:306`

### 연습 질문

1. Pool Actor가 지켜야 할 불변조건은 무엇인가?
2. 동일 Actor를 두 번 Release하면 배열이 어떻게 되는가?
3. 이후 두 번 Acquire하면 어떤 결과가 나오는가?
4. 단순 `Contains()`와 상태 enum 중 어떤 방어가 가능한가?
5. Timer와 충돌 이벤트가 동시에 반환을 요청할 수 있는가?

### 모범 리뷰

> **[중요] `ReleaseActor()`가 동일 Actor의 중복 반환을 허용합니다.**
>
> 함수는 `InUseActors.Remove()`가 실제 Actor를 제거했는지 확인하지 않고 `AvailableActors.Add()`를 실행합니다. 두 번 반환되면 동일 포인터가 Available 배열에 두 번 등록되고, 이후 서로 다른 두 Acquire 요청에 같은 Actor가 반환될 수 있습니다.
>
> 두 번째 발사가 첫 번째 발사의 Transform, Owner, Damage와 Movement를 덮어쓰거나 사용 중인 Actor가 다른 반환 경로에서 비활성화될 수 있습니다. InUse 제거 결과가 0이면 반환을 거부하고 `ensureMsgf`로 상태 위반을 노출해야 합니다.

### 예상 반박과 답변

**반박:** Projectile 반환 시 Timer를 모두 Clear하므로 두 번 호출되지 않습니다.

**답변:** 현재 경로에서 가능성이 낮아질 수는 있지만 `ReleaseActor()`는 public API이고 Pool의 불변조건은 호출자가 완벽하다는 가정에 의존해서는 안 된다. Overlap, Timer, 외부 호출의 재진입도 테스트해야 한다.

---

## 시나리오 4: 풀링 상태 초기화

### 문제 코드 위치

- `Private/Projectiles/ZProjectileBase.cpp:164`
- `Private/Projectiles/ZProjectileBase.cpp:194`
- `Private/Projectiles/ZProjectileBase.cpp:230`

### 연습 질문

각 변수를 초기화하지 않았을 때 발생할 문제를 연결한다.

| 변수                          | 예상 문제를 직접 작성 |
| ----------------------------- | --------------------- |
| `RuntimeHitActors`            |                       |
| `RuntimeDamageOverride`       |                       |
| `RuntimeRemainingPierceCount` |                       |
| `RuntimeElementType`          |                       |
| `Owner`                       |                       |
| `LifeTimerHandle`             |                       |

### 정답

| 변수                          | 초기화 누락 시 문제                                        |
| ----------------------------- | ---------------------------------------------------------- |
| `RuntimeHitActors`            | 이전 발사에서 맞힌 Enemy를 새 발사에서 맞히지 못함         |
| `RuntimeDamageOverride`       | 이전 무기의 피해량이 남을 수 있음                          |
| `RuntimeRemainingPierceCount` | 이전 관통 횟수가 새 발사에 적용됨                          |
| `RuntimeElementType`          | 이전 무기의 속성 상태이상이 적용됨                         |
| `Owner`                       | 이전 발사자가 Instigator로 남거나 충돌 제외 판단이 잘못됨  |
| `LifeTimerHandle`             | 이전 발사의 Timer가 새로 발사된 Projectile을 조기 반환시킴 |

### 리뷰 포인트

현재 Projectile은 이 상태 대부분을 획득/반환 이벤트에서 초기화한다. 코드 리뷰는 문제만 찾는 작업이 아니다. 이 구현은 긍정적인 방어 설계로 기록할 수 있다.

---

## 시나리오 5: Wave 데이터 계약

### 문제 코드 위치

- `Public/Data/FZWaveDefinition.h`
- `Private/GameModes/Project_Z_GameMode.cpp:147`
- `Private/Enemies/ZEnemyBase.cpp:194`

### 연습 질문

1. Struct에 선언된 필드 중 실제로 읽히는 것은 무엇인가?
2. `EnemyCount`와 `MonsterVariantRowNames.Num()` 중 생성 수의 기준은 무엇인가?
3. `SpawnInterval`이 적용되는가?
4. `SpawnDistance`는 사용되는가?
5. Wave 배율은 `ApplyWaveScaling()`까지 연결되는가?

### 모범 리뷰

> **[중요] `FZWaveDefinition`의 설정과 실제 Spawn 동작이 일치하지 않습니다.**
>
> `EnemyCount`, `SpawnInterval`, `SpawnDistance`, HP·이동속도·경험치 배율이 선언되어 있지만 GameMode는 Variant RowName 하나당 Enemy 한 명을 즉시 생성합니다. Spawn 위치도 GameMode의 `SpawnRadiusMin/Max`를 사용하고 `ApplyWaveScaling()`은 호출되지 않습니다.
>
> 에디터에서 값을 변경해도 게임 결과에 반영되지 않아 데이터 작성자가 잘못된 설정을 정상으로 오해할 수 있습니다. `EnemyCount`회 Variant를 선택하는 구조로 연결하거나, 배열 원소 하나를 한 명으로 정의하고 불필요한 필드를 제거해야 합니다.

---

## 시나리오 6: StageDefinition의 미사용 값

### 문제 코드 위치

- `Public/Data/UZStageDefinitionAsset.h`
- `Private/GameModes/Project_Z_GameMode.cpp`

### 연습 질문

- `StageDuration`은 어디에서 감소하는가?
- `StageHPMultiplier`, `StageDamageMultiplier`, `StageXPRewardMultiplier`는 어디에서 계산에 사용되는가?
- 에디터에 노출됐지만 사용되지 않는 필드의 위험은 무엇인가?

### 모범 리뷰

> **[중요] Stage DataAsset의 핵심 밸런스 값이 런타임에서 사용되지 않습니다.**
>
> 제한시간과 Stage별 HP, Damage, XP 배율은 선언되어 있지만 GameMode 또는 Enemy 계산 경로에서 참조되지 않습니다. 데이터 에셋을 수정해도 플레이가 변하지 않으므로 보고서의 Stage 난이도 데이터화 범위와 실제 구현 사이에 차이가 있습니다.
>
> 요구사항에 포함된다면 Stage 시작 시 Wave 및 Variant 배율과 결합해 적용하고, 포함되지 않는다면 필드를 제거하거나 Deprecated 처리해야 합니다.

---

## 시나리오 7: GAS Headshot 데이터 전달

### 문제 코드 위치

- `Private/Projectiles/ZProjectileBase.cpp:325`
- `Private/Projectiles/ZProjectileBase.cpp:371`
- `Private/AttributeSets/UZAttributeSet.cpp:47`

### 연습 질문

다음 데이터가 어디에 저장되는지 구분한다.

- `FHitResult`
- 최종 피해 수치
- Bullet Damage Tag
- Headshot Tag
- 현재 HP
- 이번 공격의 Damage

### 정답

| 데이터             | 위치                                    |
| ------------------ | --------------------------------------- |
| `FHitResult`       | Gameplay Effect Context                 |
| 최종 피해 수치     | `Data.Damage` SetByCaller               |
| Bullet Damage Tag  | EffectSpec `DynamicGrantedTags`         |
| Headshot Tag       | EffectSpec `DynamicGrantedTags`         |
| 현재 HP            | `UZAttributeSet::HP`                    |
| 이번 공격의 Damage | `UZAttributeSet::Damage` Meta Attribute |

### 예상 질문

> 완료보고서에는 Headshot Tag를 Effect Context로 전달했다고 적혀 있습니다. 맞습니까?

### 모범 답변

아니다. 현재 코드에서 HitResult는 Effect Context에 들어가고, Headshot Tag는 EffectSpec의 DynamicGrantedTags에 추가된다. 보고서 표현을 수정해야 한다.

---

## 시나리오 8: UI Tick

### 문제 코드 위치

- `Private/UI/ZHUDWidget.cpp`
- `Private/UI/ZStateHUDWidget.cpp:87`
- `Private/UI/ZEnemyHPBarWidget.cpp`

### 연습 질문

1. 같은 상태 갱신이 한 프레임에 두 번 호출될 가능성이 있는가?
2. 값이 바뀌지 않아도 Widget 속성을 갱신하는가?
3. 적 HP Bar 수가 증가하면 비용은 어떻게 변하는가?
4. 어떤 값은 Tick이 필요하고 어떤 값은 이벤트가 적합한가?

### 모범 리뷰

> **[참고] 상태 HUD가 Tick 기반 polling으로 갱신되며 중복 호출 가능성이 있습니다.**
>
> `UZStateHUDWidget::NativeTick()`이 `RefreshCurrentStatus()`를 호출하고, 상위 HUD의 Tick도 `StateHUD->TickUpdate()`를 통해 같은 갱신을 요청합니다. 구성에 따라 상태 HUD가 자체 Tick과 부모 호출을 모두 받으면 한 프레임에 두 번 갱신될 수 있습니다.
>
> HP와 Stamina는 ASC Attribute Delegate, 경험치·탄약·무기 상태는 변경 이벤트로 갱신하고, 실제 프레임 갱신이 필요한 Crosshair만 Tick을 유지하는 방향을 권장합니다.

### 주의

Blueprint의 Tick 설정에 따라 실제 중복 여부가 달라질 수 있으므로 정적 분석만으로 확정하지 말고 Widget Tick 설정과 PIE 호출 횟수를 확인해야 한다.

---

## 시나리오 9: 동기 Asset Load

### 문제 코드 위치

- `Private/GameModes/Project_Z_GameMode.cpp:93`
- `Private/Characters/ZCharacterBase.cpp:1819`
- `Private/Characters/ZCharacterBase.cpp:3321`
- `Private/Enemies/ZEnemyBase.cpp:558`

### 연습 질문

- `StaticLoadObject()`와 `LoadSynchronous()`가 호출되는 시점은 언제인가?
- 해당 Asset이 아직 메모리에 없으면 어떤 문제가 발생할 수 있는가?
- 문자열 경로는 Asset 이동에 어떻게 반응하는가?
- 모든 동기 로드가 무조건 버그인가?

### 모범 리뷰

> **[참고] 전투 및 진행 코드에 동기 Asset Load와 하드코딩 경로가 분산되어 있습니다.**
>
> Asset이 이미 로드되지 않았다면 게임 플레이 중 동기 I/O로 Hitch가 발생할 수 있고, 문자열 경로는 Asset 이동과 이름 변경에 취약합니다. 필수 Asset은 Blueprint/DataAsset 기본값으로 주입하고 선택 콘텐츠는 전투 전 비동기 로드하는 방식을 권장합니다.
>
> 다만 동기 로드 자체가 항상 오류는 아니다. 로딩 화면이나 초기화 단계처럼 Blocking이 허용되는 위치인지, 호출 빈도와 Asset 크기가 어떤지 측정해야 심각도를 결정할 수 있다.

---

## 시나리오 10: Character 책임

### 문제 코드 위치

- `Public/Characters/ZCharacterBase.h`
- `Private/Characters/ZCharacterBase.cpp`

### 연습 질문

1. Character가 가진 변경 이유를 기능별로 분류한다.
2. 어떤 책임을 먼저 분리해야 하는가?
3. Component로 옮기기만 하면 결합도가 낮아지는가?
4. 분리 전에 어떤 테스트가 필요한가?

### 모범 리뷰

> **[참고] `AZCharacterBase`가 입력, 카메라, 조준, 엄폐, 장비, 탄약, 공격, 애니메이션, 경험치와 레벨업을 함께 담당합니다.**
>
> 기능 변경 이유가 많아 회귀 범위와 파일 충돌이 커집니다. 다만 즉시 대규모 분해하면 기존 Blueprint 연결을 깨뜨릴 위험이 있습니다. 먼저 전투와 성장 테스트를 확보한 뒤 `CombatComponent`, `ProgressionComponent`, `AimComponent`, `InteractionComponent` 순서로 단계적으로 이동하는 것이 안전합니다.
>
> Component끼리 서로를 직접 탐색하고 호출하면 작은 God Object 여러 개가 생길 수 있으므로 상태 소유권과 이벤트 계약을 먼저 정의해야 합니다.

---

# 6. 예상 코드 리뷰 면접 질문과 답변

## Q1. 코드 리뷰를 시작할 때 가장 먼저 무엇을 확인합니까?

### 모범 답변

> 먼저 변경 목적과 요구사항을 확인하고, 변경된 코드가 소유하는 상태와 호출 경계를 파악합니다. 그다음 정상 흐름보다 실패, 중복 호출, 취소와 객체 파괴 경로를 확인합니다. 마지막으로 테스트가 핵심 위험을 막는지 보고 스타일과 구조 개선을 검토합니다.

---

## Q2. 긴 함수는 무조건 분리해야 합니까?

### 모범 답변

> 길이 자체보다 하나의 함수가 여러 책임과 서로 다른 변경 이유를 가지는지가 중요합니다. 단순한 순차 처리라면 길어도 이해 가능할 수 있고, 짧은 함수라도 전역 상태를 여러 개 변경하면 위험할 수 있습니다. 분리는 테스트 가능성, 재사용성과 불변조건을 명확하게 만드는 방향이어야 합니다.

---

## Q3. 코드 리뷰에서 버그와 설계 개선을 어떻게 구분합니까?

### 모범 답변

> 현재 요구사항에서 잘못된 결과를 만드는 것은 버그로 분류합니다. 현재는 정상 동작하지만 변경 비용이나 확장 위험을 높이는 것은 설계 개선으로 분리합니다. 두 항목의 심각도를 섞지 않아야 실제 결함 수정이 취향 논쟁에 묻히지 않습니다.

---

## Q4. 리뷰 대상자가 “실제로는 문제가 발생하지 않는다”고 반박하면 어떻게 합니까?

### 모범 답변

> 코드만으로 확정할 수 있는지와 실행 설정이 필요한지를 구분합니다. 발생 조건을 최소 재현 테스트로 만들고 로그, Automation Test 또는 PIE 결과로 확인합니다. 재현되지 않으면 가정을 수정하고, 재현되면 테스트를 수정 사항의 완료 조건으로 사용합니다.

---

## Q5. 모든 방어 코드를 추가하면 더 안전합니까?

### 모범 답변

> 아니다. 중복 검사가 핵심 결함을 숨기거나 복잡성을 높일 수 있습니다. 외부 입력, Asset 데이터와 객체 수명 경계에는 방어가 필요하지만 내부 불변조건 위반은 조용히 보정하기보다 `ensure`나 테스트로 드러내는 편이 좋습니다.

---

## Q6. `ensure`, `check`, 일반 조건문을 어떻게 구분합니까?

### 모범 답변

> 복구 불가능하고 반드시 참이어야 하는 개발 불변조건은 `check`, 비정상이지만 실행을 계속하며 개발 중 알려야 하는 조건은 `ensure`, 정상적으로 예상 가능한 실패는 조건문과 반환값으로 처리합니다. Shipping 동작과 프로젝트 정책도 고려해야 합니다.

---

## Q7. 성능 문제는 코드만 보고 지적해도 됩니까?

### 모범 답변

> 반복 횟수와 비용 구조를 보고 위험 가능성은 제시할 수 있지만 병목이라고 확정해서는 안 됩니다. 호출 빈도, 대상 수와 프로파일링 결과가 있어야 심각도와 수정 가치를 판단할 수 있습니다.

---

## Q8. 데이터 필드가 사용되지 않는 것이 왜 문제입니까?

### 모범 답변

> 에디터 사용자에게 설정이 동작한다는 잘못된 계약을 제공합니다. 값이 플레이에 반영되지 않는데도 정상 설정처럼 보이기 때문에 디버깅 시간과 보고 오류가 증가합니다. 실제로 연결하거나 제거·Deprecated 처리해야 합니다.

---

## Q9. 상태를 캐시하는 것은 항상 잘못입니까?

### 모범 답변

> 아니다. 계산 비용 절감이나 UI 표시를 위한 캐시는 유효합니다. 다만 원본이 하나여야 하고 캐시의 갱신 시점과 무효화 규칙이 명확해야 합니다. Enemy의 두 HP는 어떤 값이 원본인지 경로별로 달라지므로 안전한 캐시가 아닙니다.

---

## Q10. 리뷰에서 바로 리팩터링까지 요구해야 합니까?

### 모범 답변

> 현재 변경을 안전하게 만드는 최소 수정과 장기 구조 개선을 구분합니다. 예를 들어 Spawn Count는 성공 결과와 즉시 결합해야 하지만 전체 Stage 시스템 재설계는 별도 변경으로 나눌 수 있습니다. 리뷰 범위를 지나치게 키우면 핵심 버그 수정도 지연됩니다.

---

## Q11. 코드 리뷰에서 테스트를 어떻게 제안합니까?

### 모범 답변

> 구현 세부가 아니라 보장해야 할 동작을 기준으로 제안합니다. 예를 들어 “함수 A를 호출한다”보다 “근접 피해 후 GAS 피해를 적용해도 최종 HP가 누적 피해와 일치한다”처럼 작성합니다.

---

## Q12. 좋은 코드 리뷰어의 가장 중요한 태도는 무엇입니까?

### 모범 답변

> 사람을 평가하는 대신 코드의 위험과 근거를 설명하고, 사실·추론·취향을 구분하는 것입니다. 확실하지 않은 내용은 질문으로 남기고, 심각한 문제는 영향과 재현 조건을 구체적으로 제시해야 합니다.

---

# 7. 리뷰어 역할 모의 시나리오

아래는 상대 개발자가 반박하는 상황을 연습하기 위한 대화다.

## 시나리오 A: Spawn Count

### 개발자

> Spawn은 거의 실패하지 않으니까 지금 Count 처리도 문제없습니다.

### 좋지 않은 답변

> 그래도 코드를 제대로 작성해야 합니다.

### 좋은 답변

> 실패 확률의 크기보다 `AliveEnemyCount`가 실제 Actor 수라는 계약이 중요합니다. 현재 API가 `nullptr` 실패를 반환하고 있는데 Count가 결과와 분리되어 있습니다. 한 번만 실패해도 Stage가 진행 불가능해지므로 Spawn 반환값과 Count 증가를 결합하는 것이 필요합니다.

---

## 시나리오 B: Enemy HP

### 개발자

> 어차피 총기만 사용하는 프로젝트라 직접 피해 경로는 실행되지 않습니다.

### 좋은 답변

> 최종 요구사항이 총기 전용이라면 실행되지 않는 Melee, Aura와 직접 피해 API를 제거하거나 명확히 Deprecated 처리하는 편이 안전합니다. 현재 Public API와 LevelUp enum에는 해당 경로가 남아 있어 호출 가능성이 있습니다. 먼저 실제 Blueprint 참조를 확인하고, 미사용이 확인되면 제거 범위를 별도 변경으로 제안하겠습니다.

핵심은 가정으로 밀어붙이지 않고 실제 참조를 추가 확인하는 것이다.

---

## 시나리오 C: UI Tick

### 개발자

> UI 몇 개 없어서 성능 문제는 없습니다.

### 좋은 답변

> 현재 규모에서 성능 문제가 확인된 것은 아닙니다. 제 지적은 즉시 수정해야 할 병목이 아니라 중복 갱신 가능성과 확장 비용에 대한 참고 사항입니다. PIE에서 한 프레임 호출 횟수와 Widget 수를 확인한 뒤 우선순위를 결정하는 것이 맞습니다.

심각도를 낮추고 측정을 제안하는 것이 적절하다.

---

## 시나리오 D: Character 분리

### 개발자

> 컴포넌트로 나누면 오히려 복잡해지지 않나요?

### 좋은 답변

> 맞습니다. 줄 수만 기준으로 분리하면 의존성만 분산될 수 있습니다. 현재 변경 빈도와 테스트 경계를 확인한 뒤 전투와 성장처럼 독립된 상태·이벤트 계약을 정의할 수 있는 책임부터 단계적으로 분리해야 합니다. 이번 버그 수정에 대규모 분리를 포함하자는 의미는 아닙니다.

---

# 8. 혼자 연습하는 방법

## 1단계: 15분 정적 리뷰

한 파일을 선택하고 다음만 기록한다.

```text
이 클래스의 책임:
핵심 상태:
상태를 변경하는 함수:
외부 의존성:
실패할 수 있는 지점:
항상 지켜야 하는 불변조건:
```

## 2단계: 리뷰 코멘트 작성

발견 사항 중 가장 영향이 큰 하나를 선택해 다음을 작성한다.

```text
심각도:
한 줄 제목:
발생 조건:
사용자 영향:
근거 코드:
최소 수정:
검증 테스트:
```

## 3단계: 소리 내어 설명

90초 안에 다음 순서로 설명한다.

```text
현재 코드
→ 문제 조건
→ 실제 결과
→ 수정 방향
→ 검증 방법
```

## 4단계: 반박 대응

스스로 다음 질문을 한다.

- 이 문제가 실제로 호출되는가?
- Blueprint가 보완하고 있지 않은가?
- 발생 가능성이 낮다면 심각도가 과한가?
- 최소 수정으로 해결할 수 있는가?
- 내 제안이 새로운 상태 중복을 만들지 않는가?

## 5단계: 정답지 비교

`Project_Z_Code_Review.md`와 비교하되 표현이 같은지보다 다음을 비교한다.

- 동일한 상태 불변조건을 찾았는가?
- 발생 조건을 구체화했는가?
- 코드 근거를 제시했는가?
- 수정과 테스트를 연결했는가?

---

# 9. 7일 연습 계획

| 일차 | 주제           | 연습 대상               | 완료 기준                                         |
| ---: | -------------- | ----------------------- | ------------------------------------------------- |
|    1 | 상태 소유권    | Enemy HP                | 이중 HP 실패 시나리오를 설명한다.                 |
|    2 | 카운트 정합성  | GameMode Spawn          | Spawn 실패와 0명 생성 정책을 리뷰한다.            |
|    3 | 객체 수명      | Actor Pool              | Available/InUse 불변조건과 초기화를 설명한다.     |
|    4 | 데이터 계약    | Wave/Stage Data         | 선언과 실제 사용을 검색해 차이를 기록한다.        |
|    5 | GAS 흐름       | Projectile/AttributeSet | Context, Tag, SetByCaller와 Attribute를 구분한다. |
|    6 | 성능/구조      | UI Tick/Character       | 측정 필요 사항과 리팩터링 범위를 구분한다.        |
|    7 | 종합 모의 리뷰 | 전체                    | 30분 리뷰 후 발견 사항 3개를 구두 발표한다.       |

하루 학습 목표는 새로운 개념을 많이 읽는 것이 아니라 리뷰 코멘트 하나를 완성하는 것이다.

---

# 10. 실전 채점표

각 리뷰 항목을 0~2점으로 평가한다.

| 항목          | 0점           | 1점           | 2점                            |
| ------------- | ------------- | ------------- | ------------------------------ |
| 요구사항 이해 | 의도를 추측함 | 일부 파악     | 실제 계약을 명확히 설명        |
| 상태 소유권   | 찾지 못함     | 변수만 나열   | 원본과 변경 경로를 추적        |
| 발생 조건     | 없음          | 추상적        | 재현 가능한 순서 제시          |
| 사용자 영향   | 없음          | 가능성만 언급 | 게임 결과를 구체적으로 설명    |
| 코드 근거     | 없음          | 파일만 제시   | 함수와 상태 변경 위치 제시     |
| 심각도        | 취향 기준     | 대략 구분     | 영향과 가능성으로 판단         |
| 최소 수정     | 없음          | 방향만 제시   | 범위가 제한된 수정 제안        |
| 장기 개선     | 과도한 재설계 | 일부 구분     | 최소 수정과 명확히 분리        |
| 검증          | “테스트 필요” | 조건 일부     | 수정 전 실패/후 성공 조건 제시 |
| 커뮤니케이션  | 공격적/모호   | 이해 가능     | 사실·추론·제안을 분리          |

총점 20점 기준:

- 17~20점: 실제 리뷰에 사용할 수 있는 수준
- 13~16점: 핵심 문제는 찾지만 근거 또는 검증 보완 필요
- 9~12점: 코드 감상 수준이며 실행 결과 추론 연습 필요
- 0~8점: 스타일 지적보다 호출 흐름과 상태 추적부터 연습 필요

---

# 11. 다른 에이전트와 연습할 때 사용할 프롬프트

```text
너는 Unreal Engine C++ 시니어 리뷰어다.

다음 문서를 읽고 Project_Z 코드 리뷰 훈련을 진행해 줘.

1. _workspace/Project_Z/docs/Project_Z_Code_Review_Practice.md
2. _workspace/Project_Z/docs/Project_Z_Code_Review.md
3. Project/Project_Z/Source/Project_Z의 실제 코드

한 번에 하나의 코드 리뷰 시나리오만 제시해라. 먼저 파일과 함수 범위만 알려주고 정답은 보여주지 마라. 내가 리뷰 의견을 작성하면 다음 기준으로 평가해라.

- 상태 소유권을 찾았는가
- 발생 조건을 재현 가능한 순서로 설명했는가
- 영향과 심각도가 타당한가
- 코드 근거가 있는가
- 최소 수정과 장기 개선을 구분했는가
- 수정 후 검증 방법을 제시했는가

각 항목을 평가한 뒤 20점 만점으로 채점하고, 내가 놓친 핵심을 설명해라. 이후 개발자 역할로 내 리뷰에 한 번 반박하고, 내가 답할 기회를 준 뒤 다음 시나리오로 넘어가라.
```

---

# 12. 치명적 버그 수정 실습

이 절은 문제를 찾는 리뷰에서 끝나지 않고, 실제 수정 범위를 설계하고 검증하는 연습이다. 여기서는 프로젝트 소스를 자동으로 수정하지 않는다. 먼저 수정 계획과 예상 코드를 작성한 뒤 실제 변경 여부를 결정한다.

공통 진행 순서는 다음과 같다.

```text
현상 정의
→ 최소 재현
→ 상태 소유자 결정
→ 영향받는 호출부 검색
→ 실패하는 테스트 작성
→ 최소 수정
→ 빌드 및 테스트
→ Blueprint/PIE 회귀 검증
→ 수정 후 리뷰 설명
```

## 수정 실습 A: Enemy HP 이중 관리 제거

### 목표

`AZEnemyBase::CurrentHP`와 `UZAttributeSet::HP`가 서로 다른 피해 경로에서 변경되는 문제를 제거한다. 최종 목표는 `AttributeSet::HP`를 Enemy 체력의 유일한 원천으로 사용하는 것이다.

### 현재 위험

```text
Interface 직접 피해
→ CurrentHP 감소

GAS Projectile 피해
→ AttributeSet.HP 감소
→ SyncHealthFromAttributeSet()
→ CurrentHP 덮어쓰기
```

이 구조에서는 직접 피해 이후 GAS 피해가 들어오면 이전 피해가 사라질 수 있다.

### 수정 전 조사 과제

다음 검색 결과를 직접 분류한다.

```powershell
rg -n "CurrentHP|MaxHP|GetCurrentHPValue|GetHPRatioValue|SyncHealthFromAttributeSet|ReceiveDamage_Implementation|ApplyStatusDamage" Project/Project_Z/Source/Project_Z
```

분류표:

| 분류      | 확인 대상                                       |
| --------- | ----------------------------------------------- |
| 초기화    | Constructor, BeginPlay, Variant, Wave Scaling   |
| 피해      | Projectile, Melee, Fire, Poison, Lightning      |
| 회복      | Enemy 회복 기능 존재 여부                       |
| 표시      | HP Bar와 Getter                                 |
| 사망      | `Die()` 호출 조건                               |
| 복제      | Attribute UPROPERTY와 ASC Replication           |
| Blueprint | `GetCurrentHPValue()`, `GetHPRatioValue()` 참조 |

### 먼저 결정해야 할 설계

#### 권장안: AttributeSet을 단일 원천으로 사용

```text
UZAttributeSet::HP / MaxHP
 ├─ 모든 피해와 회복
 ├─ Enemy Getter
 ├─ HP Bar
 └─ 사망 판정
```

장점:

- GAS와 직접 경로 간 불일치 제거
- Attribute Delegate로 UI와 사망 처리 가능
- 향후 방어력, 무적과 GameplayEffect 확장 가능

비용:

- 기존 직접 피해와 상태이상 경로 변경 필요
- Blueprint가 `CurrentHP`를 직접 참조하는지 확인 필요
- Attribute 초기화와 Variant 배율 적용 순서를 정리해야 함

#### 비권장 임시안: 두 값을 항상 같이 갱신

빠른 패치는 가능하지만 모든 피해·회복·초기화 경로가 두 값을 갱신해야 하므로 다시 누락될 위험이 크다. 긴급 시 임시 수정으로만 사용할 수 있다.

### 단계별 권장 수정 계획

#### 1단계: Getter를 AttributeSet 기준으로 변경

개념 예시:

```cpp
float AZEnemyBase::GetCurrentHPValue() const
{
    return AttributeSet ? AttributeSet->GetHP() : 0.0f;
}

float AZEnemyBase::GetMaxHPValue() const
{
    return AttributeSet ? AttributeSet->GetMaxHP() : 0.0f;
}
```

단, 기존 Blueprint가 헤더의 Inline Getter를 사용하므로 실제 수정 시 선언과 구현 위치를 프로젝트 스타일에 맞춰 선택한다.

#### 2단계: 모든 피해를 공통 함수 또는 GameplayEffect로 통합

장기적으로 권장되는 흐름:

```text
Projectile / Melee / Status
→ Damage 요청
→ GameplayEffectSpec
→ Data.Damage SetByCaller
→ AttributeSet::PostGameplayEffectExecute()
→ HP 변경
```

상태이상 Tick마다 EffectSpec을 만드는 비용과 Tag 정책도 함께 결정해야 한다. 과제 범위에서 GAS 전체 통합이 과도하면 Enemy의 공통 `ApplyDamageToAttributes()` 함수를 만들고 모든 직접 피해가 반드시 이 함수를 통과하도록 하는 중간 단계도 가능하다.

#### 3단계: 사망 판정의 진입점을 하나로 제한

권장 구조:

```text
HP Attribute 변경
→ Enemy Handler
→ HP <= 0 && !bIsDead
→ Die()
```

Projectile의 `SyncHealthFromAttributeSet()`에서만 사망을 확인하면 다른 GameplayEffect나 회복·지속 피해 확장 시 누락될 수 있다. ASC Attribute Value Change Delegate를 등록해 공통 처리하는 편이 안전하다.

#### 4단계: 초기 능력치 적용 순서 통합

Variant와 Wave 배율이 `MaxHP`와 `CurrentHP` 멤버를 직접 곱하지 않고 최종 MaxHP를 계산해 AttributeSet에 한 번 적용하도록 한다.

```text
Base MaxHP
× Stage/Wave Multiplier
× Monster Variant Multiplier
= Final MaxHP
→ AttributeSet 초기화
```

같은 Actor에 `ApplyMonsterVariant()`가 두 번 호출될 가능성이 있다면 누적 곱셈이 발생하지 않도록 원본 Base 값을 별도로 보존하거나 최종 값을 순수 계산해야 한다.

#### 5단계: Legacy HP 제거

모든 C++ 및 Blueprint 참조가 AttributeSet 기준으로 전환된 뒤 `CurrentHP`, `MaxHP`, `SyncHealthFromAttributeSet()`을 제거한다. Blueprint 참조를 확인하지 않고 바로 UPROPERTY를 제거하면 Blueprint 로드 또는 컴파일 문제가 생길 수 있다.

### 최소 재현 테스트

#### 테스트 A-1: 피해 순서

```text
Given Enemy HP = 30
When Interface 피해 20
And GAS 피해 5
Then HP = 5
```

순서를 바꿔도 결과가 같아야 한다.

```text
GAS 5 → Interface 20 → HP 5
Interface 20 → GAS 5 → HP 5
```

#### 테스트 A-2: 상태이상

```text
Given Enemy HP = 30
When Fire 또는 Poison Tick 피해 10
And Projectile 피해 5
Then HP = 15
And HP Bar도 15/30을 표시
```

#### 테스트 A-3: 사망 중복

같은 프레임에 Projectile과 상태이상 피해가 들어와도 다음은 한 번만 발생해야 한다.

- `Die()`
- `NotifyEnemyDead()`
- 경험치 또는 아이템 보상
- 사망 애니메이션 이벤트

#### 테스트 A-4: Variant 초기화

Monster Variant의 HP 배율 적용 후 다음 값이 모두 일치해야 한다.

- AttributeSet MaxHP
- AttributeSet HP
- HP Getter
- HP Bar 비율

### 회귀 위험

- Enemy HP Bar가 갱신되지 않을 수 있음
- Variant 적용 전후 초기 HP가 달라질 수 있음
- 기존 Blueprint가 제거된 UPROPERTY를 참조할 수 있음
- `PostGameplayEffectExecute()`와 Attribute Delegate 양쪽에서 `Die()`가 호출될 수 있음
- 직접 피해 fallback이 제거되면 ASC가 없는 Damageable Actor가 피해를 받지 못할 수 있음

### 수정 완료 보고 연습

> Enemy 체력의 원천을 `UZAttributeSet::HP`로 통일했습니다. 기존 Interface 피해와 상태이상도 공통 Attribute 피해 경로를 사용하도록 변경했고, Enemy 사망은 HP 변경 처리에서 한 번만 판정합니다. 직접 피해와 GAS 피해 순서를 교차한 테스트, 상태이상 후 Projectile 테스트와 중복 사망 테스트를 수행했습니다. Blueprint HP Bar 참조도 Attribute 기반 Getter로 유지되는 것을 PIE에서 확인했습니다.

실제로 수행하지 않은 테스트는 완료했다고 말하지 않는다.

---

## 수정 실습 B: Enemy Spawn Count 정합성

### 목표

`AliveEnemyCount`가 요청한 수나 데이터 행 수가 아니라 실제로 생성되어 살아 있는 Enemy 수와 일치하도록 수정한다.

### 현재 위험

```text
SpawnEnemyWithVariant()
→ Spawn 실패 시 람다 내부 return
→ 호출부는 실패를 모름
→ AliveEnemyCount++
→ 죽을 수 없는 가짜 Count 생성
→ Stage Clear 불가
```

### 상태 불변조건

```text
AliveEnemyCount
= 현재 생성에 성공했고 아직 사망 통지를 보내지 않은 Stage Enemy 수
```

### 단계별 권장 수정 계획

#### 1단계: Spawn 결과 반환

람다가 `void`가 아니라 `AZEnemyBase*`를 반환하도록 변경한다.

개념 예시:

```cpp
auto SpawnEnemyWithVariant = [this, World, &WaveDefinition](
    const FZMonsterVariantDefinition& EnemyVariant) -> AZEnemyBase*
{
    AZEnemyBase* SpawnedEnemy = World->SpawnActor<AZEnemyBase>(
        WaveDefinition.EnemyClass,
        GetRandomSpawnLocation(),
        FRotator::ZeroRotator);

    if (!SpawnedEnemy)
    {
        return nullptr;
    }

    SpawnedEnemy->ApplyMonsterVariant(EnemyVariant);
    return SpawnedEnemy;
};
```

실제 적용 시 기존 `FActorSpawnParameters.Owner`와 Spawn 정책을 보존해야 한다.

#### 2단계: 성공 시에만 Count 증가

```cpp
if (AZEnemyBase* SpawnedEnemy = SpawnEnemyWithVariant(*EnemyVariant))
{
    ++AliveEnemyCount;
}
else
{
    ++FailedSpawnCount;
}
```

`SpawnedEnemy` 변수를 단순히 조건에만 쓰는 경우 컴파일 경고 정책도 확인한다.

#### 3단계: 0명 생성 정책

모든 생성 시도가 끝난 뒤 실제 생성 수가 0이면 현재 상태를 그대로 두지 않는다.

가능한 정책:

1. 데이터 오류로 처리하고 게임 진행 중단 UI 표시
2. 빈 Stage로 간주해 즉시 Clear
3. 개발 빌드에서 `ensureMsgf` 후 안전하게 다음 Stage 처리

어떤 정책이 맞는지는 기획 요구사항에 따라 결정한다. 코드 리뷰에서는 임의로 선택하기보다 결정이 필요하다고 명시한다.

#### 4단계: 중복 사망 통지 방어

Enemy의 `bIsDead`가 `Die()` 재진입을 막지만 GameMode의 public `NotifyEnemyDead()`는 어떤 Enemy가 통지했는지 알지 못한다. 장기적으로는 다음 구조를 고려한다.

```text
TSet<TWeakObjectPtr<AZEnemyBase>> ActiveStageEnemies
```

Spawn 성공 시 등록하고 사망 또는 Destroy 시 해당 Actor를 제거한 경우에만 Count를 갱신한다. 이 방식은 단순 정수보다 디버깅 가능성이 높지만 현재 과제 범위에는 변경량이 클 수 있다.

#### 5단계: 이름과 역할 정리

- `CurrentStateIndex` → 실제 의미에 따라 `CurrentStageIndex` 또는 `CurrentWaveIndex`
- `bStageClered` → `bStageCleared`
- 요청 수, 생성 성공 수, 생존 수를 구분

이름 변경은 Blueprint 참조에 영향을 줄 수 있으므로 핵심 Count 수정과 별도 변경으로 나누는 것이 안전하다.

### 최소 재현 테스트

#### 테스트 B-1: 정상 생성

```text
Given 유효한 Variant 3개
When 3개 Spawn 성공
Then AliveEnemyCount = 3
When Enemy 3개 사망
Then Stage Clear 1회
```

#### 테스트 B-2: 일부 Spawn 실패

```text
Given 생성 요청 3개
When 2개 성공, 1개 실패
Then AliveEnemyCount = 2
When 성공한 2개 사망
Then Stage Clear
```

#### 테스트 B-3: 전체 Spawn 실패

```text
Given 모든 Spawn 실패
Then AliveEnemyCount = 0
And 정의된 오류/빈 Stage 정책 실행
And Play 상태로 교착되지 않음
```

#### 테스트 B-4: 잘못된 데이터

다음 각각에서 상태가 교착되지 않아야 한다.

- `EnemyClass == nullptr`
- `MonsterVariantTable == nullptr`
- 빈 `MonsterVariantRowNames`
- 존재하지 않는 RowName
- RowName이 `None`

#### 테스트 B-5: 중복 사망

동일 Enemy가 두 번 사망 통지를 보내도 Count가 다른 Enemy까지 감소시키지 않아야 한다. 현재 정수 기반 API는 완전한 검증이 어려우므로 Actor 식별 기반 개선의 근거가 된다.

### 회귀 위험

- 0명 생성 시 즉시 Clear를 선택하면 잘못된 데이터가 정상 진행처럼 숨겨질 수 있음
- 실패 UI를 선택하면 자동 테스트 및 전용 서버에서 UI 의존 문제가 생길 수 있음
- Stage Clear가 Spawn 함수 실행 중 재진입하면 상태 변경 순서가 꼬일 수 있음
- 향후 지연 Spawn을 구현하면 “생성 대기 수”와 “생존 수”를 따로 관리해야 함

### 수정 완료 보고 연습

> Enemy Spawn 함수가 생성된 Actor를 반환하도록 변경하고 실제 Spawn 성공 시에만 `AliveEnemyCount`를 증가시켰습니다. 유효한 적이 한 명도 생성되지 않은 경우에는 설정 오류를 기록하고 정의된 실패 정책으로 전환하도록 했습니다. 정상 생성, 일부 실패, 전체 실패와 잘못된 RowName 조건을 검증해 Stage가 교착되지 않는 것을 확인했습니다.

---

# 13. 추가로 검증받을 가능성이 높은 수정 시나리오

상급자 코드 리뷰라면 HP와 Count 다음으로 아래 항목을 볼 가능성이 높다.

## 우선순위 1: Object Pool 중복 반환

검증 의도:

- 자료구조의 상태 전이를 이해하는가?
- 객체 수명과 재진입 문제를 고려하는가?
- 풀링을 단순히 복사해 사용한 것인지 원리를 아는가?

수정 핵심:

- `InUseActors.RemoveSingleSwap()` 결과 확인
- 이미 Available인 Actor의 반환 거부
- `ensureMsgf`로 개발 중 불변조건 위반 노출
- Acquire/Release 반복 및 중복 Release 테스트

## 우선순위 2: Wave/Stage 미사용 데이터

검증 의도:

- 데이터 구조를 만든 것과 기능을 완성한 것을 구분하는가?
- 완료보고서의 주장과 실제 구현을 스스로 대조했는가?

수정 핵심:

- `EnemyCount`와 Variant 배열의 관계 정의
- `SpawnInterval`에 따른 Timer 기반 지연 생성
- Spawn 거리와 Wave 배율 적용
- Stage 배율 및 Duration 적용 또는 필드 제거
- 생성 대기 수와 생존 수 분리

## 우선순위 3: Attribute 복제 정책

검증 의도:

- GAS Attribute가 있다고 네트워크 처리가 자동 완성되는 것이 아님을 아는가?
- 싱글플레이 요구사항과 멀티플레이 확장을 구분하는가?

수정 핵심:

- 프로젝트가 싱글플레이 전용인지 먼저 결정
- 멀티플레이 범위라면 `ReplicatedUsing`과 `OnRep`
- `GAMEPLAYATTRIBUTE_REPNOTIFY`
- ASC Replication Mode 및 Authority 정책
- GameMode 상태 중 클라이언트 표시 값은 GameState로 이전

## 우선순위 4: 재장전 취소와 Notify 의존성

검증 의도:

- AnimationNotify가 호출되지 않는 실패 경로를 고려하는가?
- 애니메이션과 코드 상태의 수명 동기화를 이해하는가?

확인 조건:

- 재장전 중 사망
- Montage 강제 중단
- 재장전 중 무기 교체
- Notify가 없는 Montage 지정
- 입력 연타

수정 핵심:

- Reload 시작/완료/취소 상태를 분리
- Montage 종료 Delegate 또는 Ability 종료 경로에서 취소 정리
- Ammo 변경은 한 경로에서만 실행

## 우선순위 5: 동기 Asset Load

검증 의도:

- Soft Reference를 사용한 목적과 실제 로드 방식이 일치하는가?
- 게임 중 Hitch 가능성을 측정할 수 있는가?

수정 핵심:

- 필수 Asset은 에디터 참조로 주입
- 선택 Asset은 Stage 시작 전 비동기 로드
- 하드코딩 경로 fallback 축소
- Asset 누락 시 안전한 실패 처리

## 우선순위 6: UI Tick 갱신

검증 의도:

- 성능 문제를 측정 없이 단정하지 않는가?
- 이벤트 기반 상태 전달을 설계할 수 있는가?

수정 핵심:

- HP/Stamina는 Attribute Delegate
- Experience/Ammo는 변경 Delegate
- Widget 생성과 Delegate 해제 수명 확인
- Crosshair처럼 프레임 갱신이 필요한 UI만 Tick 유지

## 우선순위 7: Character 책임 분리

검증 의도:

- 큰 클래스를 무조건 나누는 것이 아니라 변경 이유와 상태 소유권으로 분리하는가?
- 리팩터링 범위와 기능 버그 수정을 구분하는가?

수정 핵심:

- 테스트 없이 대규모 분리하지 않음
- Combat, Progression, Aim, Interaction 순서 검토
- Component 간 직접 결합보다 인터페이스와 Delegate 계약 정의
- 기존 Blueprint API 마이그레이션 계획 작성

---

# 14. 상급자 코드 리뷰 예상 시나리오

## 시나리오 1: 코드를 열어 직접 설명시키기

상급자 질문:

> `ZProjectileBase.cpp`를 열고 충돌부터 피해와 Pool 반환까지 한 줄씩 설명해 보세요.

확인 의도:

- 실제 코드 친숙도
- 정상/관통/GAS fallback 분기 이해
- 복사한 코드를 실행 흐름으로 설명할 수 있는지

대응 방법:

```text
입력 검증
→ 중복 타격 방지
→ 피해 경로 선택
→ 속성 상태 적용
→ 관통 여부
→ 반환
```

## 시나리오 2: 값을 바꿔 결과 예측시키기

상급자 질문:

> `PierceCount`가 2이고 `PierceDamageRetention`이 0.5이며 최초 피해가 40이면 세 대상 피해는 어떻게 됩니까?

모범 답변:

현재 코드 기준으로 첫 대상 40, 두 번째 20, 세 번째 10의 피해가 적용되고 세 번째 충돌 뒤 반환된다. 단, 모든 대상이 Damageable이고 중복 Actor가 아니며 GAS 또는 fallback 피해가 성공한다는 조건이다.

## 시나리오 3: 실패 조건을 즉석에서 만들기

상급자 질문:

> `SpawnActor()`가 두 번째 Enemy에서만 실패했다고 가정하면 Stage는 어떻게 됩니까?

모범 답변:

현재 코드는 실패 여부와 무관하게 Count를 증가시키므로 실제 생성 수보다 `AliveEnemyCount`가 1 크게 남는다. 생성된 적이 모두 죽어도 1이 남아 Stage Clear가 실행되지 않는다.

## 시나리오 4: 수정 범위 압박

상급자 질문:

> HP 문제를 고치기 위해 지금 전체 GAS 구조를 다시 만들 겁니까?

모범 답변:

> 즉시 전체 재작성하지는 않겠습니다. 먼저 모든 피해 경로가 동일한 Attribute HP를 변경하도록 최소 통합하고 공격 순서 회귀 테스트를 추가하겠습니다. 이후 사망과 UI를 Attribute Delegate로 이동하고 Legacy HP를 제거하는 작업을 별도 단계로 나누겠습니다.

## 시나리오 5: 보고서 정확성 확인

상급자 질문:

> 보고서에는 Wave별 적 수와 난이도를 데이터로 관리한다고 했는데 `EnemyCount`와 Wave 배율은 어디에서 사용합니까?

모범 답변:

> 현재 Struct에는 선언되어 있지만 실제 GameMode 생성 경로에서는 사용되지 않습니다. Variant RowName 수가 생성 수로 동작하고 Wave 배율 적용 함수도 호출되지 않습니다. 보고서 표현이 실제 완성 범위보다 넓으므로 정정하겠습니다.

## 시나리오 6: 성능 근거 확인

상급자 질문:

> Pool 적용 전후 성능 수치를 보여주세요.

모범 답변:

> 현재 비교 측정 자료는 없습니다. 따라서 반복 Spawn/Destroy 비용을 줄이려는 구조를 적용했다고만 말할 수 있고 성능 향상을 확정할 수는 없습니다. 동일 발사량에서 Game Thread, GC 지연과 메모리를 Unreal Insights로 비교하겠습니다.

---

# 15. 코드 리뷰 검증 대비 우선 학습 순서

시간이 제한돼 있다면 다음 순서로 연습한다.

1. Enemy HP 두 값의 변경 경로를 종이에 그린다.
2. Spawn 요청 수, 성공 수와 생존 수를 구분한다.
3. Pool의 Available/InUse 상태 전이를 설명한다.
4. Projectile 충돌에서 GAS와 fallback 분기를 설명한다.
5. Effect Context, DynamicGrantedTags와 SetByCaller를 구분한다.
6. Wave/Stage에서 선언만 되고 사용되지 않는 필드를 찾는다.
7. 재장전 취소, UI Tick과 Asset Load의 위험을 설명한다.
8. 각 항목에 최소 재현 테스트 하나를 붙인다.

가장 먼저 외울 것은 API 이름이 아니라 다음 두 불변조건이다.

```text
Enemy HP의 원천은 하나여야 한다.
AliveEnemyCount는 실제 살아 있는 Enemy 수와 같아야 한다.
```

---

# 16. 최종 기억 사항

좋은 코드 리뷰는 다음 문장을 완성할 수 있어야 한다.

> 이 코드는 **어떤 조건에서**, **어떤 불변조건을 깨뜨리고**, 그 결과 **사용자 또는 시스템에 어떤 영향**을 주기 때문에, **이 범위로 수정**하고 **이 테스트로 검증**해야 합니다.

반대로 다음 표현만 있는 리뷰는 피한다.

- 코드가 지저분하다.
- 확장성이 떨어진다.
- 최적화가 필요하다.
- 컴포넌트로 분리해야 한다.
- 예외 처리를 추가해야 한다.

이 표현들은 근거, 영향과 완료 조건이 없기 때문에 실행 가능한 리뷰가 아니다.

---

## 검증 상태

- Project_Z 실제 C++ 코드 기반 시나리오 작성: 완료
- 코드 리뷰 예상 질문과 답변: 완료
- 반박 대응 시나리오: 완료
- 연습 계획 및 채점표: 완료
- 프로젝트 C++/Blueprint/Asset 수정: 없음
- 빌드 및 PIE: 문서 작성 작업이므로 미실행
