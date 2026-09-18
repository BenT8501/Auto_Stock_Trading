# Project_Z 검증 회의 대비 — 다른 에이전트 인계

작성일: 2026-09-18

## 1. 목적과 사용자 상황

사용자는 Project_Z Unreal 직무과제와 완료보고서를 상사에게 제출했다. 상사가 검증을 원하여 그 회의에 대비하는 중이다.

- 상사의 구체적인 검증 의도는 직접 전달받지 못했다.
- 사용자는 직접 구현 여부, AI 활용 정도, 구조를 직접 설계했는지 등을 확인하려는 것으로 추측한다. 이를 상사의 확정된 의도로 단정하지 않는다.
- 사용자에 따르면 이미 “거의 대부분 직접 구현했고, AI는 버그 관련 도움과 로직 타당성 검토 정도에 활용했다”고 보고했다.
- 초기 연습에서는 GAS에 도움을 받았다고도 설명했다. 실제 도움의 범위는 사용자의 구체적인 경험과 근거로 확인하며 임의로 생성·작성 범위를 추정하지 않는다.
- 목적은 일반 Unreal API 시험이 아니라, 제출 결과물의 실행 흐름·설계 판단·구현 범위·검토와 검증 경험을 본인 말로 설명하는 연습이다.
- AI 사용 자체를 감점하거나, 함수명을 기억하지 못했다는 이유만으로 직접 구현을 부정하지 않는다. 보고에 맞추기 위해 경험이나 근거를 꾸며내도록 돕지 않는다.

## 2. 최신 합의: 진행 방법

이 절은 과거 면접 문서의 기본 진행 방식보다 우선한다.

1. **실제 Project_Z 코드로 진행한다.** 일반적인 가상 숫자 문제와 가상 기능 설계 질문은 사용자 요청 없이 이어가지 않는다.
2. 질문에는 관련 파일·함수 범위를 붙인다. 제출 보고서의 구체적인 주장과 연결한다.
3. 실제 코드에 있는 호출 흐름, 상태 변경, 실패 분기, 설계 선택을 묻는다.
4. 한 번에 한 질문만 한다. 답변을 기다리고 짧게 평가한다.
5. 실제 구현, 개선 제안, 사용자 진술, 미확인 사항을 구분한다.
6. C++만으로 Blueprint 그래프·에셋 설정·PIE 결과를 확정하지 않는다.
7. 소스·Blueprint·에셋·설정은 사용자가 명시적으로 요청하기 전에는 수정하지 않는다.
8. 사용자는 현재 Object Pool 이해가 부족하다고 느껴 **스파링을 멈췄다.** 다음에는 바로 채점하지 말고 실제 코드를 함수 하나씩 읽으며 설명한 뒤 본인 말로 정리하게 한다. 준비되면 검증 스파링으로 돌아간다.
9. 단순 확인 질문을 끝없이 반복하지 않는다. 오답이면 핵심을 짧게 설명하고 유사 확인을 한 번 한 뒤 학습 필요 여부를 판단한다.
10. 과거의 점수는 당시 대화에 대한 잠정 평가다. 학습 직후 정답과 독립적인 최초 답변을 구분한다. 작성 여부를 점수로 증명했다고 표현하지 않는다.

당일에는 오후 6시 30분 종료를 요청했으나, 이후 사용자가 중단하고 다른 장소에서 이어갈 준비를 요청했다. 집에서 새 세션을 시작할 때 이 종료 시각을 그대로 적용하지 않는다.

## 3. 자료 위치와 집에서의 준비

현재 작업 공간의 경로다. 집에서는 같은 경로라고 가정하지 말고 실제 위치를 확인한다.

| 자료 | 현재 경로 |
|---|---|
| **사용자 지정 제출 완료보고서** | `C:/WorkSpace/Auto_Stock_Trading/NeedPlans/박종호B_직무과제_완료보고서_정리.md` |
| 실제 프로젝트 | `C:/WorkSpace/WorkSpace/Project/Project_Z` |
| 실제 C++ 루트 | `C:/WorkSpace/WorkSpace/Project/Project_Z/Source/Project_Z` |
| 면접 가이드 | `C:/WorkSpace/Auto_Stock_Trading/Project_Z/docs/Project_Z_Verification_Mock_Interview.md` |
| 기술 가이드 | 같은 docs 폴더의 `Project_Z_Technical_Interview_Guide.md` |
| 기존 코드 리뷰 | 같은 docs 폴더의 `Project_Z_Code_Review.md` |
| 코드 리뷰 워크북 | 같은 docs 폴더의 `Project_Z_Code_Review_Practice.md` |
| 1회차 기록 | 같은 docs 폴더의 `Project_Z_Mock_Interview_Session_01.md` |
| Pool 집중 계획 | 같은 docs 폴더의 `Project_Z_ObjectPool_Next_Session.md` |

집으로 이 인계 파일뿐 아니라 **제출 보고서, docs 폴더, 실제 Source 폴더**도 함께 가져가야 코드 기반 학습이 가능하다. PIE·Blueprint 검증까지 하려면 Project_Z 프로젝트 전체와 해당 엔진 환경이 필요하다. 자료가 없으면 코드 확인을 했다고 주장하지 말고 필요한 경로를 요청한다.

원격 출처: `https://github.com/BenT8501/WorkSpace/tree/main/Project/Project_Z`

주의: 앞선 에이전트가 전체 저장소와 이력을 복제해 불필요한 용량과 트래픽이 발생했다. 사용자의 요청으로 다른 프로젝트와 `.git`을 삭제했고 **Project_Z만 보존**했다. 현재 위 프로젝트는 일반 폴더이며 Git 저장소가 아니다. 새로 받더라도 전체 저장소를 무작정 복제하지 않는다. 우선 이미 있는 로컬 자료를 사용한다. 제출 시점 소스와 현재 원격 main이 동일한지도 검증된 것은 아니다.

## 4. 제출 보고서의 범위

상사에게 전달됐다고 사용자가 지정한 것은 위 `NeedPlans` 경로의 파일이다. 다른 사본보다 이 파일을 기준으로 한다.

- C++/Blueprint 책임 분리, Character·PlayerController·GameMode·Widget 역할 분담
- TPS 이동·조준·엄폐·총기 발사와 무기별 설정
- Projectile 충돌·관통·Object Pool 반환
- 재장전 Montage와 AnimationNotify
- HUD·상호작용·Stage Clear/Game Over 및 입력 모드
- Weapon DataAsset, Wave/Monster Variant DataTable
- GAS 피해, SetByCaller, 헤드샷 판정·태그, ASC 없는 대상의 인터페이스 피해
- 적 AI, 변종, 성장 보상, Stage 진행
- 무기 파츠는 **미구현**, GAS는 **숙련이 아닌 기본 적용 수준**으로 명시

질문 연결 방식: 보고서 주장 → 실제 관련 코드 → 선택 이유와 본인 작업 경험 → 실제 검증한 결과. 문서의 주장이 코드와 다르면 정확한 적용 범위를 설명하도록 돕는다.

## 5. 현재 멈춘 핵심 논점: InitializePool은 왜 있는가?

사용자의 마지막 기술 질문:

> “InitializePool을 호출하는 데가 없다. Release나 Acquire에서 Add하는 것은 봤는데, 왜 InitializePool을 만든 것인가?”

실제 C++ 검색으로 확인한 사실:

- `InitializePool()`의 선언과 정의는 있으나 **Project_Z C++ 소스 내 호출부는 발견되지 않았다.**
- 헤더에서 `BlueprintCallable`로 노출되어 있다. **Blueprint 호출 여부는 미확인**이므로 전체 프로젝트에서 절대 호출되지 않는다고 단정하지 않는다.
- Pool은 `InitializePool()` 없이도 `AcquireActor()`에서 항목을 만들고 Actor를 생성할 수 있다.
- 왜 함수를 만들고 호출하지 않았는지, 원래 작성자의 이력·의도는 코드만으로 확정할 수 없다.

### 확인한 자료구조

`Public/Pooling/ZActorPoolSubsystem.h`:

```cpp
struct FZActorPoolBucket
{
    // 실제 선언에는 USTRUCT/GENERATED_BODY/UPROPERTY가 있음
    TArray<TObjectPtr<AActor>> AvailableActors;
    TArray<TObjectPtr<AActor>> InUseActors;
};

TMap<TSubclassOf<AActor>, FZActorPoolBucket> Pools;
TMap<TObjectPtr<AActor>, TSubclassOf<AActor>> ActorToPoolClass;
```

- `Pools`: Actor 클래스별로 대기 목록과 사용 중 목록을 가진다.
- `ActorToPoolClass`: 반환할 Actor가 어느 클래스의 Pool 소속인지 찾는 역방향 매핑이다.

### 실제 생성·재사용 경로

```text
AZCharacterBase::FirePrimaryProjectile()
→ UZActorPoolSubsystem::AcquireProjectile()
→ AcquireActor()
  → Pools.FindOrAdd(ActorClass)
  → AvailableActors에서 Pop하여 Actor 획득 시도
  → 얻은 Actor가 없으면 SpawnPooledActor()
  → 생성 실패면 nullptr 반환
  → 새로 생성했으면 ActorToPoolClass에 등록
  → PrepareActorForAcquire()
  → InUseActors.Add()
```

`Pools.FindOrAdd(ActorClass)`는 키가 없으면 빈 Bucket을 추가하고 그 참조를 반환한다.

```cpp
FZActorPoolBucket& PoolBucket = Pools.FindOrAdd(ActorClass);
```

`&` 참조이므로 `PoolBucket`의 배열을 바꾸면 `Pools` 내부의 해당 Bucket이 변경된다. Bucket을 생성하는 것과 실제 Actor를 Spawn하는 것은 별개다.

### InitializePool의 코드상 역할

```text
ActorClass/InitialSize 검사
→ Pools.FindOrAdd(ActorClass)
→ MissingCount = Max(0, InitialSize - Available 수 - InUse 수)
→ 부족한 수만큼 SpawnPooledActor()
→ PrepareActorForRelease()
→ AvailableActors.Add()
→ ActorToPoolClass.Add()
```

기능은 **Actor 사전 생성(prewarm)**이다. 이미 존재하는 대기·사용 중 Actor 수를 포함해 목표 수까지 채운다. 현재 C++ 발사 경로가 동작하기 위한 필수 초기화 함수는 아니다.

사용자에게 전달한 정확한 결론:

> 사전 생성용 InitializePool은 구현돼 있지만 C++ 호출부에는 연결되지 않았다. 실제 발사에서는 AcquireActor가 필요할 때 생성하고 반환된 Actor를 이후 재사용한다. Blueprint 호출도 없다면 현재 미사용 함수다. 왜 남겨두었는지는 작성 이력 없이 단정할 수 없다.

이전에 Pool을 일반적으로 “미리 생성해 두는 방식”이라고 설명하면서 실제 프로젝트의 호출 여부를 충분히 구분하지 않은 점을 정정했다. 다음 에이전트는 다시 사전 생성이 현재 실행된다고 설명하지 않는다.

## 6. 다음 학습 순서

먼저 사용자의 InitializePool 의문이 해소됐는지 확인한다. 전체 구조를 강의하기보다 다음 함수 순서로 실제 코드를 읽는다.

1. 헤더: `Pools`의 Key/Value, Bucket의 두 배열, 참조와 Actor 인스턴스 구분
2. `AcquireActor()`: FindOrAdd → Pop → 필요 시 Spawn → InUse 등록
3. `ReleaseActor()`: 역방향 매핑 → InUse 제거 → 비활성화 → Available 등록
4. `PrepareActorForAcquire/Release()`: 공통 Actor 상태 처리
5. Projectile의 Pool 인터페이스 구현: Timer·타격 기록·피해량·관통·속성 등 초기화
6. Character 발사 함수: 획득 후 Owner·피해·방향을 설정하는 실제 순서
7. `InitializePool()`: 사전 생성과 필요 시 생성의 차이, 실제 연결 여부

학습 후에만 보고서의 Object Pool 성과를 본인 말로 설명하게 하며, 상사 역할의 스파링으로 복귀한다.

## 7. 최근 학습 상태와 유의점

이해가 개선된 영역:

- 생성 시도 수, 생성 성공 수, 생존 수를 구분할 수 있으나 질문의 기준 시점을 놓치는 경우가 있다.
- HP 이중 관리의 값 변화와 덮어쓰기 문제를 설명했다.
- 중복 사망 통지와 조기 클리어, bIsDead를 먼저 설정해야 하는 이유를 이해했다.
- Pool 중복 반환의 포인터 중복과 발사 상태 덮어쓰기를 설명했다.
- 재장전 취소는 탄약 유지와 상태 해제를 분리해야 함을 설명 후 이해했다.
- 이벤트 기반 HUD의 초기 표시, 중복 구독, 이전 구독 해제는 별도 학습이 필요했다.
- 성능 비교의 동일 작업량과 목표 메모리 예산을 고려하는 방향으로 개선됐다.

집중 보완:

- 클래스, 개별 Actor 인스턴스, 동일 포인터, 유효한 객체의 차이
- Pool 반환과 Destroy의 차이, World와 GameInstance 수명
- Actor 재사용 성공과 상태 초기화 성공은 다른 검증임
- 이전 피해량은 반드시 중복 합산되는 것이 아니라 오래된 override가 남는 문제일 수 있음
- 화면 숨김과 충돌 비활성화는 별개
- Timer의 실제 설정·해제 경로, 반환 원인 추적
- 실제 코드 사실을 먼저 이해한 뒤 설계 이유를 설명하기

과거 반복 질문에서 생긴 혼동을 고정된 능력 부족으로 취급하지 않는다. 현재 실제 코드 이해를 새로 확인한다.

## 8. 집에서 새 에이전트에게 붙여넣을 프롬프트

```text
첨부한 Project_Z_Interview_Handoff.md를 먼저 읽어 줘.

상사에게 제출한 Project_Z와 완료보고서에 대한 검증 회의를 준비 중이야.
거의 대부분 직접 구현했고 AI는 버그 관련 도움과 로직 타당성 검토에 활용했다고 보고한 상태야.
상사의 정확한 검증 의도는 아직 모르니 추측을 확정하지 마.

지금은 스파링을 중단하고 Object Pool 실제 코드부터 학습하려고 해.
가상 문제보다 실제 파일과 함수의 동작을 설명해 줘.
특히 InitializePool은 C++ 호출부가 없는데 Pools가 어디서 채워지고
AcquireActor와 ReleaseActor만으로 어떻게 동작하는지가 현재 학습 지점이야.

먼저 이 컴퓨터의 Project_Z 소스와 제출 완료보고서 위치를 확인해 줘.
자료가 없다면 경로를 물어보고 실제 코드를 읽었다고 하지 마.
전체 WorkSpace 저장소를 다시 복제하지 마.

실제 코드를 함수 하나씩 짧게 설명하고 내가 내 말로 정리할 기회를 줘.
내가 준비됐다고 하면 제출 보고서와 실제 코드에 기반한 상사 검증 스파링으로 전환해 줘.
한 번에 한 질문씩 하고, 확인하지 않은 Blueprint나 실행 결과는 단정하지 마.
내가 요청하기 전에는 소스·에셋·설정을 수정하지 마.
```
