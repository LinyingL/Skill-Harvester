"""L5 — Skill Compiler.

把 L4 的 Production 列表编译成一份 SKILL.md (per task), 写到
~/.skill-harvester/skills/pending/<task_id>.md。

格式见 design v2 §4.7。
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Iterable

from .models import Production, TaskCatalog


def compile_skill_md(task_id: str, productions: list[Production], catalog: TaskCatalog) -> str:
    task = catalog.get(task_id)
    task_label = task.label if task else task_id
    task_desc = task.description if task else ""
    keywords = task.typical_keywords if task else []

    lines: list[str] = []

    # ---- frontmatter ----
    lines.append("---")
    lines.append(f"name: {task_id}")
    lines.append(f"description: {task_label}")
    if keywords:
        lines.append(f"trigger_keywords: [{', '.join(keywords)}]")
    lines.append("source: skill-harvester")
    lines.append(f"employee_id: {catalog.employee_id}")
    lines.append(f"generated_at: {dt.date.today().isoformat()}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {task_label}")
    if task_desc:
        lines.append("")
        lines.append(f"> {task_desc}")
    lines.append("")

    # ---- intent layer ----
    lines.append("## 业务规则(意图层)")
    lines.append("")
    if not productions:
        lines.append("_暂无规则。等待更多 episode。_")
    for i, p in enumerate(productions, 1):
        lines.append(f"### Rule {i}: {p.intent.business_action}")
        lines.append("")
        # v4.1: conditions split into trigger / decision (§4.5)
        lines.append("**当 (trigger)**:")
        if p.intent.conditions.trigger:
            for tc in p.intent.conditions.trigger:
                obs = "observable" if tc.observable else "non-observable"
                lines.append(f"- `{tc.field}` {tc.op} `{tc.value}` _({obs})_")
        else:
            lines.append("- _(none — transitional v4.1 state)_")
        lines.append("")
        lines.append("**判断 (decision)**:")
        if p.intent.conditions.decision:
            for dc in p.intent.conditions.decision:
                if dc.kind == "observable" and dc.field is not None:
                    unit = f" {dc.unit}" if dc.unit else ""
                    lines.append(f"- `{dc.field}` {dc.op} `{dc.value}{unit}`")
                else:
                    src = dc.source_dialogue or dc.source_doc or "?"
                    lines.append(f"- {dc.text} _({dc.kind}, source: {src})_")
        else:
            lines.append("- _(none)_")
        lines.append("")
        lines.append(f"**则**: `{p.intent.business_action}`")
        if p.intent.rationale:
            lines.append("")
            lines.append(f"**理由**: {p.intent.rationale}")
        lines.append("")
        lines.append(
            f"**置信度**: {p.confidence}  |  utility={p.utility:.2f}  |  "
            f"基于 {len(p.source_episodes)} 条 episode"
        )
        lines.append("")

    # ---- execution layer ----
    lines.append("## 执行映射(工具层)")
    lines.append("")
    lines.append("| 业务动作 | 首选工具 | 参数 | Fallback |")
    lines.append("|---|---|---|---|")
    for p in productions:
        args = ", ".join(f"{k}={v}" for k, v in p.execution.args.items()) or "-"
        lines.append(
            f"| `{p.intent.business_action}` | "
            f"`{p.execution.tool or '-'}` | "
            f"{args} | "
            f"`{p.execution.fallback_tool or '-'}` |"
        )
    lines.append("")

    # ---- audit trail ----
    lines.append("## 来源审计")
    lines.append("")
    for i, p in enumerate(productions, 1):
        eps = ", ".join(p.source_episodes) if p.source_episodes else "(none)"
        lines.append(f"- **Rule {i}**: episodes = {eps}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 本 skill 由 skill-harvester 自动归纳, 进入 `skills/pending/`。")
    lines.append("> 必须由人类专家 review 后才能搬到正式 `skills/` 目录。")
    return "\n".join(lines)


def group_by_task(productions: Iterable[Production]) -> dict[str, list[Production]]:
    by_task: dict[str, list[Production]] = defaultdict(list)
    for p in productions:
        by_task[p.task_id].append(p)
    return dict(by_task)
