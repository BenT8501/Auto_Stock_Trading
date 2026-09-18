# Candidate Condition Revision

## Current Conditions

종가 기준 추천 후보는 아래 조건을 모두 만족해야 한다.

1. 유니버스 포함
   - 한국: `kr_top80.csv`
   - 미국: `us_top100.csv`
   - `active=true` 종목만 사용

2. 최신 일봉 기준
   - 각 종목의 가장 최신 row만 최종 후보로 판단

3. 매수 캔들패턴 발생
   - `hammer`
   - `bullish_engulfing`
   - `morning_star`
   - `piercing_line`
   - `inverted_hammer`
   - `tweezer_bottom`

4. 추세 조건
   - `close > MA20`
   - `MA20 > MA60`
   - `MA20 slope > 0`

5. 거래량 조건
   - `volume > volume_MA20 * 1.2`

6. 최종 조건
   - 매수패턴 `true`
   - 추세조건 `true`
   - 거래량조건 `true`

## Proposed Conditions

추천 후보를 3단계 등급으로 분리한다.

## A Grade: 강한 후보

1. 매수 캔들패턴 발생
2. `close > MA20`
3. `MA20 > MA60`
4. `MA20 slope > 0`
5. `volume > volume_MA20 * 1.2`
6. 최신 일봉 기준

의미:

- 패턴, 추세, 거래량이 모두 강한 후보
- 주문 후보로 사용할 수 있는 1순위

## B Grade: 일반 후보

1. 매수 캔들패턴 발생
2. `close > MA20`
3. `MA20 > MA60`
4. `MA20 slope > 0`
5. `volume > volume_MA20 * 1.0`
6. 최근 3거래일 안에 신호 발생 허용

의미:

- 패턴과 추세는 좋지만 거래량 조건을 완화한 후보
- 바로 주문보다는 관찰 후보

## C Grade: 관찰 후보

1. 매수 캔들패턴은 없어도 됨
2. `close > MA20`
3. `MA20 > MA60`
4. `MA20 slope > 0`
5. `volume > volume_MA20 * 1.0`
6. 최근 고점 근처 또는 전고점 돌파 근접

의미:

- 캔들패턴은 없지만 추세와 거래량이 살아 있는 후보
- 관심종목/감시 후보

## ETF Conditions

ETF는 개별주보다 캔들패턴 신뢰도가 낮을 수 있으므로 별도 조건을 적용한다.

## ETF A Grade

1. `close > MA20`
2. `MA20 > MA60`
3. `MA20 slope > 0`
4. `volume > volume_MA20 * 1.0`
5. 최근 고가 돌파 또는 20일 신고가 근접

## ETF B Grade

1. `close > MA20`
2. `MA20 slope > 0`
3. `volume > volume_MA20 * 0.8`

의미:

- ETF는 패턴 필수 조건을 제외한다.
- 시장/섹터 추세 확인용으로 사용한다.

## Operating Rules

1. 화면 표시 후보
   - A등급 + B등급 + C등급 모두 표시

2. 주문 후보
   - 기본적으로 A등급만 사용

3. 수동 관찰 후보
   - B등급, C등급은 사용자가 직접 확인

4. 자동 주문
   - 현재는 사용하지 않음
   - 향후 사용하더라도 A등급 + 수동 승인 필수

5. ETF
   - 개별주 조건과 분리
   - 패턴보다는 추세/거래량/고점 돌파 중심으로 판단
