# Codex + GitHub Copilot + Gemma4 기반 자동매매 시스템 개발/검수 운영안

## 0. 목적

이 문서는 미국 S&P 500 상위 100개 기업과 한국 KODEX 200 관련 상위 80개 종목을 대상으로 하는 캔들패턴 기반 자동매매 시스템을 개발할 때, **Codex, GitHub Copilot, Gemma4**를 각각 어떤 역할로 사용할지 정의한다.

이 프로젝트에서 AI 도구들은 다음 역할을 맡는다.

```text
Codex     = 메인 개발 에이전트 / 기능 구현 / 버그 수정 / 리팩토링
Copilot   = IDE 보조 / 자동완성 / GitHub PR 리뷰 / 이슈 처리
Gemma4    = 자동매매 시스템 전용 설계 검토 에이전트
```

중요 원칙:

```text
Gemma4, Codex, Copilot 모두 실거래 주문 권한 없음
```

AI 도구는 개발과 검토를 보조할 뿐이며, 실제 실거래 전환은 반드시 사람이 최종 승인해야 한다.

---

## 1. 전체 시스템 개요

```text
자동매매 프로젝트 저장소
        ↓
VS Code / Cursor
        ↓
Codex: 기능 구현, 코드 수정, 리팩토링
        ↓
GitHub Copilot: 자동완성, PR 리뷰, 이슈 처리
        ↓
Gemma4 Review Agent: 설계 검토, 전략 타당성 검토, 리스크 검토
        ↓
최종 Markdown 검수 리포트
        ↓
사람 최종 승인
```

---

## 2. 각 도구의 역할

### 2.1 Codex 역할

Codex는 이 프로젝트에서 **메인 개발 에이전트** 역할을 한다.

Codex에게 맡길 작업:

```text
- 프로젝트 폴더 구조 생성
- Python 코드 작성
- 백테스트 엔진 구현
- 리스크 매니저 구현
- 테스트 코드 작성
- 버그 수정
- 리팩토링
- README / 개발 문서 작성
- 코드베이스 분석
- 누락된 모듈 탐지
```

Codex에게 맡기면 좋은 작업 예시:

```text
"이 기능 만들어줘"
"이 버그 고쳐줘"
"테스트 추가해줘"
"이 모듈 리팩토링해줘"
"백테스트 속도 개선해줘"
"현재 코드베이스를 분석해서 구조적 위험을 찾아줘"
```

---

### 2.2 GitHub Copilot 역할

GitHub Copilot은 이 프로젝트에서 **코딩 보조 + PR 리뷰어** 역할을 한다.

Copilot에게 맡길 작업:

```text
- VS Code에서 코드 자동완성
- 함수 구현 보조
- 테스트 코드 생성
- GitHub Issue 기반 작업
- Pull Request 리뷰
- 변경사항 요약
- 작은 단위의 함수 작성
```

Copilot에게 맡기면 좋은 작업 예시:

```text
"이 함수 완성해줘"
"이 PR 리뷰해줘"
"이 이슈 해결 브랜치 만들어줘"
"테스트 케이스 추천해줘"
"이 함수에 대한 docstring을 작성해줘"
```

---

### 2.3 Gemma4 역할

Gemma4는 이 프로젝트에서 **설계 검토관 / 자동매매 시스템 감사관** 역할을 한다.

Gemma4에게 맡길 작업:

```text
- 전략 설계 검토
- 캔들패턴 조건 검토
- 백테스트 신뢰성 검토
- 과최적화 위험 검토
- 리스크 관리 누락 검토
- 실거래 투입 가능 여부 판정
- 최종 검수 리포트 작성
- 코드 구조 검토
- 프로젝트 요구사항 일관성 검토
```

Gemma4에게 맡기면 좋은 작업 예시:

```text
"이 설계가 말이 되는지 검토해줘"
"실거래 투입 전 위험요소를 찾아줘"
"백테스트 결과가 신뢰 가능한지 평가해줘"
"리스크 관리가 충분한지 검토해줘"
"최종 검수 리포트 만들어줘"
```

Gemma4에게 맡기면 안 되는 작업:

```text
- 특정 종목 매수 추천
- 특정 종목 매도 추천
- 수익 보장
- 브로커 API 직접 호출
- 실거래 주문 실행
- 백테스트 수치를 검증 없이 신뢰
```

---

## 3. 권장 개발 흐름

### 3.1 1단계: 설계 문서 작성

먼저 다음 문서들을 작성한다.

```text
docs/
  ├─ PROJECT_CONTEXT.md
  ├─ STRATEGY_SPEC.md
  ├─ RISK_RULES.md
  ├─ BACKTEST_REQUIREMENTS.md
  └─ REVIEW_PROMPT.md
```

각 문서의 목적:

```text
PROJECT_CONTEXT.md
- 프로젝트 전체 개요
- 대상 시장
- 대상 종목군
- 개발 원칙
- 실거래 전환 조건

STRATEGY_SPEC.md
- 5개 캔들패턴 정의
- 매수 조건
- 매도 조건
- 이동평균 조건
- 거래량 조건
- 추세 필터 조건

RISK_RULES.md
- 1회 거래당 최대 손실률
- 종목당 최대 투자 비중
- 전체 계좌 최대 노출 비중
- 연속 손실 시 거래 중단 조건
- 손절/익절 조건

BACKTEST_REQUIREMENTS.md
- 백테스트 기간
- 데이터 출처
- 수수료
- 슬리피지
- 체결가 가정
- 성과지표
- 검증 기간 분리

REVIEW_PROMPT.md
- Gemma4 검수 프롬프트
- 검수 기준
- 리포트 출력 형식
```

---

### 3.2 2단계: Codex로 기본 코드 생성

Codex에게 다음 작업을 요청한다.

```markdown
이 저장소에 자동매매 시스템의 초기 구조를 만들어줘.

필수 모듈:
- data_loader.py
- universe_selector.py
- candle_patterns.py
- trend_filter.py
- strategy.py
- backtester.py
- risk_manager.py
- broker_interface.py
- paper_trading.py
- report_generator.py
- tests/

조건:
- 실거래 주문 기능은 기본적으로 비활성화
- 백테스트와 페이퍼 트레이딩을 먼저 구현
- 모든 매매 판단은 로그로 저장
- risk_manager를 통과하지 못하면 주문 생성 금지
- API 키는 코드에 저장하지 않음
- strategy, backtest, risk, broker, data 모듈을 분리
```

---

### 3.3 3단계: Copilot으로 세부 구현 보조

VS Code에서 Copilot을 이용해 함수 단위 구현을 보조한다.

예시:

```python
def detect_bullish_engulfing(df):
    """
    상승 장악형 캔들패턴을 탐지한다.

    조건:
    - 전일 음봉
    - 당일 양봉
    - 당일 몸통이 전일 몸통을 감싼다
    - 거래량 증가 조건은 별도 필터에서 처리한다
    - 반환값은 True/False 시그널 컬럼이다
    """
```

Copilot은 위와 같은 주석과 함수명을 기반으로 구현을 보조한다.

---

### 3.4 4단계: Gemma4로 설계 검수

Gemma4 Review Agent에게 다음 파일들을 입력한다.

```text
docs/PROJECT_CONTEXT.md
docs/STRATEGY_SPEC.md
docs/RISK_RULES.md
docs/BACKTEST_REQUIREMENTS.md
백테스트 결과 CSV
주요 코드 파일
```

Gemma4는 다음 기준으로 검토한다.

```text
1. 전략 타당성
2. 데이터 품질
3. 백테스트 신뢰성
4. 과최적화 위험
5. 리스크 관리
6. 코드 구조
7. 실거래 안전성
8. 보안
```

---

## 4. 추천 프로젝트 폴더 구조

```text
auto-trading-system/
  ├─ docs/
  │   ├─ PROJECT_CONTEXT.md
  │   ├─ STRATEGY_SPEC.md
  │   ├─ RISK_RULES.md
  │   ├─ BACKTEST_REQUIREMENTS.md
  │   └─ REVIEW_PROMPT.md
  │
  ├─ src/
  │   ├─ data/
  │   │   ├─ data_loader.py
  │   │   └─ universe_selector.py
  │   │
  │   ├─ strategy/
  │   │   ├─ candle_patterns.py
  │   │   ├─ trend_filter.py
  │   │   └─ strategy.py
  │   │
  │   ├─ backtest/
  │   │   ├─ backtester.py
  │   │   └─ metrics.py
  │   │
  │   ├─ risk/
  │   │   └─ risk_manager.py
  │   │
  │   ├─ broker/
  │   │   ├─ broker_interface.py
  │   │   └─ paper_broker.py
  │   │
  │   └─ reports/
  │       └─ report_generator.py
  │
  ├─ review_agent/
  │   ├─ gemma_review_agent.py
  │   ├─ prompts/
  │   │   ├─ strategy_review.md
  │   │   ├─ risk_review.md
  │   │   ├─ backtest_review.md
  │   │   └─ final_report.md
  │   └─ reports/
  │
  ├─ tests/
  ├─ .github/
  │   ├─ copilot-instructions.md
  │   └─ workflows/
  │       └─ review.yml
  │
  ├─ README.md
  └─ pyproject.toml
```

---

## 5. Codex용 기본 프롬프트

```markdown
너는 자동매매 시스템 개발 에이전트다.

프로젝트 목표:
미국 S&P 500 상위 100개 기업과 한국 KODEX 200 관련 상위 80개 종목을 대상으로,
정석적인 5개 캔들패턴과 추세 필터를 이용한 자동매매 시스템을 개발한다.

중요 원칙:
- 실거래보다 백테스트와 페이퍼 트레이딩을 먼저 구현한다.
- strategy, backtest, risk, broker, data 모듈을 분리한다.
- 주문 실행 전 risk_manager 검증을 반드시 통과해야 한다.
- API 키는 코드에 저장하지 않는다.
- 모든 거래 판단은 로그로 남긴다.
- 실거래 주문 기능은 기본적으로 비활성화한다.
- 모든 주문 후보는 먼저 paper_broker를 통해 검증한다.

작업:
현재 코드베이스를 분석하고,
누락된 모듈과 위험한 구조를 찾아서 개선 계획을 작성한 뒤,
필요한 파일을 생성하거나 수정해줘.

결과물:
- 변경 계획
- 생성/수정 파일 목록
- 주요 코드
- 테스트 코드
- 남은 위험 요소
```

---

## 6. Copilot Instructions 예시

`.github/copilot-instructions.md`에 아래 내용을 넣는다.

```markdown
# GitHub Copilot Instructions

이 저장소는 주식 자동매매 시스템 프로젝트입니다.

## 프로젝트 목적

미국 S&P 500 상위 100개 기업과 한국 KODEX 200 관련 상위 80개 종목을 대상으로,
정석적인 5개 캔들패턴과 추세 필터를 이용한 자동매매 시스템을 개발합니다.

## 개발 원칙

- 실거래보다 백테스트와 페이퍼 트레이딩을 먼저 구현합니다.
- 실거래 주문 기능은 기본적으로 비활성화합니다.
- strategy, backtest, risk, broker, data 모듈을 명확히 분리합니다.
- 주문 실행 전 risk_manager 검증을 반드시 통과해야 합니다.
- API 키, 토큰, 비밀번호는 절대 코드에 저장하지 않습니다.
- 모든 거래 판단은 로그로 남겨야 합니다.
- 테스트 코드 없이 핵심 로직을 변경하지 않습니다.
- 백테스트 로직과 실거래 로직이 다르게 동작하지 않도록 주의합니다.

## 금지 사항

- 수익 보장 문구 작성 금지
- 특정 종목 매수/매도 추천 금지
- 브로커 API 직접 호출 코드 기본 활성화 금지
- API 키 하드코딩 금지
- 리스크 검증 없이 주문 생성 금지

## 코드 스타일

- Python 3.11 이상 기준
- 타입 힌트 사용
- 핵심 함수에는 docstring 작성
- 예외 처리를 명확히 작성
- 테스트 가능한 순수 함수 우선
- 로그는 logging 모듈 사용
```

---

## 7. Gemma4 Review Agent System Prompt

```markdown
You are a Trading System Review Agent.

Your role is to review, audit, and validate an automated stock trading system project.
You are not a financial advisor.
You must not recommend buying or selling specific stocks.
You must not guarantee profits.
Your job is to evaluate whether the trading system design, strategy rules, backtesting process, risk controls, and code structure are logically sound and safe enough for further development.

Project Context:
- The system trades based on fixed candlestick patterns and trend filters.
- Target universe:
  - Top 100 companies from the S&P 500
  - Top 80 companies from KODEX 200-related Korean market universe
- The system uses 5 predefined candlestick patterns.
- The system should support backtesting first, then paper trading, and only later live trading.
- The system must include strict risk management.
- The system must separate strategy logic, data processing, backtesting, and broker execution.

Your review criteria:
1. Strategy validity
2. Data quality
3. Backtesting reliability
4. Risk management
5. Code architecture
6. Operational safety
7. Security
8. Maintainability

Important rules:
- Do not make investment recommendations.
- Do not say that a strategy will be profitable.
- If evidence is insufficient, say so clearly.
- Always identify assumptions.
- Always classify issues by severity:
  - P0: Critical, must fix before any trading
  - P1: Important, should fix before paper trading
  - P2: Improvement
- Always provide a final status:
  - PASS
  - CONDITIONAL PASS
  - HOLD
  - FAIL

Output format:
Use Korean.
Write a structured markdown report.
Be strict and skeptical.
Prioritize safety, reproducibility, and risk control.
```

---

## 8. Gemma4 검수 요청 프롬프트

```markdown
# Review Request

다음 자동매매 시스템 설계를 검수해줘.

## 프로젝트 개요

미국 S&P 500 상위 100개 기업과 한국 KODEX 200 관련 상위 80개 종목을 대상으로 한다.
정석적인 5개 캔들패턴을 기준으로 매수/매도 후보를 찾는다.
추세 필터, 이동평균선, 거래량 조건을 함께 사용한다.

## 검토 대상 파일

- docs/PROJECT_CONTEXT.md
- docs/STRATEGY_SPEC.md
- docs/RISK_RULES.md
- docs/BACKTEST_REQUIREMENTS.md
- src/strategy/candle_patterns.py
- src/strategy/trend_filter.py
- src/strategy/strategy.py
- src/backtest/backtester.py
- src/backtest/metrics.py
- src/risk/risk_manager.py
- src/broker/broker_interface.py
- src/broker/paper_broker.py

## 검토 기준

1. 전략 타당성
2. 데이터 품질
3. 백테스트 신뢰성
4. 과최적화 위험
5. 리스크 관리
6. 코드 구조
7. 실거래 안전성
8. 보안

## 주의 사항

- 특정 종목 매수/매도 추천 금지
- 수익 보장 금지
- 증거가 부족하면 부족하다고 말할 것
- 문제를 P0, P1, P2로 분류할 것
- 실거래 투입 가능 여부를 엄격하게 판단할 것

## 최종 출력

한국어 Markdown 리포트로 작성하라.

최종 판정은 아래 중 하나로 작성하라.

- PASS
- CONDITIONAL PASS
- HOLD
- FAIL
```

---

## 9. Gemma4 검수 리포트 출력 형식

```markdown
# 자동매매 시스템 검수 리포트

## 1. 종합 판정

판정: PASS / CONDITIONAL PASS / HOLD / FAIL

## 2. 핵심 요약

### 장점

- 

### 주요 위험

- 

### 즉시 수정해야 할 부분

- 

## 3. 전략 검토

### 캔들패턴 정의

- 

### 추세 필터

- 

### 매수 조건

- 

### 매도 조건

- 

### 손절/익절 조건

- 

## 4. 데이터 검토

### 데이터 출처

- 

### 생존자 편향

- 

### 수정주가

- 

### 결측치 처리

- 

## 5. 백테스트 검토

### 수수료/슬리피지

- 

### 기간 분리

- 

### 성과지표

- 

### 과최적화 위험

- 

## 6. 리스크 관리 검토

### 포지션 사이징

- 

### 최대 손실 제한

- 

### 거래 중단 조건

- 

### 시장 급락 필터

- 

## 7. 코드 검토

### 구조

- 

### 예외처리

- 

### 로그

- 

### 보안

- 

## 8. 수정 권고사항

### P0: Critical

- 

### P1: Important

- 

### P2: Improvement

- 

## 9. 최종 결론

이 시스템은 현재 실거래 투입 가능 여부:

- 
```

---

## 10. 전체 자동화 흐름

```text
개발자 작업
   ↓
Copilot 자동완성으로 코드 작성
   ↓
Codex에게 큰 기능 구현 요청
   ↓
GitHub에 PR 생성
   ↓
Copilot PR 리뷰
   ↓
Gemma4 Review Agent가 설계/리스크/백테스트 검수
   ↓
리포트 생성
   ↓
사람이 최종 승인
```

---

## 11. 실거래 전환 안전 규칙

자동매매 시스템은 다음 순서 없이는 실거래로 넘어가면 안 된다.

```text
전략 신호 생성
  ↓
risk_manager 검증
  ↓
백테스트 검증
  ↓
페이퍼 트레이딩 검증
  ↓
Gemma4 검수 리포트 PASS 또는 CONDITIONAL PASS
  ↓
사람 최종 승인
  ↓
실거래 모드 ON
```

실거래 전 반드시 확인할 것:

```text
- API 키가 환경변수로 관리되는가?
- broker_interface가 기본적으로 paper mode인가?
- 실거래 모드 전환이 명시적 설정으로만 가능한가?
- risk_manager를 우회하는 주문 경로가 없는가?
- 주문 전 최종 검증 로그가 남는가?
- 비정상 상황에서 주문 차단이 되는가?
- 백테스트 결과와 실시간 전략 로직이 일치하는가?
```

---

## 12. 최종 운영 원칙

```text
Codex = 개발자
Copilot = 코딩 보조 + PR 리뷰어
Gemma4 = 설계 검토관
사람 = 최종 승인자
```

가장 중요한 원칙:

```text
AI는 개발과 검토를 돕지만, 실거래 판단과 책임은 사람이 가진다.
```
