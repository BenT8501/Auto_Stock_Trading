# Project_Z 검증 대비 분석 및 학습 목록

## 1. 문서 목적

이 문서는 제출한 Project_Z의 검증에 대비해 프로젝트 구조, 게임 로직, C++ 코드, Blueprint 및 데이터 연결 상태를 체계적으로 분석하기 위한 작업 목록이다.

새로운 기능을 추가하거나 제출본을 임의로 수정하는 것이 목적이 아니다. 현재 제출된 기능이 어떤 구조로 동작하는지 확인하고, 구현 근거와 한계, 미완성 항목 및 개선 방향을 설명할 수 있도록 준비하는 것이 목적이다.

## 2. 기본 원칙

- 제출본 코드를 임의로 수정하지 않는다.
- 분석 기준이 되는 commit, 압축 파일 또는 전달 버전을 기록한다.
- 정상 동작, 부분 동작, 미구현을 명확히 구분한다.
- 문서 설명이 아니라 실제 코드와 Blueprint 연결을 근거로 판단한다.
- 추측한 내용은 `추정`으로 표시하고 실행 또는 코드로 확인한다.
- 문제를 발견해도 숨기지 않고 재현 조건, 원인 후보 및 영향 범위를 기록한다.
- 수정이 필요하면 먼저 수정안과 영향 범위를 보고한 후 승인받는다.

## 3. 최종 산출물 목록

분석 담당 에이전트는 다음 자료를 작성한다.

1. 프로젝트 전체 구조도
2. 핵심 클래스 책임표
3. 객체 간 참조·호출 관계도
4. 핵심 게임플레이 로직 흐름도
5. 데이터 흐름 및 에셋 연결표
6. 기능별 코드 위치 목록
7. 기능별 검증 결과표
8. 완료·부분 완료·미구현 목록
9. 알려진 문제 및 기술 부채 목록
10. 예상 코드 리뷰 질문과 답변 초안
11. 발표자가 공부해야 할 핵심 개념 목록
12. 실행·빌드·시연 절차

## 4. 프로젝트 기준 정보 확인

### 확인할 내용

- Unreal Engine 정확한 버전
- 프로젝트명과 기본 실행 맵
- 기본 GameMode, PlayerController 및 Character
- 사용 중인 플러그인
- Target 및 Build 설정
- 필수 모듈과 의존성
- 프로젝트 실행에 필요한 외부 에셋
- 소스 관리 기준 commit 또는 전달 일자
- 에디터 빌드와 패키징 성공 여부

### 산출물 형식

| 항목 | 확인 결과 | 근거 파일 또는 위치 | 비고 |
|---|---|---|---|
| Unreal 버전 |  | `.uproject` |  |
| 기본 맵 |  | Project Settings |  |
| 기본 GameMode |  | World Settings 또는 Config |  |
| 필수 플러그인 |  | `.uproject` |  |
| 주요 모듈 |  | `.Build.cs` |  |

## 5. 구조적 설계 분석

### 5.1 전체 계층 구조

다음 영역을 구분하여 구조도를 작성한다.

- Game Framework
- Player
- Enemy 및 AI
- Weapon 및 Combat
- Projectile 및 Object Pool
- GAS 및 Attribute
- XP 및 Level Up
- Wave 및 Spawn
- UI 및 HUD
- DataAsset 및 DataTable

구조도에는 단순 클래스 목록이 아니라 소유 관계와 참조 방향을 표시한다.

```text
GameMode
├─ Wave/Spawn 관리
├─ 게임 상태 전환
└─ Player/Enemy 흐름 제어

Player
├─ 입력 및 이동
├─ 현재 Weapon 참조
├─ AbilitySystemComponent
└─ HUD에 상태 제공

Weapon
├─ WeaponData 참조
├─ 발사 조건 검사
└─ Projectile Pool 요청
```

### 5.2 클래스 책임 분석

각 핵심 클래스에 대해 다음을 정리한다.

| 클래스 | 핵심 책임 | 소유 객체 | 주요 참조 | 생성·소멸 시점 | 문제 가능성 |
|---|---|---|---|---|---|
| GameMode |  |  |  |  |  |
| Character |  |  |  |  |  |
| PlayerController |  |  |  |  |  |
| Weapon |  |  |  |  |  |
| Projectile |  |  |  |  |  |
| Enemy |  |  |  |  |  |
| AIController |  |  |  |  |  |
| AttributeSet |  |  |  |  |  |

### 확인 질문

- 한 클래스가 지나치게 많은 책임을 가지고 있지 않은가?
- GameMode, Character, Controller 및 Component의 역할이 섞이지 않았는가?
- 서로 강하게 결합된 클래스는 무엇인가?
- 순환 참조 또는 불필요한 Cast가 반복되는가?
- C++과 Blueprint의 책임 분리 기준이 일관적인가?
- 향후 기능 추가 시 수정 범위가 한 곳에 집중되는가?

## 6. 로직 설계 분석

각 기능은 `입력 또는 시작 조건 → 상태 확인 → 핵심 처리 → 결과 반영 → 종료 또는 다음 상태` 순서로 정리한다.

### 6.1 플레이어 입력과 이동

- Enhanced Input Mapping Context 등록 시점
- Move, Look, Jump 및 Attack 입력 연결 위치
- Controller 입력과 Character 동작의 분리
- 이동 및 조준 상태가 Animation Blueprint에 전달되는 과정
- 입력 중복 바인딩 가능성

### 6.2 무기 발사

다음 흐름을 함수명과 파일 위치까지 추적한다.

```text
입력
→ 발사 요청
→ 현재 무기 확인
→ 탄약·쿨다운 확인
→ Projectile Pool 요청
→ Projectile 활성화
→ 이동 및 충돌
→ 피격 처리
→ Projectile 비활성화 및 반환
```

확인 항목:

- 발사 가능 조건이 한 곳에서 관리되는가?
- 무기 데이터가 DataAsset에서 실제로 적용되는가?
- 총알 생성 위치와 발사 방향의 기준은 무엇인가?
- 중복 발사와 중복 피격이 방지되는가?
- Object Pool 사용 중 `Destroy()` 경로가 남아 있지 않은가?

### 6.3 데미지 및 Headshot

```text
Projectile 충돌
→ HitResult 확인
→ 대상의 GAS 적용 여부 확인
→ Bone 또는 위치로 Headshot 판정
→ 데미지 및 배율 계산
→ GameplayEffect 또는 Damage Interface 적용
→ HP 감소
→ 사망 조건 확인
```

확인 항목:

- 데미지의 최종 결정 위치는 어디인가?
- Headshot 판정 기준과 실패 시 fallback은 무엇인가?
- 기본 데미지와 Headshot 배율은 어디에서 관리하는가?
- GAS 경로와 기존 Damage Interface 경로가 중복 적용될 가능성은 없는가?
- HP가 0 이하로 내려갈 때 사망 처리가 한 번만 호출되는가?

### 6.4 GAS 처리

- AbilitySystemComponent 생성 및 초기화 시점
- OwnerActor와 AvatarActor 설정
- AttributeSet 생성과 기본값 초기화
- GameplayAbility 부여 시점
- GameplayEffectSpec 생성 과정
- SetByCaller `Data.Damage` 전달 과정
- GameplayTag 등록과 사용 위치
- Attribute 변경 이후 기존 체력·사망 시스템과의 연결

설명할 수 있어야 하는 질문:

- GAS를 도입한 이유는 무엇인가?
- 단순 데미지 처리와 비교한 장단점은 무엇인가?
- 왜 기존 Damage Interface를 함께 유지했는가?
- GAS 적용 대상과 미적용 대상을 어떻게 구분하는가?

### 6.5 Enemy AI

- Enemy 생성 주체
- AIController Possess 시점
- 플레이어 감지 조건
- Idle, Chase 및 Attack 상태 전환
- 엄폐 상태가 감지에 반영되는 위치
- 공격 범위와 공격 간격
- 플레이어 또는 Enemy 참조가 무효화될 때 처리

보고서에 기재한 AI 기능과 실제 구현 수준을 비교하고, 부분 구현이면 조건과 한계를 기록한다.

### 6.6 사망, XP 및 보상

```text
Enemy HP 0
→ 중복 사망 방지
→ 공격 및 충돌 중지
→ 사망 표현
→ XP 또는 보상 생성
→ Player 획득
→ 레벨업 조건 확인
→ 선택 UI 표시
→ 선택 결과 적용
```

확인 항목:

- 사망 처리가 여러 번 호출되지 않는가?
- XP 보상을 받을 플레이어는 어떻게 결정하는가?
- XP Pickup의 소유권과 수명은 어떻게 관리하는가?
- 레벨업 도중 입력과 게임 진행은 어떻게 처리되는가?
- 선택 결과가 실제 능력치에 누적 적용되는가?

### 6.7 Wave 및 게임 진행

- Ready, Playing, Stage Clear 및 Game Over 상태 정의
- Wave 시작과 종료 조건
- 적 생성 수와 동시 생존 수 관리
- Boss 생성 조건
- Timer 정리 시점
- 재시작 시 이전 상태가 남지 않는지 확인

### 6.8 UI 갱신

- HP, XP, Level, Ammo 및 Wave 데이터 제공 주체
- Tick Binding인지 이벤트 기반 갱신인지 확인
- Widget 생성과 Viewport 등록 시점
- Character 사망 또는 재생성 시 참조 갱신
- UI가 게임 로직을 직접 변경하는지 확인
- `BindWidgetOptional` 사용 이유와 fallback 구조

## 7. 코드 설계 및 품질 검토

### 7.1 Unreal 객체 수명

- `UPROPERTY`가 필요한 UObject 참조에 적용됐는가?
- Actor와 Component 생성 방식이 적절한가?
- `BeginPlay`, `EndPlay`, `Destroyed`의 역할이 올바른가?
- Timer와 Delegate가 종료 시 해제되는가?
- 비동기 또는 지연 호출에서 무효 객체를 참조하지 않는가?
- `IsValid()` 검사가 필요한 경로는 어디인가?

### 7.2 포인터와 참조 안전성

- Raw Pointer, TObjectPtr, TWeakObjectPtr 사용 기준
- Null 확인 누락
- 다운캐스팅이 실패했을 때 처리
- Blueprint에서 설정하지 않은 클래스·에셋 처리
- 배열 인덱스와 DataTable Row 조회 실패 처리

### 7.3 성능

- Tick을 사용하는 클래스와 Tick에서 하는 작업
- 반복적인 `GetAllActorsOfClass` 사용 여부
- 잦은 Cast 및 객체 탐색
- Projectile Pool의 초기 크기와 고갈 처리
- Widget Binding과 매 프레임 호출 비용
- 로그가 Shipping 또는 장시간 실행에 미치는 영향
- Enemy 다수 생성 시 병목 가능성

### 7.4 코드 가독성과 유지보수

- Unreal 명명 규칙 준수
- Header와 CPP 책임 분리
- 함수 길이와 중첩 조건문
- 중복 코드
- Magic Number 및 하드코딩
- 접근 지정자와 캡슐화
- Blueprint 노출 범위의 적절성
- 주석과 실제 동작의 일치
- 사용하지 않는 변수, 함수 및 include
- 디버그 코드와 임시 코드 잔존 여부

### 7.5 빌드 안정성

- Clean Build 성공 여부
- 컴파일 Warning
- Blueprint Compile Warning 및 Error
- Redirector 및 누락 에셋
- 패키징 Warning 및 Error
- 에디터 재실행 후 참조 유지 여부

## 8. C++·Blueprint·데이터 연결 검증

각 기능에 대해 세 영역의 연결을 한 줄로 추적한다.

| 기능 | C++ 시작점 | Blueprint 연결 | 데이터 에셋 | 런타임 결과 |
|---|---|---|---|---|
| 플레이어 입력 |  |  | Input Action |  |
| 무기 발사 |  |  | Weapon DataAsset |  |
| Projectile |  |  | Projectile DataTable |  |
| Enemy |  |  | Character DataAsset |  |
| GAS Damage |  | GameplayEffect | GameplayTag |  |
| Wave |  |  | Wave DataTable |  |
| HUD |  | Widget Blueprint |  |  |

확인 항목:

- C++ 기본값과 Blueprint 재정의 값 중 무엇이 최종 적용되는가?
- 필수 Blueprint Class가 비어 있을 때 안전하게 실패하는가?
- DataAsset 및 DataTable Row 이름이 코드에 하드코딩되어 있는가?
- 에셋 이름 변경 시 코드가 깨질 가능성이 있는가?
- Blueprint에서만 존재해 코드 검토로 찾기 어려운 핵심 로직이 있는가?

## 9. 기능별 검증표

다음 상태값만 사용한다.

- `완료`: 제출본에서 정상 동작을 재현함
- `부분 완료`: 제한 조건 또는 알려진 문제가 있음
- `미구현`: 코드 또는 실제 동작이 없음
- `검증 불가`: 에셋, 환경 또는 재현 조건 부족

| 기능 | 보고서 상태 | 실제 상태 | 코드 근거 | 실행 검증 | 문제 및 한계 |
|---|---|---|---|---|---|
| 이동·카메라·조준 |  |  |  |  |  |
| 무기 발사 |  |  |  |  |  |
| Projectile Pool |  |  |  |  |  |
| Enemy 피격·사망 |  |  |  |  |  |
| GAS Damage |  |  |  |  |  |
| Headshot |  |  |  |  |  |
| XP·Level Up |  |  |  |  |  |
| Wave·Spawn |  |  |  |  |  |
| Enemy AI |  |  |  |  |  |
| 엄폐 |  |  |  |  |  |
| HUD |  |  |  |  |  |
| 패키징 |  |  |  |  |  |

## 10. 문제 발견 시 기록 형식

```text
문제명:
관련 기능:
발생 환경:
재현 절차:
예상 결과:
실제 결과:
로그 또는 코드 위치:
원인 분석:
영향 범위:
임시 대응:
권장 수정안:
수정 예상 범위:
```

수정하지 않은 문제도 정확히 기록한다. 검증 대응에서는 문제의 존재보다 문제를 인식하지 못하거나 설명하지 못하는 것이 더 큰 위험이 될 수 있다.

## 11. 일정 및 범위 변경 분석

기존 계획과 실제 진행 내용을 비교한다.

| 원래 계획 | 실제 진행 | 변경 이유 | 일정 영향 | 사전 공유 여부 | 결과 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

각 변경에 대해 다음을 설명할 수 있어야 한다.

- 왜 변경이 필요하다고 판단했는가?
- 원래 항목을 미루면서 발생한 영향은 무엇인가?
- 당시 상관에게 공유하거나 승인받았는가?
- 동일한 상황이 발생하면 다음에는 어떻게 처리할 것인가?

권장 답변:

> 구현 과정에서 기술적 필요를 우선해 일정과 순서를 변경했지만, 변경 전에 사유와 영향을 공유하고 승인받아야 한다는 점을 놓쳤습니다. 다음부터는 변경 사유, 영향 범위, 예상 기간을 먼저 보고하고 확인받은 후 진행하겠습니다.

## 12. 예상 코드 리뷰 질문

### 구조 관련

- 이 프로젝트의 전체 실행 흐름을 설명해 보세요.
- Character와 PlayerController의 책임은 어떻게 구분했나요?
- GameMode가 담당하는 기능은 무엇인가요?
- C++과 Blueprint를 어떤 기준으로 분리했나요?
- DataAsset과 DataTable을 각각 어디에 사용했나요?

### 전투 관련

- 발사 입력부터 Enemy HP 감소까지 설명해 보세요.
- Projectile을 Destroy하지 않고 Pooling한 이유는 무엇인가요?
- Pool이 고갈되면 어떻게 처리되나요?
- 한 Projectile이 여러 번 데미지를 주지 않도록 어떻게 막았나요?
- Headshot은 어떤 정보를 기준으로 판정하나요?

### GAS 관련

- AbilitySystemComponent는 언제 초기화되나요?
- GameplayEffect는 어떻게 생성하고 적용하나요?
- SetByCaller를 사용한 이유는 무엇인가요?
- GameplayTag는 실제로 어디에 사용되나요?
- 기존 Damage Interface와 GAS가 중복 적용되지 않나요?

### 안정성·성능 관련

- Tick에서 수행하는 작업은 무엇인가요?
- UObject 참조가 Garbage Collection에 의해 사라지지 않나요?
- Delegate와 Timer는 언제 해제하나요?
- Enemy 수가 증가하면 어떤 부분이 병목이 되나요?
- 패키징 환경에서도 확인했나요?

### 작업 방식 관련

- 일정과 구현 순서를 변경한 이유는 무엇인가요?
- 변경 전에 보고하지 않은 이유는 무엇인가요?
- AI 또는 참고 자료를 사용한 부분을 어떻게 검증했나요?
- 본인이 직접 설계하고 해결한 핵심 문제는 무엇인가요?
- 현재 프로젝트에서 가장 위험한 부분은 무엇인가요?

## 13. 발표자가 공부할 핵심 개념

우선순위 순으로 학습한다.

### 필수

1. Unreal Gameplay Framework
   - GameMode, GameState, PlayerController, Character
2. UObject와 Actor 수명
   - UPROPERTY, Garbage Collection, BeginPlay, EndPlay
3. Enhanced Input
   - Input Action, Mapping Context, Binding
4. Actor Component와 Subsystem
5. Collision 및 HitResult
6. Interface 기반 호출
7. Delegate와 Timer
8. DataAsset과 DataTable
9. Object Pool 패턴
10. GAS 기본 구조
    - ASC, AttributeSet, GameplayAbility, GameplayEffect, GameplayTag

### 추가

1. Animation Blueprint와 Montage
2. Widget 수명 및 이벤트 기반 UI 갱신
3. AIController와 상태 기반 AI
4. Unreal Profiling 기초
5. 패키징과 에셋 참조

각 개념은 정의만 외우지 말고 Project_Z에서 사용된 실제 클래스와 함수에 연결해 설명할 수 있어야 한다.

## 14. 검증 실행 순서

### 환경 검증

1. 제출 버전 확인
2. Unreal Engine 버전 확인
3. 프로젝트 파일 생성 또는 IDE 연동 확인
4. C++ Clean Build
5. Editor 실행
6. Blueprint Compile Error 확인
7. 기본 맵 확인

### 기능 검증

1. 이동과 조준
2. 기본 공격
3. Projectile Pool 재사용
4. Enemy 피격과 사망
5. 일반 피격과 Headshot 비교
6. Aura 피해
7. XP 획득과 Level Up
8. 강화 선택 적용
9. Wave 진행
10. HUD 갱신
11. Stage Clear 및 Game Over

### 안정성 검증

1. 연속 발사
2. 적 다수 생성
3. 빠른 사망 반복
4. 레벨업 반복
5. 맵 재시작
6. Editor 재실행
7. 장시간 실행
8. Development 패키징

## 15. 다른 에이전트 전달용 작업 지시문

아래 내용을 그대로 복사해 분석 담당 에이전트에게 전달할 수 있다.

```text
Project_Z 제출본의 검증 대비 분석을 진행해 주세요.

목적은 새 기능 구현이나 리팩터링이 아니라, 현재 제출본의 구조와 실제 동작을 확인하고 코드 리뷰와 질의응답에 대비하는 것입니다. 제출본은 임의로 수정하지 마세요.

다음 항목을 실제 C++ 코드, Blueprint, Config, DataAsset 및 DataTable을 근거로 조사해 주세요.

1. 프로젝트 전체 구조와 핵심 클래스 책임
2. 객체 생성·소유·참조 관계
3. 입력부터 이동·공격까지의 호출 흐름
4. Weapon 발사와 Projectile Object Pool 흐름
5. 충돌, Headshot, GAS Damage 및 기존 Damage Interface 흐름
6. Enemy AI, 사망, XP, Level Up 및 보상 흐름
7. Wave, 게임 상태 및 HUD 갱신 흐름
8. UObject 참조, Timer, Delegate 및 객체 수명 안정성
9. Tick, 반복 탐색, Cast, Pooling 및 UI의 성능 위험
10. C++·Blueprint·DataAsset·DataTable 연결 상태
11. 보고서의 완료 항목과 실제 구현 상태 비교
12. 빌드, 실행 및 패키징 검증 결과
13. 알려진 문제, 미완성 기능 및 기술 부채
14. 예상 코드 리뷰 질문과 근거 있는 답변

모든 판단에는 파일명, 클래스명, 함수명 또는 에셋 경로를 근거로 표시하세요. 확인하지 못한 내용은 추측하지 말고 `검증 불가`로 기록하세요. 문제가 발견되어도 코드를 수정하지 말고 재현 절차, 영향 범위 및 권장 수정안을 문서화하세요.

최종 결과는 다음 순서로 작성해 주세요.

- 한 페이지 요약
- 프로젝트 구조도
- 핵심 로직 흐름도
- 클래스 책임표
- 기능별 검증표
- 문제 및 위험 목록
- 예상 질문과 답변
- 발표자가 우선 공부할 코드 목록
```

## 16. 준비 완료 기준

다음 조건을 만족하면 검증 준비가 완료된 것으로 판단한다.

- 제출 버전과 실행 환경을 정확히 말할 수 있다.
- 프로젝트를 처음부터 빌드하고 실행할 수 있다.
- 주요 기능의 시작점과 호출 흐름을 코드 위치와 함께 설명할 수 있다.
- 보고서와 실제 구현의 차이를 알고 있다.
- 완료, 부분 완료, 미구현 기능을 구분할 수 있다.
- 핵심 설계 결정의 이유와 장단점을 설명할 수 있다.
- 알려진 문제의 재현 조건과 영향 범위를 설명할 수 있다.
- 일정 변경 문제를 인정하고 재발 방지 방법을 제시할 수 있다.
- 모르는 질문에 추측하지 않고 확인 방법을 답할 수 있다.
