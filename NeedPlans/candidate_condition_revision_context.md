# Candidate Condition Revision Context

## 1. Purpose

기존 종가 기준 추천 후보 조건은 너무 엄격해서 실제 운영 시 후보가 거의 나오지 않을 수 있다.

따라서 추천 후보를 단일 통과/탈락 방식이 아니라 아래 등급 체계로 분리한다.

- A Grade: 강한 후보 / 주문 후보 1순위
- B Grade: 일반 후보 / 관찰 후보
- C Grade: 관심 후보 / 감시 후보
- ETF_A Grade: ETF 강한 후보
- ETF_B Grade: ETF 일반 관찰 후보

현재 시스템의 기본 방향은 자동매매가 아니라 **후보 발굴 + 사용자의 수동 확인**이다.

---

## 2. Common Universe Rules

모든 후보는 아래 유니버스 파일 안에서만 판단한다.

### Korea

```text
kr_top80.csv
```

### United States

```text
us_top100.csv
```

### Common Filter

```text
active = true
```

`active=false` 종목은 분석 및 후보 산출 대상에서 제외한다.

---

## 3. Buy Pattern Signals

개별주 A/B Grade에서 사용하는 매수 캔들패턴은 아래와 같다.

```text
hammer
bullish_engulfing
morning_star
piercing_line
inverted_hammer
tweezer_bottom
```

하나 이상의 패턴이 발생하면 `buy_pattern_signal = true`로 판단한다.

---

## 4. Stock Candidate Grades

ETF가 아닌 일반 개별주는 아래 A/B/C Grade 조건을 적용한다.

---

## 4.1 A Grade: Strong Candidate

A Grade는 가장 강한 후보이며, 기본 주문 후보로 사용할 수 있는 1순위이다.

### Conditions

```text
buy_pattern_signal = true
close > MA20
MA20 > MA60
MA20_slope > 0
volume > volume_MA20 * 1.2
latest daily candle only
```

### Meaning

```text
캔들패턴 + 상승 추세 + 강한 거래량 증가
```

### Usage

```text
화면 표시 대상
기본 주문 후보
자동 주문을 향후 추가하더라도 A Grade + 사용자 수동 승인 필수
```

---

## 4.2 B Grade: Normal Candidate

B Grade는 패턴과 추세는 좋지만 거래량 조건을 완화한 관찰 후보이다.

### Conditions

```text
buy_pattern_signal = true
close > MA20
MA20 > MA60
MA20_slope > 0
volume > volume_MA20 * 1.0
signal occurred within recent 3 trading days
```

### Meaning

```text
패턴 있음
추세 양호
거래량은 평균 이상
최근 3거래일 안의 신호 허용
```

### Usage

```text
화면 표시 대상
바로 주문하지 않음
사용자가 직접 차트 확인 후 판단
```

---

## 4.3 C Grade: Watch Candidate

C Grade는 캔들패턴이 없어도 되는 관심/감시 후보이다.

### Conditions

```text
buy_pattern_signal is not required
close > MA20
MA20 > MA60
MA20_slope > 0
volume > volume_MA20 * 1.0
near_recent_high = true OR near_breakout = true
```

### Meaning

```text
캔들패턴은 없을 수 있음
추세 양호
거래량 평균 이상
최근 고점 근처 또는 전고점 돌파 근접
```

### Usage

```text
화면 표시 대상
관심종목/감시종목
자동 주문 대상 아님
```

---

## 5. ETF Candidate Grades

ETF는 개별주보다 캔들패턴 신뢰도가 낮을 수 있으므로 별도 조건을 적용한다.

ETF는 캔들패턴을 필수 조건으로 사용하지 않는다.

판단 중심:

```text
추세
거래량
최근 고점 돌파
20일 신고가 근접
```

---

## 5.1 ETF A Grade

### Conditions

```text
close > MA20
MA20 > MA60
MA20_slope > 0
volume > volume_MA20 * 1.0
recent_high_breakout = true OR near_20day_high = true
```

### Meaning

```text
ETF 상승 추세가 강함
평균 이상 거래량
최근 고가 돌파 또는 20일 신고가 근접
```

### Usage

```text
화면 표시 대상
시장/섹터 방향성 확인용
기본 자동 주문 대상 아님
```

---

## 5.2 ETF B Grade

### Conditions

```text
close > MA20
MA20_slope > 0
volume > volume_MA20 * 0.8
```

### Meaning

```text
단기 추세 양호
거래량이 평균 대비 크게 부족하지 않음
시장/섹터 흐름 확인용
```

### Usage

```text
화면 표시 대상
시장/섹터 관찰 후보
기본 자동 주문 대상 아님
```

---

## 6. Operating Rules

### 6.1 Display Candidates

화면에는 아래 등급을 모두 표시한다.

```text
A
B
C
ETF_A
ETF_B
```

### 6.2 Order Candidates

기본 주문 후보는 아래 등급으로 제한한다.

```text
A only
```

### 6.3 Manual Observation

```text
B Grade = 사용자가 직접 확인하는 관찰 후보
C Grade = 관심종목/감시 후보
ETF_A / ETF_B = 시장/섹터 흐름 확인용
```

### 6.4 Auto Order

현재 자동 주문은 사용하지 않는다.

향후 자동 주문을 추가하더라도 아래 규칙을 반드시 지킨다.

```text
A Grade만 자동 주문 후보 가능
사용자 수동 승인 필수
B/C Grade 자동 주문 금지
ETF 자동 주문 금지 또는 별도 승인 필요
```

---

## 7. Recommended Implementation Columns

후보 판정을 위해 단일 boolean만 만들지 말고, 아래 컬럼들을 분리해서 저장한다.

```text
is_buy_pattern
buy_pattern_names
is_trend_ok
is_volume_a_ok
is_volume_b_ok
is_recent_signal_3d
is_near_recent_high
is_near_breakout
is_recent_high_breakout
is_near_20day_high
is_etf
candidate_grade
candidate_reason
```

---

## 8. candidate_grade Values

`candidate_grade`는 아래 값 중 하나를 사용한다.

```text
A
B
C
ETF_A
ETF_B
NONE
```

---

## 9. candidate_reason Examples

후보가 왜 선정되었는지 UI에서 바로 확인할 수 있도록 `candidate_reason`을 문자열로 남긴다.

```text
A Grade: bullish_engulfing + trend ok + volume 1.35x
B Grade: hammer signal within 3 days + trend ok + volume 1.05x
C Grade: trend ok + volume 1.12x + near recent high
ETF_A: trend ok + volume 1.08x + near 20-day high
ETF_B: close>MA20 + MA20 slope positive + volume 0.91x
```

---

## 10. Grade Priority Rules

하나의 종목이 여러 조건을 동시에 만족할 수 있으므로 우선순위를 명확히 한다.

### Stock Priority

```text
A > B > C > NONE
```

### ETF Priority

```text
ETF_A > ETF_B > NONE
```

### Important

ETF는 일반 개별주 A/B/C 조건으로 평가하지 않는다.

```text
if is_etf == true:
    apply ETF rules only
else:
    apply stock rules only
```

---

## 11. Suggested Pseudocode

```python
def classify_candidate(row, recent_rows):
    if not row["active"]:
        return "NONE", "inactive symbol"

    if row["is_etf"]:
        return classify_etf_candidate(row)

    return classify_stock_candidate(row, recent_rows)


def classify_stock_candidate(row, recent_rows):
    buy_pattern_signal = row["is_buy_pattern"]
    trend_ok = (
        row["close"] > row["MA20"]
        and row["MA20"] > row["MA60"]
        and row["MA20_slope"] > 0
    )

    volume_a_ok = row["volume"] > row["volume_MA20"] * 1.2
    volume_b_ok = row["volume"] > row["volume_MA20"] * 1.0

    recent_signal_3d = any(r["is_buy_pattern"] for r in recent_rows[-3:])

    near_breakout_ok = (
        row["is_near_recent_high"]
        or row["is_near_breakout"]
    )

    if buy_pattern_signal and trend_ok and volume_a_ok:
        return "A", "buy pattern + trend ok + volume > 1.2x"

    if recent_signal_3d and trend_ok and volume_b_ok:
        return "B", "buy pattern within 3 days + trend ok + volume > 1.0x"

    if trend_ok and volume_b_ok and near_breakout_ok:
        return "C", "trend ok + volume > 1.0x + near high/breakout"

    return "NONE", "conditions not met"


def classify_etf_candidate(row):
    trend_a_ok = (
        row["close"] > row["MA20"]
        and row["MA20"] > row["MA60"]
        and row["MA20_slope"] > 0
    )

    volume_a_ok = row["volume"] > row["volume_MA20"] * 1.0

    high_ok = (
        row["is_recent_high_breakout"]
        or row["is_near_20day_high"]
    )

    trend_b_ok = (
        row["close"] > row["MA20"]
        and row["MA20_slope"] > 0
    )

    volume_b_ok = row["volume"] > row["volume_MA20"] * 0.8

    if trend_a_ok and volume_a_ok and high_ok:
        return "ETF_A", "ETF trend ok + volume > 1.0x + near/break high"

    if trend_b_ok and volume_b_ok:
        return "ETF_B", "ETF close>MA20 + MA20 slope positive + volume > 0.8x"

    return "NONE", "ETF conditions not met"
```

---

## 12. Development Task Instruction

아래 작업을 수행한다.

```text
현재 종가 기준 추천 후보 조건을 A/B/C 등급 체계로 개정한다.

기존에는 매수 캔들패턴, 추세조건, 거래량조건을 모두 만족하는 종목만 최종 후보로 판단했지만,
이제는 후보를 A Grade, B Grade, C Grade로 나누어 표시해야 한다.

개별주 조건:

A Grade:
- buy pattern signal true
- close > MA20
- MA20 > MA60
- MA20 slope > 0
- volume > volume_MA20 * 1.2
- latest daily candle only

B Grade:
- buy pattern signal true
- close > MA20
- MA20 > MA60
- MA20 slope > 0
- volume > volume_MA20 * 1.0
- signal occurred within recent 3 trading days

C Grade:
- buy pattern is not required
- close > MA20
- MA20 > MA60
- MA20 slope > 0
- volume > volume_MA20 * 1.0
- near recent high or near breakout

ETF는 개별주와 별도 조건을 적용한다.

ETF A Grade:
- close > MA20
- MA20 > MA60
- MA20 slope > 0
- volume > volume_MA20 * 1.0
- recent high breakout or near 20-day high

ETF B Grade:
- close > MA20
- MA20 slope > 0
- volume > volume_MA20 * 0.8

운영 규칙:
- 화면에는 A/B/C/ETF_A/ETF_B 후보를 모두 표시한다.
- 주문 후보는 기본적으로 A Grade만 사용한다.
- B/C Grade는 사용자가 직접 확인하는 관찰 후보이다.
- 현재 자동 주문은 사용하지 않는다.
- 향후 자동 주문을 추가하더라도 A Grade + 수동 승인 조건을 필수로 한다.
- ETF는 개별주 조건과 분리하고, 패턴보다 추세/거래량/고점 돌파 중심으로 판단한다.

구현 시 candidate_grade 컬럼을 추가한다.
값은 A, B, C, ETF_A, ETF_B, NONE 중 하나로 한다.

또한 candidate_reason 컬럼을 추가해서 왜 해당 등급이 되었는지 사람이 읽을 수 있는 문자열로 남긴다.
```

---

## 13. Validation Checklist

개발 후 아래 항목을 확인한다.

```text
[ ] active=false 종목이 후보에서 제외되는가?
[ ] 개별주와 ETF가 서로 다른 조건으로 평가되는가?
[ ] A Grade가 기존 강한 조건과 동일하게 동작하는가?
[ ] B Grade가 최근 3거래일 신호를 허용하는가?
[ ] C Grade가 패턴 없이도 추세/거래량/고점 조건으로 선정되는가?
[ ] ETF_A가 패턴 없이 추세/거래량/고점 조건으로 선정되는가?
[ ] ETF_B가 완화된 ETF 조건으로 선정되는가?
[ ] candidate_grade 값이 A/B/C/ETF_A/ETF_B/NONE 중 하나로 저장되는가?
[ ] candidate_reason이 사람이 읽을 수 있게 생성되는가?
[ ] 화면에 A/B/C/ETF_A/ETF_B가 모두 표시되는가?
[ ] 주문 후보가 A Grade로만 제한되는가?
[ ] 자동 주문이 현재 비활성화되어 있는가?
```
