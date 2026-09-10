# Project_Z 과제 검증 모의 인터뷰 가이드

## 1. 사용 목적

이 문서는 다른 AI 에이전트 또는 검증 담당자가 `Project_Z` 직무과제 검증 회의를 진행할 수 있도록 만든 질문·정답·평가 가이드다.

검증의 핵심 목적은 다음 세 가지다.

1. 제출자가 프로젝트를 실제로 구현하고 연결했는지 확인한다.
2. 완료보고서의 주장과 실제 코드가 일치하는지 확인한다.
3. 사용한 기술의 적용 범위, 한계와 개선 방향을 이해하는지 확인한다.

검증 대상:

- 완료보고서: `Plans/박종호B_직무과제_완료보고서_정리.md`
- Unreal 프로젝트: `Project/Project_Z/Project_Z.uproject`
- 주요 C++ 코드: `Project/Project_Z/Source/Project_Z`

---

## 1-1. 검증 회의 상황 설정

다른 에이전트는 다음 상황을 전제로 면접관 역할을 수행한다.

- 제출자는 `Project_Z` Unreal 프로젝트와 직무과제 완료보고서를 이미 상관 또는 검증 담당자에게 전달했다.
- 과제 제출과 결과 보고는 완료되었고, 남은 절차는 결과물 검증 회의다.
- 검증 담당자는 제출자가 프로젝트를 실제로 구현했는지, 단순히 다른 사람이나 AI가 만든 결과를 전달한 것인지 확인하려고 한다.
- 검증 담당자는 제출자의 암기력보다 실제 구현 당시의 판단, 코드 연결 관계, 디버깅 경험과 한계 인식을 확인한다.
- 제출자는 Unreal 및 GAS 전문가라고 주장하는 상황이 아니다. 완료보고서에서도 GAS는 숙련보다 기본 적용 수준이라고 기술했다.
- 검증은 공격하거나 함정에 빠뜨리는 자리가 아니라, 보고서의 신뢰성과 제출자의 실제 업무 수행 범위를 판정하는 자리다.
- 다만 답변자의 기분을 보호하기 위해 기술적 오류를 완곡하게 통과시키지 않는다. 사실과 코드가 다르면 명확히 지적한다.

### 면접관 역할

면접관은 `Project_Z`를 전달받은 직속 상관 또는 기술 검증 책임자다. 다음과 같은 관점을 유지한다.

> “나는 제출자가 모든 Unreal 기술을 완벽하게 아는지 시험하려는 것이 아니다. 이 결과물을 실제로 만들고 문제를 해결한 사람이라면 알고 있어야 할 코드 흐름, 선택 이유, 시행착오와 한계를 확인하려 한다. 모르는 세부 API가 있는 것은 허용하지만, 본인이 핵심 성과로 보고한 기능의 실제 실행 경로를 전혀 설명하지 못하거나 코드와 다른 주장을 반복하면 구현 소유권을 의심한다.”

### 기본 검증 태도

- 처음에는 넓은 질문을 하고, 응답자가 선택한 핵심 기능을 따라 깊게 들어간다.
- 응답자가 언급하지 않은 생소한 기능으로 갑자기 공격하기보다, 본인이 구현했다고 주장한 기능을 중심으로 검증한다.
- 함수명을 완벽히 외우지 못한 것과 실행 원리를 모르는 것을 구분한다.
- 정확한 함수명을 기억하지 못해도 객체의 책임과 데이터 흐름이 맞으면 부분 점수를 준다.
- 함수명은 많이 말하지만 상태가 어디에 저장되고 언제 바뀌는지 설명하지 못하면 암기 가능성을 의심한다.
- 결함을 솔직히 인정하고 원인·영향·수정·검증을 설명하면 긍정적으로 평가한다.
- 발견된 결함을 “확장성을 위한 설계”라고 방어하거나 실제 코드와 다른 설명을 하면 강하게 감점한다.

---

## 1-2. 질문자의 핵심 의도

모든 질문은 아래 검증 목적 중 하나 이상을 가진다.

### 의도 A: 실제 구현 소유 여부 확인

확인하려는 것:

- 입력부터 결과까지 실제 호출 순서를 설명할 수 있는가?
- 클래스 이름뿐 아니라 핵심 함수와 변수를 알고 있는가?
- 정상 경로뿐 아니라 실패했을 때 어떤 값이 남는지 알고 있는가?
- 구현 과정에서 부딪혔을 법한 문제를 구체적으로 설명하는가?

소유 가능성이 높은 답변 신호:

- “처음에는 A로 처리했는데 B 문제가 생겨 C로 변경했다”는 구체적인 이력
- `Owner`, `InputID`, `AliveEnemyCount`, `RuntimeHitActors`처럼 실제 상태를 언급
- 모르는 부분과 직접 구현한 범위를 구분
- 예상 밖 동작을 재현한 절차나 로그 위치를 설명

소유 가능성이 낮아 보이는 답변 신호:

- “확장성을 높였다”, “최적화했다”, “연동했다”만 반복
- 함수 이름은 나열하지만 호출 주체와 순서를 설명하지 못함
- 코드와 다른 내용도 끝까지 구현됐다고 주장
- 실패 조건이나 디버깅 경험을 전혀 말하지 못함

### 의도 B: 완료보고서의 신뢰성 확인

확인하려는 것:

- 보고서에 적힌 달성 내용이 실제 코드 범위와 일치하는가?
- 데이터 구조가 존재하는 것과 실제 동작하는 것을 구분하는가?
- “GAS 기반”, “Wave 설정”, “Boss 조건”, “성능 개선” 같은 표현을 과장하지 않는가?

면접관은 보고서의 표현을 그대로 정답으로 취급하지 않는다. 실제 코드와 다르면 제출자가 정확히 정정할 수 있는지 확인한다.

### 의도 C: 기술 선택의 판단 근거 확인

확인하려는 것:

- 왜 DataAsset, DataTable, Subsystem, Interface 또는 GAS를 사용했는가?
- 다른 선택과 비교했는가?
- 얻는 효과뿐 아니라 복잡성 비용도 알고 있는가?
- 현재 프로젝트 규모에 필요한 설계였는지 설명할 수 있는가?

좋은 답변 구조:

```text
문제
→ 선택
→ 실제 적용 위치
→ 얻은 효과
→ 비용과 한계
→ 검증 방법
```

### 의도 D: 상태 소유권과 정합성 이해 확인

확인하려는 것:

- HP, 탄약, 경험치, Stage 상태의 실제 소유자가 누구인가?
- 하나의 상태가 두 곳에 중복 저장되는지 알고 있는가?
- 중복 사망, 중복 반환, Spawn 실패 같은 상황에서 불변조건이 유지되는가?

이 영역은 함수 암기보다 중요하다. 시니어 여부와 관계없이 실제 게임 로직을 안전하게 관리할 수 있는지 판단하는 핵심이다.

### 의도 E: Unreal Framework 이해 확인

확인하려는 것:

- Character, PlayerController, GameMode와 Widget의 책임을 구분하는가?
- World와 GameInstance의 수명 차이를 이해하는가?
- GameMode가 서버에만 존재한다는 것을 아는가?
- UObject 참조와 GC, Asset Reference의 기본 차이를 설명할 수 있는가?

### 의도 F: 도구 사용과 개념 이해 구분

확인하려는 것:

- GAS나 Pool 코드를 사용했다는 사실과 내부 원리 이해를 구분하는가?
- 튜토리얼, 기존 코드 또는 AI의 도움을 받았더라도 최종 코드를 검토하고 책임질 수 있는가?
- 모르는 코드를 그대로 제출했는가, 아니면 필요한 범위를 학습해 수정했는가?

외부 도움을 받은 것 자체를 실패로 판단하지 않는다. 다만 핵심 성과로 보고한 코드의 위험과 수정 방법을 설명하지 못하면 업무 결과를 독립적으로 유지보수하기 어렵다고 평가한다.

### 의도 G: 문제 해결과 성장 가능성 확인

확인하려는 것:

- 결함을 지적받았을 때 방어하는가, 분석하는가?
- 우선순위를 게임 영향 기준으로 정하는가?
- 수정 방법뿐 아니라 재현과 검증 방법을 제안하는가?
- 현재 수준을 정확히 인식하고 다음 학습 범위를 정할 수 있는가?

모르는 질문에 대한 좋은 대응:

> “그 부분은 사용했지만 내부 원리까지 충분히 이해하지 못했습니다. 현재 코드에서 확인되는 적용 범위는 여기까지이며, 이 상태로는 유지보수 위험이 있습니다. 코드 흐름을 다시 확인하고 이 조건으로 테스트하겠습니다.”

모르는 질문에 대한 나쁜 대응:

> “확장성을 위해 그렇게 했습니다.”

---

## 1-3. 질문 영역별 숨은 검증 목적

| 질문 영역 | 겉으로 묻는 내용 | 실제로 확인하는 것 |
|---|---|---|
| 전체 구조 | 클래스와 기능 설명 | 프로젝트를 본인이 구조화해 기억하는가 |
| C++/Blueprint | 역할 분담 | 구현과 콘텐츠 연결의 실제 경계를 아는가 |
| 입력/Ability | 클릭 후 호출 흐름 | 실제 디버깅 가능한 수준으로 호출 관계를 아는가 |
| Weapon Data | 사용 변수 | 데이터가 존재하는 것과 실제 읽히는 것을 구분하는가 |
| Projectile | 충돌과 관통 | 정상 경로와 상태 초기화를 이해하는가 |
| Object Pool | 재사용 구조 | 자료구조 불변조건과 객체 수명을 이해하는가 |
| GAS | SetByCaller와 Attribute | API를 연결한 것인지 원리를 이해한 것인지 |
| Headshot | 판정 방식 | 보고서 설명과 실제 코드를 구분하는가 |
| Enemy HP | 이중 상태 | 핵심 데이터의 단일 원천을 이해하는가 |
| Enemy AI | 추적과 상태 | Tick 기반 상태 전이와 한계를 아는가 |
| GameMode | Stage 흐름 | 전역 규칙의 책임과 카운트 정합성을 이해하는가 |
| Wave Data | 필드 의미 | 선언된 데이터가 실제 적용되는지 확인했는가 |
| UI | 갱신과 입력 모드 | 표현과 게임 상태의 책임을 구분하는가 |
| AnimationNotify | 재장전 타이밍 | 비동기 애니메이션과 코드 상태 동기화를 이해하는가 |
| 성능 | Pool 효과 | 측정과 추측을 구분하는가 |
| 코드 결함 | 잘못 설계한 부분 | 책임감, 자기검토와 개선 우선순위 |
| 압박 질문 | 설계 가치 | 외운 장점이 아니라 트레이드오프를 판단하는가 |

---

## 1-4. 구현 소유권 판단 원칙

면접관은 한두 개의 오답만으로 대리 구현을 단정하지 않는다. 다음 네 단계의 일관성을 종합한다.

### 1단계: 표면적 인식

- 클래스와 기능 이름을 말할 수 있다.
- 보고서 내용을 요약할 수 있다.

이 단계만 통과하면 문서를 읽은 사람도 답할 수 있으므로 소유권 증거가 약하다.

### 2단계: 실행 흐름

- 호출 주체와 대상 함수를 순서대로 설명한다.
- 어떤 DataAsset 값이 어느 객체에 주입되는지 안다.

실제 구현 가능성이 올라간다.

### 3단계: 상태와 실패 조건

- 어떤 객체가 상태를 소유하는지 설명한다.
- Spawn 실패, 중복 반환, Timer 잔존, 이중 HP 같은 조건을 분석한다.

코드를 실제로 유지보수할 가능성이 높은 신호다.

### 4단계: 수정과 검증

- 최소 수정과 장기 개선을 구분한다.
- 재현 절차, 테스트와 프로파일링 방법을 제시한다.

결과물을 책임질 수 있는 수준의 강한 증거다.

### 판단 예시

- Q3 호출 흐름을 정확히 답하고 Q12 GAS 개념을 모름: 직접 구현 가능성은 유지하되 GAS 이해 부족으로 평가
- 모든 클래스 이름은 말하지만 어떤 함수도 이어서 설명하지 못함: 소유권 추가 검증 필요
- 결함을 처음에는 몰라도 설명 후 유사 문제를 정확히 추론함: 학습과 문제 해결 능력 긍정
- 정답을 설명한 직후에도 같은 개념을 반복해서 틀림: 내부 원리 이해 및 유지보수 역량 낮음

---

## 1-5. 이 모의 인터뷰에서 유지할 대화 방식

면접관은 차갑되 모욕적이지 않게 진행한다.

- “틀렸습니다”라고 말할 수 있지만 왜 틀렸는지 코드 상태로 설명한다.
- 답변 점수를 제시하되 사람의 능력 전체를 점수 하나로 단정하지 않는다.
- 제출자의 답변을 대신 완성하기 전에 한 번은 스스로 보충할 기회를 준다.
- 모른다고 하면 정답을 설명하고 같은 개념의 짧은 확인 질문을 한다.
- 질문마다 긴 강의를 하지 않는다. 학습 모드가 필요한 경우에만 상세히 설명한 뒤 다시 검증 모드로 돌아온다.
- 최종 평가에서는 지식 부족, 코드 결함, 구현 소유 의심을 서로 구분한다.

최종 평가는 다음 세 축을 따로 기록한다.

```text
1. 실제 구현 신뢰도
2. 현재 기술 이해도
3. 결과물을 수정·유지할 가능성
```

---

## 2. 면접 진행 에이전트용 지침

아래 지침을 그대로 사용해 인터뷰를 진행한다.

### 새 에이전트에게 전달할 시작 프롬프트

```text
너는 Project_Z 직무과제 결과물을 전달받은 직속 상관이자 기술 검증 책임자다.

현재 과제 제출과 완료보고는 끝났고 검증 회의만 남아 있다. 목적은 응답자가 Project_Z를 실제로 구현했는지, 보고서의 내용을 이해하고 책임질 수 있는지 확인하는 것이다. 모든 Unreal 기술을 완벽하게 아는지를 시험하는 자리가 아니라 실제 구현 범위, 호출 흐름, 기술 선택, 실패 조건, 디버깅 경험과 한계 인식을 확인하는 자리다.

먼저 다음 파일을 읽어라.

1. _workspace/Project_Z/docs/Project_Z_Verification_Mock_Interview.md
2. Plans/박종호B_직무과제_완료보고서_정리.md
3. 필요한 경우 Project/Project_Z/Source/Project_Z의 실제 C++ 코드

모의 인터뷰 가이드의 상황 설정, 질문 의도, 채점 기준과 추천 질문 순서를 따라 진행하라. 한 번에 질문 하나만 하고 정답을 먼저 보여주지 마라. 내가 답하면 정확한 내용, 누락, 오답, 10점 점수와 직접 구현 신뢰도를 평가한 뒤 답변에 맞는 꼬리 질문 하나를 하라.

함수명 암기보다 상태 소유자와 실행 흐름을 중요하게 평가하라. “확장성”, “최적화”, “연동” 같은 추상 표현에는 실제 클래스, 변수와 효과를 다시 질문하라. 모르는 답변은 정직성을 인정하되 핵심 보고 기능이라면 이해 부족을 감점하라. 코드 결함 인정과 수정·검증 제안은 긍정적으로 평가하라.

최종적으로 실제 구현 신뢰도, 기술 이해도, 유지보수 가능성을 분리해 100점 기준으로 평가하라.
```

### 기본 진행 방식

1. 한 번에 질문 하나만 한다.
2. 먼저 정답이나 힌트를 제공하지 않는다.
3. 응답자가 답하면 정확한 부분, 누락된 부분, 잘못된 부분을 구분해 평가한다.
4. 답변이 불완전하면 바로 다음 주제로 넘어가지 말고 해당 호출 흐름을 한 단계 더 질문한다.
5. 클래스 이름만 나열하는 답변보다 상태 소유자와 호출 순서를 높게 평가한다.
6. “확장성”, “최적화”, “GAS 기반” 같은 표현에는 반드시 구체적인 근거를 요구한다.
7. 모른다고 답하면 감점하되, 실제 구현 범위와 정답을 설명한 후 유사한 확인 질문을 한 번 더 한다.
8. 모든 질문을 반드시 소진할 필요는 없다. 답변에 따라 꼬리 질문을 선택한다.

### 답변 평가 형식

각 답변 뒤에 다음 형식으로 평가한다.

```text
[평가]
- 정확한 내용:
- 누락된 내용:
- 잘못된 내용:
- 점수: 10점 만점
- 직접 구현 신뢰도: 높음 / 보통 / 낮음

[다음 질문]
질문 한 개
```

### 검증 시 주의사항

- 암기한 정답과 실제 이해를 구분하기 위해 변수 하나를 바꿨을 때의 결과를 묻는다.
- 완료보고서의 표현이 코드보다 과장된 경우 제출자가 이를 인정하고 정확히 수정하는지 확인한다.
- 코드 결함을 발견하지 못했다고 구현하지 않은 것으로 단정하지 않는다. 대신 원인과 수정 방법을 이해하는지 추가 검증한다.
- 성능은 측정 자료 없이 개선됐다고 단정하지 못하게 한다.
- Blueprint 내부 그래프는 C++ 정적 분석만으로 단정하지 않는다.

---

## 3. 전체 채점 기준

| 평가 영역 | 배점 | 확인 내용 |
|---|---:|---|
| 프로젝트 소유 이해 | 20 | 본인이 구현한 범위, 클래스 책임, C++/Blueprint 경계 |
| 호출 흐름 이해 | 20 | 입력부터 공격, 피해, 사망, 스테이지 진행까지 |
| Unreal Framework 이해 | 15 | Character, Controller, GameMode, Subsystem 수명과 책임 |
| GAS 이해 | 15 | ASC, AbilitySpec, EffectSpec, SetByCaller, AttributeSet |
| 데이터 설계 | 10 | DataAsset/DataTable 선택, 원본과 런타임 상태 분리 |
| 안정성 및 디버깅 | 10 | 이중 HP, Spawn Count, Pool 상태 등 실패 조건 |
| 검증 및 성능 | 10 | 테스트, 프로파일링, 근거와 추측 구분 |

### 종합 판단

| 총점 | 판단 |
|---:|---|
| 85~100 | 구현 소유와 기술 판단이 명확함 |
| 70~84 | 실제 구현 신뢰도 높음, 일부 기술 이해 보완 필요 |
| 55~69 | 기능 연결 경험은 있으나 내부 원리와 실패 대응이 약함 |
| 40~54 | 일부 구현 또는 조립 경험은 확인되나 프로젝트 전체 소유는 불명확 |
| 0~39 | 보고서 내용을 실제 코드 수준으로 설명하지 못함 |

GAS나 풀링 한 영역을 모른다는 이유만으로 전체 구현을 부정하지 않는다. 여러 영역에서 실제 함수, 변수와 실패 조건을 일관되게 설명하는지가 더 중요하다.

---

# A. 프로젝트와 아키텍처

## Q1. Project_Z에서 본인이 구현한 핵심 기능과 전체 구조를 설명해 주세요.

### 모범 답안

`Project_Z`는 TPS 이동, 카메라 조준, 총기 발사와 재장전, 엄폐, 적 AI, 스테이지 진행, HUD, 데이터 기반 설정과 일부 GAS 피해를 구현한 샘플 프로젝트다.

역할은 대략 다음과 같이 나뉜다.

- `AZCharacterBase`: 이동, 조준, 장비, 발사, 재장전, 엄폐와 플레이어 상태
- `AProject_Z_PlayerController`: 입력 모드, HUD와 게임 흐름 UI
- `AProject_Z_GameMode`: 적 생성, 생존 수, Stage Clear와 Game Over
- `AZEnemyBase`: 추적, 공격, 피격, 상태이상, 사망과 보상
- `UZWeaponDataAsset`: 총기별 수치와 Projectile 설정
- `AZProjectileBase`: 이동, 충돌, 관통, Headshot과 피해
- `UZActorPoolSubsystem`: Projectile 재사용
- `UZAttributeSet`: GAS Attribute와 Damage 처리

C++이 실행 규칙과 반복 로직을 담당하고 Blueprint가 Mesh, Animation, Montage, Widget과 데이터 에셋을 연결한다.

### 필수 키워드

- 구체적인 클래스 3개 이상
- 각 클래스의 책임
- C++과 Blueprint의 역할 경계
- 본인이 구현한 범위와 미구현 범위

### 감점 기준

- 기능 목록만 나열하고 클래스 책임을 말하지 못함
- 무기 파츠 등 미구현 기능을 구현했다고 주장함
- “확장성을 위해 분리했다”만 반복하고 무엇이 분리됐는지 설명하지 못함

### 꼬리 질문

> `AZCharacterBase`에 남아 있는 책임 중 가장 먼저 분리할 것은 무엇이며 그 이유는 무엇입니까?

### 꼬리 질문 정답

전투 안정성과 변경 빈도를 고려하면 장비·탄약·공격을 `CombatComponent`로, 경험치·레벨업을 `ProgressionComponent`로 단계적으로 분리할 수 있다. 다만 현재는 구조 분리 전에 Enemy HP 정합성과 Spawn Count 같은 실제 기능 결함을 먼저 수정하는 것이 우선이다.

---

## Q2. C++과 Blueprint의 역할을 어떤 기준으로 나눴습니까?

### 모범 답안

C++에는 여러 에셋이 공유하는 실행 규칙, 상태 검증, 피해 처리, 스테이지 판정과 풀링을 둔다. Blueprint에는 Mesh, Animation Blueprint, Montage, Widget, DataAsset 등 콘텐츠 연결과 시각 표현을 둔다.

기준은 단순히 “중요하면 C++”이 아니라 다음과 같다.

- 반복 사용되고 오류 시 게임 규칙에 영향을 주는 로직: C++
- 디자이너가 교체하거나 조정할 콘텐츠와 표현: Blueprint/Asset
- 복잡한 Blueprint 그래프보다 재사용·검증이 중요한 로직: C++

### 감점 기준

- Blueprint는 느리고 C++은 빠르기 때문이라고만 답함
- Animation State 전체가 C++인지 Blueprint인지 구분하지 못함

---

# B. 입력과 발사 호출 흐름

## Q3. 마우스 왼쪽 클릭부터 Primary Ability가 실행될 때까지 설명해 주세요.

### 모범 답안

1. `AZCharacterBase::SetupPlayerInputComponent()`에서 `IA_Ability_Primary`를 바인딩한다.
2. `ETriggerEvent::Started`에 `OnAbilityInputPressed()`를 연결하며 `EProject_Z_AbilityInputID::Primary`를 전달한다.
3. `OnAbilityInputPressed()`가 ASC의 `GetActivatableAbilities()`를 순회한다.
4. `AbilitySpec.InputID`가 Primary ID와 같은 Spec을 찾는다.
5. `AbilitySystemComponent->TryActivateAbility(AbilitySpec.Handle)`을 호출한다.
6. 등록된 `UZGA_PrimaryAttack::ActivateAbility()`가 실행된다.
7. `ActorInfo->AvatarActor`를 `AZCharacterBase`로 Cast한다.
8. `ActivatePrimaryWeapon()`을 호출한다.

### 필수 키워드

- InputAction 에셋
- `Started`
- `AbilitySpec.InputID`
- `TryActivateAbility`
- AvatarActor

### 감점 기준

- `IA_Ability_Primary`를 함수 또는 Blueprint라고 설명함
- Enhanced Input이 GameplayAbility를 직접 호출한다고 설명함
- ASC와 AbilitySpec을 설명하지 못함

### 꼬리 질문

> Ability는 언제 ASC에 등록됩니까?

### 꼬리 질문 정답

Character의 `InitAbilityActorInfo()`에서 Owner/Avatar 정보를 초기화하고, 기본 Ability 및 Character DataAsset의 시작 Ability를 `FGameplayAbilitySpec`으로 만들어 `GiveAbility()`로 등록한다. 멀티플레이에서는 Ability 부여가 Authority에서 수행돼야 한다.

---

## Q4. `FirePrimaryProjectile()`이 투사체를 발사하기까지 어떤 데이터를 사용합니까?

### 모범 답안

`GetActiveWeaponData()`로 현재 `UZWeaponDataAsset`을 가져온 뒤 다음 값을 사용한다.

- `ProjectileClass`, `ProjectileRowName`
- `Range`, `ProjectileSpeed`
- `BaseDamage`, `ProjectileDamageMultiplier`
- `FirePattern`, `ProjectileCount`, `SpreadAngleDegrees`
- `PierceCount`, `PierceDamageRetention`
- 무기 속성

총구 위치와 Aim Point로 기본 방향을 계산한다. Shotgun 또는 Spread 패턴은 여러 방향을 만든다. `UZActorPoolSubsystem::AcquireProjectile()`로 Projectile을 얻은 뒤 Owner, 최종 피해, 관통, 속성, 속도와 반환 거리를 설정한다. 한 번의 발사에 Projectile이 여러 개 생성돼도 탄약은 발사 성공 후 1만 감소한다.

### 꼬리 질문

> Pool에서 Projectile 획득이 모두 실패하면 탄약은 감소합니까?

### 꼬리 질문 정답

`FiredProjectileCount <= 0`이면 `false`를 반환하므로 탄약은 감소하지 않는다. 일부만 성공하면 성공한 Projectile은 발사되고 탄약은 1 감소한다.

---

# C. Projectile과 Object Pool

## Q5. Actor Pool을 사용한 이유와 `UWorldSubsystem`을 선택한 이유는 무엇입니까?

### 모범 답안

Projectile의 반복적인 Spawn/Destroy와 GC 부담을 줄이기 위해 Actor를 비활성화한 뒤 재사용한다. 풀링 대상이 현재 World에 소속된 Actor이므로 풀의 수명을 World와 일치시키기 위해 `UWorldSubsystem`을 사용했다.

`UGameInstanceSubsystem`은 맵 전환 후에도 유지되므로 이전 World에서 생성되어 파괴된 Actor 참조가 다음 World까지 남거나 서로 다른 World의 Actor가 같은 풀에 섞일 수 있다.

성능 개선은 설계 목적일 뿐이며 Unreal Insights 비교 측정 전에는 실제 개선 폭을 단정할 수 없다.

### 필수 키워드

- Spawn/Destroy와 GC
- World 수명
- 이전 World의 무효 Actor 참조
- 성능 측정 필요

---

## Q6. `AvailableActors`와 `InUseActors`를 설명해 주세요.

### 모범 답안

- `AvailableActors`: 숨김, 충돌과 Tick이 비활성화된 대기 Actor
- `InUseActors`: 현재 획득되어 월드에서 동작 중인 Actor

Actor는 정상적으로는 두 상태 중 정확히 하나에만 존재해야 한다.

```text
Available XOR InUse
```

`AcquireActor()`는 Available에서 제거해 InUse에 넣고, `ReleaseActor()`는 InUse에서 제거해 Available에 넣는다.

---

## Q7. 풀에서 Projectile을 재사용할 때 어떤 상태를 초기화해야 합니까?

### 모범 답안

- `RuntimeDamageOverride`
- `RuntimeRemainingPierceCount`
- `RuntimePierceDamageRetention`
- `RuntimeHitActors`
- `RuntimeElementType`, EffectScale, Color
- Projectile Movement 속도
- Life Timer와 Return Distance Timer
- Owner
- 충돌, Tick, 가시성

PoolSubsystem은 공통 Actor 상태를 처리하고, Projectile 고유 상태는 `IZPoolableActorInterface`의 획득/반환 이벤트에서 Projectile이 직접 초기화한다.

### 꼬리 질문

> `RuntimeHitActors`를 초기화하지 않으면 어떻게 됩니까?

### 꼬리 질문 정답

이전 발사에서 맞힌 Enemy가 목록에 남아, 재사용된 새로운 발사에서도 이미 맞은 대상으로 판단된다. 그 결과 해당 Enemy에게 피해가 적용되지 않는다. 피해량이 중복되는 문제가 아니라 과거 타격 대상이 새로운 발사에서 면역처럼 되는 문제다.

---

## Q8. 같은 Projectile에 `ReleaseActor()`가 두 번 호출되면 현재 코드에서 어떤 문제가 발생합니까?

### 모범 답안

현재 `ReleaseActor()`는 Actor가 실제 `InUseActors`에 있었는지 확인하지 않고 `AvailableActors.Add()`를 실행한다. 두 번 반환되면 동일 포인터가 Available 배열에 두 번 들어간다.

이후 두 번의 Acquire가 같은 Actor를 반환할 수 있어 두 번째 발사가 첫 번째 발사의 위치, 방향, Owner, 피해와 속성을 덮어쓸 수 있다.

개선 방법은 `InUseActors.RemoveSingleSwap()`의 반환값을 검사하고, 제거 수가 0이면 중복 반환으로 판단해 Available에 추가하지 않는 것이다.

### 감점 기준

- 중복 반환을 단순 상태 초기화 누락 문제로 설명함
- 같은 Actor 포인터가 두 번 저장된다는 핵심을 말하지 못함

---

## Q9. Projectile은 충돌 후 항상 바로 Pool로 반환됩니까?

### 모범 답안

아니다. Damageable Actor를 맞혔고 `RuntimeRemainingPierceCount > 0`이면 관통 수를 감소시키고 `RuntimeDamageOverride`에 `PierceDamageRetention`을 곱한 뒤 계속 이동한다.

남은 관통이 없거나 다른 충돌로 종료되면 `HandleProjectileLifeExpired()`가 PoolSubsystem의 `ReleaseActor()`를 호출한다. Life Timer 또는 Return Distance 초과도 반환 조건이다.

---

# D. GAS 피해와 Headshot

## Q10. Projectile 충돌부터 Enemy HP 감소까지 설명해 주세요.

### 모범 답안

1. `CollisionComponent`의 Overlap으로 `HandleProjectileOverlap()`이 호출된다.
2. Owner, 자기 자신, 같은 Owner의 Actor와 기존 `RuntimeHitActors` 대상을 제외한다.
3. 최종 기본 피해를 정하고 `ApplyGameplayDamage()`를 호출한다.
4. `IsHeadshotHit()`이 Bone 이름 또는 피격 높이 비율로 Headshot을 판정한다.
5. Headshot이면 `HeadshotDamageMultiplier`를 적용한다.
6. Source 또는 Target ASC로 `GE_Damage_Bullet`의 `GameplayEffectSpec`을 만든다.
7. `Data.Damage` Tag의 SetByCaller 값으로 최종 피해를 전달한다.
8. Bullet Damage Tag와 필요 시 Headshot Tag를 `DynamicGrantedTags`에 추가한다.
9. Target ASC에 GameplayEffect를 적용한다.
10. `UZAttributeSet::PostGameplayEffectExecute()`가 Damage를 읽어 HP에서 차감하고 Damage를 0으로 초기화한다.
11. Enemy가 AttributeSet HP를 `CurrentHP`로 동기화하고 사망 여부를 확인한다.

### 필수 키워드

- `HandleProjectileOverlap`
- `IsHeadshotHit`
- EffectSpec
- `Data.Damage`
- SetByCaller
- `PostGameplayEffectExecute`

---

## Q11. Bone 정보가 없으면 Headshot을 판정할 수 없습니까?

### 모범 답안

판정할 수 있다. 먼저 Bone 이름에 `head` 또는 `neck`이 있는지 검사한다. 일치하지 않으면 대상 Actor의 Component Bounds를 구하고, Bounds의 최저점 대비 피격 위치의 높이 비율이 `HeadshotHeightRatio` 이상인지 확인한다.

다만 Bounds 기반 판정은 큰 장비, 비정상적인 Collision Bounds, 자세 변화에 영향을 받을 수 있으므로 정확한 Hitbox나 Physical Material 방식보다 오탐 가능성이 있다.

---

## Q12. `Damage` Attribute와 `HP` Attribute의 차이는 무엇입니까?

### 모범 답안

- `HP`: 현재 체력을 지속해서 저장하는 상태 Attribute
- `Damage`: 한 번의 피해량을 전달하는 임시 Meta Attribute

GameplayEffect 적용 후 `PostGameplayEffectExecute()`가 Damage를 읽고 HP를 감소시킨 다음 Damage를 0으로 초기화한다. 이 구조를 사용하면 무적, 방어력, 실드, 저항과 같은 방어 규칙을 HP 변경 전에 한곳에서 처리할 수 있다.

---

## Q13. SetByCaller를 사용한 이유는 무엇입니까?

### 모범 답안

피해량이 GameplayEffect 에셋에 고정된 값이 아니라 발사할 때 계산되는 값이기 때문이다.

```text
(Weapon BaseDamage + Runtime Bonus)
× ProjectileDamageMultiplier
× HeadshotMultiplier
```

하나의 `GE_Damage_Bullet`을 재사용하면서 계산된 최종 피해를 `Data.Damage` GameplayTag를 키로 EffectSpec에 전달한다.

---

## Q14. HitResult와 Headshot Tag는 각각 어디에 저장됩니까?

### 모범 답안

- `FHitResult`: `EffectContext`에 `AddHitResult()`로 저장
- Headshot Tag: EffectSpec의 `DynamicGrantedTags`에 추가
- 최종 피해 수치: `Data.Damage` SetByCaller에 저장

완료보고서의 “Head Shot Tag를 Effect Context에 전달”이라는 표현은 실제 코드와 다르다. 정확히는 HitResult가 Effect Context에 들어가고 Headshot Tag는 DynamicGrantedTags에 추가된다.

### 감점 기준

- Effect Context, DynamicGrantedTags, SetByCaller를 동일한 저장소로 설명함

---

## Q15. GAS 적용 범위와 현재 한계를 설명해 주세요.

### 모범 답안

현재 ASC와 AttributeSet, Primary Ability 진입점, Projectile의 일부 GameplayEffect 피해, SetByCaller와 GameplayTag를 구현했다. 그러나 모든 피해가 GAS로 통합된 상태는 아니다.

- Projectile GAS 피해: `AttributeSet::HP`
- Interface 직접 피해와 일부 상태이상: `AZEnemyBase::CurrentHP`
- 공격 쿨다운과 탄약은 Ability Cost/Cooldown이 아니라 Character 로직
- 피격 VFX는 Gameplay Cue로 통합되지 않음
- 네트워크 복제와 예측이 완성되지 않음

따라서 “GAS를 숙련했다”보다 “GAS 기본 피해 파이프라인을 부분 적용했고 통합 과제를 이해한다”고 말하는 것이 정확하다.

---

# E. Enemy와 HP 정합성

## Q16. Enemy가 `CurrentHP`와 `AttributeSet::HP`를 동시에 가지는 이유와 문제를 설명해 주세요.

### 모범 답안

최종 의도라기보다 기존 직접 HP 시스템에 GAS를 나중에 추가하면서 생긴 과도기적 구조다. 직접 피해는 `CurrentHP`를 변경하고 GAS 피해는 AttributeSet HP를 변경한 후 `SyncHealthFromAttributeSet()`이 CurrentHP를 덮어쓴다.

예시:

```text
초기: CurrentHP 30 / AttributeSet.HP 30
근접 피해 20: CurrentHP 10 / AttributeSet.HP 30
GAS 피해 5: AttributeSet.HP 25
동기화: CurrentHP 25
```

이전 피해가 사라져 체력이 회복되는 것처럼 보일 수 있다. 해결 방법은 `AttributeSet::HP`를 유일한 체력 원천으로 두고 모든 피해와 사망 판정을 공통 경로로 통합하는 것이다.

### 감점 기준

- 두 HP가 항상 자동 동기화된다고 답함
- 이중 관리가 안정성을 높인다고 답함

---

## Q17. Enemy의 기본 AI 상태와 전환을 설명해 주세요.

### 모범 답안

Enemy는 Tick에서 Target을 갱신하고 거리에 따라 추적과 공격을 결정한다. 주요 값은 `TargetPlayer`, `ChaseRange`, `StopRange`, `AttackRange`, `AttackCooldown`이다.

상태는 다음 bool과 남은 시간 값으로 관리한다.

- `bIsChasingTarget`
- `bIsAttackingTarget`
- `bIsInHitReactState`
- `bIsRunnerDashing`
- `bIsDead`

피격이나 사망 중에는 추적과 공격을 중단한다. 현재 행동 수에서는 단순하지만 행동과 전이가 늘면 bool 조합이 모순될 수 있으므로 enum 상태 머신, StateTree 또는 Behavior Tree를 고려할 수 있다.

---

## Q18. Monster Type과 Rank를 하나의 Enemy 클래스에서 처리한 이유는 무엇입니까?

### 모범 답안

적 변형 대부분이 HP, 이동속도, 공격력, 크기, 색상, 애니메이션 속도와 대시 배율 같은 데이터 차이이기 때문이다. `FZMonsterVariantDefinition`을 적용해 Basic, Heavy, Runner 및 Normal, Elite, Boss를 표현한다.

공통 로직을 재사용하고 Blueprint 복제를 줄일 수 있지만, 타입별 행동이 크게 증가하면 Strategy, Component 또는 별도 클래스 분리가 필요하다.

---

# F. GameMode와 Stage

## Q19. Stage 시작부터 Clear까지의 호출 흐름을 설명해 주세요.

### 모범 답안

1. `BeginPlay()`에서 `LoadWaveDefinition()`과 `StartTPSStage()`를 호출한다.
2. `StageDefinitionAsset`에서 Wave DataTable을 가져와 `LoadedWaveDefinitions`에 복사한다.
3. `CurrentStateIndex`로 현재 Definition을 선택한다.
4. `SpawnEnemiesFromWaveDefinition()`이 Variant RowName을 순회한다.
5. Enemy를 생성하고 `ApplyMonsterVariant()`를 호출한다.
6. 생성 대상으로 처리한 적마다 `AliveEnemyCount`를 증가시킨다.
7. Enemy의 `Die()`가 GameMode의 `NotifyEnemyDead()`를 호출한다.
8. `AliveEnemyCount`를 감소시키고 0이면 `HandleStageClear()`를 실행한다.
9. `bStageClered`로 중복 Clear를 막고 `CurrentStateIndex`를 증가시킨 뒤 UI를 표시한다.

주의: 현재 Spawn 성공 여부와 카운트 증가가 정확히 결합되어 있지 않다.

---

## Q20. Enemy Spawn이 실패하면 현재 코드에서 어떤 문제가 발생합니까?

### 모범 답안

Spawn 람다는 실패하면 내부에서 반환하지만 성공 여부를 호출자에게 전달하지 않는다. 호출부는 이후 `AliveEnemyCount++`를 무조건 실행한다.

실제 Actor가 없는데 생존 수에는 포함되므로 해당 카운트를 감소시킬 사망 통지가 존재하지 않고 Stage가 종료되지 않을 수 있다.

수정 방법:

- Spawn 함수가 `AZEnemyBase*` 또는 `bool`을 반환
- 성공했을 때만 `AliveEnemyCount` 증가
- 모든 시도 후 생성 수가 0이면 오류 또는 빈 Stage 처리 정책 실행

---

## Q21. `FZWaveDefinition`에서 선언됐지만 현재 실행 코드에 반영되지 않는 값은 무엇입니까?

### 모범 답안

- `EnemyCount`
- `SpawnInterval`
- `SpawnDistance`
- `HPMultiplier`
- `MoveSpeedMultiplier`
- `ExperienceMultiplier`

현재는 `MonsterVariantRowNames`의 원소마다 Enemy 한 명을 즉시 생성하고, GameMode의 `SpawnRadiusMin/Max`를 사용한다. `ApplyWaveScaling()`도 호출되지 않는다.

따라서 완료보고서의 “Wave별 적 생성 수와 난이도 설정”은 데이터 구조는 존재하지만 모든 필드가 실제 적용되는 상태는 아니다.

---

## Q22. `UZStageDefinitionAsset`에서 현재 사용되지 않는 필드는 무엇이며 어떤 의미가 있습니까?

### 모범 답안

- `StageDuration`
- `StageHPMultiplier`
- `StageDamageMultiplier`
- `StageXPRewardMultiplier`

현재 C++ 실행 경로에서 참조되지 않는다. 에디터에서 값을 변경해도 플레이 결과가 달라지지 않는다. 요구사항에 따라 실제 시작·Spawn·보상 계산에 연결하거나 사용하지 않는 필드를 제거해야 한다.

---

## Q23. GameMode와 GameState의 차이는 무엇입니까?

### 모범 답안

GameMode는 서버에만 존재하며 게임 규칙, 승패와 Spawn 정책을 담당한다. GameState는 클라이언트도 알아야 하는 전체 게임 상태를 복제하는 데 사용한다.

현재 싱글플레이에서는 GameMode에서 Stage 상태와 UI 호출이 동작하지만 멀티플레이로 확장한다면 현재 Stage, Wave, 생존 적 수와 진행 시간처럼 클라이언트가 표시해야 하는 값은 GameState로 옮겨 복제해야 한다.

---

# G. 데이터 설계와 Asset

## Q24. 무기에 DataAsset을 사용하고 Wave/Variant에 DataTable을 사용한 이유는 무엇입니까?

### 모범 답안

Weapon은 Mesh, Projectile Class, VFX, GameplayTag와 다양한 설정을 하나의 독립 콘텐츠 단위로 묶기 때문에 DataAsset이 적합하다. Wave와 Monster Variant는 동일한 스키마를 가진 여러 행을 표 형태로 비교·편집하기 때문에 DataTable이 적합하다.

다만 기준을 절대적인 규칙으로 보기는 어렵고, 참조 방식, 로딩 정책, 협업 방식에 따라 달라질 수 있다.

---

## Q25. DataAsset을 런타임에 직접 수정하지 않고 Character에 Runtime Bonus를 둔 이유는 무엇입니까?

### 모범 답안

DataAsset은 여러 인스턴스가 공유하는 정의 데이터다. 런타임 강화로 DataAsset을 변경하면 같은 Asset을 참조하는 다른 객체에도 영향을 줄 수 있다.

따라서 기본 공격력과 쿨다운은 Weapon DataAsset에 유지하고, 현재 플레이에서 얻은 강화는 Character의 `RuntimeProjectileDamageBonus`, `RuntimeProjectileCooldownReduction` 등에 저장해 최종 값을 계산한다.

---

## Q26. `TObjectPtr`, `TSubclassOf`, `TSoftObjectPtr`를 각각 왜 사용했습니까?

### 모범 답안

- `TObjectPtr<T>`: 로드된 UObject 인스턴스에 대한 GC 추적 참조
- `TSubclassOf<T>`: 특정 기반 클래스를 상속한 UClass만 지정하도록 타입 제한
- `TSoftObjectPtr<T>`: 에셋을 즉시 강제 로드하지 않는 경로 기반 참조

현재 일부 Soft Reference에 `LoadSynchronous()`를 사용하므로 전투 중 처음 로드되면 Hitch 가능성이 있다. 사전 로드 또는 Streamable Manager를 통한 비동기 로드를 고려해야 한다.

---

# H. UI, Animation과 상호작용

## Q27. PlayerController가 UI를 관리하도록 한 이유는 무엇입니까?

### 모범 답안

PlayerController는 로컬 플레이어 입력과 화면 흐름을 관리하기 적합하다. Character가 메뉴와 Widget 수명주기를 알 필요가 없고, GameMode가 로컬 UI를 직접 소유하지 않게 한다.

`AProject_Z_PlayerController`는 HUD, Crosshair, Interaction Marker, Stage Clear와 Game Over Widget을 만들고 Game/UI Input Mode와 Mouse Cursor를 전환한다.

멀티플레이에서는 로컬 Controller에서만 UI를 생성하는지 확인해야 한다.

---

## Q28. HUD를 Tick에서 갱신하는 현재 방식의 장단점은 무엇입니까?

### 모범 답안

장점은 구현이 단순하고 이벤트 연결 누락이 적어 초기 기능 검증이 쉽다는 것이다. 단점은 값이 변하지 않아도 매 프레임 Cast, Getter와 Widget 속성 갱신이 반복된다는 것이다.

확장 시 다음처럼 이벤트 기반으로 변경할 수 있다.

- HP/Stamina: ASC Attribute 변경 Delegate
- 경험치/레벨/탄약: Character 또는 Component Delegate
- 무기 아이콘: 장비 변경 Event

---

## Q29. 재장전에서 AnimationNotify를 사용한 이유는 무엇입니까?

### 모범 답안

입력 직후 탄약을 채우는 대신 Montage의 실제 장전 완료 프레임과 코드 상태 변경 시점을 맞추기 위해서다. 재장전 시작 시 상태를 잠그고 Montage를 재생한 뒤 `UZAnimNotify_ReloadAmmo`가 Character의 완료 함수를 호출해 탄약을 갱신한다.

검증해야 할 실패 조건은 Montage 중단, Notify 누락, 무기 교체, 사망과 중복 입력이다. Notify만을 유일한 해제 경로로 사용하면 Montage 취소 시 재장전 상태가 영구히 남을 수 있으므로 종료/취소 처리도 필요하다.

---

# I. 검증과 성능

## Q30. Object Pool을 사용해 성능이 얼마나 향상됐습니까?

### 모범 답안

현재 정량 측정 자료가 없다면 향상됐다고 단정해서는 안 된다. 풀링은 Spawn/Destroy와 GC 부담을 줄이기 위한 설계지만, 객체 수가 적으면 관리 복잡성만 늘어날 수 있다.

동일 조건에서 다음을 비교해야 한다.

- Game Thread 평균 및 최대 시간
- Actor 생성 수
- GC 횟수와 최대 지연
- 메모리 사용량
- 최대 동시 Projectile 수

Unreal Insights와 `stat unit`, `stat game` 등을 이용해 Spawn/Destroy 버전과 Pool 버전을 비교한다.

### 감점 기준

- 측정 없이 “풀링했으므로 빨라졌다”고 단정함
- FPS 하나만 보고 원인을 확정함

---

## Q31. 이 프로젝트에서 우선 작성해야 할 테스트 세 가지는 무엇입니까?

### 모범 답안

1. 직접 피해와 GAS 피해 순서를 바꿔도 HP가 정확히 누적되는지 검사
2. Spawn 실패 또는 잘못된 Variant Row에서 `AliveEnemyCount`와 Stage 상태가 교착되지 않는지 검사
3. Projectile 반복 Acquire/Release 후 Damage, Pierce, Element, HitActors와 Timer가 초기화되는지 검사

추가로 재장전 Montage 취소, SaveGame 구매와 환불, UI 입력 모드 전환을 검증할 수 있다.

---

## Q32. 현재 코드에서 가장 먼저 수정할 세 가지를 우선순위와 함께 말해 주세요.

### 모범 답안

1. Enemy HP를 AttributeSet으로 단일화한다. 전투 결과 자체가 잘못될 수 있기 때문이다.
2. Spawn 성공 시에만 AliveEnemyCount를 증가시키고 0명 생성 정책을 추가한다. Stage 진행이 멈출 수 있기 때문이다.
3. Pool 중복 반환을 차단한다. 같은 Actor가 동시에 두 발로 사용되는 풀 상태 손상을 막기 위해서다.

Character 분리와 명명 정리는 중요하지만 현재 게임 결과를 훼손하는 위 항목보다 뒤에 둔다.

---

# J. 완료보고서 교차 검증

## Q33. 완료보고서에서 현재 구현보다 넓게 표현된 내용을 직접 지적해 주세요.

### 모범 답안

다음 표현은 범위를 제한해 설명해야 한다.

1. **“GAS 기반 데미지 처리 구조”**
   - Projectile 일부는 GAS를 사용하지만 직접 피해와 상태이상은 `CurrentHP` 경로가 남아 있다.

2. **“GAS를 이용한 피격 반응 및 사망 처리”**
   - GAS는 HP 변경 일부를 담당하고 실제 피격 bool, Animation Event와 `Die()`는 Enemy가 처리한다.

3. **“Head Shot Tag를 Effect Context에 전달”**
   - HitResult는 Effect Context, Headshot Tag는 EffectSpec의 DynamicGrantedTags에 들어간다.

4. **“Wave별 적 생성 수와 난이도 설정”**
   - 데이터 필드는 있으나 `EnemyCount`, Spawn Interval과 Wave 배율은 실제 GameMode에서 사용되지 않는다.

5. **“Stage별 Boss 출현 및 완료 조건 관리”**
   - Variant Row로 Boss 등급을 생성할 수 있지만 전용 Boss 조건 및 Getter 일부는 더미 API다.

6. **“모든 기능을 Character에 몰아넣지 않았다”**
   - UI와 GameMode는 분리됐지만 Character는 여전히 입력, 조준, 장비, 전투, 성장과 상호작용을 폭넓게 가진다.

좋은 답변은 보고서가 틀리지 않았다고 방어하는 것이 아니라 실제 구현 범위를 정확히 정정하고 개선 계획을 제시해야 한다.

---

## Q34. 본인이 이 프로젝트에서 가장 잘못 설계한 부분은 무엇입니까?

### 모범 답안

가장 직접적인 문제는 GAS를 추가하면서 기존 Enemy `CurrentHP`를 제거하지 않아 체력 원천을 이중화한 것이다. 공격 순서에 따라 HP가 복구될 수 있으므로 구조적 취향이 아니라 실제 기능 결함이다.

원인은 기존 직접 피해와 새로운 GAS 경로를 단계적으로 통합하면서 완료 조건과 회귀 테스트를 정의하지 않은 것이다. 수정은 AttributeSet HP 단일화, 공통 Damage Pipeline, Attribute Delegate 기반 사망/UI 처리와 공격 순서 테스트 순으로 진행한다.

### 평가 포인트

- 책임 회피 없이 구체적인 결함을 선택하는가?
- “시간이 부족했다”에서 끝나지 않고 발생 원인을 분석하는가?
- 수정과 검증 계획을 구분하는가?

---

## Q35. 다시 구현한다면 처음부터 무엇을 다르게 하겠습니까?

### 모범 답안

- HP, 탄약, 경험치와 Stage 상태의 소유자를 먼저 정의한다.
- 피해 경로를 하나로 만들고 자동화 테스트를 추가한 뒤 무기 종류를 늘린다.
- Stage와 Wave를 별도 구조로 정의하고 데이터 필드가 실행 코드에 연결되는지 검증한다.
- 풀링은 예상 동시 Projectile 수를 측정한 뒤 도입하고 중복 반환 불변조건을 테스트한다.
- Character는 초기부터 최소 책임을 유지하되, 과도한 추상화는 피하고 변경이 확인된 Combat/Progression부터 분리한다.

---

# K. 압박 질문

## Q36. “DataAsset을 쓴 것이 왜 설계라고 할 수 있습니까?”

### 모범 답안

DataAsset API를 사용한 사실 자체가 설계는 아니다. 설계의 핵심은 공유 정의 데이터와 Actor별 런타임 상태를 분리하고, 코드로 표현할 행동과 데이터로 표현할 변형의 경계를 정한 것이다.

현재 Weapon은 공통 행동을 C++로 재사용하고 피해량, 발사 패턴, Mesh와 VFX 차이를 DataAsset으로 구성한다. 동시에 타입별 필드가 하나의 에셋에 모인 한계도 있으므로 행동 종류가 늘면 Fragment 또는 전략 객체 분리가 필요하다.

---

## Q37. “풀링이 오히려 복잡성만 늘린 것 아닙니까?”

### 모범 답안

측정 전에는 그 가능성을 배제할 수 없다. 현재 풀에는 중복 반환 방어와 최대 크기 정책도 없어 복잡성 비용이 존재한다. 목표 발사량에서 Spawn/Destroy와 Pool 방식을 측정해 GC와 Game Thread 이득이 유지비용보다 큰지 판단해야 한다.

---

## Q38. “이 프로젝트가 시니어 수준이라고 생각합니까?”

### 모범 답안

현재 결과만으로 시니어 수준을 증명한다고 보지 않는다. 여러 Unreal 시스템을 연결한 구현 경험은 보여주지만 핵심 상태 정합성, 자동화 테스트, 성능 측정과 네트워크 권한 설계 증거가 부족하다.

확인된 결함을 수정하고 테스트와 프로파일링 결과를 남기는 과정까지 완료해야 시스템을 안정적으로 소유할 수 있다는 증거가 된다.

---

## Q39. “정말 본인이 구현했다는 것을 어떻게 증명할 수 있습니까?”

### 모범 답안

기능 목록보다 실제 코드의 호출 흐름, 변수 소유권, 실패 조건과 수정 과정을 설명하겠다. 예를 들어 입력부터 AbilitySpec, Projectile Pool, EffectSpec, AttributeSet까지 디버거로 따라가고, Spawn 실패나 이중 HP 문제를 재현한 뒤 수정 전후 테스트 결과를 제시할 수 있다.

Git 기록이 본인 작업을 구분할 수 있다면 커밋 단위의 문제와 변경 이유도 함께 설명할 수 있다. 단, 기록이 실제로 없는 경우 있다고 주장하면 안 된다.

---

# L. 짧은 용어 확인 질문

## Q40. `TObjectPtr`는 무엇입니까?

### 정답

UObject 참조를 Unreal의 리플렉션과 GC가 추적할 수 있게 표현하는 포인터 래퍼다. 일반적으로 `UPROPERTY`와 함께 소유 참조에 사용한다.

## Q41. `TWeakObjectPtr`는 무엇입니까?

### 정답

객체를 소유하지 않으며 대상 UObject가 파괴되면 유효하지 않게 되는 약한 참조다. 사용 전 `IsValid()` 확인이 필요하다.

## Q42. `TSoftObjectPtr`는 무엇입니까?

### 정답

에셋 경로를 기반으로 참조하여 에셋을 항상 메모리에 강제 로드하지 않게 한다. 필요하면 동기 또는 비동기 로드할 수 있다.

## Q43. `BlueprintImplementableEvent`와 `BlueprintNativeEvent`의 차이는 무엇입니까?

### 정답

- `BlueprintImplementableEvent`: C++ 기본 구현 없이 Blueprint가 구현
- `BlueprintNativeEvent`: C++ `_Implementation()` 기본 구현이 있고 Blueprint가 선택적으로 Override

## Q44. `Transient`는 왜 사용합니까?

### 정답

런타임에만 필요한 값으로 에셋이나 SaveGame 등의 영구 직렬화 대상이 아니어야 한다는 의도를 나타낸다. 생성된 Widget, 현재 선택지, 런타임 VFX 참조 등에 사용한다.

## Q45. GameMode는 클라이언트에도 존재합니까?

### 정답

네트워크 게임에서 GameMode는 서버에만 존재한다. 클라이언트가 알아야 하는 전체 게임 상태는 GameState에 두고 복제한다.

---

# 4. 실전 추천 질문 순서

전체 45개를 모두 묻기보다 다음 순서로 진행하면 구현 여부를 효율적으로 확인할 수 있다.

## 30분 인터뷰

1. Q1 전체 구조
2. Q3 입력과 Ability
3. Q4 발사 데이터
4. Q10 충돌과 GAS 피해
5. Q12 Damage/HP
6. Q16 이중 HP
7. Q5 Pool과 WorldSubsystem
8. Q8 중복 반환
9. Q19 Stage 흐름
10. Q20 Spawn 실패
11. Q33 보고서 불일치
12. Q34 가장 잘못 설계한 부분

## 60분 인터뷰

30분 질문에 다음을 추가한다.

- Q2 C++/Blueprint 경계
- Q7 Pool 초기화
- Q9 관통
- Q11 Headshot fallback
- Q13 SetByCaller
- Q14 Context와 Tag
- Q17 Enemy AI
- Q21 Wave 미사용 데이터
- Q24 DataAsset/DataTable
- Q28 UI Tick
- Q30 성능 검증
- Q31 테스트 전략
- Q35 재설계

---

# 5. 최종 평가 양식

```text
# Project_Z 과제 검증 결과

## 응답자
- 이름:
- 검증 일시:
- 소요 시간:

## 점수
- 프로젝트 소유 이해: /20
- 호출 흐름 이해: /20
- Unreal Framework 이해: /15
- GAS 이해: /15
- 데이터 설계: /10
- 안정성 및 디버깅: /10
- 검증 및 성능: /10
- 총점: /100

## 직접 구현 신뢰도
- 높음 / 보통 / 낮음

## 강점
-

## 확인된 부족 영역
-

## 보고서와 실제 구현의 불일치 인식
-

## 위험한 오답 또는 과장
-

## 후속 학습 및 수정 우선순위
1.
2.
3.

## 최종 판단
- 통과 / 조건부 통과 / 추가 검증 / 미통과

## 판단 근거
-
```

---

# 6. 응답자가 최소한 기억해야 할 핵심 문장

1. DataAsset은 공유 정의이고 Actor 변수는 인스턴스 런타임 상태다.
2. Enhanced Input은 ASC의 AbilitySpec을 찾아 Ability를 활성화하는 진입점이다.
3. HitResult는 Effect Context, Headshot Tag는 DynamicGrantedTags, 피해 수치는 SetByCaller에 들어간다.
4. `Damage`는 임시 Meta Attribute이고 `HP`는 지속 상태다.
5. 현재 Enemy HP는 이중 관리되어 AttributeSet으로 단일화해야 한다.
6. 풀의 Actor는 Available과 InUse 중 정확히 한 상태에만 있어야 한다.
7. Poolable Interface는 객체별 런타임 상태 초기화를 분리한다.
8. GameMode는 서버 규칙이고, 복제할 게임 상태는 GameState의 책임이다.
9. 현재 Wave와 Stage 데이터의 일부 필드는 선언만 되어 있고 실행 코드에 반영되지 않는다.
10. 성능 개선은 구현 사실이 아니라 프로파일링 결과로 증명한다.

---

# 7. 검증 상태

- 완료보고서와 C++ 소스 교차 확인: 완료
- 질문 및 모범 답안 작성: 완료
- Blueprint 그래프 내부 확인: 미실행
- PIE 재현: 미실행
- C++ 빌드: 미실행
- 프로젝트 소스와 에셋 수정: 없음

본 문서의 코드 결함 평가는 정적 분석 기준이다. 실제 검증 회의에서는 현재 Blueprint 기본값과 PIE 동작이 다른 경로를 보완하는지 추가 확인해야 한다.
