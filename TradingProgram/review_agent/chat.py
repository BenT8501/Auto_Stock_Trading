from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from review_agent.gemma_review_agent import build_review


HELP_TEXT = """사용법:
- 질문을 입력하면 로컬 프로젝트 문서/코드 기준으로 답합니다.
- 명령어: review, files, risks, backtest, help, exit
- 이 CLI는 투자 추천을 하지 않습니다. 실거래 판단은 사람이 최종 승인해야 합니다.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    print("Trading Review Chat Agent")
    print("투자 추천/수익 보장은 하지 않습니다. 'help' 또는 'exit' 입력 가능.")

    while True:
        try:
            question = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nagent> 종료합니다.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("agent> 종료합니다.")
            break

        print(f"agent> {answer(question, project_root)}")


def answer(question: str, project_root: Path) -> str:
    normalized = question.lower()

    if normalized in {"help", "도움말"}:
        return HELP_TEXT
    if "review" in normalized or "검토" in question or "리포트" in question:
        return build_review(project_root)
    if "file" in normalized or "파일" in question or "구조" in question:
        return _file_summary(project_root)
    if "risk" in normalized or "리스크" in question or "위험" in question:
        return _risk_answer(project_root)
    if "backtest" in normalized or "백테스트" in question:
        return _backtest_answer(project_root)
    if "실거래" in question or "주문" in question:
        return (
            "현재 구현은 실거래에 부적합합니다. `config.yaml`의 `broker.live_trading_enabled`는 false이고, "
            "`src/broker/kis.py`는 호출 시 RuntimeError를 발생시킵니다. 이 상태가 맞습니다. "
            "페이퍼 트레이딩 장기 검증, 운영 체크리스트, 수동 승인 체계 없이는 실거래 전환하면 안 됩니다."
        )

    return (
        "현재 CLI는 로컬 규칙 기반 답변만 제공합니다. 더 정확한 답을 원하면 질문에 "
        "`검토`, `리스크`, `백테스트`, `파일 구조`, `실거래` 중 하나를 포함해 주세요. "
        "냉정한 판단: 아직 LLM 기반 대화 에이전트가 아니라 프로젝트 감사용 CLI입니다."
    )


def _file_summary(project_root: Path) -> str:
    important = [
        "config.yaml",
        "main.py",
        "app.py",
        "src/backtester.py",
        "src/execution.py",
        "src/risk.py",
        "src/patterns.py",
        "review_agent/gemma_review_agent.py",
    ]
    existing = [path for path in important if (project_root / path).exists()]
    missing = [path for path in important if not (project_root / path).exists()]
    return "핵심 파일:\n" + "\n".join(f"- {path}" for path in existing) + (
        "\n누락:\n" + "\n".join(f"- {path}" for path in missing) if missing else ""
    )


def _risk_answer(project_root: Path) -> str:
    risk_path = project_root / "docs/RISK_RULES.md"
    if risk_path.exists():
        risk_text = risk_path.read_text(encoding="utf-8")
        return (
            "핵심 리스크 판단:\n"
            "- 캔들 패턴 + 이동평균만으로 초과수익을 가정하면 근거가 약합니다.\n"
            "- 현재 구현은 손절/익절, 포지션 크기, 신규 진입 수 제한이 있습니다.\n"
            "- 가장 큰 운영 리스크는 검증 부족 상태에서 실거래로 넘어가는 것입니다.\n\n"
            f"현재 문서 기준:\n{risk_text}"
        )
    return "docs/RISK_RULES.md가 없습니다. 리스크 규칙부터 문서화해야 합니다."


def _backtest_answer(project_root: Path) -> str:
    metrics_path = project_root / "outputs/reports/metrics.csv"
    if metrics_path.exists():
        return (
            "백테스트 산출물은 존재합니다. 단, 샘플 데이터 결과는 전략 타당성 증거가 아닙니다.\n"
            f"지표 파일: {metrics_path}\n"
            "다음 검증 없이는 실전 가치 판단을 하면 안 됩니다: 충분한 기간, 종목군 확장, "
            "거래비용 민감도, 워크포워드, 벤치마크 비교, 생존편향 제거."
        )
    return "아직 백테스트 지표 파일이 없습니다. `python main.py --config config.yaml`를 먼저 실행하세요."


if __name__ == "__main__":
    main()
