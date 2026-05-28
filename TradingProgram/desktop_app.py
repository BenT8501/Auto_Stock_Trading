from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.broker.holdings import display_holdings, normalize_domestic_holdings, normalize_overseas_holdings
from src.broker.kis import KisBroker
from src.config import load_config
from src.search.manual_search import has_meaningful_filter, search_by_conditions
from src.search.query_parser import parse_search_query
from src.trading.automation import load_recommendation_universe, run_recommendation_cycle
from src.trading.desktop_automation import run_desktop_automation_cycle
from src.trading.order_manager import PaperOrderManager
from src.trading.order_queue import OrderQueue


class TradingDesktopApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("트레이딩 리서치 도구")
        self.resize(1200, 800)
        self.config = load_config("config.yaml")
        self.queue = OrderQueue()
        self.paper_order_manager = PaperOrderManager()
        self.broker: KisBroker | None = None
        self.last_manual_search_query = ""
        self.automation_timer = QTimer(self)
        self.automation_timer.timeout.connect(self.run_auto_monitor_cycle)

        tabs = QTabWidget()
        tabs.addTab(self._holdings_tab(), "보유 주식")
        tabs.addTab(self._recommendations_tab(), "종가 기준 후보")
        tabs.addTab(self._manual_search_tab(), "수동 검색")
        tabs.addTab(self._review_tab(), "리뷰")
        self.setCentralWidget(tabs)

    def _get_broker(self) -> KisBroker:
        if self.broker is None:
            self.broker = KisBroker.from_config(self.config)
        return self.broker

    def _holdings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        refresh = QPushButton("보유 주식 새로고침")
        refresh.clicked.connect(self.refresh_holdings)
        layout.addWidget(refresh)
        layout.addWidget(QLabel("국내 보유 주식"))
        self.domestic_table = QTableWidget()
        layout.addWidget(self.domestic_table)
        layout.addWidget(QLabel("해외 보유 주식"))
        self.overseas_table = QTableWidget()
        layout.addWidget(self.overseas_table)
        return widget

    def _recommendations_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("장마감 후 갱신된 OHLCV 데이터 기반 종가 후보입니다. KIS는 보유 종목/주문 단계에만 사용합니다.")
        layout.addWidget(info)

        buttons = QHBoxLayout()
        analyze = QPushButton("종가 후보 분석 실행")
        analyze.clicked.connect(self.run_recommendations)
        approve = QPushButton("선택 주문 수동 승인")
        approve.clicked.connect(lambda: self.update_selected_order("approved_paper"))
        reject = QPushButton("선택 주문 거절")
        reject.clicked.connect(lambda: self.update_selected_order("rejected"))
        buttons.addWidget(analyze)
        buttons.addWidget(approve)
        buttons.addWidget(reject)
        layout.addLayout(buttons)

        automation = self.config.get("desktop_automation", {})
        auto_controls = QHBoxLayout()
        self.buy_amount_input = QDoubleSpinBox()
        self.buy_amount_input.setRange(0, 1_000_000_000)
        self.buy_amount_input.setDecimals(0)
        self.buy_amount_input.setSingleStep(100_000)
        self.buy_amount_input.setValue(float(automation.get("available_buy_amount", 1_000_000)))
        self.auto_buy_checkbox = QCheckBox("자동 매수(paper)")
        self.auto_buy_checkbox.setChecked(bool(automation.get("auto_buy", False)))
        self.auto_sell_checkbox = QCheckBox("자동 매도(paper)")
        self.auto_sell_checkbox.setChecked(bool(automation.get("auto_sell", False)))
        self.auto_run_button = QPushButton("자동 감시 1회 실행")
        self.auto_run_button.clicked.connect(self.run_auto_monitor_cycle)
        self.auto_buy_checkbox.stateChanged.connect(self.update_auto_monitor_timer)
        self.auto_sell_checkbox.stateChanged.connect(self.update_auto_monitor_timer)
        auto_controls.addWidget(QLabel("매수 가능 금액"))
        auto_controls.addWidget(self.buy_amount_input)
        auto_controls.addWidget(self.auto_buy_checkbox)
        auto_controls.addWidget(self.auto_sell_checkbox)
        auto_controls.addWidget(self.auto_run_button)
        layout.addLayout(auto_controls)

        self.auto_search_input = QLineEdit()
        self.auto_search_input.setPlaceholderText("자동 감시에 적용할 검색어/조건. 비우면 종가 기준 후보 전체")
        layout.addWidget(self.auto_search_input)
        self.auto_status_label = QLabel("자동 감시 대기 중: 10분마다 데이터 갱신/조건 재계산/paper 주문 중복 체크")
        layout.addWidget(self.auto_status_label)
        self.update_auto_monitor_timer()

        self.universe_label = QLabel(self._universe_summary())
        layout.addWidget(self.universe_label)
        self.orders_table = QTableWidget()
        layout.addWidget(self.orders_table)
        layout.addWidget(QLabel("Paper 매수/매도 기록"))
        paper_buttons = QHBoxLayout()
        refresh_paper = QPushButton("Paper 기록 새로고침")
        refresh_paper.clicked.connect(self.refresh_paper_orders)
        paper_buttons.addWidget(refresh_paper)
        layout.addLayout(paper_buttons)
        self.paper_orders_table = QTableWidget()
        layout.addWidget(self.paper_orders_table)
        self.refresh_orders()
        self.refresh_paper_orders()
        return widget

    def _manual_search_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("로컬 OHLCV/유니버스 기준 조건 검색입니다. 투자 추천이 아니라 조건 통과 후보 조회입니다."))
        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("예: 삼성 / Apple / 미국 거래량 1.2배 / keyword=삼성")
        search_button = QPushButton("검색")
        search_button.clicked.connect(self.run_manual_search)
        row.addWidget(self.search_input)
        row.addWidget(search_button)
        layout.addLayout(row)
        self.search_table = QTableWidget()
        layout.addWidget(self.search_table)
        return widget

    def _review_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = QTextEdit()
        text.setReadOnly(True)
        report_path = Path("outputs/reports/gemma_review.md")
        text.setPlainText(report_path.read_text(encoding="utf-8", errors="ignore") if report_path.exists() else "리뷰 리포트가 없습니다.")
        layout.addWidget(text)
        return widget

    def refresh_holdings(self) -> None:
        try:
            broker = self._get_broker()
            domestic = display_holdings(normalize_domestic_holdings(broker.get_domestic_balance()))
            overseas = display_holdings(normalize_overseas_holdings(broker.get_overseas_balance()))
            set_table(self.domestic_table, domestic)
            set_table(self.overseas_table, overseas)
        except Exception as exc:
            QMessageBox.critical(self, "오류", str(exc))

    def run_recommendations(self) -> None:
        try:
            orders = run_recommendation_cycle(self.config)
            self.queue.append_many(orders)
            self.refresh_orders()
            QMessageBox.information(self, "완료", f"종가 후보 주문 {len(orders)}건을 추가했습니다.")
        except Exception as exc:
            QMessageBox.critical(self, "오류", str(exc))

    def update_auto_monitor_timer(self) -> None:
        enabled = self.auto_buy_checkbox.isChecked() or self.auto_sell_checkbox.isChecked()
        interval_minutes = int(self.config.get("desktop_automation", {}).get("interval_minutes", 10))
        if enabled:
            self.automation_timer.start(interval_minutes * 60 * 1000)
            self.auto_status_label.setText(f"자동 감시 켜짐: {interval_minutes}분마다 데이터 갱신/조건 재계산/paper 동작")
        else:
            self.automation_timer.stop()
            self.auto_status_label.setText("자동 감시 꺼짐")

    def run_auto_monitor_cycle(self) -> None:
        try:
            search_query = self.auto_search_input.text().strip() or self.last_manual_search_query
            if self.auto_buy_checkbox.isChecked() and not search_query:
                self.auto_status_label.setText("자동 매수 중단: 자동 감시 조건을 입력하거나 수동 검색을 먼저 실행하세요.")
                QMessageBox.information(
                    self,
                    "자동 매수 조건 필요",
                    "의도하지 않은 종목 매수를 막기 위해 자동 매수는 검색 조건이 있을 때만 실행합니다.",
                )
                return
            result = run_desktop_automation_cycle(
                self.config,
                search_query=search_query,
                available_buy_amount=float(self.buy_amount_input.value()),
                auto_buy=self.auto_buy_checkbox.isChecked(),
                auto_sell=self.auto_sell_checkbox.isChecked(),
                refresh_data=True,
            )
            self.universe_label.setText(self._universe_summary())
            self.auto_status_label.setText(f"{result.message} / 로그: {result.logs_path}")
            self.refresh_paper_orders()
        except Exception as exc:
            QMessageBox.critical(self, "?ㅻ쪟", str(exc))

    def refresh_orders(self) -> None:
        set_table(self.orders_table, pd.DataFrame(self.queue.read_all()))

    def refresh_paper_orders(self) -> None:
        frame = pd.DataFrame(self.paper_order_manager.read_all())
        if not frame.empty:
            if "name" not in frame.columns:
                frame["name"] = ""
            frame["name"] = frame.apply(lambda row: row.get("name") or self._symbol_name(str(row.get("symbol", ""))), axis=1)
            columns = [
                column
                for column in [
                    "created_at",
                    "market",
                    "symbol",
                    "name",
                    "side",
                    "quantity",
                    "reference_price",
                    "status",
                    "reason",
                    "dedupe_key",
                ]
                if column in frame.columns
            ]
            frame = frame[columns].sort_values("created_at", ascending=False)
        set_table(self.paper_orders_table, frame)

    def _symbol_name(self, symbol: str) -> str:
        symbol_key = str(symbol).upper()
        for market in ["KR", "US"]:
            universe = load_recommendation_universe(self.config, market)
            if universe.empty or "name" not in universe.columns:
                continue
            matches = universe[universe["symbol"].astype(str).str.upper() == symbol_key]
            if not matches.empty:
                return str(matches.iloc[0]["name"])
        return symbol

    def run_manual_search(self) -> None:
        try:
            query = self.search_input.text().strip()
            if not query:
                QMessageBox.information(self, "검색 조건 필요", "검색 조건을 입력하세요. 예: 거래량 1.2배 이상, 20일선 위")
                return
            defaults = self.config.get("manual_search", {})
            filters = parse_search_query(query, defaults)
            if not has_meaningful_filter(filters):
                QMessageBox.information(
                    self,
                    "조건 인식 실패",
                    "시장만 인식되면 목록이 거의 전부 표시됩니다. 키워드, 거래량, MA20, MA20>MA60, 패턴 같은 조건을 함께 입력하세요.",
                )
                return
            result = search_by_conditions(self.config, filters)
            set_table(self.search_table, result)
            self.last_manual_search_query = query
            if not self.auto_search_input.text().strip():
                self.auto_search_input.setText(query)
        except Exception as exc:
            QMessageBox.critical(self, "오류", str(exc))

    def update_selected_order(self, status: str) -> None:
        row = self.orders_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "선택 필요", "주문 행을 먼저 선택하세요.")
            return
        id_column = table_column_index(self.orders_table, "id")
        if id_column is None:
            QMessageBox.critical(self, "오류", "주문 ID 컬럼이 없습니다.")
            return
        order_id = self.orders_table.item(row, id_column).text()
        try:
            self.queue.update_status(order_id, status, "desktop manual action")
            self.refresh_orders()
        except Exception as exc:
            QMessageBox.critical(self, "오류", str(exc))

    def _universe_summary(self) -> str:
        kr = load_recommendation_universe(self.config, "KR")
        us = load_recommendation_universe(self.config, "US")
        data_path = Path(self.config["data"]["universe_ohlcv_file"])
        data_status = "있음" if data_path.exists() else "없음"
        return f"국내 {len(kr)}개 / 미국 {len(us)}개 / 분석 데이터: {data_status} ({data_path})"


def set_table(table: QTableWidget, frame: pd.DataFrame) -> None:
    table.clear()
    if frame is None or frame.empty:
        table.setRowCount(0)
        table.setColumnCount(0)
        return
    table.setColumnCount(len(frame.columns))
    table.setRowCount(len(frame))
    table.setHorizontalHeaderLabels([str(column) for column in frame.columns])
    for row_idx, (_, row) in enumerate(frame.iterrows()):
        for col_idx, value in enumerate(row):
            item = QTableWidgetItem("" if pd.isna(value) else str(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


def table_column_index(table: QTableWidget, name: str) -> int | None:
    for idx in range(table.columnCount()):
        header = table.horizontalHeaderItem(idx)
        if header and header.text() == name:
            return idx
    return None


def main() -> None:
    app = QApplication(sys.argv)
    window = TradingDesktopApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
