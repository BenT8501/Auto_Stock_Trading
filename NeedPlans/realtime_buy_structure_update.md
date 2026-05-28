# 실시간 매수 구조 반영 요청서

## 목적

현재 자동매매 시스템은 최신 일봉 row 기준으로 `buy_signal=True` 종목을 추천하는 구조다.  
하지만 실제 매매에서는 일봉 캔들이 장중에 계속 변하고, 캔들패턴은 장마감 후에야 확정된다.

따라서 기존 구조를 다음과 같이 변경한다.

```text
전일 장마감 후 확정 데이터 분석 = setup_signal
다음 거래일 장중 현재가 감시 = trigger_signal
조건 충족 시 주문 실행 또는 알림 = buy_order
```

즉, **오늘 장중 캔들패턴을 실시간으로 확정 신호로 사용하지 않는다.**  
캔들패턴은 반드시 **전일 종가 기준 확정 일봉**으로만 판단한다.

---

## 핵심 원칙

### 1. 캔들패턴은 전일 확정 일봉 기준

다음 3개 매수 캔들패턴은 장마감 후 확정된 일봉에서만 판단한다.

```text
- Hammer
- Bullish Engulfing
- Morning Star
```

장중에는 오늘 일봉이 계속 바뀌므로 오늘 캔들패턴을 확정 신호로 사용하지 않는다.

---

### 2. 실시간 매수는 오늘 캔들패턴이 아니라 가격 트리거를 본다

장중 실시간으로 감시할 것은 아래 항목이다.

```text
- 현재가
- 오늘 시가
- 전일 고가 돌파 여부
- 갭상승 과열 여부
- 보유 여부
- 현금/포지션 제한
- 체결 여부
```

---

## 신호 정의 변경

### setup_signal

`setup_signal`은 전일 장마감 후 생성되는 감시 후보 신호다.

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

---

### trigger_signal

`trigger_signal`은 다음 거래일 장중 실시간 가격이 매수 트리거에 도달했을 때 발생한다.

조건:

```text
1. setup_signal = true인 종목
2. 장 시작 후 대기 시간이 지남
3. today_open <= prev_high * 1.03
4. current_price >= prev_high * 1.001
5. current_price <= prev_high * 1.03
6. 이미 보유 중인 종목이 아님
7. 일일 신규 매수 제한 초과 아님
8. 최대 보유 종목 수 초과 아님
9. 현금 충분
```

의미:

```text
실제 매수 타이밍 발생
```

---

### buy_order

`buy_order`는 trigger_signal 발생 후 실제 주문 단계다.

초기 버전에서는 바로 실주문하지 않는다.

v1 우선순위:

```text
1. 콘솔 로그 출력
2. CSV 저장
3. 텔레그램 알림
4. PaperOrderManager로 모의 주문
5. 충분히 검증 후 실거래 API 연결
```

---

## 매수 가격 규칙

### trigger_price

전일 고가를 기준으로 매수 트리거 가격을 계산한다.

```python
trigger_price = prev_high * 1.001
```

예시:

```text
전일 고가: 100,000
매수 트리거: 100,100
```

---

### gap_limit_price

과도한 갭상승은 추격매수 위험이 크므로 제외한다.

```python
gap_limit_price = prev_high * 1.03
```

조건:

```text
today_open > gap_limit_price 이면 해당 종목은 당일 매수 제외
```

예시:

```text
전일 고가: 100,000
갭상승 제외 기준: 103,000

오늘 시가 104,000 → 매수 제외
오늘 시가 101,000 → 감시 유지
```

---

## 장 시작 직후 매수 금지

장 초반에는 가격 변동성과 스프레드가 커질 수 있으므로 일정 시간 동안 매수하지 않는다.

기본값:

```yaml
realtime:
  entry_delay_minutes:
    KR: 10
    US: 15
```

적용:

```text
한국장: 09:00~09:10 매수 금지, 09:10 이후 감시
미국장: 09:30~09:45 ET 매수 금지, 09:45 이후 감시
```

---

## 주문 방식

시장가 매수는 기본적으로 사용하지 않는다.

기본 주문 방식:

```text
지정가 매수
```

지정가 계산:

```python
limit_price = current_price * 1.001
```

또는 더 보수적으로:

```python
limit_price = trigger_price * 1.001
```

초기 구현에서는 config에서 선택 가능하게 한다.

```yaml
order:
  buy_order_type: limit
  limit_price_basis: current_price
  limit_price_buffer_pct: 0.001
```

---

## 포지션 사이징

초기 실험에서는 종목당 자산 비중을 낮게 잡는다.

기본값:

```yaml
risk:
  position_size_pct: 0.05
  max_positions: 10
  max_new_positions_per_day: 2
```

수량 계산:

```python
buy_amount = total_equity * position_size_pct
quantity = int(buy_amount // limit_price)
```

수량이 0이면 주문하지 않는다.

---

## 손절/익절 기본값

매수 체결 후 즉시 관리 대상에 등록한다.

기본값:

```yaml
risk:
  stop_loss_pct: -0.03
  take_profit_pct: 0.07
```

계산:

```python
stop_loss_price = entry_price * (1 + stop_loss_pct)
take_profit_price = entry_price * (1 + take_profit_pct)
```

---

## 새로 추가할 파일

아래 파일을 추가한다.

```text
src/trading/watchlist_builder.py
src/trading/realtime_scanner.py
src/trading/order_manager.py
src/trading/position_manager.py
src/trading/market_calendar.py
src/trading/notifier.py
```

---

## watchlist_builder.py 역할

장마감 후 다음 거래일 감시 후보를 생성한다.

필수 기능:

```text
1. 유니버스 CSV 로드
2. OHLCV 데이터 로드
3. 종목별 전일 확정 row 기준 보조지표 계산
4. 캔들패턴 계산
5. setup_signal 생성
6. trigger_price 계산
7. gap_limit_price 계산
8. stop_loss_price, take_profit_price 예비 계산
9. data/watchlist/watchlist_YYYY-MM-DD.csv 저장
```

출력 컬럼 예시:

```csv
setup_date,trade_date,market,symbol,name,pattern,prev_open,prev_high,prev_low,prev_close,prev_volume,ma20,ma60,ma20_slope,volume_ma20,trigger_price,gap_limit_price,stop_loss_price,take_profit_price,setup_signal
```

주의:

```text
setup_date = 전일 신호 발생일
trade_date = 다음 거래일, 실시간 감시 대상일
```

---

## realtime_scanner.py 역할

장중 실시간 현재가를 감시한다.

필수 기능:

```text
1. watchlist 파일 로드
2. 장 시작 후 entry_delay_minutes 동안 매수 금지
3. today_open 확인
4. gap_limit_price 초과 시 제외
5. current_price가 trigger_price 이상인지 확인
6. current_price가 gap_limit_price 이하인지 확인
7. 리스크 조건 확인
8. trigger_signal 생성
9. triggered_candidates.csv 저장
10. 콘솔 로그 또는 텔레그램 알림 전송
```

초기 버전에서는 실제 API 주문을 넣지 않는다.

---

## order_manager.py 역할

주문 실행 인터페이스를 정의한다.

초기에는 실주문이 아니라 PaperOrderManager만 구현한다.

예시:

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

---

## position_manager.py 역할

보유 종목의 손절/익절을 관리한다.

필수 기능:

```text
1. 보유 종목 로드
2. 실시간 현재가 기준 손절 여부 확인
3. 실시간 현재가 기준 익절 여부 확인
4. MA20 이탈 등 장마감 조건 확인
5. 매도 후보 생성
```

---

## market_calendar.py 역할

시장 시간과 휴장일을 처리한다.

필수 기능:

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

---

## notifier.py 역할

알림을 담당한다.

초기에는 콘솔 출력만 구현해도 된다.

추후 확장:

```text
- Telegram
- Discord
- Email
```

알림 예시:

```text
[매수 트리거 발생]
종목: 012330 현대모비스
현재가: 713,000
트리거: 712,712
전일 고가: 712,000
패턴: bullish_engulfing
주문 방식: 지정가
```

---

## config.yaml 추가 항목

아래 설정을 추가한다.

```yaml
realtime:
  enabled: false
  entry_delay_minutes:
    KR: 10
    US: 15
  scan_interval_seconds: 5

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
```

---

## 기존 automation.py 수정 방향

현재 `automation.py`에서 최신 row 기준으로 바로 추천 후보를 만드는 구조는 유지하되, 역할을 분리한다.

수정 방향:

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

## CSV 컬럼명 주의

현재 유니버스 CSV 컬럼은 다음 기준으로 통일한다.

```text
symbol
name
market
rank
active
exchange
```

따라서 코드에서 아래 컬럼명을 사용하지 않는다.

```text
ticker
corp_name
```

수정:

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

## 결과 파일 분리

후보 결과는 아래처럼 분리해서 저장한다.

```text
data/results/trend_candidates_YYYY-MM-DD.csv
data/watchlist/setup_candidates_YYYY-MM-DD.csv
data/results/triggered_candidates_YYYY-MM-DD.csv
```

의미:

```text
trend_candidates:
추세 + 거래량 조건만 통과

setup_candidates:
전일 확정 캔들패턴 + 추세 + 거래량 조건 통과
다음 거래일 감시 대상

triggered_candidates:
장중 가격 트리거까지 발생한 실제 매수 후보
```

---

## 최종 개발 요청

아래 요구사항을 반영해 코드를 수정해줘.

```text
1. 캔들패턴은 전일 종가 기준 확정 일봉으로만 판단한다.
2. 최신 row에서 바로 buy_signal을 추천하지 말고 setup_signal로 분리한다.
3. setup_signal은 다음 거래일 감시 후보로 저장한다.
4. 장중 실시간 현재가 기준 trigger_signal 구조를 추가한다.
5. 장 시작 직후 10분은 한국장 매수 금지한다.
6. 전일 고가 * 1.001을 trigger_price로 사용한다.
7. 전일 고가 * 1.03을 gap_limit_price로 사용한다.
8. today_open > gap_limit_price이면 해당 종목은 당일 매수 제외한다.
9. 시장가 매수는 금지하고 지정가 매수를 기본으로 한다.
10. v1에서는 실주문하지 말고 PaperOrderManager와 알림까지만 구현한다.
11. trend_candidates, setup_candidates, triggered_candidates 결과를 분리 저장한다.
12. CSV 컬럼명은 symbol/name 기준으로 통일하고 ticker/corp_name 사용을 제거한다.
```

---

## 중요한 해석

최종 자동매수 후보는 `setup_candidates`가 아니다.

```text
setup_candidates = 내일 감시할 후보
triggered_candidates = 실제 장중 매수 트리거 발생 후보
```

실제 주문 또는 알림은 `triggered_candidates` 기준으로만 수행한다.
