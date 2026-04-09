"""Phase 0 verification scorer.

Reads phase0/data.yaml, scores 7 hypotheses against the thresholds defined in
design v3 §1, prints a PASS/FAIL table, and exits non-zero if any hypothesis
fails (so this can sit in a CI gate before Phase 1 work begins).

Usage:
    python verify.py                  # default: ./data.yaml
    python verify.py --data foo.yaml  # custom path
    python verify.py --verbose        # show per-sample details
    python verify.py --only A2        # run a single hypothesis
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# ----------------------------------------------------------------------------
# Thresholds — keep these in lockstep with design v3 §1
# ----------------------------------------------------------------------------

THRESHOLDS = {
    "A1": {
        "min_real_tasks": 5,
        "max_real_tasks": 15,
        "max_vague": 0,
        "min_coverage_pct": 80,
    },
    "A2": {
        "min_top1_acc": 0.70,
        "min_high_conf_acc": 0.90,
        "min_high_conf_share": 0.50,
    },
    "A3a": {
        "min_voluntary_trigger_rate": 0.10,
        "min_avg_info_score": 3.0,
    },
    "A3b": {
        "min_avg_info_score": 3.0,
        "max_cant_recall_rate": 0.30,
    },
    "A4": {
        "min_endorsed_with_critique": 1,
    },
    "A5": {
        "min_absolute_lift_pp": 20,
    },
    "A6": {
        "min_usable_candidates": 1,
    },
}


# ----------------------------------------------------------------------------
# Result type
# ----------------------------------------------------------------------------

@dataclass
class Result:
    hid: str
    title: str
    status: str  # "PASS" | "FAIL" | "SKIP"
    metric_summary: str
    detail: str = ""
    fallback: str = ""


# ----------------------------------------------------------------------------
# Per-hypothesis scorers
# ----------------------------------------------------------------------------

def score_a1(data: dict | None) -> Result:
    title = "任务清单可写性"
    if not data:
        return Result("A1", title, "SKIP", "no data", fallback="")
    th = THRESHOLDS["A1"]
    tasks = data.get("tasks", [])
    real_tasks = [t for t in tasks if t.get("id") != "other"]
    has_other = any(t.get("id") == "other" for t in tasks)
    vague = int(data.get("vague_count", 0))
    coverage = float(data.get("self_reported_coverage_percent", 0))

    problems: list[str] = []
    if not has_other:
        problems.append("missing 'other' fallback")
    if len(real_tasks) < th["min_real_tasks"]:
        problems.append(f"only {len(real_tasks)} real tasks (need ≥{th['min_real_tasks']})")
    if len(real_tasks) > th["max_real_tasks"]:
        problems.append(f"{len(real_tasks)} real tasks (need ≤{th['max_real_tasks']})")
    if vague > th["max_vague"]:
        problems.append(f"{vague} vague tasks (need ≤{th['max_vague']})")
    if coverage < th["min_coverage_pct"]:
        problems.append(f"coverage {coverage}% (need ≥{th['min_coverage_pct']}%)")

    summary = f"{len(real_tasks)} real tasks, vague={vague}, coverage={coverage:.0f}%"
    if problems:
        return Result(
            "A1", title, "FAIL", summary,
            detail="; ".join(problems),
            fallback="工作太碎片化或写得太空泛 → 换目标用户, 或给员工更具体的'对着真实痕迹写'指引",
        )
    return Result("A1", title, "PASS", summary)


def score_a2(data: dict | None) -> Result:
    title = "LLM goal 分类"
    if not data:
        return Result("A2", title, "SKIP", "no data")
    th = THRESHOLDS["A2"]
    samples = data.get("samples", [])
    cutoff = float(data.get("high_confidence_cutoff", 0.80))

    if not samples:
        return Result("A2", title, "SKIP", "no samples")

    n = len(samples)
    correct = sum(1 for s in samples if s.get("truth") == s.get("prediction"))
    high_conf = [s for s in samples if float(s.get("confidence", 0)) >= cutoff]
    high_conf_correct = sum(1 for s in high_conf if s.get("truth") == s.get("prediction"))

    top1 = correct / n
    hc_share = len(high_conf) / n if n else 0
    hc_acc = (high_conf_correct / len(high_conf)) if high_conf else 0

    problems: list[str] = []
    if top1 < th["min_top1_acc"]:
        problems.append(f"top1 {top1:.2f} < {th['min_top1_acc']:.2f}")
    if hc_acc < th["min_high_conf_acc"]:
        problems.append(f"high-conf acc {hc_acc:.2f} < {th['min_high_conf_acc']:.2f}")
    if hc_share < th["min_high_conf_share"]:
        problems.append(f"high-conf share {hc_share:.2f} < {th['min_high_conf_share']:.2f}")

    summary = (
        f"n={n}, top1={top1:.2f}, "
        f"high_conf({cutoff:.2f}): share={hc_share:.2f}, acc={hc_acc:.2f}"
    )
    if problems:
        return Result(
            "A2", title, "FAIL", summary,
            detail="; ".join(problems),
            fallback="加视觉信号 (截图喂多模态 LLM); 再不行退回每条都问 goal",
        )
    return Result("A2", title, "PASS", summary)


def score_a3a(data: dict | None) -> Result:
    title = "immediate 一句话快问"
    if not data:
        return Result("A3a", title, "SKIP", "no data")
    th = THRESHOLDS["A3a"]
    attempts = data.get("attempts", [])
    if not attempts:
        return Result("A3a", title, "SKIP", "no attempts")

    n = len(attempts)
    triggered = [a for a in attempts if a.get("voluntary_trigger")]
    trigger_rate = len(triggered) / n
    scores = [a.get("info_score") for a in triggered if a.get("info_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    problems: list[str] = []
    if trigger_rate < th["min_voluntary_trigger_rate"]:
        problems.append(
            f"voluntary trigger rate {trigger_rate:.2f} < {th['min_voluntary_trigger_rate']:.2f}"
        )
    if avg_score < th["min_avg_info_score"]:
        problems.append(f"avg info score {avg_score:.2f} < {th['min_avg_info_score']:.1f}")

    summary = f"opportunities={n}, triggered={len(triggered)} ({trigger_rate:.0%}), avg_score={avg_score:.2f}"
    if problems:
        return Result(
            "A3a", title, "FAIL", summary,
            detail="; ".join(problems),
            fallback="immediate 档作废, L3 只剩 close-window + deferred. 批评 2 的修复打折",
        )
    return Result("A3a", title, "PASS", summary)


def score_a3b(data: dict | None) -> Result:
    title = "deferred 对比追问"
    if not data:
        return Result("A3b", title, "SKIP", "no data")
    th = THRESHOLDS["A3b"]
    attempts = data.get("attempts", [])
    if not attempts:
        return Result("A3b", title, "SKIP", "no attempts")

    n = len(attempts)
    scores = [a.get("info_score", 0) for a in attempts]
    avg_score = sum(scores) / n
    cant_recall = sum(1 for a in attempts if a.get("said_cant_recall"))
    cant_recall_rate = cant_recall / n

    problems: list[str] = []
    if avg_score < th["min_avg_info_score"]:
        problems.append(f"avg score {avg_score:.2f} < {th['min_avg_info_score']:.1f}")
    if cant_recall_rate > th["max_cant_recall_rate"]:
        problems.append(
            f"can't-recall rate {cant_recall_rate:.2f} > {th['max_cant_recall_rate']:.2f}"
        )

    summary = f"n={n}, avg_score={avg_score:.2f}, cant_recall={cant_recall_rate:.0%}"
    if problems:
        return Result(
            "A3b", title, "FAIL", summary,
            detail="; ".join(problems),
            fallback="对比追问也撑不住 deferred → 缩短到 close-window 时延; 或退回'每天必须当场处理'",
        )
    return Result("A3b", title, "PASS", summary)


def score_a4(data: dict | None) -> Result:
    title = "小样本归纳可信度"
    if not data:
        return Result("A4", title, "SKIP", "no data")
    th = THRESHOLDS["A4"]
    rules = data.get("rules", [])
    if not rules:
        return Result("A4", title, "SKIP", "no rules")

    endorsed_with_critique = sum(
        1 for r in rules if r.get("peer_endorsed") and r.get("peer_can_critique")
    )
    summary = f"{len(rules)} rules, {endorsed_with_critique} endorsed-and-falsifiable"
    if endorsed_with_critique < th["min_endorsed_with_critique"]:
        return Result(
            "A4", title, "FAIL", summary,
            detail=f"need ≥{th['min_endorsed_with_critique']} endorsed-and-falsifiable rule(s)",
            fallback="样本量不够或归纳质量不行 → 等待更大样本; 或换更强的 LLM; 或用 active probing",
        )
    return Result("A4", title, "PASS", summary)


def score_a5(data: dict | None) -> Result:
    title = "端到端 A/B 一致率提升"
    if not data:
        return Result("A5", title, "SKIP", "no data")
    th = THRESHOLDS["A5"]
    cases = data.get("cases", [])
    if not cases:
        return Result("A5", title, "SKIP", "no cases")

    n = len(cases)
    skill_hits = sum(1 for c in cases if c.get("skill_agent"))
    bare_hits = sum(1 for c in cases if c.get("bare_agent"))
    skill_rate = skill_hits / n
    bare_rate = bare_hits / n
    lift_pp = (skill_rate - bare_rate) * 100

    summary = f"n={n}, skill={skill_rate:.0%}, bare={bare_rate:.0%}, lift={lift_pp:+.0f}pp"
    if lift_pp < th["min_absolute_lift_pp"]:
        return Result(
            "A5", title, "FAIL", summary,
            detail=f"lift {lift_pp:.0f}pp < {th['min_absolute_lift_pp']}pp",
            fallback="SKILL.md 没价值 → 中间表示选错; 换格式 (e.g. 自然语言 + IF-THEN 嵌入)",
        )
    return Result("A5", title, "PASS", summary)


def score_a6(data: dict | None) -> Result:
    title = "routine 触发器可行性"
    if not data:
        return Result("A6", title, "SKIP", "no data")
    th = THRESHOLDS["A6"]
    cands = data.get("candidates", [])
    if not cands:
        return Result("A6", title, "SKIP", "no candidates")

    usable = [c for c in cands if c.get("employee_can_state_rule") and c.get("rule_text")]
    summary = f"{len(cands)} candidates, {len(usable)} with usable rule statements"
    if len(usable) < th["min_usable_candidates"]:
        return Result(
            "A6", title, "FAIL", summary,
            detail=f"need ≥{th['min_usable_candidates']} usable candidate(s)",
            fallback="sensor B 路径作废, 系统只剩 surprisal 触发. 已压实产生式抓不到, 批评 1 的修复失败",
        )
    return Result("A6", title, "PASS", summary)


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

SCORERS: dict[str, Callable[[Optional[dict]], Result]] = {
    "A1": score_a1,
    "A2": score_a2,
    "A3a": score_a3a,
    "A3b": score_a3b,
    "A4": score_a4,
    "A5": score_a5,
    "A6": score_a6,
}


STATUS_STYLE = {"PASS": "green", "FAIL": "red", "SKIP": "yellow"}
STATUS_ICON = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "SKIP": "⚪ SKIP"}


def run(data_path: Path, only: Optional[str], verbose: bool) -> int:
    console = Console()
    if not data_path.exists():
        console.print(f"[red]Data file not found: {data_path}[/red]")
        console.print("Run [cyan]cp data.example.yaml data.yaml[/cyan] and edit it.")
        return 2

    raw = yaml.safe_load(data_path.read_text()) or {}
    targets = [only] if only else list(SCORERS.keys())
    results: list[Result] = []
    for hid in targets:
        scorer = SCORERS.get(hid)
        if not scorer:
            console.print(f"[red]Unknown hypothesis id: {hid}[/red]")
            return 2
        results.append(scorer(raw.get(hid)))

    # Table
    table = Table(title="Phase 0 — verification report", show_lines=False)
    table.add_column("ID", style="bold")
    table.add_column("假设")
    table.add_column("结果")
    table.add_column("关键指标")
    for r in results:
        style = STATUS_STYLE[r.status]
        table.add_row(r.hid, r.title, f"[{style}]{STATUS_ICON[r.status]}[/{style}]", r.metric_summary)
    console.print(table)

    # Failure detail
    failures = [r for r in results if r.status == "FAIL"]
    skips = [r for r in results if r.status == "SKIP"]
    for r in failures:
        console.print(
            Panel(
                f"[bold]详情[/bold]: {r.detail}\n\n[bold]备选方案[/bold]: {r.fallback}",
                title=f"❌ {r.hid} — {r.title}",
                border_style="red",
            )
        )

    # Verbose dump
    if verbose:
        for r in results:
            console.print(f"  {r.hid}: status={r.status}  detail={r.detail or '-'}")

    # Verdict
    n_pass = sum(1 for r in results if r.status == "PASS")
    n_fail = len(failures)
    n_skip = len(skips)
    if n_fail == 0 and n_skip == 0:
        console.print(
            Panel(
                "[bold green]全部 7 个假设通过[/bold green] — 可以进入 Phase 1 工程。\n"
                "在 CHANGELOG.md 顶部追加一条 Phase 0 记录, 说明这一轮的目标用户和数据规模。",
                title="🎉 GO",
                border_style="green",
            )
        )
        return 0
    if n_fail == 0:
        console.print(
            Panel(
                f"[yellow]{n_skip} 个假设缺数据 (SKIP)[/yellow]\n"
                "Phase 0 不应该有 SKIP — 缺数据的假设必须补完才能下结论。",
                title="⚠ INCOMPLETE",
                border_style="yellow",
            )
        )
        return 1
    console.print(
        Panel(
            f"[bold red]{n_fail} 个假设失败[/bold red] — 不要直接进入 Phase 1。\n"
            "下一步: 在 CHANGELOG.md 顶部新建 v3.1 章节, 写出失败的假设和应对方案。\n"
            "对照 design v3 §1 的备选方案表, 决定是 pivot 还是 graceful degrade。",
            title="🛑 NO-GO",
            border_style="red",
        )
    )
    return 1


def main() -> None:
    p = argparse.ArgumentParser(description="Phase 0 verification scorer")
    p.add_argument("--data", default=str(Path(__file__).parent / "data.yaml"))
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--only", help="run a single hypothesis (e.g. A2)")
    args = p.parse_args()
    sys.exit(run(Path(args.data), args.only, args.verbose))


if __name__ == "__main__":
    main()
