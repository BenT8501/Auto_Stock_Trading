# 프로젝트 Context: 주식 자동 매수·매도 프로그램

## 1. 프로젝트 목표

미국 S&P 500 상위 100개 종목과 한국 KODEX 200/KOSPI200 상위 80개 종목을 대상으로 하는 캔들·추세 기반 자동매매 시스템을 개발한다.

초기 버전에서는 복잡한 AI 예측 모델을 사용하지 않고, 정석적인 5개의 캔들패턴과 기본 추세 필터만 사용한다.

목표는 다음과 같다.

- 미국 대형주 100개 + 한국 대표 대형주 80개 감시
- 일봉 OHLCV 데이터 기반 캔들패턴 탐지
- 추세 조건과 거래량 조건을 만족할 때만 매수 후보 생성
- 보유 종목에 대해 매도 패턴, 손절, 익절 조건 감시
- 먼저 백테스트 시스템을 완성
- 이후 모의투자 API 연동
- 마지막 단계에서 실거래 자동매매로 확장

이 프로젝트는 투자 조언 시스템이 아니라, 사용자가 정의한 규칙을 자동으로 계산하고 실행하는 자동매매 엔진이다.

---

## 2. 투자 유니버스

### 미국 종목

대상:

- S&P 500 구성종목 중 비중 또는 시가총액 상위 100개

처음 개발 단계에서는 수동 CSV 파일로 종목 리스트를 관리해도 된다.

예시 파일:

```text
data/universe/us_top100.csv
```

컬럼 예시:

```csv
symbol,name,market,rank,active
AAPL,Apple,US,1,true
MSFT,Microsoft,US,2,true
NVDA,NVIDIA,US,3,true
```

### 한국 종목

대상:

- KODEX 200 또는 KOSPI200 구성종목 중 비중/시가총액 상위 80개

예시 파일:

```text
data/universe/kr_top80.csv
```

컬럼 예시:

```csv
symbol,name,market,rank,active
005930,삼성전자,KR,1,true
000660,SK하이닉스,KR,2,true
```

---

## 3. 사용할 캔들패턴 5개

초기 버전에서는 반드시 아래 5개 패턴만 구현한다.

### 매수 패턴 3개

1. Hammer, 망치형
2. Bullish Engulfing, 상승 장악형
3. Morning Star, 샛별형

### 매도 패턴 2개

4. Bearish Engulfing, 하락 장악형
5. Shooting Star, 유성형

추후 패턴을 추가할 수 있도록 구조는 확장 가능하게 만들되, v1에서는 이 5개 외에는 사용하지 않는다.

---

## 4. 데이터 기준

초기 버전은 일봉 데이터만 사용한다.

필수 OHLCV 컬럼:

```text
date
symbol
open
high
low
close
volume
```

### 데이터 소스

**미국 종목:**
- yfinance 라이브러리 사용 (무료, 실시간 데이터)
- 백테스트 데이터: 최소 5년 이상 (2018~현재)

**한국 종목:**
- pykrx 라이브러리 사용 (한국 거래소 공식)
- 또는 CSV 파일로 수동 관리

### 데이터 처리 규칙

- 모든 계산은 종가 기준
- 캔들패턴은 일봉 기준
- 매수는 패턴 발생 당일이 아니라 다음 거래일 조건 충족 시 실행하는 방식으로 시뮬레이션
- 한국/미국 시장 휴장일 차이 처리:
  - 미국: NYSE 휴장 확인 필수
  - 한국: 거래소 휴장 확인 필수
  - 연간 휴장일 정보를 config에서 관리
- 시간대: 미국(09:30-16:00 EST) vs 한국(09:00-15:30 KST) 시간대 차이 존재
  - 백테스트에서는 한국 시간 기준으로 통일
  - 실거래 단계에서 시간대 동기화 필수
- 수수료 및 스프레드:
  - 백테스트 단계: 편의상 생략 가능 (v2에서 반영)
  - 실거래 단계: 반드시 포함
  - 한국: 0.015% 증권사 수수료 + 거래세 0.25%
  - 미국: 0.1% 수수료(또는 무료 브로커 사용)
- 결측치가 있는 종목은 해당 날짜 계산에서 제외

---

## 5. 캔들패턴 정의

### 5.1 Hammer, 망치형

하락 또는 조정 흐름 이후 발생하는 반전 후보 패턴.

조건 예시:

```python
body = abs(close - open)
upper_shadow = high - max(open, close)
lower_shadow = min(open, close) - low

is_hammer = (
    lower_shadow >= body * 2
    and upper_shadow <= body * 0.5
    and body > 0
)
```

추가 필터:

```text
최근 3~10일 동안 하락 또는 조정 흐름이어야 함
거래량 증가가 있으면 신뢰도 상승
```

---

### 5.2 Bullish Engulfing, 상승 장악형

전일 음봉을 당일 양봉이 감싸는 패턴.

조건 예시:

```python
prev_bearish = prev_close < prev_open
curr_bullish = close > open

is_bullish_engulfing = (
    prev_bearish
    and curr_bullish
    and open < prev_close
    and close > prev_open
)
```

---

### 5.3 Morning Star, 샛별형

3개 캔들로 구성된 상승 반전 패턴.

조건 예시:

```text
i-2 캔들 (2일 전): 장대 음봉
i-1 캔들 (1일 전): 작은 몸통
i 캔들 (현재):    강한 양봉
현재 종가가 2일 전 몸통의 중간 이상 회복
```

구현 예시 (DataFrame에서 iloc 또는 shift 사용):

```python
# i-2 캔들: 장대 음봉
candle_2days_ago_bearish = df['close'].shift(2) < df['open'].shift(2)
candle_2days_ago_large_body = abs(df['close'].shift(2) - df['open'].shift(2)) > avg_body * 1.2

# i-1 캔들: 작은 몸통
candle_1day_ago_small_body = abs(df['close'].shift(1) - df['open'].shift(1)) < avg_body * 0.7

# i 캔들: 강한 양봉
candle_current_bullish = df['close'] > df['open']

# 회복 조건: 현재 종가 >= (i-2 open + i-2 close) / 2
recovery = df['close'] >= (df['open'].shift(2) + df['close'].shift(2)) / 2

is_morning_star = (
    candle_2days_ago_bearish
    and candle_2days_ago_large_body
    and candle_1day_ago_small_body
    and candle_current_bullish
    and recovery
)
```

---

### 5.4 Bearish Engulfing, 하락 장악형

전일 양봉을 당일 음봉이 감싸는 패턴.

조건 예시:

```python
prev_bullish = prev_close > prev_open
curr_bearish = close < open

is_bearish_engulfing = (
    prev_bullish
    and curr_bearish
    and open > prev_close
    and close < prev_open
)
```

---

### 5.5 Shooting Star, 유성형

상승 흐름 이후 윗꼬리가 길게 달리는 하락 반전 후보 패턴.

조건 예시:

```python
body = abs(close - open)
upper_shadow = high - max(open, close)
lower_shadow = min(open, close) - low

is_shooting_star = (
    upper_shadow >= body * 2
    and lower_shadow <= body * 0.5
    and body > 0
)
```

추가 필터:

```text
최근 상승 흐름 이후 발생해야 함
전고점 또는 저항선 근처면 신뢰도 상승
```

---

## 6. 추세 필터

캔들패턴만으로 매수하지 않는다.

매수 패턴이 발생하더라도 아래 조건을 만족해야 매수 후보가 된다.

### 매수 추세 조건

```text
close > MA20
MA20 > MA60
MA20 기울기 > 0
volume > volume_MA20 * 1.2
```

### 시장 필터

미국 종목:

```text
S&P 500 지수 또는 SPY가 MA20 위에 있을 것
```

한국 종목:

```text
KOSPI 200 또는 KODEX 200이 MA20 위에 있을 것
```

시장 필터는 v1에서는 옵션으로 두고, config에서 켜고 끌 수 있게 한다.

---

## 7. 매수 규칙

매수 신호는 다음 조건을 모두 만족할 때 발생한다.

```text
1. 종목이 투자 유니버스에 포함되어 있음
2. 매수 캔들패턴 3개 중 하나 발생
   - Hammer
   - Bullish Engulfing
   - Morning Star
3. close > MA20
4. MA20 > MA60
5. volume > volume_MA20 * 1.2
6. 다음 거래일에 전일 고가 돌파
```

### 매수 타이밍 및 가격

**신호 발생 시점:** 날짜 i에서 매수 패턴 발생

**매수 실행:** 날짜 i+1 (다음 거래일)

**매수 조건:**
```text
i+1일의 high > i일의 high 이어야 함
(즉, 전일 고가를 돌파했을 때)
```

**매수 가격:**
```text
보수적 방식: i일 high × 1.001
또는
실제 체결 방식: i+1일 open 사용 (시뮬레이션 단순화)
```

**갭상승 제외 규칙 (중요):**
```text
만약 i+1일 open이 너무 높게 갭상승하면 해당 신호 제외

조건: next_open > signal_high × (1.0 + max_gap_up_pct)
예시: next_open > signal_high × 1.03 이면 매수 스킵

이유: 신호 발생 후 너무 많은 상승이 일어났다면,
추가 상승 여력이 적고 손절 위험이 높아짐
```

**결과:**
- 신호 발생 (i) → 다음날 확인 (i+1) → 갭상승 체크 → 매수 실행
- v1에서는 갭상승 제외 여부를 config에서 온/오프 가능하게 구현

---

## 8. 매도 규칙

매도는 아래 조건 중 하나라도 발생하면 실행한다.

### 8.1 손절

```text
매수가 대비 -3% 도달 시 전량 매도
```

### 8.2 익절

```text
매수가 대비 +5% 도달 시 50% 부분 익절
매수가 대비 +10% 도달 시 잔여 물량 전량 매도
```

초기 백테스트에서는 부분 매도를 구현하기 어렵다면 v1에서는 단순화해도 된다.

단순 v1 매도:

```text
+7% 도달 시 전량 익절
-3% 도달 시 전량 손절
```

### 8.3 추세 이탈

```text
종가가 MA20 아래로 이탈하면 전량 매도
```

### 8.4 매도 캔들패턴

```text
Bearish Engulfing 발생 시 매도
Shooting Star 발생 후 다음날 저가 이탈 시 매도
```

---

## 9. 포지션 관리

### 포지션 사이징 방식 (명시)

**선택 방식: 균등 분할 (Equal Weight)**

```text
최대 보유 종목 수: 10개

포지션 크기 계산:
- 1회 신규 매수 시 배치되는 자본 = 현재 자산 × 10%
- 최대 10개 보유 시 한 종목당 자산 비중 = 10% (균등)
- 예시: 초기 자산 1,000만원
  - 신규 매수 시 배치 자본 = 1,000만원 × 10% = 100만원
  - 10개 종목 보유 시 각 종목 = 10%씩 = 100만원씩
```

### 추가 제한 규칙

```text
1일 신규 매수 제한: 최대 3개
동일 시장 비중 제한:
- 미국 최대 60% (최대 6개)
- 한국 최대 40% (최대 4개)
```

config에서 변경 가능하게 한다.

예시:

```yaml
risk:
  initial_cash: 10000000
  max_positions: 10
  position_size_pct: 0.10        # 1회 신규 매수 시 10% 배치
  max_new_positions_per_day: 3
  stop_loss_pct: -0.03
  take_profit_pct: 0.07
  market_allocation:
    us_max_pct: 0.60
    kr_max_pct: 0.40
```

---

## 10. 개발 단계

### Phase 1: 백테스트 엔진

우선 실거래 API를 붙이지 말고 백테스트부터 만든다.

필수 기능:

```text
- 종목 리스트 로딩
- OHLCV 데이터 로딩
- 이동평균 계산
- 거래량 평균 계산
- 5개 캔들패턴 탐지
- 매수 후보 생성
- 매수/매도 시뮬레이션
- 거래 기록 저장
- 성과 지표 계산
```

성과 지표:

```text
총 수익률
CAGR
MDD
승률
평균 수익률
평균 손실률
손익비
거래 횟수
평균 보유 기간
```

---

### Phase 2: 모의투자

백테스트 결과가 안정적이면 모의투자 API를 붙인다.

필수 기능:

```text
- 실시간 또는 장마감 후 데이터 업데이트
- 당일 신호 계산
- 주문 후보 생성
- 모의투자 주문 전송
- 주문 체결 여부 확인
- 포지션 동기화
- 텔레그램 알림
```

---

### Phase 3: 실거래

모의투자 검증 후 소액 실거래로 전환한다.

초기 실거래 제한:

```text
1회 주문 금액: 1만~5만 원
최대 보유 종목: 3개
운영 기간: 최소 1~2개월
```

---

## 11. 추천 기술 스택

언어:

```text
Python
```

주요 라이브러리:

```text
pandas
numpy
yfinance
pykrx
pandas-ta
matplotlib
sqlite3
APScheduler
pydantic
PyYAML
```

백테스트는 처음에는 직접 구현한다.  
복잡해지면 vectorbt 또는 backtrader를 검토한다.

대시보드는 추후 Streamlit으로 만든다.

---

## 12. 프로젝트 폴더 구조

아래 구조로 개발한다.

```text
auto-trading-bot/
│
├── README.md
├── requirements.txt
├── config.yaml
├── main.py
│
├── data/
│   ├── universe/
│   │   ├── us_top100.csv
│   │   └── kr_top80.csv
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── indicators.py
│   ├── patterns.py
│   ├── signals.py
│   ├── backtester.py
│   ├── portfolio.py
│   ├── risk.py
│   ├── broker/
│   │   ├── base.py
│   │   ├── paper.py
│   │   └── kis.py
│   └── utils.py
│
├── notebooks/
│   └── research.ipynb
│
├── tests/
│   ├── test_patterns.py
│   ├── test_indicators.py
│   └── test_backtester.py
│
└── logs/
```

---

## 13. 주요 파일 역할

### `src/data_loader.py`

역할:

```text
- 종목 리스트 로드
- OHLCV 데이터 다운로드
- CSV 저장/불러오기
- 백테스트 기간 필터링
```

---

### `src/indicators.py`

역할:

```text
- MA20
- MA60
- volume_MA20
- RSI, 추후 옵션
```

필수 함수 예시:

```python
def add_indicators(df):
    pass
```

---

### `src/patterns.py`

역할:

```text
5개 캔들패턴 탐지
```

필수 함수:

```python
def detect_hammer(df):
    pass

def detect_bullish_engulfing(df):
    pass

def detect_morning_star(df):
    pass

def detect_bearish_engulfing(df):
    pass

def detect_shooting_star(df):
    pass

def add_candle_patterns(df):
    pass
```

각 함수는 boolean Series를 반환한다.

---

### `src/signals.py`

역할:

```text
캔들패턴 + 추세 필터를 조합해서 매수/매도 신호 생성
```

필수 함수:

```python
def generate_buy_signals(df, config):
    pass

def generate_sell_signals(df, config):
    pass
```

---

### `src/backtester.py`

역할:

```text
과거 데이터를 기준으로 매수/매도 시뮬레이션
```

필수 기능:

```text
- 현금 관리
- 보유 종목 관리
- 매수 조건 체크
- 매도 조건 체크
- 거래 내역 저장
- 수익률 계산
```

---

### `src/portfolio.py`

역할:

```text
포트폴리오 상태 관리
```

필수 필드:

```text
cash
positions
equity
trade_history
```

---

### `src/risk.py`

역할:

```text
포지션 사이징
최대 보유 종목 수 제한
1일 신규 매수 제한
시장별 비중 제한
```

---

### `src/broker/base.py`

역할:

```text
실거래/모의투자 브로커 공통 인터페이스
```

예시:

```python
class BrokerBase:
    def get_balance(self):
        raise NotImplementedError

    def get_positions(self):
        raise NotImplementedError

    def buy(self, symbol, qty, price=None):
        raise NotImplementedError

    def sell(self, symbol, qty, price=None):
        raise NotImplementedError
```

---

### `src/broker/paper.py`

역할:

```text
모의투자 또는 내부 페이퍼 트레이딩 브로커
```

---

### `src/broker/kis.py`

역할:

```text
추후 한국투자증권 Open API 연동
초기에는 빈 클래스 또는 TODO로 둔다
```

---

## 14. config.yaml 예시

```yaml
project:
  name: auto-trading-bot
  mode: backtest

universe:
  us_file: data/universe/us_top100.csv
  kr_file: data/universe/kr_top80.csv

data:
  start_date: "2018-01-01"
  end_date: "2025-12-31"
  timeframe: "1d"

strategy:
  use_market_filter: false

  moving_average:
    short_window: 20
    long_window: 60

  volume:
    window: 20
    multiplier: 1.2

  buy_patterns:
    - hammer
    - bullish_engulfing
    - morning_star

  sell_patterns:
    - bearish_engulfing
    - shooting_star

risk:
  initial_cash: 10000000
  max_positions: 10
  position_size_pct: 0.10
  max_new_positions_per_day: 3
  stop_loss_pct: -0.03
  take_profit_pct: 0.07
  max_gap_up_pct: 0.03

broker:
  type: paper
```

---

## 15. 백테스트 실행 흐름

`main.py`는 아래 순서로 동작한다.

```text
1. config.yaml 로드
2. 미국/한국 종목 리스트 로드
3. 각 종목의 OHLCV 데이터 로드 또는 다운로드
4. 보조지표 계산
5. 캔들패턴 탐지
6. 매수/매도 신호 생성
7. 날짜 순서대로 백테스트 실행
8. 거래 내역 저장
9. 성과 지표 출력
```

---

## 16. 첫 번째 구현 목표

가장 먼저 아래 기능부터 완성한다.

```text
1. 프로젝트 폴더 구조 생성
2. config.yaml 생성
3. requirements.txt 생성
4. patterns.py에 5개 캔들패턴 함수 구현
5. indicators.py에 MA20, MA60, volume_MA20 구현
6. signals.py에 매수/매도 신호 생성 함수 구현
7. 간단한 단일 종목 백테스트 구현
8. 이후 다중 종목 백테스트로 확장
```

---

## 17. 중요한 개발 원칙

아래 원칙을 지켜야 한다.

```text
- 처음부터 실거래 API를 붙이지 않는다.
- 백테스트 → 페이퍼 트레이딩 → 소액 실거래 순서로 진행한다.
- 모든 매매 판단은 로그로 남긴다.
- 매수보다 매도와 손절 로직을 더 엄격하게 관리한다.
- 캔들패턴 단독 매수는 금지한다.
- 반드시 추세 필터와 거래량 필터를 함께 사용한다.
- 함수는 테스트 가능하게 작게 분리한다.
- 전략 파라미터는 코드에 하드코딩하지 않고 config.yaml에서 관리한다.
```

---

## 18. VSCode 에이전트에게 요청할 첫 작업

아래 작업부터 수행한다.

```text
Python 기반 주식 자동매매 백테스트 프로젝트를 생성해줘.

요구사항:
1. 위 폴더 구조를 생성한다.
2. config.yaml과 requirements.txt를 작성한다.
3. src/patterns.py에 5개 캔들패턴 감지 함수를 구현한다.
4. src/indicators.py에 이동평균과 거래량 평균 계산 함수를 구현한다.
5. src/signals.py에 매수/매도 신호 생성 함수를 구현한다.
6. tests/test_patterns.py에 간단한 유닛 테스트를 작성한다.
7. main.py에서는 샘플 CSV 데이터를 불러와서 패턴과 신호를 계산하는 예시를 실행한다.
8. 실거래 API는 아직 구현하지 말고 broker/base.py와 broker/paper.py만 기본 구조로 만든다.
```

---

## 19. VSCode 에이전트 작업 지시문

아래 문장을 그대로 VSCode 에이전트에게 입력한다.

```text
위 Context를 기준으로 Phase 1 백테스트 뼈대부터 만들어줘.

처음부터 실거래 API를 연결하지 말고, 다음 순서대로 구현해줘.

1. 프로젝트 폴더 구조 생성
2. config.yaml 생성
3. requirements.txt 생성
4. src/patterns.py 구현
5. src/indicators.py 구현
6. src/signals.py 구현
7. src/backtester.py에 단일 종목 백테스트 최소 기능 구현
8. tests/test_patterns.py 작성
9. main.py에서 샘플 데이터로 실행 가능한 예시 작성

코드는 유지보수 가능하게 함수 단위로 나누고, 모든 전략 파라미터는 config.yaml에서 읽도록 만들어줘.
```
