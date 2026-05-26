from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = [
    "docs/PROJECT_CONTEXT.md",
    "docs/STRATEGY_SPEC.md",
    "docs/RISK_RULES.md",
    "docs/BACKTEST_REQUIREMENTS.md",
    "src/backtester.py",
    "src/execution.py",
    "src/risk.py",
    "src/broker/kis.py",
]

P0_TERMS = [
    ("live_trading_enabled: true", "config.yaml enables live trading"),
    ("requests.post", "code may call external broker/network endpoint directly"),
]


def build_review(project_root: Path) -> str:
    missing = [path for path in REQUIRED_FILES if not (project_root / path).exists()]
    issues: list[tuple[str, str]] = []

    if missing:
        issues.extend(("P0", f"필수 파일 누락: {path}") for path in missing)

    for file_path in project_root.rglob("*"):
        if file_path.is_file() and file_path.suffix in {".py", ".yaml", ".yml", ".md"}:
            if _should_skip_scan(file_path, project_root):
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            rel = file_path.relative_to(project_root).as_posix()
            for term, message in P0_TERMS:
                if term in text:
                    issues.append(("P0", f"{rel}: {message}"))

    if not (project_root / "tests").exists():
        issues.append(("P1", "tests 디렉터리가 없습니다."))

    if not issues:
        status = "CONDITIONAL PASS"
    elif any(severity == "P0" for severity, _ in issues):
        status = "HOLD"
    else:
        status = "CONDITIONAL PASS"

    return _render_report(status, issues)


def _should_skip_scan(file_path: Path, project_root: Path) -> bool:
    rel = file_path.relative_to(project_root).as_posix()
    return rel.startswith("review_agent/") or rel.startswith("outputs/")


def _render_report(status: str, issues: list[tuple[str, str]]) -> str:
    lines = [
        "# 자동매매 시스템 검토 리포트",
        "",
        "## 1. 종합 판정",
        "",
        f"판정: {status}",
        "",
        "## 2. 핵심 요약",
        "",
        "- 이 검토는 로컬 파일 구조, 안전장치, 실거래 비활성화 여부를 점검한 결정론적 감사입니다.",
        "- 특정 종목 매수/매도 추천이나 수익 보장은 하지 않습니다.",
        "- 전략의 초과수익 가능성은 아직 입증되지 않았습니다.",
        "",
        "## 3. 주요 이슈",
        "",
    ]
    if issues:
        for severity, issue in issues:
            lines.append(f"- {severity}: {issue}")
    else:
        lines.append("- P2: 현재 자동 점검 기준에서는 치명적 구조 결함이 발견되지 않았습니다.")

    lines.extend(
        [
            "",
            "## 4. 최종 결론",
            "",
            "현재 상태는 연구용 백테스트 단계로만 적합합니다. 실거래 전환은 별도 운영 체크리스트, 장기간 페이퍼 트레이딩, 수동 승인 체계 없이는 허용하면 안 됩니다.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="outputs/reports/gemma_review.md")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output = project_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_review(project_root), encoding="utf-8")
    print(f"Wrote review report: {output}")


if __name__ == "__main__":
    main()
