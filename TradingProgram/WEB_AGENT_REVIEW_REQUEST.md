# 웹 에이전트 검수 요청서

## 검수 목적

아래 로컬 프로젝트의 추천 항목 생성 조건과 데이터/시장 전제를 웹 자료 기준으로 검수해주세요.

목표는 투자 추천을 받는 것이 아니라, 자동매매/백테스트 프로그램의 전제와 구현 조건이 현실 시장 기준으로 타당한지 확인하는 것입니다.

## 프로젝트 경로

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram
```

## 함께 검토할 문서

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\RECOMMENDATION_CONDITIONS.md
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\STRUCTURE_DESIGN.md
C:\GitHub\WrokSpace\Auto_Stock_Trading\vscode_agent_context_auto_trading.md
```

## 주요 코드 파일

```text
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\app.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\config.yaml
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\trading\automation.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\signals.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\patterns.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\indicators.py
C:\GitHub\WrokSpace\Auto_Stock_Trading\TradingProgram\src\external_data_collector.py
```

## 현재 추천 로직 요약

추천 항목은 웹 검색이나 뉴스 검색이 아니라, 저장된 OHLCV 데이터 기준으로 계산됩니다.

현재 흐름:

```text
KR/US 유니버스 CSV 로드
  -> active=true 종목만 선택
  -> rank 기준 상위 종목 선택
  -> universe_ohlcv.csv 로드
  -> 유니버스에 포함된 종목만 필터링
  -> 이동평균/거래량 평균 계산
  -> 캔들패턴 계산
  -> 매수 신호 계산
  -> 종목별 최신 날짜 row만 선택
  -> buy_signal=True인 종목만 추천 주문 후보 생성
```

현재 설정:

```yaml
automation:
  scan_us: true
  scan_kr: true
  max_scan_us: 100
  max_scan_kr: 80

strategy:
  volume:
    window: 20
    multiplier: 1.0
  buy_patterns:
    - hammer
    - bullish_engulfing
    - morning_star
```

현재 코드상 매수 조건:

```text
1. KR 또는 US 유니버스에 포함
2. active=true
3. 최신 row에서 매수 캔들패턴 발생
4. close > ma_long
5. ma_short_slope > 0
6. volume >= volume_ma * 1.0
7. 각 종목의 최신 row에서 buy_signal=True
```

최근 실행 결과:

```text
total 2
KR 2
US 0
```

국내만 검색한 것이 아니라, 미국도 검색했지만 현재 조건 통과 종목이 0개인 상태입니다.

## 웹 검수 요청 항목

### 1. 데이터 소스 검수

아래 전제가 맞는지 최신 공식/신뢰 자료 기준으로 확인해주세요.

- 미국 OHLCV 수집에 `yfinance`를 쓰는 것이 백테스트용으로 어느 정도 허용 가능한가?
- `yfinance`가 실시간/운영용 데이터 소스로 적합하지 않다는 판단이 맞는가?
- 한국 OHLCV 수집에 `pykrx`를 쓰는 것이 백테스트용으로 타당한가?
- yfinance/pykrx 데이터에서 수정주가, 배당, 액면분할, 거래정지, 상장폐지 이슈를 어떻게 다뤄야 하는가?

필요하면 공식 문서 또는 신뢰 가능한 출처 링크를 포함해주세요.

### 2. 시장 시간/휴장일 전제 검수

다음 전제가 최신 기준으로 맞는지 확인해주세요.

- 미국 정규장 시간: 09:30~16:00 ET
- 한국 정규장 시간: 09:00~15:30 KST
- 한국/미국 휴장일 차이를 별도 처리해야 한다는 전제
- 일봉 백테스트에서 "다음 거래일"은 달력상 다음날이 아니라 해당 종목 데이터의 다음 row로 처리해야 한다는 전제

### 3. 수수료/세금/슬리피지 검수

현재 config에는 아래 placeholder가 들어 있습니다.

```yaml
costs:
  US:
    buy_fee_pct: 0.001
    sell_fee_pct: 0.001
    sell_tax_pct: 0.0
    slippage_pct: 0.001
  KR:
    buy_fee_pct: 0.00015
    sell_fee_pct: 0.00015
    sell_tax_pct: 0.0015
    slippage_pct: 0.001
```

검수 요청:

- 2026년 현재 한국 주식 거래세/농특세/수수료 전제가 맞는지 확인해주세요.
- 미국 주식 거래비용, SEC fee, TAF fee 등 매도 시 비용을 고려해야 하는지 확인해주세요.
- 백테스트 v1부터 거래비용을 반영해야 한다는 판단이 타당한지 검토해주세요.
- 단기 캔들 전략에서 슬리피지 0.1% 기본값이 과한지/부족한지 의견을 주세요.

### 4. 전략 조건 검수

현재 코드 조건:

```text
close > MA60
MA20 slope > 0
volume >= volume_MA20 * 1.0
buy pattern in [hammer, bullish_engulfing, morning_star]
```

원래 기획 문서 조건:

```text
close > MA20
MA20 > MA60
MA20 slope > 0
volume > volume_MA20 * 1.2
```

검수 요청:

- 현재 코드 조건과 기획 문서 조건 중 어느 쪽이 더 일관적인 추세 필터인지 평가해주세요.
- `MA20 > MA60` 조건이 빠진 것이 전략 의미를 약화시키는지 검토해주세요.
- 거래량 multiplier를 `1.0`으로 둔 것이 너무 완화된 조건인지 평가해주세요.
- 캔들패턴 3개가 실전적으로 유의미한지, 아니면 널리 알려져 알파가 약할 가능성이 높은지 검토해주세요.

### 5. 백테스트 체결 가정 검수

아래 전제가 타당한지 검토해주세요.

- 신호 발생 당일에는 매수하지 않음
- 다음 거래일 전일 고가 돌파 시 매수 체결로 가정
- 갭상승이 과하면 매수 제외
- 일봉 데이터에서 손절가와 익절가가 같은 날 모두 닿으면 보수적으로 손절 우선 처리
- 실거래 전에는 반드시 페이퍼 트레이딩 단계를 거침

### 6. 유니버스/생존편향 검수

현재 유니버스:

```text
US: S&P 500 상위 100개 수동 CSV
KR: KOSPI200/KODEX200 상위 80개 수동 CSV
```

검수 요청:

- 현재 시점의 상위 종목 리스트로 과거 백테스트를 돌리면 생존편향이 생긴다는 판단이 맞는지 확인해주세요.
- 생존편향을 줄이기 위한 현실적인 데이터 대안을 제안해주세요.
- Phase 1에서는 생존편향을 문서에 명시하고 제한적 검증으로 진행해도 되는지 평가해주세요.

## 원하는 출력 형식

아래 형식으로 답해주세요.

```markdown
# 검수 결과

## 결론

- 통과:
- 수정 필요:
- 위험:

## 항목별 검토

### 1. 데이터 소스

판단:

근거:

수정 제안:

### 2. 시장 시간/휴장일

판단:

근거:

수정 제안:

### 3. 수수료/세금/슬리피지

판단:

근거:

수정 제안:

### 4. 전략 조건

판단:

근거:

수정 제안:

### 5. 체결 가정

판단:

근거:

수정 제안:

### 6. 유니버스/생존편향

판단:

근거:

수정 제안:

## 우선 수정해야 할 Top 5

1.
2.
3.
4.
5.

## 참고 링크

-
```

## 주의사항

- 투자 종목 추천을 하지 마세요.
- 수익 가능성을 단정하지 마세요.
- 최신 규정/수수료/세금은 반드시 웹 자료로 확인해주세요.
- 공식 출처가 있으면 공식 출처를 우선 사용해주세요.
- 불확실한 내용은 추정이라고 명확히 표시해주세요.

