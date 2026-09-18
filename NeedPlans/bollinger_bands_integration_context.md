# Bollinger Bands Integration Context

## 1. Purpose

기존 Candidate Grade 시스템에 볼린저 밴드(Bollinger Bands)를 보조 지표로 추가한다.

볼린저 밴드는 단독 매수 신호로 사용하지 않고, 아래 목적에 사용한다.

```text
추세 확인
돌파 확인
변동성 축소/확대 확인
후보 필터 강화
화면에서 사용자가 직접 판단하기 위한 보조 정보 제공
```

현재 시스템의 기본 방향은 자동매매가 아니라 **후보 발굴 + 사용자 수동 확인**이다.

따라서 볼린저 밴드 조건은 자동 주문 조건으로 바로 연결하지 않는다.

---

## 2. Bollinger Bands Definition

기본 설정은 일반적으로 많이 사용하는 20일 기준을 사용한다.

```text
BB_MA20 = close rolling mean 20
BB_STD20 = close rolling std 20
BB_UPPER = BB_MA20 + BB_STD20 * 2
BB_LOWER = BB_MA20 - BB_STD20 * 2
BB_WIDTH = (BB_UPPER - BB_LOWER) / BB_MA20
BB_POSITION = (close - BB_LOWER) / (BB_UPPER - BB_LOWER)
```

### Meaning

```text
BB_UPPER 근처 또는 돌파 = 강한 상승 / 과열 가능성
BB_LOWER 근처 = 약세 / 반등 가능성
BB_WIDTH 축소 = 변동성 축소, 큰 움직임 전 대기 가능성
BB_WIDTH 확대 = 변동성 확대, 추세 진행 가능성
BB_POSITION 0.8 이상 = 상단 밴드 근처
BB_POSITION 0.2 이하 = 하단 밴드 근처
```

---

## 3. Required Data Columns

아래 컬럼을 추가한다.

```text
bb_middle
bb_upper
bb_lower
bb_width
bb_width_ma20
bb_position
is_bb_upper_breakout
is_bb_upper_near
is_bb_squeeze
is_bb_squeeze_breakout
is_bb_width_expanding
bb_signal_summary
```

---

## 4. Column Definitions

### bb_middle

```text
20일 이동평균선
기존 MA20이 있다면 MA20을 그대로 사용 가능
```

### bb_upper

```text
MA20 + 2 * close_20day_std
```

### bb_lower

```text
MA20 - 2 * close_20day_std
```

### bb_width

```text
(bb_upper - bb_lower) / bb_middle
```

### bb_width_ma20

```text
bb_width의 20일 평균
```

### bb_position

```text
(close - bb_lower) / (bb_upper - bb_lower)
```

값의 의미:

```text
0.0 근처 = 하단 밴드 근처
0.5 근처 = 중심선 근처
1.0 근처 = 상단 밴드 근처
1.0 초과 = 상단 밴드 돌파
```

---

## 5. Bollinger Signal Rules

## 5.1 Upper Band Breakout

상단 밴드 돌파 조건이다.

```text
is_bb_upper_breakout = close > bb_upper
```

의미:

```text
강한 상승 추세 가능성
단기 과열 가능성도 있으므로 거래량과 함께 확인 필요
```

---

## 5.2 Near Upper Band

상단 밴드 근접 조건이다.

```text
is_bb_upper_near = bb_position >= 0.8
```

의미:

```text
주가가 밴드 상단 영역에 위치
상승 탄력이 있는 상태일 수 있음
```

---

## 5.3 Bollinger Squeeze

밴드 폭 축소 조건이다.

기본 조건:

```text
is_bb_squeeze = bb_width < bb_width_ma20 * 0.8
```

의미:

```text
변동성이 평소보다 작아진 상태
향후 큰 움직임이 나올 수 있는 준비 구간
```

---

## 5.4 Squeeze Breakout

스퀴즈 이후 상방 돌파 조건이다.

```text
is_bb_squeeze_breakout =
    recent_squeeze_within_5d == true
    AND close > bb_upper
    AND volume > volume_MA20 * 1.0
```

의미:

```text
변동성 축소 후 상단 밴드 돌파
강한 상승 시작 후보
```

---

## 5.5 Band Width Expanding

밴드 폭 확장 조건이다.

```text
is_bb_width_expanding = bb_width > previous_bb_width
```

또는 더 보수적으로:

```text
is_bb_width_expanding = bb_width > bb_width_ma20
```

의미:

```text
변동성이 다시 커지는 상태
추세가 시작되거나 진행 중일 수 있음
```

---

## 6. How to Use with Candidate Grades

볼린저 밴드는 기존 A/B/C 등급 조건을 대체하지 않는다.

기존 후보 조건은 유지하고, 볼린저 밴드는 아래처럼 보조 점수 또는 보조 태그로 사용한다.

---

## 6.1 A Grade Enhancement

A Grade의 기본 조건은 유지한다.

추가로 아래 중 하나가 있으면 `bb_confirmed = true`로 표시한다.

```text
is_bb_upper_near = true
OR is_bb_upper_breakout = true
OR is_bb_squeeze_breakout = true
```

표시 예시:

```text
A Grade + BB Confirmed
A Grade + Upper Band Breakout
A Grade + Squeeze Breakout
```

주의:

```text
A Grade 조건에 볼린저 밴드를 필수로 넣지는 않는다.
처음에는 보조 확인용으로만 사용한다.
```

---

## 6.2 B Grade Enhancement

B Grade에서는 아래 조건이 있으면 관찰 우선순위를 높인다.

```text
is_bb_upper_near = true
OR is_bb_width_expanding = true
OR is_bb_squeeze_breakout = true
```

표시 예시:

```text
B Grade + BB Watch
B Grade + Band Width Expanding
B Grade + Near Upper Band
```

---

## 6.3 C Grade Enhancement

C Grade에서는 볼린저 밴드가 특히 유용하다.

C Grade는 패턴이 없어도 되므로, 아래 조건이 있으면 관심 후보로 더 의미가 있다.

```text
is_bb_squeeze = true
OR is_bb_squeeze_breakout = true
OR is_bb_upper_near = true
```

표시 예시:

```text
C Grade + Squeeze Watch
C Grade + Squeeze Breakout
C Grade + Near Upper Band
```

---

## 6.4 ETF Usage

ETF는 캔들패턴보다 추세/거래량/고점 돌파 중심으로 판단한다.

따라서 ETF에는 볼린저 밴드를 적극적으로 보조 지표로 사용한다.

### ETF A Grade Enhancement

```text
is_bb_upper_near = true
OR is_bb_upper_breakout = true
OR is_bb_squeeze_breakout = true
```

### ETF B Grade Enhancement

```text
is_bb_width_expanding = true
OR is_bb_squeeze = true
```

표시 예시:

```text
ETF_A + BB Breakout
ETF_A + Near Upper Band
ETF_B + Squeeze Watch
ETF_B + Width Expanding
```

---

## 7. Recommended UI Buttons / Filters

화면에 아래 버튼 또는 체크박스를 추가한다.

---

## 7.1 Candidate Grade Filter Buttons

기존 후보 등급을 빠르게 필터링하는 버튼이다.

```text
전체
A만 보기
B만 보기
C만 보기
ETF만 보기
```

---

## 7.2 Bollinger Filter Buttons

볼린저 밴드 상태별 필터 버튼이다.

```text
BB 돌파
상단 근접
스퀴즈
스퀴즈 돌파
밴드 확장
```

### Button Mapping

```text
BB 돌파 = is_bb_upper_breakout == true
상단 근접 = is_bb_upper_near == true
스퀴즈 = is_bb_squeeze == true
스퀴즈 돌파 = is_bb_squeeze_breakout == true
밴드 확장 = is_bb_width_expanding == true
```

---

## 7.3 Risk / Safety Toggle

자동 주문을 아직 사용하지 않더라도, 안전한 운영을 위해 아래 토글을 둔다.

```text
A등급만 주문 후보
B/C 주문 후보 제외
ETF 주문 제외
수동 승인 필수
```

기본값:

```text
A등급만 주문 후보 = ON
B/C 주문 후보 제외 = ON
ETF 주문 제외 = ON
수동 승인 필수 = ON
```

---

## 7.4 Detail View Buttons

각 후보 row에 아래 버튼을 추가하면 좋다.

```text
차트 보기
캔들패턴 보기
볼린저 보기
후보 사유 보기
관심종목 추가
주문 후보로 표시
제외
```

### Meaning

```text
차트 보기 = 가격/이동평균/거래량 전체 차트 확인
캔들패턴 보기 = 어떤 패턴이 감지되었는지 확인
볼린저 보기 = BB upper/middle/lower와 squeeze 상태 확인
후보 사유 보기 = candidate_reason, bb_signal_summary 확인
관심종목 추가 = watchlist에 저장
주문 후보로 표시 = 수동 확인 후 후보로 따로 표시, 즉시 주문 아님
제외 = 해당 종목을 당일 후보 목록에서 숨김
```

---

## 8. Recommended Display Columns

후보 리스트 화면에는 아래 컬럼을 표시한다.

```text
symbol
name
market
is_etf
candidate_grade
candidate_reason
bb_signal_summary
close
change_rate
volume_ratio
MA20
MA60
bb_position
bb_width
is_bb_upper_breakout
is_bb_squeeze
is_bb_squeeze_breakout
```

---

## 9. bb_signal_summary Examples

사람이 이해하기 쉽게 볼린저 상태를 문자열로 요약한다.

```text
BB: upper breakout + volume 1.35x
BB: near upper band, position 0.86
BB: squeeze watch, width 0.042
BB: squeeze breakout, volume 1.22x
BB: width expanding
BB: neutral
```

---

## 10. Candidate Reason Example with Bollinger

기존 `candidate_reason`에 볼린저 요약을 같이 붙인다.

```text
A Grade: bullish_engulfing + trend ok + volume 1.35x | BB: upper breakout
B Grade: hammer within 3 days + trend ok + volume 1.04x | BB: near upper band
C Grade: trend ok + volume 1.10x + near recent high | BB: squeeze breakout
ETF_A: trend ok + volume 1.08x + near 20-day high | BB: near upper band
ETF_B: close>MA20 + MA20 slope positive + volume 0.91x | BB: width expanding
```

---

## 11. Suggested Pseudocode

```python
def add_bollinger_bands(df):
    df["bb_middle"] = df["close"].rolling(20).mean()
    df["bb_std"] = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_middle"] + df["bb_std"] * 2
    df["bb_lower"] = df["bb_middle"] - df["bb_std"] * 2
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_width_ma20"] = df["bb_width"].rolling(20).mean()
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    df["is_bb_upper_breakout"] = df["close"] > df["bb_upper"]
    df["is_bb_upper_near"] = df["bb_position"] >= 0.8
    df["is_bb_squeeze"] = df["bb_width"] < df["bb_width_ma20"] * 0.8
    df["is_bb_width_expanding"] = df["bb_width"] > df["bb_width"].shift(1)

    df["recent_squeeze_within_5d"] = (
        df["is_bb_squeeze"]
        .rolling(5)
        .max()
        .fillna(False)
        .astype(bool)
    )

    df["is_bb_squeeze_breakout"] = (
        df["recent_squeeze_within_5d"]
        & df["is_bb_upper_breakout"]
        & (df["volume"] > df["volume_MA20"] * 1.0)
    )

    return df
```

---

## 12. Suggested Summary Function

```python
def make_bb_signal_summary(row):
    signals = []

    if row.get("is_bb_squeeze_breakout"):
        signals.append("squeeze breakout")
    elif row.get("is_bb_upper_breakout"):
        signals.append("upper breakout")
    elif row.get("is_bb_upper_near"):
        signals.append("near upper band")

    if row.get("is_bb_squeeze"):
        signals.append("squeeze watch")

    if row.get("is_bb_width_expanding"):
        signals.append("width expanding")

    if not signals:
        return "BB: neutral"

    return "BB: " + " + ".join(signals)
```

---

## 13. Development Task Instruction

아래 작업을 수행한다.

```text
기존 Candidate Grade 시스템에 Bollinger Bands 보조 지표를 추가한다.

볼린저 밴드는 단독 매수 신호로 사용하지 않고,
기존 A/B/C/ETF_A/ETF_B 후보의 보조 확인 지표로 사용한다.

계산 컬럼:
- bb_middle
- bb_upper
- bb_lower
- bb_width
- bb_width_ma20
- bb_position

신호 컬럼:
- is_bb_upper_breakout
- is_bb_upper_near
- is_bb_squeeze
- is_bb_squeeze_breakout
- is_bb_width_expanding
- bb_signal_summary

기본 공식:
- bb_middle = close rolling mean 20
- bb_upper = bb_middle + close rolling std 20 * 2
- bb_lower = bb_middle - close rolling std 20 * 2
- bb_width = (bb_upper - bb_lower) / bb_middle
- bb_position = (close - bb_lower) / (bb_upper - bb_lower)

조건:
- is_bb_upper_breakout = close > bb_upper
- is_bb_upper_near = bb_position >= 0.8
- is_bb_squeeze = bb_width < bb_width_ma20 * 0.8
- is_bb_width_expanding = bb_width > previous_bb_width
- is_bb_squeeze_breakout = recent_squeeze_within_5d AND close > bb_upper AND volume > volume_MA20 * 1.0

운영:
- A/B/C 등급 조건 자체를 볼린저 밴드로 대체하지 않는다.
- 볼린저 밴드는 candidate_reason 또는 bb_signal_summary에 표시한다.
- A Grade에 BB 돌파/상단근접/스퀴즈돌파가 있으면 강한 확인 신호로 본다.
- B/C Grade에 BB 신호가 있으면 관찰 우선순위를 높인다.
- ETF에는 볼린저 밴드를 적극적으로 보조 지표로 사용한다.

UI:
- 후보 등급 필터 버튼: 전체, A만 보기, B만 보기, C만 보기, ETF만 보기
- 볼린저 필터 버튼: BB 돌파, 상단 근접, 스퀴즈, 스퀴즈 돌파, 밴드 확장
- 안전 토글: A등급만 주문 후보, B/C 주문 후보 제외, ETF 주문 제외, 수동 승인 필수
- Row 버튼: 차트 보기, 캔들패턴 보기, 볼린저 보기, 후보 사유 보기, 관심종목 추가, 주문 후보로 표시, 제외

주의:
- 현재 자동 주문은 사용하지 않는다.
- 향후 자동 주문을 추가하더라도 A Grade + 사용자 수동 승인 조건을 유지한다.
```

---

## 14. Validation Checklist

개발 후 아래 항목을 확인한다.

```text
[ ] bb_middle, bb_upper, bb_lower가 정상 계산되는가?
[ ] bb_width가 정상 계산되는가?
[ ] bb_position이 정상 계산되는가?
[ ] close > bb_upper일 때 is_bb_upper_breakout이 true가 되는가?
[ ] bb_position >= 0.8일 때 is_bb_upper_near가 true가 되는가?
[ ] bb_width < bb_width_ma20 * 0.8일 때 is_bb_squeeze가 true가 되는가?
[ ] 최근 5일 안에 squeeze가 있고 close > bb_upper이며 거래량 조건 충족 시 is_bb_squeeze_breakout이 true가 되는가?
[ ] 볼린저 조건이 기존 A/B/C 등급을 대체하지 않는가?
[ ] bb_signal_summary가 사람이 읽을 수 있게 생성되는가?
[ ] candidate_reason에 볼린저 요약이 포함되는가?
[ ] UI에서 BB 돌파/상단근접/스퀴즈/스퀴즈돌파/밴드확장 필터가 동작하는가?
[ ] 자동 주문이 여전히 비활성화되어 있는가?
```
