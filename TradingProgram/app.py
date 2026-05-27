from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

from src.backtester import run_multi_symbol_backtest, run_single_symbol_backtest
from src.broker.holdings import display_holdings, normalize_domestic_holdings, normalize_overseas_holdings
from src.broker.kis import KisBroker
from src.config import load_config
from src.data_loader import filter_ohlcv_by_universe, load_ohlcv_csv, load_universe_csv
from src.metrics import compute_metrics
from src.external_data_collector import collect_external_universe_ohlcv
from src.trading.automation import load_recommendation_universe, run_recommendation_cycle
from src.trading.order_queue import OrderQueue

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from review_agent.chat import answer


@st.cache_resource
def get_kis_broker(_config: dict) -> KisBroker:
    return KisBroker.from_config(_config)


def main() -> None:
    st.set_page_config(page_title="트레이딩 리서치 도구", layout="wide")
    st.title("트레이딩 리서치 도구")

    config_path = st.sidebar.text_input("설정 파일", "config.yaml")
    config = load_config(config_path)
    show_backtest = st.sidebar.checkbox("백테스트 보이기", value=False)

    tab_names = ["보유 주식", "종가 기준 후보", "리뷰 채팅"]
    if show_backtest:
        tab_names.append("백테스트")
    tabs = st.tabs(tab_names)
    tab_map = dict(zip(tab_names, tabs, strict=True))

    with tab_map["보유 주식"]:
        render_holdings_tab(config)
    with tab_map["종가 기준 후보"]:
        render_recommendation_tab(config)
    with tab_map["리뷰 채팅"]:
        render_chat_tab()
    if show_backtest:
        with tab_map["백테스트"]:
            render_backtest_tab(config)


def render_recommendation_tab(config: dict) -> None:
    automation = config.get("automation", {})
    st.caption("종가 기준 후보는 장마감 후 갱신된 OHLCV 데이터와 유니버스 CSV 기준으로 분석합니다. KIS는 보유 종목 확인과 주문 단계에 사용합니다.")
    st.warning("2단계 운영 방식: 시스템이 주문 제안을 만들고, 사용자가 수동 승인해야 주문 단계로 넘어갑니다.")

    cols = st.columns(4)
    cols[0].metric("종가 후보 분석", "가능")
    cols[1].metric("대상", "유니버스 CSV")
    cols[2].metric("수동 승인", "필수" if automation.get("manual_approval_required", True) else "아님")
    cols[3].metric("실주문 자동 실행", "비활성")

    kr_universe = load_recommendation_universe(config, "KR")
    us_universe = load_recommendation_universe(config, "US")
    st.subheader("분석 대상")
    target_cols = st.columns(2)
    target_cols[0].metric("국내 분석 대상", len(kr_universe))
    target_cols[1].metric("미국 분석 대상", len(us_universe))

    with st.expander("국내 유니버스 보기"):
        st.dataframe(kr_universe[["symbol", "name", "market", "rank", "active"]], use_container_width=True, hide_index=True)
    with st.expander("미국 유니버스 보기"):
        st.dataframe(us_universe[["symbol", "name", "market", "rank", "active"]], use_container_width=True, hide_index=True)

    if len(kr_universe) < 80:
        st.warning(f"국내 유니버스가 {len(kr_universe)}개뿐입니다. 요구사항은 상위 80개입니다.")
    if len(us_universe) < 100:
        st.warning(f"미국 유니버스가 {len(us_universe)}개뿐입니다. 요구사항은 상위 100개입니다.")

    data_file = Path(config["data"]["universe_ohlcv_file"])
    st.subheader("분석 데이터")
    if data_file.exists():
        st.success(f"분석용 OHLCV 파일 있음: {data_file}")
    else:
        st.warning(f"분석용 OHLCV 파일이 없습니다: {data_file}")

    if st.button("외부 데이터 1년치 수집", type="secondary"):
        try:
            data = collect_external_universe_ohlcv(config)
            st.success(f"수집 완료: {data['symbol'].nunique()}개 종목, {len(data)}행")
        except Exception as exc:
            st.error(str(exc))

    queue = OrderQueue()
    if st.button("저장된 데이터로 종가 후보 분석 실행", type="primary"):
        try:
            candidates = run_recommendation_cycle(config)
            queued_count = queue.append_many(candidates)
            if candidates:
                counts = pd.Series([candidate.market.upper() for candidate in candidates]).value_counts()
                kr_count = int(counts.get("KR", 0))
                us_count = int(counts.get("US", 0))
                st.success(
                    f"이번 종가 후보 {len(candidates)}건을 분석했습니다. "
                    f"대기열 반영 {queued_count}건, 국내 {kr_count}건 / 미국 {us_count}건입니다."
                )
            else:
                st.info("현재 조건에 맞는 종가 기준 후보가 없습니다.")
        except Exception as exc:
            st.error(str(exc))

    st.subheader("2단계: 수동 승인 주문")
    st.caption("주문 제안을 선택한 뒤 수동 승인 또는 거절을 기록합니다. 현재 승인 처리는 페이퍼 기록이며 실주문은 전송하지 않습니다.")
    orders = queue.read_pending()
    if not orders:
        st.info("승인 대기 중인 주문 제안이 없습니다.")
        return

    orders_df = pd.DataFrame(orders)
    event = st.dataframe(
        orders_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="manual_order_approval_table",
    )
    selected_rows = event.selection.rows
    if not selected_rows:
        return

    selected = orders_df.iloc[selected_rows[0]].to_dict()
    st.markdown("#### 선택 주문")
    st.json(selected)
    approve_col, reject_col = st.columns(2)
    if approve_col.button("수동 승인 주문으로 기록", type="primary"):
        updated = queue.update_status(str(selected["id"]), "approved_paper", "manual approval recorded; live order not sent")
        st.success(f"승인 기록 완료: {updated['symbol']} {updated['side']}")
        st.rerun()
    if reject_col.button("거절 처리"):
        updated = queue.update_status(str(selected["id"]), "rejected", "manual rejection")
        st.info(f"거절 기록 완료: {updated['symbol']} {updated['side']}")
        st.rerun()


def render_holdings_tab(config: dict) -> None:
    st.caption("한국투자증권 KIS 조회 전용 화면입니다. 주문 기능은 자동으로 실행되지 않습니다.")
    st.warning("API 키는 화면에 입력하지 마세요. `.env` 파일에만 저장하세요.")

    refresh = st.button("보유 주식 새로고침", type="primary")
    if refresh or "domestic_holdings" not in st.session_state or "overseas_holdings" not in st.session_state:
        try:
            broker = get_kis_broker(config)
            domestic_response = broker.get_domestic_balance()
            overseas_response = broker.get_overseas_balance()
            st.session_state.domestic_holdings = normalize_domestic_holdings(domestic_response)
            st.session_state.overseas_holdings = normalize_overseas_holdings(overseas_response)
        except Exception as exc:
            st.error(str(exc))
            st.stop()

    st.subheader("국내 보유 주식")
    selected_domestic = render_holdings_table("domestic_table", st.session_state.domestic_holdings)
    if selected_domestic is not None:
        render_holding_detail(selected_domestic)

    st.divider()
    st.subheader("해외 보유 주식")
    selected_overseas = render_holdings_table("overseas_table", st.session_state.overseas_holdings)
    if selected_overseas is not None:
        render_holding_detail(selected_overseas)


def render_holdings_table(key: str, df: pd.DataFrame) -> dict | None:
    display_df = display_holdings(df)
    if display_df.empty:
        st.info("표시할 보유 종목이 없습니다.")
        return None
    event = st.dataframe(
        display_df,
        key=key,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    selected_rows = event.selection.rows
    if not selected_rows:
        return None
    return df.iloc[selected_rows[0]].to_dict()


def render_holding_detail(row: dict) -> None:
    st.markdown("#### 선택 종목 상세")
    cols = st.columns(5)
    cols[0].metric("시장", row.get("시장", ""))
    cols[1].metric("이름", row.get("이름", ""))
    cols[2].metric("코드", row.get("코드", ""))
    cols[3].metric("수량", f"{row.get('수량', 0):,.4g}")
    cols[4].metric("평가 금액", f"{row.get('평가 금액', 0):,.2f}")
    with st.expander("원본 API 응답 보기"):
        st.json(row.get("_raw", {}))


def render_backtest_tab(config: dict) -> None:
    st.caption("Phase 1: 캔들 패턴 + 추세/거래량 필터 기반 백테스트입니다. 실주문은 실행하지 않습니다.")
    mode = st.radio("백테스트 범위", ["샘플 단일 종목", "유니버스 다종목"], horizontal=True)
    market = st.selectbox("기본 시장", ["US", "KR"])
    data_path = st.text_input("OHLCV CSV", config["data"]["sample_file"])

    us_enabled = False
    kr_enabled = False
    if mode == "유니버스 다종목":
        us_enabled = st.checkbox("미국 유니버스 포함", value=True)
        kr_enabled = st.checkbox("한국 유니버스 포함", value=True)

    if not st.button("백테스트 실행", type="primary"):
        return

    df = load_ohlcv_csv(data_path)
    if mode == "유니버스 다종목":
        symbols: list[str] = []
        market_map: dict[str, str] = {}
        if us_enabled:
            us_symbols = load_universe_csv(config["universe"]["us_file"])
            symbols.extend(us_symbols)
            market_map.update({symbol: "US" for symbol in us_symbols})
        if kr_enabled:
            kr_symbols = load_universe_csv(config["universe"]["kr_file"])
            symbols.extend(kr_symbols)
            market_map.update({symbol: "KR" for symbol in kr_symbols})
        df = filter_ohlcv_by_universe(df, symbols)
        if df.empty:
            st.error("선택한 유니버스와 일치하는 OHLCV 데이터가 없습니다.")
            return
        result = run_multi_symbol_backtest(df, config, market_map)
    else:
        result = run_single_symbol_backtest(df, config, market=market)

    metrics = compute_metrics(result["equity_curve"], result["trades"], float(config["risk"]["initial_cash"]))
    render_metrics(metrics)
    st.subheader("자산 곡선")
    st.line_chart(result["equity_curve"], x="date", y="equity")
    st.subheader("거래 내역")
    st.dataframe(result["trades"], use_container_width=True)
    if "open_positions" in result:
        st.subheader("미청산 포지션")
        st.dataframe(result["open_positions"], use_container_width=True)
    st.subheader("건너뛴 신호")
    st.dataframe(result["skipped_signals"], use_container_width=True)


def render_metrics(metrics: dict) -> None:
    cols = st.columns(5)
    cols[0].metric("총수익률 %", f"{metrics.get('total_return_pct', 0):.2f}")
    cols[1].metric("CAGR %", f"{metrics.get('cagr_pct', 0):.2f}")
    cols[2].metric("최대낙폭 %", f"{metrics.get('max_drawdown_pct', 0):.2f}")
    cols[3].metric("거래 수", metrics.get("trade_count", 0))
    cols[4].metric("승률 %", f"{metrics.get('win_rate_pct', 0):.2f}")


def render_chat_tab() -> None:
    st.caption("로컬 프로젝트 파일 기준으로 답합니다. 투자 추천이나 수익 보장은 하지 않습니다.")
    if "review_chat_messages" not in st.session_state:
        st.session_state.review_chat_messages = [
            {"role": "assistant", "content": "질문을 입력하세요. 예: `리스크 알려줘`, `실거래 가능해?`"}
        ]
    for message in st.session_state.review_chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("리뷰 에이전트에게 질문")
    if prompt:
        st.session_state.review_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        response = answer(prompt, PROJECT_ROOT)
        st.session_state.review_chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


if __name__ == "__main__":
    main()
