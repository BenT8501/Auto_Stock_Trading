# VSCode 에이전트 전달용 통합 작업 Context

## 전달 목적

현재 주식 자동매매 프로그램에 아래 기능을 한 번에 반영한다.

1. 전일 확정 일봉 기준 `setup_signal` 생성
2. 다음 거래일 장중 실시간 `trigger_signal` 감시
3. 장 시작 후 10분 매수 금지 로직
4. 현재가 감시 주기와 상태 갱신 주기 분리
5. 수동 검색 기능 추가
6. Chat Agent 백엔드 추가
7. Streamlit UI는 후순위로 미루고, 기존 데스크톱 앱 또는 `app.py`에 붙일 수 있는 구조로 설계
8. LLM은 Gemma 4 또는 FunctionGemma 연결 가능성을 열어두되, v1에서는 `MockLLMClient` 또는 `RuleBasedAgent`로 구현
9. Chat Agent는 절대 실주문/실매도 함수를 호출하지 않음

---

## 1. 현재 프로젝트 개요

프로젝트는 미국 S&P 500 상위 100개 종목과 한국 KODEX200/KOSPI200 상위 80개 종목을 대상으로 하는 캔들·추세 기반 자동매매 시스템이다.

초기 전략은 아래 5개 정석 캔들패턴만 사용한다.

### 매수 패턴

```text
- Hammer
- Bullish Engulfing
- Morning Star
```

### 매도 패턴

```text
- Bearish Engulfing
- Shooting Star
```

기본 매수 기획 조건:

```text
1. 유니버스 포함
2. active = true
3. 매수 캔들패턴 발생
4. close > MA20
5. MA20 > MA60
6. MA20 slope > 0
7. volume > volume_MA20 * 1.2
```

중요: 캔들패턴은 장중에 계속 변하므로 반드시 **전일 종가 기준 확정 일봉**으로만 판단한다.

---

## 2. 신호 구조 변경

기존처럼 최신 row에서 바로 `buy_signal=True`를 최종 추천으로 쓰면 안 된다.

신호를 아래 3단계로 분리한다.

```text
trend_candidates
setup_candidates
triggered_candidates
```

### 2.1 trend_candidates

추세 + 거래량 조건만 통과한 후보.

조건:

```text
close > MA20
MA20 > MA60
MA20 slope > 0
volume > volume_MA20 * 1.2
```

의미:

```text
관심 추세 후보
최종 매수 후보 아님
```

### 2.2 setup_signal / setup_candidates

전일 장마감 후 확정 데이터 기준으로 생성되는 다음 거래일 감시 후보.

조건:

```text
1. 유니버스 포함
2. active = true
3. 전일 확정 일봉에서 매수 캔들패턴 발생
   - hammer
   - bullish_engulfing
   - morning_star
4. close > MA20
5. MA20 > MA60
6. MA20 slope > 0
7. volume > volume_MA20 * 1.2
```

의미:

```text
다음 거래일 장중 감시할 후보
```

주의:

```text
setup_signal은 매수 주문 신호가 아니다.
setup_signal은 watchlist 생성용 신호다.
```

### 2.3 trigger_signal / triggered_candidates

다음 거래일 장중 실시간 현재가 기준으로 실제 매수 트리거가 발생한 후보.

조건:

```text
1. setup_signal = true인 종목
2. 장 시작 후 매수 금지 시간이 지남
3. today_open <= prev_high * 1.03
4. current_price >= prev_high * 1.001
5. current_price <= prev_high * 1.03
6. 이미 보유 중인 종목이 아님
7. 일일 신규 매수 제한 초과 아님
8. 최대 보유 종목 수 초과 아님
9. 현금 충분
```

초기 v1에서는 실제 주문하지 않고 `paper/log/알림`만 수행한다.

---

## 3. 실시간 매수 구조

### 3.1 전일 장마감 후 작업

```text
1. 유니버스 CSV 로드
2. OHLCV 데이터 로드
3. 이동평균/거래량 평균 계산
4. 캔들패턴 계산
5. trend_candidates 생성
6. setup_candidates 생성
7. 다음 거래일 watchlist 저장
```

### 3.2 다음 거래일 장중 작업

장중에는 setup 후보를 다시 계산하지 않는다.

```text
1. 오늘 감시할 watchlist 로드
2. 장 시작 후 entry delay 적용
3. 현재가를 짧은 주기로 조회
4. 전일 고가 돌파 여부 확인
5. 갭상승 제외 여부 확인
6. trigger_signal 발생 시 triggered_candidates 저장
7. 콘솔/로그/알림/PaperOrderManager 처리
```

---

## 4. 10분 로직 정리

“10분”은 현재가 조회 주기가 아니다.

```text
장 시작 후 10분 = 매수 금지 시간
상태/화면 리포트 10분 = 가능
현재가 감시 10분 = 비추천
```

한국장:

```text
09:00 ~ 09:10 = 매수 금지
09:10 이후 = trigger 감시 가능
```

미국장:

```text
09:30 ~ 09:45 ET = 매수 금지
09:45 이후 = trigger 감시 가능
```

현재가 감시는 5~30초 권장.

기본값:

```text
10초
```

API 제한이 있으면:

```text
30초
```

전일 고가 돌파 전략에서는 10분마다 현재가를 보면 트리거를 놓칠 수 있으므로 금지한다.

데스크톱 앱 화면이나 상태 리포트는 10분 주기로 갱신해도 된다.

예시 표시 항목:

```text
- 현재 감시 중인 종목 수
- trigger_price 근접 종목
- 갭상승 제외 종목
- 현재가와 trigger_price 차이
- 발생한 trigger_signal 목록
- 오늘 신규 매수 횟수
- 마지막 가격 조회 시각
- 마지막 상태 리포트 갱신 시각
```

---

## 5. 매수 가격 규칙

전일 고가 기준 돌파 매수 트리거:

```python
trigger_price = prev_high * 1.001
```

과도한 갭상승 제외 기준:

```python
gap_limit_price = prev_high * 1.03
```

조건:

```text
today_open > gap_limit_price 이면 해당 종목은 당일 매수 제외
```

시장가 매수는 기본 금지.

기본 주문 방식:

```text
지정가 매수
```

지정가 계산:

```python
limit_price = current_price * 1.001
```

또는 보수적으로:

```python
limit_price = trigger_price * 1.001
```

---

## 6. config.yaml 추가/수정 항목

```yaml
realtime:
  enabled: true

  entry_delay_minutes:
    KR: 10
    US: 15

  price_scan_interval_seconds: 10
  status_refresh_interval_minutes: 10
  rebuild_setup_intraday: false

setup:
  trigger_buffer_pct: 0.001
  gap_limit_pct: 0.03

order:
  mode: paper
  buy_order_type: limit
  limit_price_basis: current_price
  limit_price_buffer_pct: 0.001
  allow_market_order: false

risk:
  position_size_pct: 0.05
  max_positions: 10
  max_new_positions_per_day: 2
  stop_loss_pct: -0.03
  take_profit_pct: 0.07

manual_search:
  enabled: true
  default_market: KR
  latest_only: true
  max_results: 50

chat:
  enabled: true
  provider: mock
  mode: local
  model: mock
  allow_order_execution: false
  max_tool_calls: 3

agent_safety:
  block_real_order_tools: true
  require_user_confirmation_for_order: true
  hide_api_keys: true
  answer_as_condition_based_analysis: true
```

---

## 7. CSV 컬럼명 통일

유니버스 CSV 컬럼은 다음 기준으로 통일한다.

```text
symbol
name
market
rank
active
exchange
```

아래 컬럼명은 사용하지 않는다.

```text
ticker
corp_name
```

수정 예시:

```python
symbol = str(row["symbol"]).zfill(6)
name = row["name"]
```

OHLCV CSV도 `symbol` 기준으로 통일한다.

```text
date
symbol
open
high
low
close
volume
```

한국 종목코드는 반드시 6자리 문자열로 처리한다.

```python
df["symbol"] = df["symbol"].astype(str).str.zfill(6)
```

---

## 8. 추가/수정할 모듈

```text
src/trading/watchlist_builder.py
src/trading/realtime_scanner.py
src/trading/order_manager.py
src/trading/position_manager.py
src/trading/market_calendar.py
src/trading/notifier.py

src/search/manual_search.py
src/search/search_schema.py
src/search/query_parser.py

src/agent/chat_agent.py
src/agent/llm_client.py
src/agent/tools.py
src/agent/prompts.py
src/agent/memory.py
```

Streamlit 기반 `chat_ui.py`는 후순위다.

먼저 기존 데스크톱 앱 또는 `app.py`에 붙일 수 있도록 백엔드 함수를 만든다.

---

## 9. trading 모듈 요구사항

### 9.1 watchlist_builder.py

장마감 후 다음 거래일 감시 후보를 생성한다.

필수 기능:

```text
1. 유니버스 CSV 로드
2. OHLCV 데이터 로드
3. 종목별 전일 확정 row 기준 보조지표 계산
4. 캔들패턴 계산
5. trend_candidates 생성
6. setup_candidates 생성
7. trigger_price 계산
8. gap_limit_price 계산
9. stop_loss_price, take_profit_price 예비 계산
10. data/watchlist/setup_candidates_YYYY-MM-DD.csv 저장
```

출력 컬럼 예시:

```csv
setup_date,trade_date,market,symbol,name,pattern,prev_open,prev_high,prev_low,prev_close,prev_volume,ma20,ma60,ma20_slope,volume_ma20,trigger_price,gap_limit_price,stop_loss_price,take_profit_price,setup_signal
```

### 9.2 realtime_scanner.py

장중 실시간 현재가를 감시한다.

필수 기능:

```text
1. watchlist 파일 로드
2. 장 시작 후 entry_delay_minutes 동안 매수 금지
3. today_open 확인
4. today_open > gap_limit_price이면 당일 제외
5. current_price가 trigger_price 이상인지 확인
6. current_price가 gap_limit_price 이하인지 확인
7. 리스크 조건 확인
8. trigger_signal 생성
9. triggered_candidates_YYYY-MM-DD.csv 저장
10. realtime_status_YYYY-MM-DD.csv 저장
11. 콘솔 로그 또는 알림 전송
```

### 9.3 루프 분리

가격 감시 루프:

```python
while market_is_open:
    scan_realtime_prices()
    check_trigger_signals()
    sleep(config.realtime.price_scan_interval_seconds)
```

상태 리포트 갱신:

```python
if now - last_status_refresh >= status_refresh_interval:
    update_status_summary()
    last_status_refresh = now
```

중요:

```text
가격 감시 주기와 상태 리포트 주기를 같은 값으로 묶지 않는다.
```

### 9.4 entry delay 함수

```python
def is_entry_delay_passed(market: str, now) -> bool:
    """
    장 시작 후 매수 금지 시간이 지났는지 확인한다.

    KR:
      09:00 + 10분 이후 true

    US:
      09:30 ET + 15분 이후 true
    """
    pass
```

대기 시간이 지나기 전에는 가격 조건을 만족해도 trigger_signal을 생성하지 않는다.

entry delay 이전:

```text
- 현재가 조회 가능
- 로그 출력 가능
- trigger_signal 생성 금지
- 주문 금지
```

### 9.5 order_manager.py

초기에는 실주문이 아니라 `PaperOrderManager`만 구현한다.

```python
class OrderManagerBase:
    def buy(self, symbol, quantity, limit_price):
        raise NotImplementedError

    def sell(self, symbol, quantity, limit_price=None):
        raise NotImplementedError


class PaperOrderManager(OrderManagerBase):
    def buy(self, symbol, quantity, limit_price):
        # 실제 주문 없이 모의 체결 기록만 남긴다.
        pass
```

### 9.6 position_manager.py

보유 종목의 손절/익절을 관리한다.

```text
1. 보유 종목 로드
2. 실시간 현재가 기준 손절 여부 확인
3. 실시간 현재가 기준 익절 여부 확인
4. MA20 이탈 등 장마감 조건 확인
5. 매도 후보 생성
```

### 9.7 market_calendar.py

시장 시간과 휴장일을 처리한다.

```text
1. 한국장 정규장 시간 확인
2. 미국장 정규장 시간 확인
3. 장 시작 후 대기 시간 계산
4. 다음 거래일 계산
5. 휴장일이면 실행 중단
```

중요:

```text
다음 거래일은 달력상 다음날이 아니라 해당 시장의 실제 거래일 기준이어야 한다.
```

### 9.8 notifier.py

초기에는 콘솔 출력만 구현한다.

추후 확장:

```text
- Telegram
- Discord
- Email
```

---

## 10. search 모듈 요구사항

### 10.1 manual_search.py

LLM 없이 정확하게 조건 검색을 수행한다.

```python
def search_stocks(
    market=None,
    min_rank=None,
    max_rank=None,
    min_volume_ratio=None,
    close_above_ma20=None,
    ma20_above_ma60=None,
    patterns=None,
    latest_only=True,
):
    pass
```

예시 사용:

```python
search_stocks(
    market="KR",
    max_rank=80,
    min_volume_ratio=1.2,
    close_above_ma20=True,
    ma20_above_ma60=True,
    patterns=["bullish_engulfing"],
)
```

### 10.2 query_parser.py

자연어 또는 간단한 key=value 명령을 검색 필터 dict로 변환한다.

예시:

```text
"한국 종목 중 거래량 1.2배 이상이고 MA20 위에 있는 종목"
```

변환:

```python
{
  "market": "KR",
  "min_volume_ratio": 1.2,
  "close_above_ma20": True
}
```

처음에는 rule-based parser로 충분하다.

### 10.3 search_schema.py

검색 조건의 스키마 또는 dataclass를 정의한다.

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class SearchFilters:
    market: Optional[str] = None
    min_rank: Optional[int] = None
    max_rank: Optional[int] = None
    min_volume_ratio: Optional[float] = None
    close_above_ma20: Optional[bool] = None
    ma20_above_ma60: Optional[bool] = None
    patterns: Optional[List[str]] = None
    latest_only: bool = True
```

---

## 11. agent 모듈 요구사항

### 11.1 기본 원칙

Chat Agent는 사용자의 질문에 답하는 도구다.

LLM의 역할:

```text
- 질문 해석
- 필요한 내부 tool 선택
- tool 결과 요약
- 사람이 읽기 쉬운 설명 생성
```

실제 계산은 기존 Python 함수가 수행한다.

금지:

```text
- 실제 매수 주문
- 실제 매도 주문
- API 키 조회/출력
- 계좌번호 출력
- config에서 실거래 모드 변경
- 수익 보장 표현
```

### 11.2 llm_client.py

```python
class LLMClientBase:
    def generate(self, messages, tools=None):
        raise NotImplementedError


class MockLLMClient(LLMClientBase):
    def generate(self, messages, tools=None):
        # v1에서는 규칙 기반 또는 고정 응답으로 동작
        pass
```

추후 확장:

```python
class GemmaLLMClient(LLMClientBase):
    pass
```

### 11.3 tools.py

허용 도구:

```python
def get_setup_candidates():
    pass

def get_triggered_candidates():
    pass

def search_by_conditions(filters: dict):
    pass

def explain_stock_status(symbol: str):
    pass

def get_stock_latest_metrics(symbol: str):
    pass

def compare_strategy_conditions(symbol: str, relaxed: bool = False):
    pass

def get_trigger_price(symbol: str):
    pass

def summarize_backtest_result():
    pass
```

금지 도구:

```text
- 실제 매수
- 실제 매도
- 주문 모드 변경
- API 키 표시
```

### 11.4 chat_agent.py

사용자 질문을 받고 필요한 tool을 호출한 뒤 한국어 답변을 생성한다.

예시:

```text
사용자:
"SK하이닉스는 왜 후보에서 빠졌어?"

Agent:
→ explain_stock_status("000660") 호출

답변:
"SK하이닉스는 추세와 거래량은 통과했지만, 현재 전략에서 요구하는 매수 캔들패턴이 없어서 setup 후보에서는 제외됐습니다. 이 답변은 현재 로컬 데이터 기준입니다."
```

### 11.5 prompts.py

Agent 시스템 프롬프트를 정의한다.

필수 원칙:

```text
- 너는 투자 추천자가 아니라 조건 기반 자동매매 분석 보조자다.
- 수익 가능성을 단정하지 않는다.
- 종목 매수/매도 추천을 직접 하지 않는다.
- "추천"보다는 "조건 통과 후보"라고 표현한다.
- 답변은 현재 로컬 데이터 기준임을 명시한다.
- 불확실한 데이터는 불확실하다고 말한다.
- 실주문 도구를 호출하지 않는다.
```

### 11.6 memory.py

v1에서는 간단한 대화 기록만 저장한다.

저장 가능:

```text
- 최근 질문
- 최근 조회한 종목
- 최근 검색 조건
```

민감정보는 저장하지 않는다.

---

## 12. 데스크톱 앱 반영 방향

Streamlit UI는 후순위다.

먼저 기존 데스크톱 앱 또는 `app.py`에 아래 기능을 붙일 수 있게 백엔드 함수를 만든다.

권장 탭:

```text
[자동매매 대시보드]
[수동 검색]
[Chat Agent]
[후보/감시목록]
[로그]
[설정]
```

### 수동 검색 탭 표시 항목

```text
시장 선택: KR / US / ALL
rank 범위
거래량 배수
MA 조건 체크
캔들패턴 체크
검색 버튼
결과 테이블
```

### Chat Agent 탭 표시 항목

```text
질문 입력창
답변 출력창
관련 종목 테이블
도구 호출 로그
```

질문 예시:

```text
SK하이닉스 왜 후보에서 빠졌어?
거래량 조건을 1.0으로 낮추면 몇 개 나와?
오늘 setup 후보 보여줘
현대모비스 트리거 가격 알려줘
```

---

## 13. 결과 파일 분리

```text
data/results/trend_candidates_YYYY-MM-DD.csv
data/watchlist/setup_candidates_YYYY-MM-DD.csv
data/results/triggered_candidates_YYYY-MM-DD.csv
data/logs/realtime_status_YYYY-MM-DD.csv
```

의미:

```text
trend_candidates:
추세 + 거래량 조건만 통과

setup_candidates:
전일 확정 캔들 + 추세 + 거래량 조건 통과
다음 거래일 감시 대상

triggered_candidates:
장중 가격 트리거까지 발생한 실제 매수 후보

realtime_status:
실시간 감시 상태 요약 로그
```

---

## 14. 기존 automation.py 수정 방향

현재 `automation.py`에서 최신 row 기준으로 바로 추천 후보를 만드는 구조는 유지하되, 역할을 분리한다.

```text
1. filter_trending_stocks 함수는 trend_candidates 생성용으로 유지한다.
2. 최종 매수 추천이라는 표현을 제거한다.
3. setup_signal 생성 함수 추가:
   - 추세 조건
   - 거래량 조건
   - 매수 캔들패턴 조건
4. trigger_signal은 realtime_scanner.py에서 처리한다.
```

함수명 제안:

```python
def filter_trending_stocks(...):
    """추세 + 거래량 조건 통과 후보를 반환한다. 최종 매수 후보가 아니다."""
    pass


def build_setup_candidates(...):
    """전일 확정 일봉 기준 다음 거래일 감시 후보를 생성한다."""
    pass


def build_trigger_candidates(...):
    """장중 실시간 현재가 기준 실제 매수 트리거 후보를 생성한다."""
    pass
```

---

## 15. 구현할 함수 제안

```python
def load_today_watchlist(trade_date: str):
    """오늘 감시할 setup_candidates/watchlist를 로드한다."""
    pass


def calculate_trigger_prices(df):
    """prev_high 기준 trigger_price와 gap_limit_price를 계산한다."""
    pass


def is_entry_delay_passed(market: str, now):
    """장 시작 후 매수 금지 시간이 지났는지 확인한다."""
    pass


def scan_realtime_prices(watchlist):
    """watchlist 종목들의 현재가를 조회한다."""
    pass


def evaluate_trigger_signal(row, current_price, today_open, now):
    """장중 현재가 기준 trigger_signal 여부를 판단한다."""
    pass


def update_realtime_status(watchlist_status):
    """데스크톱 앱/로그용 상태 요약을 갱신한다."""
    pass
```

---

## 16. 안전 원칙

```text
1. 캔들패턴은 전일 확정 일봉으로만 판단한다.
2. 장중에는 오늘 캔들패턴을 확정 신호로 사용하지 않는다.
3. 장중에는 setup 후보를 재계산하지 않는다.
4. 현재가 감시는 5~30초 주기로 한다.
5. 현재가 감시를 10분 주기로 하지 않는다.
6. 10분은 장 시작 후 매수 금지 시간 또는 상태 리포트 갱신 주기로만 사용한다.
7. v1에서는 실주문하지 않고 paper/log/알림만 수행한다.
8. 시장가 주문은 기본적으로 금지한다.
9. Chat Agent가 주문 함수를 직접 호출하지 못하게 한다.
10. Chat Agent는 “추천”이라는 표현보다 “조건 통과 후보”라고 답한다.
11. 수익 가능성을 단정하지 않는다.
12. API 키, 계좌번호, 토큰 등 민감정보를 출력하지 않는다.
13. 모든 답변은 현재 로컬 데이터 기준임을 명시한다.
```

---

## 17. 최종 작업 요청

```text
1. config.yaml에 realtime, setup, order, risk, manual_search, chat, agent_safety 설정을 추가/수정한다.
2. CSV 컬럼명을 symbol/name 기준으로 통일하고 ticker/corp_name 사용을 제거한다.
3. 한국 종목코드는 반드시 6자리 문자열로 zfill(6) 처리한다.
4. automation.py에서 filter_trending_stocks는 trend_candidates용으로 역할을 명확히 한다.
5. build_setup_candidates 함수를 추가한다.
6. watchlist_builder.py를 추가하여 장마감 후 setup_candidates를 생성한다.
7. realtime_scanner.py를 추가/수정하여 장중 현재가 감시와 trigger_signal 생성을 구현한다.
8. price_scan_interval_seconds와 status_refresh_interval_minutes를 분리한다.
9. entry_delay_minutes를 시장별로 적용한다.
10. 장중에는 setup 후보를 재계산하지 않고 watchlist에서 로드한다.
11. trigger_price = prev_high * 1.001을 적용한다.
12. gap_limit_price = prev_high * 1.03을 적용한다.
13. today_open > gap_limit_price이면 해당 종목은 당일 매수 제외한다.
14. current_price >= trigger_price이고 current_price <= gap_limit_price일 때만 trigger_signal을 생성한다.
15. triggered_candidates와 realtime_status를 별도 파일로 저장한다.
16. order_manager.py에 PaperOrderManager를 구현하고 실주문은 하지 않는다.
17. market_calendar.py에 시장 시간/장 시작 후 대기 시간/다음 거래일 계산 구조를 만든다.
18. notifier.py는 v1에서 콘솔 출력만 구현한다.
19. manual_search.py, search_schema.py, query_parser.py를 추가하여 수동 검색 기능을 구현한다.
20. agent/tools.py에 내부 조회 도구를 구현한다.
21. llm_client.py에 LLMClientBase와 MockLLMClient를 구현한다.
22. chat_agent.py에 RuleBased 또는 Mock 기반 Chat Agent를 구현한다.
23. prompts.py에 안전한 시스템 프롬프트를 정의한다.
24. memory.py는 간단한 대화 기록만 저장하고 민감정보는 저장하지 않는다.
25. Streamlit chat_ui.py는 후순위로 미루고, 기존 데스크톱 앱/app.py에서 호출 가능한 백엔드 함수 중심으로 구현한다.
26. 데스크톱 앱에서 setup 후보, trigger 근접 상태, entry delay 상태, 수동 검색 결과, Chat Agent 답변을 표시할 수 있도록 함수 인터페이스를 준비한다.
```

---

## 18. 완료 기준

```text
1. 장마감 후 setup_candidates 파일 생성 가능
2. 장중 watchlist 로드 가능
3. 장 시작 후 10분 전에는 trigger_signal 생성 금지
4. 10초 단위 현재가 감시 가능
5. 10분 단위 상태 리포트 갱신 가능
6. trigger_price/gap_limit_price 기준으로 triggered_candidates 생성 가능
7. 실주문 없이 PaperOrderManager로 모의 주문 기록 가능
8. 수동 조건 검색 가능
9. "SK하이닉스 왜 후보에서 빠졌어?" 같은 질문에 Chat Agent가 내부 데이터 기준으로 답변 가능
10. Chat Agent가 실제 주문 함수를 호출하지 않음
```
