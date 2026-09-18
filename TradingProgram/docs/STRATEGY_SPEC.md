# Strategy Spec

The v1 strategy combines raw candlestick patterns with trend and volume filters.

Buy patterns:

- piercing line
- hammer
- bullish engulfing
- morning star
- inverted hammer
- tweezer bottom

Sell patterns:

- dark cloud cover
- evening star
- bearish engulfing
- shooting star
- tweezer top

Filters:

- close above long moving average
- short moving average slope positive
- volume above configured volume moving average threshold

Execution:

- A buy signal on day `i` may only be filled on day `i + 1`.
- The next row must trade through the breakout trigger.
- Gap-up entries are skipped when they exceed the configured threshold.

This specification does not claim profitability.
