from __future__ import annotations

from copy import deepcopy
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.broker.holdings import display_holdings, normalize_domestic_holdings, normalize_overseas_holdings
from src.broker.kis import KisBroker
from src.broker.paper import PaperBroker
from src.config import load_config
from src.external_data_collector import collect_external_universe_ohlcv
from src.search.manual_search import has_meaningful_filter, search_by_conditions
from src.search.query_parser import parse_search_query
from src.trading.automation import (
    _calculate_order_quantity,
    _order_sizing_label,
    build_setup_candidates,
    load_recommendation_universe,
    run_recommendation_cycle,
)
from src.trading.desktop_automation import run_desktop_automation_cycle
from src.trading.order_manager import PaperOrderManager
from src.trading.order_queue import OrderCandidate, OrderQueue
from src.trading.position_manager import PositionManager


class TradingDesktopApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("트레이딩 리서치 도구")
        self.resize(1200, 800)
        self.config = load_config("config.yaml")
        self.queue = OrderQueue()
        self.paper_order_manager = PaperOrderManager()
        self.paper_broker = PaperBroker.from_config(self.config)
        self.position_manager = PositionManager()
        self.broker: KisBroker | None = None
        self.last_manual_search_query = ""
        self.raw_candidate_frame = pd.DataFrame()
        self.latest_candidate_frame = pd.DataFrame()
        self.latest_search_frame = pd.DataFrame()
        self.candidate_grade_filter = "ALL"
        self.candidate_bb_filter = "ALL"
        self.hidden_candidate_keys: set[str] = set()
        self.active_progress_dialog: QProgressDialog | None = None
        self.exit_requested = False
        self.automation_timer = QTimer(self)
        self.automation_timer.timeout.connect(self.run_auto_monitor_cycle)
        self.tray_icon = self._create_tray_icon()
        self.setStyleSheet(APP_STYLE)

        tabs = QTabWidget()
        tabs.addTab(self._holdings_tab(), "보유 주식")
        tabs.addTab(self._recommendations_tab(), "종가 기준 후보")
        tabs.addTab(self._manual_search_tab(), "수동 검색")
        tabs.addTab(self._review_tab(), "리뷰")
        self.setCentralWidget(tabs)

    def _create_tray_icon(self) -> QSystemTrayIcon | None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None

        icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip("트레이딩 리서치 도구")

        menu = QMenu(self)
        show_action = QAction("창 보이기", self)
        show_action.triggered.connect(self.show_from_tray)
        exit_action = QAction("완전 종료", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._handle_tray_activated)
        tray.show()
        return tray

    def _handle_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick}:
            self.show_from_tray()

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit_application(self) -> None:
        self.exit_requested = True
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.exit_requested or self.tray_icon is None:
            event.accept()
            return

        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "트레이딩 리서치 도구",
            "창은 숨겨졌고 프로그램은 백그라운드에서 계속 실행됩니다. 완전 종료는 트레이 메뉴에서 선택하세요.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _get_broker(self) -> KisBroker:
        if self.broker is None:
            self.broker = KisBroker.from_config(self.config)
        return self.broker

    def start_progress(self, title: str, message: str) -> None:
        self.active_progress_dialog = QProgressDialog(message, None, 0, 100, self)
        self.active_progress_dialog.setWindowTitle(title)
        self.active_progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.active_progress_dialog.setAutoClose(True)
        self.active_progress_dialog.setAutoReset(True)
        self.active_progress_dialog.setMinimumDuration(0)
        self.active_progress_dialog.setValue(0)
        QApplication.processEvents()

    def update_progress(self, value: int, message: str | None = None) -> None:
        if self.active_progress_dialog is None:
            return
        if message is not None:
            self.active_progress_dialog.setLabelText(message)
        self.active_progress_dialog.setValue(max(0, min(100, int(value))))
        QApplication.processEvents()

    def finish_progress(self, message: str = "완료") -> None:
        if self.active_progress_dialog is None:
            return
        self.active_progress_dialog.setLabelText(message)
        self.active_progress_dialog.setValue(100)
        QApplication.processEvents()
        self.active_progress_dialog = None

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

    def _holdings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        refresh = QPushButton("보유/자산 새로고침")
        refresh.clicked.connect(self.refresh_holdings)
        layout.addWidget(refresh)

        summary_box, summary_layout = section_box("자산 요약", "summary")
        summary_layout.addWidget(QLabel("실제 계좌 요약"))
        self.real_asset_summary_table = QTableWidget()
        self.real_asset_summary_table.setMinimumHeight(120)
        summary_layout.addWidget(self.real_asset_summary_table)
        summary_layout.addWidget(QLabel("가상 투자 요약"))
        self.paper_asset_summary_table = QTableWidget()
        self.paper_asset_summary_table.setMinimumHeight(120)
        summary_layout.addWidget(self.paper_asset_summary_table)
        layout.addWidget(summary_box)

        real_box, real_layout = section_box("실제 투자 보유 목록", "holdings")
        real_layout.addWidget(QLabel("국내 보유 주식"))
        self.domestic_table = QTableWidget()
        self.domestic_table.setMinimumHeight(220)
        real_layout.addWidget(self.domestic_table)
        real_layout.addWidget(QLabel("해외 보유 주식"))
        self.overseas_table = QTableWidget()
        self.overseas_table.setMinimumHeight(220)
        real_layout.addWidget(self.overseas_table)
        layout.addWidget(real_box)

        paper_box, paper_layout = section_box("가상 투자 보유 목록", "paper")
        self.paper_positions_table = QTableWidget()
        self.paper_positions_table.setMinimumHeight(260)
        paper_layout.addWidget(self.paper_positions_table)
        layout.addWidget(paper_box)

        return scrollable_panel(widget)

    def _recommendations_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel("장마감 후 갱신된 OHLCV 데이터 기반 종가 후보입니다. KIS는 보유 종목/주문 단계에만 사용합니다.")
        layout.addWidget(info)

        data_box, data_layout = section_box("데이터 갱신", "data")
        data_box.setMaximumHeight(115)
        data_controls = QHBoxLayout()
        self.data_status_label = QLabel("")
        self.refresh_history_days_input = QSpinBox()
        self.refresh_history_days_input.setRange(30, 1500)
        self.refresh_history_days_input.setSingleStep(30)
        self.refresh_history_days_input.setValue(int(self.config["strategy"]["data_window"].get("history_days", 365)))
        self.refresh_limit_input = QSpinBox()
        self.refresh_limit_input.setRange(0, 500)
        self.refresh_limit_input.setSingleStep(10)
        self.refresh_limit_input.setValue(0)
        self.refresh_data_button = QPushButton("분석 CSV 갱신")
        self.refresh_data_button.clicked.connect(self.refresh_analysis_data)
        refresh_data_status = QPushButton("CSV 상태 새로고침")
        refresh_data_status.clicked.connect(self.refresh_data_status)
        add_step_control(data_controls, "수집 기간(일)", self.refresh_history_days_input)
        add_step_control(data_controls, "시장별 제한(0=전체)", self.refresh_limit_input)
        data_controls.addWidget(self.refresh_data_button)
        data_controls.addWidget(refresh_data_status)
        data_layout.addLayout(data_controls)
        data_layout.addWidget(self.data_status_label)
        layout.addWidget(data_box)

        order_box, order_layout = section_box("후보 분석 및 주문 기준", "order")
        order_box.setMaximumHeight(170)
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
        order_layout.addLayout(buttons)

        sizing_controls = QHBoxLayout()
        self.order_sizing_mode = QComboBox()
        self.order_sizing_mode.addItems(["금액", "수량", "자산비율"])
        self.order_amount_krw_input = QDoubleSpinBox()
        self.order_amount_krw_input.setRange(0, 1_000_000_000)
        self.order_amount_krw_input.setDecimals(0)
        self.order_amount_krw_input.setSingleStep(100_000)
        self.order_amount_krw_input.setValue(float(self.config.get("automation", {}).get("max_order_amount_krw", 1_000_000)))
        self.order_amount_usd_input = QDoubleSpinBox()
        self.order_amount_usd_input.setRange(0, 10_000_000)
        self.order_amount_usd_input.setDecimals(0)
        self.order_amount_usd_input.setSingleStep(100)
        self.order_amount_usd_input.setValue(float(self.config.get("automation", {}).get("max_order_amount_usd", 1_000)))
        self.order_quantity_input = QDoubleSpinBox()
        self.order_quantity_input.setRange(0, 1_000_000)
        self.order_quantity_input.setDecimals(0)
        self.order_quantity_input.setSingleStep(1)
        self.order_quantity_input.setValue(1)
        self.order_equity_pct_input = QDoubleSpinBox()
        self.order_equity_pct_input.setRange(0, 100)
        self.order_equity_pct_input.setDecimals(2)
        self.order_equity_pct_input.setSingleStep(0.5)
        self.order_equity_pct_input.setValue(float(self.config.get("risk", {}).get("position_size_pct", 0.05)) * 100)
        sizing_controls.addWidget(QLabel("주문 기준"))
        sizing_controls.addWidget(self.order_sizing_mode)
        add_step_control(sizing_controls, "KRW", self.order_amount_krw_input)
        add_step_control(sizing_controls, "USD", self.order_amount_usd_input)
        add_step_control(sizing_controls, "수량", self.order_quantity_input)
        add_step_control(sizing_controls, "자산 %", self.order_equity_pct_input)
        order_layout.addLayout(sizing_controls)
        safety_controls = QHBoxLayout()
        self.safety_a_only_checkbox = QCheckBox("A등급만 주문 후보")
        self.safety_a_only_checkbox.setChecked(True)
        self.safety_exclude_bc_checkbox = QCheckBox("B/C 주문 후보 제외")
        self.safety_exclude_bc_checkbox.setChecked(True)
        self.safety_exclude_etf_checkbox = QCheckBox("ETF 주문 제외")
        self.safety_exclude_etf_checkbox.setChecked(True)
        self.safety_manual_approval_checkbox = QCheckBox("수동 승인 필수")
        self.safety_manual_approval_checkbox.setChecked(True)
        self.safety_manual_approval_checkbox.setEnabled(False)
        safety_controls.addWidget(self.safety_a_only_checkbox)
        safety_controls.addWidget(self.safety_exclude_bc_checkbox)
        safety_controls.addWidget(self.safety_exclude_etf_checkbox)
        safety_controls.addWidget(self.safety_manual_approval_checkbox)
        order_layout.addLayout(safety_controls)
        layout.addWidget(order_box)

        automation = self.config.get("desktop_automation", {})
        automation_box, automation_layout = section_box("자동 감시", "automation")
        automation_box.setMaximumHeight(135)
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
        add_step_control(auto_controls, "매수 가능 금액", self.buy_amount_input)
        auto_controls.addWidget(self.auto_buy_checkbox)
        auto_controls.addWidget(self.auto_sell_checkbox)
        auto_controls.addWidget(self.auto_run_button)
        automation_layout.addLayout(auto_controls)

        self.auto_search_input = QLineEdit()
        self.auto_search_input.setPlaceholderText("자동 감시에 적용할 검색어/조건. 비우면 종가 기준 후보 전체")
        automation_layout.addWidget(self.auto_search_input)
        self.auto_status_label = QLabel("자동 감시 대기 중: 10분마다 데이터 갱신/조건 재계산/paper 주문 중복 체크")
        automation_layout.addWidget(self.auto_status_label)
        self.update_auto_monitor_timer()
        layout.addWidget(automation_box)

        candidates_box, candidates_layout = section_box("후보 목록", "candidates")
        self.universe_label = QLabel(self._universe_summary())
        candidates_layout.addWidget(self.universe_label)
        candidate_actions = QHBoxLayout()
        add_checked_candidates = QPushButton("체크한 A등급 주문 대기열 추가")
        add_checked_candidates.clicked.connect(self.add_checked_candidates_to_order_queue)
        clear_candidate_checks = QPushButton("후보 체크 해제")
        clear_candidate_checks.clicked.connect(lambda: clear_table_checks(self.candidates_table))
        candidate_actions.addWidget(add_checked_candidates)
        candidate_actions.addWidget(clear_candidate_checks)
        candidates_layout.addLayout(candidate_actions)
        add_button_grid(
            candidates_layout,
            [
                ("전체", lambda _checked=False: self.set_candidate_grade_filter("ALL")),
                ("A만 보기", lambda _checked=False: self.set_candidate_grade_filter("A")),
                ("B만 보기", lambda _checked=False: self.set_candidate_grade_filter("B")),
                ("C만 보기", lambda _checked=False: self.set_candidate_grade_filter("C")),
                ("ETF만 보기", lambda _checked=False: self.set_candidate_grade_filter("ETF")),
                ("BB 전체", lambda _checked=False: self.set_candidate_bb_filter("ALL")),
                ("BB 돌파", lambda _checked=False: self.set_candidate_bb_filter("is_bb_upper_breakout")),
                ("상단 근접", lambda _checked=False: self.set_candidate_bb_filter("is_bb_upper_near")),
                ("스퀴즈", lambda _checked=False: self.set_candidate_bb_filter("is_bb_squeeze")),
                ("스퀴즈 돌파", lambda _checked=False: self.set_candidate_bb_filter("is_bb_squeeze_breakout")),
                ("밴드 확장", lambda _checked=False: self.set_candidate_bb_filter("is_bb_width_expanding")),
            ],
            columns=4,
        )
        add_button_grid(
            candidates_layout,
            [
                ("차트 보기", self.show_selected_candidate_chart),
                ("캔들패턴 보기", self.show_selected_candidate_patterns),
                ("볼린저 보기", self.show_selected_candidate_bollinger),
                ("후보 사유 보기", self.show_selected_candidate_reason),
                ("관심종목 추가", self.add_selected_candidate_to_watchlist),
                ("주문 후보로 표시", self.mark_selected_candidate_order_candidate),
                ("제외", self.exclude_selected_candidate),
            ],
            columns=4,
        )
        grade_filters = QHBoxLayout()
        for label, value in [
            ("전체", "ALL"),
            ("A만 보기", "A"),
            ("B만 보기", "B"),
            ("C만 보기", "C"),
            ("ETF만 보기", "ETF"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, filter_value=value: self.set_candidate_grade_filter(filter_value))
            grade_filters.addWidget(button)
        candidates_layout.addLayout(grade_filters)
        hide_layout_widgets(grade_filters)
        bb_filters = QHBoxLayout()
        for label, value in [
            ("BB 전체", "ALL"),
            ("BB 돌파", "is_bb_upper_breakout"),
            ("상단 근접", "is_bb_upper_near"),
            ("스퀴즈", "is_bb_squeeze"),
            ("스퀴즈 돌파", "is_bb_squeeze_breakout"),
            ("밴드 확장", "is_bb_width_expanding"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, filter_value=value: self.set_candidate_bb_filter(filter_value))
            bb_filters.addWidget(button)
        candidates_layout.addLayout(bb_filters)
        hide_layout_widgets(bb_filters)
        detail_actions = QHBoxLayout()
        for label, handler in [
            ("차트 보기", self.show_selected_candidate_chart),
            ("캔들패턴 보기", self.show_selected_candidate_patterns),
            ("볼린저 보기", self.show_selected_candidate_bollinger),
            ("후보 사유 보기", self.show_selected_candidate_reason),
            ("관심종목 추가", self.add_selected_candidate_to_watchlist),
            ("주문 후보로 표시", self.mark_selected_candidate_order_candidate),
            ("제외", self.exclude_selected_candidate),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            detail_actions.addWidget(button)
        candidates_layout.addLayout(detail_actions)
        hide_layout_widgets(detail_actions)
        candidates_layout.addWidget(QLabel("후보 등급 목록"))
        self.candidates_table = QTableWidget()
        self.candidates_table.setMinimumHeight(360)
        candidates_layout.addWidget(self.candidates_table)

        records_box, records_layout = section_box("주문 대기열 및 Paper 기록", "records")
        records_layout.addWidget(QLabel("A등급 주문 대기열"))
        self.orders_table = QTableWidget()
        self.orders_table.setMinimumHeight(180)
        records_layout.addWidget(self.orders_table)
        records_layout.addWidget(QLabel("Paper 매수/매도 기록"))
        paper_buttons = QHBoxLayout()
        refresh_paper = QPushButton("Paper 기록 새로고침")
        refresh_paper.clicked.connect(lambda: self.refresh_paper_orders())
        paper_buttons.addWidget(refresh_paper)
        records_layout.addLayout(paper_buttons)
        self.paper_orders_table = QTableWidget()
        self.paper_orders_table.setMinimumHeight(180)
        records_layout.addWidget(self.paper_orders_table)
        result_tabs = QTabWidget()
        result_tabs.addTab(candidates_box, "후보 목록")
        result_tabs.addTab(records_box, "주문/기록")
        layout.addWidget(result_tabs, 1)
        self.refresh_data_status()
        self.refresh_orders()
        self.refresh_paper_orders(show_progress=False)
        return scrollable_panel(widget)

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
        search_actions = QHBoxLayout()
        add_checked_search = QPushButton("체크한 A등급 주문 대기열 추가")
        add_checked_search.clicked.connect(self.add_checked_search_to_order_queue)
        clear_search_checks = QPushButton("검색 체크 해제")
        clear_search_checks.clicked.connect(lambda: clear_table_checks(self.search_table))
        search_actions.addWidget(add_checked_search)
        search_actions.addWidget(clear_search_checks)
        layout.addLayout(search_actions)
        self.search_table = QTableWidget()
        self.search_table.setMinimumHeight(520)
        layout.addWidget(self.search_table)
        return scrollable_panel(widget)

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
            self.start_progress("보유 주식 새로고침", "KIS 보유 주식 정보를 요청하는 중입니다.")
            broker = self._get_broker()
            self.update_progress(30, "국내 보유 주식을 불러오는 중입니다.")
            domestic = display_holdings(normalize_domestic_holdings(broker.get_domestic_balance()))
            self.update_progress(65, "해외 보유 주식을 불러오는 중입니다.")
            overseas = display_holdings(normalize_overseas_holdings(broker.get_overseas_balance()))
            set_table(self.domestic_table, domestic)
            set_table(self.overseas_table, overseas)
            self.finish_progress("보유 주식 새로고침 완료")
        except Exception as exc:
            self.finish_progress("보유 주식 새로고침 실패")
            QMessageBox.critical(self, "오류", str(exc))

    def refresh_holdings(self) -> None:
        real_error = ""
        domestic = pd.DataFrame()
        overseas = pd.DataFrame()
        try:
            self.start_progress("보유/자산 새로고침", "실제 계좌와 가상 투자 현황을 갱신하는 중입니다.")
            try:
                broker = self._get_broker()
                self.update_progress(20, "국내 보유 주식을 불러오는 중입니다.")
                domestic = display_holdings(normalize_domestic_holdings(broker.get_domestic_balance()))
                self.update_progress(45, "해외 보유 주식을 불러오는 중입니다.")
                overseas = display_holdings(normalize_overseas_holdings(broker.get_overseas_balance()))
            except Exception as exc:
                real_error = str(exc)

            self.update_progress(65, "가상 투자 포지션을 불러오는 중입니다.")
            paper_state = self.paper_broker.snapshot()
            paper_positions = build_paper_positions_frame(paper_state, self.position_manager.read_all())

            self.update_progress(82, "자산 요약을 계산하는 중입니다.")
            set_table(self.domestic_table, domestic)
            set_table(self.overseas_table, overseas)
            set_table(self.real_asset_summary_table, build_real_asset_summary(domestic, overseas, real_error))
            set_table(self.paper_positions_table, paper_positions)
            set_table(self.paper_asset_summary_table, build_paper_asset_summary(paper_state, paper_positions))

            self.finish_progress("보유/자산 새로고침 완료")
            if real_error:
                QMessageBox.warning(
                    self,
                    "실제 계좌 조회 실패",
                    f"실제 계좌 정보는 불러오지 못했습니다.\n가상 투자 현황은 갱신했습니다.\n\n{real_error}",
                )
        except Exception as exc:
            self.finish_progress("보유/자산 새로고침 실패")
            QMessageBox.critical(self, "오류", str(exc))

    def run_recommendations(self) -> None:
        try:
            self.start_progress("종가 후보 분석", "주문 기준 설정을 준비하는 중입니다.")
            order_config = self._order_config()
            self.update_progress(20, "후보 등급과 보조 지표를 계산하는 중입니다.")
            candidates = build_setup_candidates(order_config)
            self.update_progress(55, "후보 목록 화면을 갱신하는 중입니다.")
            self.refresh_candidates(candidates)
            self.update_progress(75, "A등급 주문 대기열을 계산하는 중입니다.")
            orders = run_recommendation_cycle(order_config)
            self.queue.append_many(orders)
            self.update_progress(70, "주문 대기열 화면을 갱신하는 중입니다.")
            self.refresh_orders()
            self.finish_progress("종가 후보 분석 완료")
            QMessageBox.information(
                self,
                "완료",
                f"표시 후보 {len(candidates)}건을 갱신했습니다.\nA등급 주문 대기열 {len(orders)}건을 반영했습니다.",
            )
        except Exception as exc:
            self.finish_progress("종가 후보 분석 실패")
            QMessageBox.critical(self, "오류", str(exc))

    def _order_config(self) -> dict:
        config = deepcopy(self.config)
        automation = config.setdefault("automation", {})
        mode_label = self.order_sizing_mode.currentText()
        if mode_label == "수량":
            mode = "fixed_quantity"
        elif mode_label == "자산비율":
            mode = "equity_pct"
        else:
            mode = "fixed_amount"
        automation["order_sizing"] = {
            "mode": mode,
            "amount_krw": float(self.order_amount_krw_input.value()),
            "amount_usd": float(self.order_amount_usd_input.value()),
            "quantity": float(self.order_quantity_input.value()),
            "equity_pct": float(self.order_equity_pct_input.value()),
        }
        return config

    def refresh_analysis_data(self) -> None:
        try:
            self.refresh_data_button.setEnabled(False)
            self.start_progress("분석 CSV 갱신", "갱신 준비 중입니다.")
            QApplication.processEvents()

            data = collect_external_universe_ohlcv(
                self.config,
                history_days=int(self.refresh_history_days_input.value()),
                limit_per_market=int(self.refresh_limit_input.value()) or None,
                progress_callback=self.update_refresh_progress,
            )
            self.finish_progress("분석 CSV 갱신 완료")
            self.refresh_data_status()
            self.update_progress(80, "자동 감시 결과를 화면에 반영하는 중입니다.")
            self.universe_label.setText(self._universe_summary())
            QMessageBox.information(
                self,
                "갱신 완료",
                f"분석 CSV를 갱신했습니다.\n종목 수: {data['symbol'].nunique() if not data.empty else 0}\n행 수: {len(data)}",
            )
        except Exception as exc:
            self.finish_progress("분석 CSV 갱신 실패")
            QMessageBox.critical(self, "오류", str(exc))
        finally:
            self.refresh_data_button.setEnabled(True)

    def update_refresh_progress(self, completed: int, total: int, symbol: str, market: str) -> None:
        if total <= 0:
            self.finish_progress("갱신 대상 없음")
            QApplication.processEvents()
            return

        percent = int(completed / total * 100)
        if market == "done":
            self.finish_progress("갱신 완료 100%")
        elif market == "start":
            self.update_progress(0, f"갱신 시작 0% / 대상 {total}개")
        else:
            self.update_progress(percent, f"{percent}% ({completed}/{total}) {market} {symbol}")
        QApplication.processEvents()

    def refresh_data_status(self) -> None:
        self.data_status_label.setText(self._data_file_summary())

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
            self.start_progress("자동 감시 1회 실행", "자동 감시 설정을 준비하는 중입니다.")
            order_config = self._order_config()
            search_query = self.auto_search_input.text().strip() or self.last_manual_search_query
            self.update_progress(25, "데이터 갱신과 후보 재계산을 실행하는 중입니다.")
            result = run_desktop_automation_cycle(
                order_config,
                search_query=search_query,
                available_buy_amount=float(self.buy_amount_input.value()),
                auto_buy=self.auto_buy_checkbox.isChecked(),
                auto_sell=self.auto_sell_checkbox.isChecked(),
                refresh_data=True,
            )
            self.universe_label.setText(self._universe_summary())
            self.auto_status_label.setText(f"{result.message} / 로그: {result.logs_path}")
            if self.auto_buy_checkbox.isChecked() and result.buy_orders_created == 0:
                self.auto_status_label.setText(
                    f"{result.message} / A등급 후보가 없거나 중복 주문입니다. / 로그: {result.logs_path}"
                )
            self.refresh_paper_orders(show_progress=False)
            self.finish_progress("자동 감시 1회 실행 완료")
        except Exception as exc:
            self.finish_progress("자동 감시 1회 실행 실패")
            QMessageBox.critical(self, "?ㅻ쪟", str(exc))

    def refresh_orders(self) -> None:
        set_table(self.orders_table, pd.DataFrame(self.queue.read_all()))

    def refresh_candidates(self, candidates: pd.DataFrame) -> None:
        if candidates.empty:
            self.raw_candidate_frame = pd.DataFrame()
            self.latest_candidate_frame = pd.DataFrame()
            set_table(self.candidates_table, candidates, checkable=True)
            return
        columns = [
            column
            for column in [
                "candidate_grade",
                "market",
                "symbol",
                "name",
                "is_etf",
                "pattern",
                "buy_pattern",
                "candidate_reason",
                "bb_signal_summary",
                "close",
                "prev_close",
                "volume_ratio",
                "prev_volume",
                "ma_short",
                "ma20",
                "ma_long",
                "ma60",
                "ma20_slope",
                "volume_ma",
                "volume_ma20",
                "bb_position",
                "bb_width",
                "is_bb_upper_breakout",
                "is_bb_upper_near",
                "is_bb_squeeze",
                "is_bb_squeeze_breakout",
                "is_bb_width_expanding",
                "trigger_price",
                "date",
                "trade_date",
            ]
            if column in candidates.columns
        ]
        grade_order = {"A": 0, "B": 1, "C": 2, "ETF_A": 3, "ETF_B": 4}
        frame = candidates[columns].copy()
        frame["_grade_order"] = frame["candidate_grade"].map(grade_order).fillna(99)
        frame = frame.sort_values(["_grade_order", "market", "symbol"]).drop(columns=["_grade_order"])
        self.raw_candidate_frame = frame.reset_index(drop=True)
        self.apply_candidate_filters()

    def set_candidate_grade_filter(self, value: str) -> None:
        self.candidate_grade_filter = value
        self.apply_candidate_filters()

    def set_candidate_bb_filter(self, value: str) -> None:
        self.candidate_bb_filter = value
        self.apply_candidate_filters()

    def apply_candidate_filters(self) -> None:
        frame = self.raw_candidate_frame.copy()
        if frame.empty:
            self.latest_candidate_frame = frame
            set_table(self.candidates_table, frame, checkable=True)
            return
        if self.hidden_candidate_keys:
            keys = frame.apply(lambda row: candidate_key(row), axis=1)
            frame = frame[~keys.isin(self.hidden_candidate_keys)]
        if self.candidate_grade_filter == "ETF":
            frame = frame[frame["candidate_grade"].astype(str).str.startswith("ETF")]
        elif self.candidate_grade_filter != "ALL":
            frame = frame[frame["candidate_grade"].astype(str) == self.candidate_grade_filter]
        if self.candidate_bb_filter != "ALL" and self.candidate_bb_filter in frame.columns:
            frame = frame[frame[self.candidate_bb_filter].astype(bool)]
        self.latest_candidate_frame = frame.reset_index(drop=True)
        set_table(self.candidates_table, self.latest_candidate_frame, checkable=True)

    def _selected_candidate_row(self) -> pd.Series | None:
        row_idx = self.candidates_table.currentRow()
        if row_idx < 0:
            checked = checked_table_rows(self.candidates_table)
            row_idx = checked[0] if checked else -1
        if row_idx < 0 or row_idx >= len(self.latest_candidate_frame):
            QMessageBox.information(self, "선택 필요", "먼저 후보 행을 선택하거나 체크하세요.")
            return None
        return self.latest_candidate_frame.iloc[row_idx]

    def show_selected_candidate_reason(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        QMessageBox.information(
            self,
            "후보 사유",
            f"{row.get('symbol', '')} {row.get('name', '')}\n\n"
            f"{row.get('candidate_reason', '')}\n\n{row.get('bb_signal_summary', '')}",
        )

    def show_selected_candidate_bollinger(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        QMessageBox.information(
            self,
            "볼린저 보기",
            "\n".join(
                [
                    f"종목: {row.get('symbol', '')} {row.get('name', '')}",
                    f"요약: {row.get('bb_signal_summary', '')}",
                    f"position: {_number(row.get('bb_position')):.3f}",
                    f"width: {_number(row.get('bb_width')):.3f}",
                    f"upper breakout: {bool(row.get('is_bb_upper_breakout', False))}",
                    f"near upper: {bool(row.get('is_bb_upper_near', False))}",
                    f"squeeze: {bool(row.get('is_bb_squeeze', False))}",
                    f"squeeze breakout: {bool(row.get('is_bb_squeeze_breakout', False))}",
                    f"width expanding: {bool(row.get('is_bb_width_expanding', False))}",
                ]
            ),
        )

    def show_selected_candidate_patterns(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        QMessageBox.information(
            self,
            "캔들패턴 보기",
            f"종목: {row.get('symbol', '')} {row.get('name', '')}\n"
            f"패턴: {row.get('pattern') or row.get('buy_pattern') or '-'}\n"
            f"등급: {row.get('candidate_grade', '')}",
        )

    def show_selected_candidate_chart(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        QMessageBox.information(
            self,
            "차트 보기",
            "\n".join(
                [
                    "현재 버전은 차트 핵심 수치를 먼저 표시합니다.",
                    f"종목: {row.get('symbol', '')} {row.get('name', '')}",
                    f"종가: {_number(row.get('close') or row.get('prev_close')):,.2f}",
                    f"MA20: {_number(row.get('ma_short') or row.get('ma20')):,.2f}",
                    f"MA60: {_number(row.get('ma_long') or row.get('ma60')):,.2f}",
                    f"거래량 배수: {_number(row.get('volume_ratio')):.2f}x",
                    f"BB: {row.get('bb_signal_summary', '')}",
                ]
            ),
        )

    def add_selected_candidate_to_watchlist(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        self.start_progress("관심종목 추가", "관심종목 파일을 준비하는 중입니다.")
        path = Path("outputs/manual_watchlist.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.update_progress(45, "선택 후보를 관심종목으로 저장하는 중입니다.")
        record = pd.DataFrame([row.to_dict()])
        if path.exists():
            existing = pd.read_csv(path, dtype={"symbol": str})
            record = pd.concat([existing, record], ignore_index=True)
            record = record.drop_duplicates(subset=["market", "symbol"], keep="last")
        record.to_csv(path, index=False)
        self.finish_progress("관심종목 추가 완료")
        QMessageBox.information(self, "관심종목 추가", f"{row.get('symbol', '')}을 관심종목 파일에 저장했습니다.\n{path}")

    def mark_selected_candidate_order_candidate(self) -> None:
        row_idx = self.candidates_table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "선택 필요", "주문 후보로 표시할 행을 선택하세요.")
            return
        clear_table_checks(self.candidates_table)
        item = self.candidates_table.item(row_idx, 0)
        if item is not None:
            item.setCheckState(Qt.CheckState.Checked)
        self.add_checked_candidates_to_order_queue()

    def exclude_selected_candidate(self) -> None:
        row = self._selected_candidate_row()
        if row is None:
            return
        self.hidden_candidate_keys.add(candidate_key(row))
        self.apply_candidate_filters()

    def add_checked_candidates_to_order_queue(self) -> None:
        if self.latest_candidate_frame.empty:
            QMessageBox.information(self, "후보 없음", "먼저 종가 후보 분석을 실행하세요.")
            return

        checked_rows = checked_table_rows(self.candidates_table)
        if not checked_rows:
            QMessageBox.information(self, "선택 필요", "주문 대기열에 추가할 A등급 후보를 체크하세요.")
            return

        self.start_progress("주문 대기열 추가", f"체크한 후보 {len(checked_rows)}건을 확인하는 중입니다.")
        config = self._order_config()
        orders: list[OrderCandidate] = []
        skipped_non_a = 0
        skipped_etf = 0
        skipped_quantity = 0
        total_rows = max(1, len(checked_rows))
        for progress_idx, row_idx in enumerate(checked_rows, start=1):
            self.update_progress(10 + int(progress_idx / total_rows * 65), f"후보 {progress_idx}/{total_rows}건 처리 중입니다.")
            if row_idx >= len(self.latest_candidate_frame):
                continue
            row = self.latest_candidate_frame.iloc[row_idx]
            grade = str(row.get("candidate_grade", ""))
            if self.safety_a_only_checkbox.isChecked() and grade != "A":
                skipped_non_a += 1
                continue
            if self.safety_exclude_bc_checkbox.isChecked() and grade in {"B", "C"}:
                skipped_non_a += 1
                continue
            if self.safety_exclude_etf_checkbox.isChecked() and (grade.startswith("ETF") or _truthy(row.get("is_etf", False))):
                skipped_etf += 1
                continue
            market = str(row.get("market", "US")).upper()
            symbol = str(row.get("symbol", ""))
            name = str(row.get("name") or symbol)
            price = _number(row.get("prev_close") or row.get("trigger_price") or row.get("close"))
            quantity = _calculate_order_quantity(price, market, config)
            if quantity <= 0:
                skipped_quantity += 1
                continue
            reason = f"{row.get('candidate_reason', 'A Grade')}; {_order_sizing_label(config, market)}"
            orders.append(
                OrderCandidate.create(
                    market=market.lower(),
                    symbol=symbol,
                    name=name,
                    side="BUY",
                    quantity=quantity,
                    reference_price=price,
                    reason=reason,
                )
            )

        queued = self.queue.append_many(orders)
        self.update_progress(90, "주문 대기열 화면을 갱신하는 중입니다.")
        self.refresh_orders()
        self.finish_progress("주문 대기열 추가 완료")
        QMessageBox.information(
            self,
            "주문 대기열 반영",
            f"추가 대상 {len(orders)}건 / 대기열 반영 {queued}건\n"
            f"A/B/C 안전 제외 {skipped_non_a}건 / ETF 제외 {skipped_etf}건 / 수량 0 제외 {skipped_quantity}건",
        )

    def add_checked_search_to_order_queue(self) -> None:
        if self.latest_search_frame.empty:
            QMessageBox.information(self, "검색 결과 없음", "먼저 수동 검색을 실행하세요.")
            return

        checked_rows = checked_table_rows(self.search_table)
        if not checked_rows:
            QMessageBox.information(self, "선택 필요", "주문 대기열에 추가할 A등급 검색 결과를 체크하세요.")
            return

        self.start_progress("검색 결과 주문 대기열 추가", f"체크한 검색 결과 {len(checked_rows)}건을 확인하는 중입니다.")
        config = self._order_config()
        orders: list[OrderCandidate] = []
        skipped_non_a = 0
        skipped_etf = 0
        skipped_quantity = 0
        total_rows = max(1, len(checked_rows))
        for progress_idx, row_idx in enumerate(checked_rows, start=1):
            self.update_progress(10 + int(progress_idx / total_rows * 65), f"검색 결과 {progress_idx}/{total_rows}건 처리 중입니다.")
            if row_idx >= len(self.latest_search_frame):
                continue
            row = self.latest_search_frame.iloc[row_idx]
            grade = str(row.get("candidate_grade", ""))
            if self.safety_a_only_checkbox.isChecked() and grade != "A":
                skipped_non_a += 1
                continue
            if self.safety_exclude_bc_checkbox.isChecked() and grade in {"B", "C"}:
                skipped_non_a += 1
                continue
            if self.safety_exclude_etf_checkbox.isChecked() and (grade.startswith("ETF") or _truthy(row.get("is_etf", False))):
                skipped_etf += 1
                continue
            market = str(row.get("market", "US")).upper()
            symbol = str(row.get("symbol", ""))
            name = str(row.get("name") or symbol)
            price = _number(row.get("prev_close") or row.get("trigger_price") or row.get("close"))
            quantity = _calculate_order_quantity(price, market, config)
            if quantity <= 0:
                skipped_quantity += 1
                continue
            reason = f"{row.get('candidate_reason', 'manual search A Grade')}; {_order_sizing_label(config, market)}"
            orders.append(
                OrderCandidate.create(
                    market=market.lower(),
                    symbol=symbol,
                    name=name,
                    side="BUY",
                    quantity=quantity,
                    reference_price=price,
                    reason=reason,
                )
            )

        queued = self.queue.append_many(orders)
        self.update_progress(90, "주문 대기열 화면을 갱신하는 중입니다.")
        self.refresh_orders()
        self.finish_progress("검색 결과 주문 대기열 추가 완료")
        QMessageBox.information(
            self,
            "주문 대기열 반영",
            f"추가 대상 {len(orders)}건 / 대기열 반영 {queued}건\n"
            f"A/B/C 안전 제외 {skipped_non_a}건 / ETF 제외 {skipped_etf}건 / 수량 0 제외 {skipped_quantity}건",
        )

    def refresh_paper_orders(self, show_progress: bool = True) -> None:
        if show_progress:
            self.start_progress("Paper 기록 새로고침", "Paper 주문 기록을 불러오는 중입니다.")
        frame = pd.DataFrame(self.paper_order_manager.read_all())
        if show_progress:
            self.update_progress(60, "Paper 주문 기록을 정리하는 중입니다.")
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
        if show_progress:
            self.finish_progress("Paper 기록 새로고침 완료")

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
            self.start_progress("검색", "검색 조건을 해석하는 중입니다.")
            defaults = self.config.get("manual_search", {})
            filters = parse_search_query(query, defaults)
            if not has_meaningful_filter(filters):
                self.finish_progress("검색 조건 확인 완료")
                QMessageBox.information(
                    self,
                    "조건 인식 실패",
                    "시장만 인식되면 목록이 거의 전부 표시됩니다. 키워드, 거래량, MA20, MA20>MA60, 패턴 같은 조건을 함께 입력하세요.",
                )
                return
            self.update_progress(45, "조건에 맞는 후보를 검색하는 중입니다.")
            result = search_by_conditions(self.config, filters)
            self.update_progress(80, "검색 결과를 화면에 표시하는 중입니다.")
            self.latest_search_frame = result.copy().reset_index(drop=True)
            set_table(self.search_table, result, checkable=True)
            self.last_manual_search_query = query
            if not self.auto_search_input.text().strip():
                self.auto_search_input.setText(query)
            self.finish_progress("검색 완료")
        except Exception as exc:
            self.finish_progress("검색 실패")
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
            action_label = "수동 승인" if status == "approved_paper" else "주문 거절"
            self.start_progress(action_label, "선택 주문 상태를 업데이트하는 중입니다.")
            self.queue.update_status(order_id, status, "desktop manual action")
            self.update_progress(70, "주문 대기열 화면을 갱신하는 중입니다.")
            self.refresh_orders()
            self.finish_progress(f"{action_label} 완료")
        except Exception as exc:
            self.finish_progress("주문 상태 업데이트 실패")
            QMessageBox.critical(self, "오류", str(exc))

    def _universe_summary(self) -> str:
        kr = load_recommendation_universe(self.config, "KR")
        us = load_recommendation_universe(self.config, "US")
        data_path = Path(self.config["data"]["universe_ohlcv_file"])
        data_status = "있음" if data_path.exists() else "없음"
        return f"국내 {len(kr)}개 / 미국 {len(us)}개 / 분석 데이터: {data_status} ({data_path})"

    def _data_file_summary(self) -> str:
        data_path = Path(self.config["data"]["universe_ohlcv_file"])
        if not data_path.exists():
            return f"분석 CSV 없음: {data_path} / `분석 CSV 갱신`을 눌러 생성하세요."
        try:
            stat = data_path.stat()
            frame = pd.read_csv(data_path, usecols=["date", "symbol"])
            dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
            latest_date = dates.max().strftime("%Y-%m-%d") if not dates.empty else "-"
            modified_at = pd.Timestamp(stat.st_mtime, unit="s").strftime("%Y-%m-%d %H:%M:%S")
            symbols = frame["symbol"].astype(str)
            kr_count = symbols[symbols.str.fullmatch(r"\d{6}")].nunique()
            us_count = symbols[~symbols.str.fullmatch(r"\d{6}")].nunique()
            return (
                f"분석 CSV: {data_path} / 행 {len(frame):,}개 / KR {kr_count:,}개 / US {us_count:,}개 / "
                f"최근 일자 {latest_date} / 수정 {modified_at}"
            )
        except Exception as exc:
            return f"분석 CSV 상태 확인 실패: {data_path} / {exc}"


def build_real_asset_summary(domestic: pd.DataFrame, overseas: pd.DataFrame, error: str = "") -> pd.DataFrame:
    domestic_value = _last_numeric_column_sum(domestic)
    overseas_value = _last_numeric_column_sum(overseas)
    status = "조회 실패" if error else "정상"
    return pd.DataFrame(
        [
            {"구분": "국내 실제", "종목수": len(domestic), "평가금액": f"{domestic_value:,.2f}", "상태": status},
            {"구분": "해외 실제", "종목수": len(overseas), "평가금액": f"{overseas_value:,.2f}", "상태": status},
            {"구분": "실제 합계", "종목수": len(domestic) + len(overseas), "평가금액": f"{domestic_value + overseas_value:,.2f}", "상태": status},
        ]
    )


def build_paper_positions_frame(paper_state: dict[str, Any], saved_positions: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    account_positions = paper_state.get("positions", {})
    if isinstance(account_positions, dict):
        for market, positions_by_symbol in account_positions.items():
            if not isinstance(positions_by_symbol, dict):
                continue
            for symbol, position in positions_by_symbol.items():
                if not isinstance(position, dict):
                    continue
                market_key = str(market).upper()
                symbol_key = str(symbol).upper()
                quantity = _number(position.get("quantity"))
                avg_price = _number(position.get("avg_price"))
                rows.append(
                    {
                        "구분": "가상계좌",
                        "시장": market_key,
                        "종목코드": symbol_key,
                        "종목명": str(position.get("name") or symbol_key),
                        "수량": quantity,
                        "진입/평균가": f"{avg_price:,.4f}",
                        "평가금액": quantity * avg_price,
                        "손절가": "",
                        "익절가": "",
                        "출처": "paper_account",
                    }
                )
                seen.add(f"{market_key}|{symbol_key}")

    for position in saved_positions:
        market_key = str(position.get("market", "")).upper()
        symbol_key = str(position.get("symbol", "")).upper()
        if not symbol_key or f"{market_key}|{symbol_key}" in seen:
            continue
        quantity = _number(position.get("quantity"))
        entry_price = _number(position.get("entry_price"))
        rows.append(
            {
                "구분": "가상포지션",
                "시장": market_key,
                "종목코드": symbol_key,
                "종목명": str(position.get("name") or symbol_key),
                "수량": quantity,
                "진입/평균가": f"{entry_price:,.4f}",
                "평가금액": quantity * entry_price,
                "손절가": f"{_number(position.get('stop_loss_price')):,.4f}",
                "익절가": f"{_number(position.get('take_profit_price')):,.4f}",
                "출처": "paper_positions",
            }
        )
        seen.add(f"{market_key}|{symbol_key}")

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["구분", "시장", "종목코드", "종목명", "수량", "진입/평균가", "평가금액", "손절가", "익절가", "출처"])
    frame["평가금액"] = frame["평가금액"].map(lambda value: f"{_number(value):,.2f}")
    return frame


def build_paper_asset_summary(paper_state: dict[str, Any], paper_positions: pd.DataFrame) -> pd.DataFrame:
    cash_by_market = paper_state.get("cash", {})
    if not isinstance(cash_by_market, dict):
        cash_by_market = {}
    markets = {str(market).upper() for market in cash_by_market.keys()}
    if not paper_positions.empty and "시장" in paper_positions.columns:
        markets.update(str(market).upper() for market in paper_positions["시장"].dropna().tolist())
    if not markets:
        markets = {"KR", "US"}

    rows: list[dict[str, Any]] = []
    total_cash = 0.0
    total_position_value = 0.0
    total_count = 0
    for market in sorted(markets):
        cash = _number(cash_by_market.get(market, 0))
        market_positions = paper_positions[paper_positions["시장"].astype(str).str.upper() == market] if not paper_positions.empty and "시장" in paper_positions.columns else pd.DataFrame()
        position_value = sum(_number(value) for value in market_positions.get("평가금액", pd.Series(dtype=object)).tolist())
        count = len(market_positions)
        total_cash += cash
        total_position_value += position_value
        total_count += count
        rows.append(
            {
                "구분": f"{market} 가상",
                "현금": f"{cash:,.2f}",
                "포지션 평가": f"{position_value:,.2f}",
                "추정 총자산": f"{cash + position_value:,.2f}",
                "보유 종목수": count,
            }
        )

    rows.append(
        {
            "구분": "가상 합계",
            "현금": f"{total_cash:,.2f}",
            "포지션 평가": f"{total_position_value:,.2f}",
            "추정 총자산": f"{total_cash + total_position_value:,.2f}",
            "보유 종목수": total_count,
        }
    )
    return pd.DataFrame(rows)


def _last_numeric_column_sum(frame: pd.DataFrame) -> float:
    if frame is None or frame.empty:
        return 0.0
    for column in reversed(list(frame.columns)):
        values = pd.to_numeric(frame[column].astype(str).str.replace(",", "", regex=False), errors="coerce")
        if values.notna().any():
            return float(values.fillna(0).sum())
    return 0.0


def set_table(table: QTableWidget, frame: pd.DataFrame, *, checkable: bool = False) -> None:
    table.clear()
    if frame is None or frame.empty:
        table.setRowCount(0)
        table.setColumnCount(0)
        return
    extra_columns = 1 if checkable else 0
    table.setColumnCount(len(frame.columns) + extra_columns)
    table.setRowCount(len(frame))
    headers = ["선택"] if checkable else []
    headers.extend([str(column) for column in frame.columns])
    table.setHorizontalHeaderLabels(headers)
    for row_idx, (_, row) in enumerate(frame.iterrows()):
        col_offset = 0
        if checkable:
            check_item = QTableWidgetItem("")
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check_item.setCheckState(Qt.CheckState.Unchecked)
            table.setItem(row_idx, 0, check_item)
            col_offset = 1
        for col_idx, value in enumerate(row):
            item = QTableWidgetItem("" if pd.isna(value) else str(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, col_idx + col_offset, item)
    table.resizeColumnsToContents()


def checked_table_rows(table: QTableWidget) -> list[int]:
    rows: list[int] = []
    for row_idx in range(table.rowCount()):
        item = table.item(row_idx, 0)
        if item is not None and item.checkState() == Qt.CheckState.Checked:
            rows.append(row_idx)
    return rows


def clear_table_checks(table: QTableWidget) -> None:
    for row_idx in range(table.rowCount()):
        item = table.item(row_idx, 0)
        if item is not None and item.flags() & Qt.ItemIsUserCheckable:
            item.setCheckState(Qt.CheckState.Unchecked)


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def candidate_key(row: pd.Series) -> str:
    return f"{str(row.get('market', '')).upper()}|{str(row.get('symbol', '')).upper()}"


def scrollable_panel(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(content)
    return scroll


def section_box(title: str, role: str) -> tuple[QGroupBox, QVBoxLayout]:
    box = QGroupBox(title)
    box.setProperty("role", role)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(10, 12, 10, 10)
    layout.setSpacing(8)
    return box, layout


def add_button_grid(layout: QVBoxLayout, buttons: list[tuple[str, Any]], columns: int = 4) -> None:
    grid = QGridLayout()
    grid.setHorizontalSpacing(6)
    grid.setVerticalSpacing(6)
    for idx, (label, handler) in enumerate(buttons):
        button = QPushButton(label)
        button.clicked.connect(handler)
        grid.addWidget(button, idx // columns, idx % columns)
    layout.addLayout(grid)


def hide_layout_widgets(layout: QHBoxLayout) -> None:
    for idx in range(layout.count()):
        item = layout.itemAt(idx)
        widget = item.widget() if item is not None else None
        if widget is not None:
            widget.hide()


def add_step_control(layout: QHBoxLayout, label: str, spinbox: QSpinBox | QDoubleSpinBox) -> None:
    minus = QPushButton("-")
    plus = QPushButton("+")
    minus.setFixedWidth(26)
    plus.setFixedWidth(26)
    minus.clicked.connect(lambda _checked=False, target=spinbox: target.stepDown())
    plus.clicked.connect(lambda _checked=False, target=spinbox: target.stepUp())
    layout.addWidget(QLabel(label))
    layout.addWidget(minus)
    layout.addWidget(spinbox)
    layout.addWidget(plus)


def table_column_index(table: QTableWidget, name: str) -> int | None:
    for idx in range(table.columnCount()):
        header = table.horizontalHeaderItem(idx)
        if header and header.text() == name:
            return idx
    return None


APP_STYLE = """
QWidget {
    background: #f6f7f9;
    color: #1f2933;
}
QGroupBox {
    border: 1px solid #c8d0d9;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QGroupBox[role="data"] {
    background: #eef6ff;
    border-color: #7da9d6;
}
QGroupBox[role="order"] {
    background: #f3f7ed;
    border-color: #94b76b;
}
QGroupBox[role="automation"] {
    background: #fff6e8;
    border-color: #d7a856;
}
QGroupBox[role="candidates"] {
    background: #f5f1ff;
    border-color: #a995d6;
}
QGroupBox[role="records"] {
    background: #f2f5f7;
    border-color: #9aa8b4;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f4f7fb;
    gridline-color: #d8dee6;
    border: 1px solid #cfd7df;
}
QHeaderView::section {
    background: #e7edf3;
    border: 1px solid #c8d0d9;
    padding: 4px;
    font-weight: 600;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #b7c1cc;
    border-radius: 4px;
    padding: 5px 9px;
}
QPushButton:hover {
    background: #edf4fb;
}
QPushButton:pressed {
    background: #dbe8f5;
}
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
    background: #ffffff;
    border: 1px solid #b7c1cc;
    border-radius: 4px;
    padding: 3px;
}
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = TradingDesktopApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
