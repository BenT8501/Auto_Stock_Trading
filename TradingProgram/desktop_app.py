from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
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
from src.trading.automation import load_recommendation_universe, run_recommendation_cycle
from src.trading.order_queue import OrderQueue


class TradingDesktopApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("트레이딩 리서치 도구")
        self.resize(1200, 800)
        self.config = load_config("config.yaml")
        self.queue = OrderQueue()
        self.broker: KisBroker | None = None

        tabs = QTabWidget()
        tabs.addTab(self._holdings_tab(), "보유 주식")
        tabs.addTab(self._recommendations_tab(), "종가 기준 후보")
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

        self.universe_label = QLabel(self._universe_summary())
        layout.addWidget(self.universe_label)
        self.orders_table = QTableWidget()
        layout.addWidget(self.orders_table)
        self.refresh_orders()
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

    def refresh_orders(self) -> None:
        set_table(self.orders_table, pd.DataFrame(self.queue.read_all()))

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
