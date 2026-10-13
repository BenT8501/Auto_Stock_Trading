# Project_Z 공통 캐릭터 로직 BaseMulti 이관 기록

- 작성일: 2026-10-14
- 대상 프로젝트: `Project/Project_Z`
- 대상 클래스:
  - 부모: `AZCharacterBaseMulti`
  - 자식: `AZCharacter_TPS`
- 검증 엔진: Unreal Engine 5.7.4
- 빌드 타깃: `Project_ZEditor Win64 Development`

## 1. 작업 목적

TPS 클래스에 들어 있던 공통 캐릭터 데이터 적용, 재장전/공통 애니메이션, 투사체 생성 및 발사 로직을 `AZCharacterBaseMulti`로 이관한다.

TPS 클래스에는 TPS 조작 방식에 종속적인 카메라, 마우스 조준, 조준 방향 및 총구 위치 보정만 남긴다.

무기 메시 장착/해제와 Niagara 시각화는 이번 작업에서 이관하지 않는다. 해당 범위는 별도 검토 후 진행한다.

## 2. 이관한 공개 API

다음 Blueprint/C++ API의 선언과 구현을 `AZCharacter_TPS`에서 `AZCharacterBaseMulti`로 이동했다.

### 캐릭터 데이터 적용

- `ApplyCharacterDataAsset()`
- `ApplyResolvedCharacterData(...)`

처리 내용:

- `UZCharacterDataAsset` 값을 `FCharacterDataRow`로 변환
- 기본 원거리 무기 데이터 선택
- 캐릭터 Skeletal Mesh 적용
- Animation Blueprint 적용
- 이동 속도 적용
- AttributeSet 기본 HP/MP/Stamina/MoveSpeed 초기화
- 메타 진행 보너스 적용 기준값 초기화

### 재장전

- `Reload()`
- `FinishReload()`

처리 내용:

- 활성 원거리 무기 존재 여부 확인
- 현재 탄약과 레벨 기준 기본 탄약 비교
- 재장전 몽타주 재생
- AnimNotify 이후 탄약 충전

### 공통 애니메이션

- `ResolveAnimationSetForWeapon(...)`
- `RefreshCharacterAnimation()`
- `PlayEquipAnimation()`
- `PlayReloadAnimation()`
- `PlayDeathAnimation()`
- `PlayAttackAnimation()`

처리 내용:

- 무기 애니메이션 타입별 AnimBP/몽타주 조회
- 현재 AnimBP 교체
- 장착/재장전/사망/공격 몽타주 재생
- 무기 데이터의 `AttackAnimationPlayRate` 적용

### 투사체 생성 및 발사

- `ActivatePrimaryWeapon()`
- `FirePrimaryProjectile()`
- `FireSecondaryProjectile()`

공통 발사 처리:

- 활성 무기 및 ProjectileClass 검증
- `UZActorPoolSubsystem`에서 투사체 획득
- 단발/산탄 발사 방향 계산
- 런타임 공격력 보너스 적용
- 관통 수치 적용
- 속성 상태와 색상 적용
- 투사체 속도 및 반환 거리 적용
- 성공한 발사에 한해 공격 애니메이션 재생
- 탄약 1 감소

## 3. BaseMulti로 이동한 상태 데이터

캐릭터 데이터 재적용 시 초기화되는 다음 상태도 부모로 이동했다.

- `AppliedMetaMaxHPBonus`
- `AppliedMetaMoveSpeedBonus`
- `AppliedMetaDamageBonus`
- `AppliedMetaPickupRadiusBonus`

기존에 부모로 이동돼 있던 다음 상태와 함께 공통 로직에서 사용한다.

- `CharacterDataAsset`
- `CurrentData`
- `CurrentWeaponData`
- `CurrentEquipMontage`
- `CurrentReloadMontage`
- `DeathMontage`
- `currentAmmo`
- 투사체 런타임 보너스 값

## 4. TPS에 남긴 투사체 훅

실제 투사체 생성과 발사는 부모가 담당하지만, 조준 방식은 모드마다 다르므로 다음 함수를 가상 함수로 분리했다.

### BaseMulti 기본 구현

- `GetProjectileAimPoint(...)`
  - Controller 회전 또는 캐릭터 전방 기준
  - Visibility LineTrace 수행

- `GetProjectileSpawnLocation(...)`
  - 장착 무기 Muzzle 소켓 우선
  - 캐릭터 Attach 소켓 대체
  - 캐릭터 전방 위치 최종 대체

### TPS override

- `AZCharacter_TPS::GetProjectileAimPoint(...)`
  - TPS 카메라 위치/방향
  - 마우스 조준점
  - AimYawOffset/AimPitchOffset 반영

- `AZCharacter_TPS::GetProjectileSpawnLocation(...)`
  - 장착 무기 Muzzle 소켓
  - 라이플/샷건별 위치 오프셋
  - FollowCamera 기반 대체 위치

따라서 발사 규칙은 공통이고 조준·생성 위치 정책만 TPS에 남는다.

## 5. 의도적으로 TPS에 남긴 범위

이번 이관에서 다음 로직은 수정하거나 부모로 이동하지 않았다.

### 무기 장착 및 시각화

- `EquipWeaponFromPickup(...)`
- `RefreshWeaponState()`
- `EquipWeaponVisual()`
- `UnequipWeaponVisual()`
- `RefreshWeaponElementEffect()`
- `ResolveWeaponElementEffect()`

관련 TPS 전용 상태:

- `WeaponElementEffectComponent`
- `WeaponElementEffectAsset`
- Niagara 파라미터 이름 및 시각 효과 보정값
- 크로스헤어 표시 갱신

검토가 필요한 이유:

- 논리적 장착과 메시 부착 코드가 중복돼 있다.
- 데이터/메시 컴포넌트는 부모에 있지만 표시 로직은 TPS에 있다.
- 무기 표시가 모든 캐릭터 모드의 공통 책임인지 결정이 필요하다.
- `UnequipWeaponVisual()`은 메시만 제거하고 `CurrentWeaponData`는 유지한다.

## 6. 변경 파일

- `Source/Project_Z/Public/Characters/ZCharacterBaseMulti.h`
- `Source/Project_Z/Private/Characters/ZCharacterBaseMulti.cpp`
- `Source/Project_Z/Public/Characters/ZCharacter_TPS.h`
- `Source/Project_Z/Private/Characters/ZCharacter_TPS.cpp`

Unreal 에셋 파일은 변경하지 않았다.

## 7. 검증 결과

실행 명령:

```powershell
D:\UE_5.7\Engine\Build\BatchFiles\Build.bat Project_ZEditor Win64 Development -Project=<Project_Z.uproject> -WaitMutex -NoHotReloadFromIDE
```

결과:

- UnrealHeaderTool 성공
- `ZCharacterBaseMulti.cpp` 컴파일 성공
- `ZCharacter_TPS.cpp` 컴파일 성공
- `UnrealEditor-Project_Z.lib` 링크 성공
- `UnrealEditor-Project_Z.dll` 링크 성공
- 최종 결과: `Succeeded`

## 8. 에디터 회귀 테스트 필요 항목

C++ 빌드는 통과했지만 다음 항목은 PIE에서 확인해야 한다.

- 기본 캐릭터 데이터 에셋 적용
- 기본 무기 및 시작 탄약 적용
- 공격 몽타주 재생
- 재장전 몽타주와 AnimNotify 이후 탄약 충전
- 단발 무기 발사
- 샷건 분산 발사
- 관통 수치와 속성 상태 전달
- 자동 공격
- 수동 조준 및 마우스 조준
- TPS 카메라 기준 발사 방향
- 무기 Muzzle 소켓과 대체 생성 위치
- 사망 몽타주
- 기존 무기 메시와 Niagara 시각화 유지

## 9. 다음 검토 권장 사항

무기 장착/시각화 이관 전 다음 정책을 먼저 결정한다.

1. `BaseMulti`가 무기 메시 컴포넌트를 직접 생성할 것인지
2. 논리적 장착과 화면 표시를 별도 함수로 유지할 것인지
3. FPS와 TPS가 동일한 소켓/오프셋 규칙을 사용할 것인지
4. 무기 속성 Niagara가 공통인지 TPS 전용인지
5. `UnequipWeaponVisual()` 호출 시 `CurrentWeaponData`도 제거할 것인지
