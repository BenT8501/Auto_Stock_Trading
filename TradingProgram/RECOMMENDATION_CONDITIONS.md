# 종가 기준 후보 검색 조건 및 파일 경로

## Context

- 원본 기획 문서: `C:\GitHub\WrokSpace\Auto_Stock_Trading\vscode_agent_context_auto_trading.md`
- 실제 프로그램 경로: `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram`

## 후보 실행 경로

- UI 버튼:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\app.py`
  - 함수: `render_recommendation_tab`
  - 버튼명: `저장된 데이터로 추천 분석 실행`

- 추천 로직:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\trading\automation.py`
  - 함수: `run_recommendation_cycle`

- 신호 생성:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\signals.py`
  - 함수: `add_signals`

- 캔들패턴 계산:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\patterns.py`
  - 함수: `add_patterns`

- 지표 계산:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\indicators.py`
  - 함수: `add_indicators`

- 설정 파일:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\config.yaml`

## 분석 대상 파일

- 국내 유니버스:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\data\universe\kr_top80.csv`

- 미국 유니버스:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\data\universe\us_top100.csv`

- 분석용 OHLCV 데이터:
  - `C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\data\processed\universe_ohlcv.csv`

## 현재 시장 스캔 설정

`config.yaml` 기준:

```yaml
automation:
  scan_us: true
  scan_kr: true
  max_scan_us: 100
  max_scan_kr: 80
```

따라서 현재 구조는 국내만 검색하는 것이 아니라, 국내와 미국을 모두 검색한다.

다만 현재 저장된 OHLCV 데이터의 최신 row 기준으로는 미국 종목 중 추천 조건을 통과한 종목이 없어서 국내 종목만 표시된 상태다.

## 데이터 갱신 스케줄

저장 데이터 기반 후보는 실시간 매수 신호가 아니라 장마감 후 종가 기준 후보이다.

스케줄 설정:

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\config.yaml
```

스케줄 계산:

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\market_schedule.py
```

스케줄 실행:

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\scheduled_data_refresh.py
```

현재 기본값:

```yaml
schedule:
  timezone: Asia/Seoul
  refresh:
    KR:
      enabled: true
      local_time: "15:50"
    US:
      enabled: true
      market_timezone: America/New_York
      market_close_time: "16:00"
      buffer_minutes_after_close: 15
```

의미:

- 한국: 정규장 마감 후 15:50 KST에 갱신
- 미국: 뉴욕 정규장 16:00 ET 마감 후 15분 뒤 갱신
  - 미국 서머타임 기간: 한국시간 다음날 05:15
  - 미국 표준시간 기간: 한국시간 다음날 06:15

실행 명령:

```powershell
python scheduled_data_refresh.py
```

다음 실행 시간 확인:

```powershell
python scheduled_data_refresh.py --dry-run
```

즉시 1회 갱신:

```powershell
python scheduled_data_refresh.py --once
```

## 장중 실시간 돌파 감시

종가 기준 후보는 즉시 매수 신호가 아니라 다음 거래일 감시 대상이다.

장중에는 KIS 현재가 API로 후보 종목의 전일 고가 돌파 여부만 감시한다.

설정:

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\config.yaml
```

현재 기본값:

```yaml
realtime_monitor:
  enabled: false
  interval_minutes: 10
  breakout_buffer_pct: 0.001
  manual_approval_required: true
  max_candidates_per_cycle: 20
```

실행 파일:

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\realtime_breakout_monitor.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\realtime_breakout_monitor.bat
```

감시 조건:

```text
현재가 >= 후보 발생일 high * (1 + breakout_buffer_pct)
```

기본값 기준:

```text
현재가 >= 후보 발생일 high * 1.001
```

돌파가 감지되면 실주문을 보내지 않고 수동 승인 대기열에 주문 후보만 추가한다.

실행 명령:

```powershell
python realtime_breakout_monitor.py
```

후보 목록만 확인:

```powershell
python realtime_breakout_monitor.py --dry-run
```

1회만 감시:

```powershell
python realtime_breakout_monitor.py --once
```

주의:

- `--once`와 일반 실행은 KIS 현재가 API를 호출한다.
- `.env`에 KIS API 키가 있어야 한다.
- 실주문은 전송하지 않는다.
- 10분 주기는 노트북/API 부담과 돌파 감시 속도의 균형을 위한 기본값이다.

## setup_signal과 trigger_signal 분리

현재 구조는 두 단계로 분리된다.

```text
setup_signal:
  장마감 후 다음 거래일에 감시할 후보

trigger_signal:
  장중 현재가가 setup 후보의 trigger_price를 돌파했을 때 발생하는 실행 후보
```

setup 조건:

```text
close > MA20
MA20 > MA60
MA20 slope > 0
volume > volume_MA20 * 1.2
buy pattern 발생
```

trigger 조건:

```text
current_price >= previous_high * 1.001
open_price <= previous_high * 1.03
```

최종 자동매수 후보로 의미가 있는 것은 `triggered_candidates.csv`에 기록된 항목뿐이다.

## 후보 항목 생성 흐름

```text
KR/US 유니버스 CSV 로드
  -> active=true 종목만 선택
  -> rank 기준 상위 종목 선택
  -> universe_ohlcv.csv 로드
  -> 유니버스에 포함된 종목만 필터링
  -> 이동평균/거래량 평균 계산
  -> 캔들패턴 계산
  -> setup_signal 계산
  -> 종목별 최신 날짜 row만 선택
  -> setup_signal=True인 종목을 다음 거래일 watchlist로 저장
  -> 장중 realtime_scanner가 trigger_signal 감시
```

## 실제 setup 후보 조건

각 종목의 최신 일봉 row에서 아래 조건을 모두 통과해야 추천된다.

### 1. 유니버스 포함 조건

- `kr_top80.csv` 또는 `us_top100.csv`에 포함
- `active=true`
- rank 기준 상위 제한 적용
  - 국내: 최대 80개
  - 미국: 최대 100개

관련 파일:

```text
src/trading/automation.py
```

관련 함수:

```python
load_recommendation_universe(config, market)
```

## 2. 매수 캔들패턴 조건

아래 3개 중 하나가 true여야 한다.

```yaml
buy_patterns:
  - hammer
  - bullish_engulfing
  - morning_star
```

관련 파일:

```text
src/patterns.py
```

패턴 함수:

```python
detect_hammer(df)
detect_bullish_engulfing(df)
detect_morning_star(df)
```

## 3. 추세 조건

현재 코드 기준:

```python
trend_ok = (close > ma_long) and (ma_short_slope > 0)
```

pandas 코드에서는 실제로 아래처럼 계산된다.

```python
trend_ok = (result["close"] > result["ma_long"]) & (result["ma_short_slope"] > 0)
```

의미:

- 종가가 장기 이동평균 위에 있어야 함
- 단기 이동평균 기울기가 양수여야 함

주의:

- 원래 기획 문서에는 `close > MA20` 및 `MA20 > MA60` 조건이 있었다.
- 현재 실제 코드는 `close > MA60` 및 `MA20 slope > 0` 조건이다.
- 즉, 기획 문서와 실제 코드 조건이 완전히 동일하지 않다.

관련 파일:

```text
src/signals.py
```

## 4. 거래량 조건

현재 코드 기준:

```python
volume_ok = volume >= volume_ma * multiplier
```

현재 설정:

```yaml
volume:
  window: 20
  multiplier: 1.0
```

의미:

- 당일 거래량이 20일 평균 거래량 이상이어야 함

주의:

- 원래 기획 문서에는 `volume > volume_MA20 * 1.2` 조건이 있었다.
- 현재 설정은 `1.0`이므로 문서보다 완화되어 있다.

관련 파일:

```text
src/signals.py
config.yaml
```

## 5. 최근 데이터 조건

현재 설정:

```yaml
data_window:
  buy_signal_recent_days: 90
```

의미:

- 각 종목의 최신 날짜 기준 최근 90일 안의 row만 매수 신호 계산에 포함한다.
- 최종 추천은 그중에서도 각 종목의 최신 row만 사용한다.

관련 파일:

```text
src/signals.py
src/trading/automation.py
```

## 6. 최종 setup 후보 생성 조건

종목별 최신 row에서:

```python
setup_signal == True
```

이면 다음 거래일 watchlist 후보를 생성한다.

관련 파일:

```text
src/trading/automation.py
```

관련 코드 개념:

```python
latest_rows = prepared.sort_values("date").groupby("symbol", as_index=False).tail(1)
```

그리고:

```python
if not bool(row.get("setup_signal", False)):
    continue
```

## 출력 파일 분리

장마감 후 `watchlist_builder.py` 실행 결과:

```text
data/results/trend_candidates_YYYY-MM-DD.csv
data/watchlist/setup_candidates_YYYY-MM-DD.csv
data/watchlist/watchlist_YYYY-MM-DD.csv
```

장중 `realtime_scanner.py` 실행 결과:

```text
data/results/triggered_candidates_YYYY-MM-DD.csv
```

역할:

```text
trend_candidates.csv:
  추세/거래량 필터를 통과한 종목

setup_candidates.csv:
  추세/거래량/캔들패턴까지 통과해 다음 거래일 감시 대상이 된 종목

triggered_candidates.csv:
  장중 현재가가 trigger_price를 돌파하고 gap 조건도 통과한 종목
```

buy_order:

```text
v1에서는 실주문하지 않는다.
triggered_candidates 기준으로 콘솔/텔레그램 알림과 PaperOrderManager 모의 주문 기록만 생성한다.
시장가 주문은 금지하고 지정가 주문 가격만 계산한다.
```

## 현재 추천 결과 해석

최근 실행 결과:

```text
total 2
KR 2
US 0
```

추천된 종목:

```text
KR 036570 NC
KR 012330 현대모비스
```

추천 사유:

```text
buy_signal=bullish_engulfing
close>MA trend and volume filter passed
```

해석:

- 국내만 검색한 것이 아니다.
- 국내와 미국을 모두 검색했다.
- 현재 데이터와 조건 기준으로는 미국 종목 중 최종 추천 조건을 통과한 종목이 0개다.
- 국내 종목 2개만 조건을 통과했다.

## 현재 조건의 문제점

### 1. 기획 문서와 실제 코드 조건이 다르다

기획 문서:

```text
close > MA20
MA20 > MA60
MA20 기울기 > 0
volume > volume_MA20 * 1.2
```

현재 코드:

```text
close > MA60
MA20 기울기 > 0
volume >= volume_MA20 * 1.0
```

즉, `MA20 > MA60` 조건이 빠져 있고, 거래량 조건도 더 완화되어 있다.

### 2. 추천은 최신 row 하나만 본다

과거 90일 안에 신호가 있었더라도 최신 row의 `buy_signal`이 false이면 추천되지 않는다.

### 3. 미국 종목이 없는 이유는 시장 제외가 아니라 조건 미통과다

확인 결과, 분석용 OHLCV 파일에는 미국 유니버스 100개 종목이 포함되어 있다.

따라서 미국 추천이 0개인 이유는:

```text
미국 데이터 없음
```

이 아니라:

```text
미국 종목 중 최신 row에서 buy_signal=True인 종목 없음
```

이다.
