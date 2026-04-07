"""L3 step 1 — Goal classification.

不试图从屏幕推断"员工在做什么"。流程是:
  1. 把 L0 任务清单 + episode 文本特征塞进 LLM
  2. LLM 给出 task_id + 置信度
  3. CLI 端再让员工确认 (Phase 1 阶段不设阈值, 全部都问)

为什么是这种结构: 见 design v2 §4.5
"""

from __future__ import annotations

import json
from typing import Optional

from .llm import LLMBackend
from .models import Episode, TaskCatalog


SYSTEM_PROMPT = """You are a workflow classifier for the Skill Harvester system.

Given an employee's daily task catalog and a single work moment ("episode"),
your job is to decide which task this episode belongs to.

Rules:
- Only return a task id that exists in the catalog.
- If nothing fits, return "other".
- Confidence is your honest belief, not a sales pitch.

Respond with a JSON object: {"task_id": "...", "confidence": 0.0-1.0, "reason": "short"}
"""


def _episode_features(ep: Episode) -> str:
    ctx = ep.context
    parts = [
        f"active_app: {ctx.active_app or '(unknown)'}",
        f"window_title: {ctx.window_title or '(unknown)'}",
    ]
    if ctx.url:
        parts.append(f"url: {ctx.url}")
    if ctx.clipboard_excerpt:
        parts.append(f"clipboard: {ctx.clipboard_excerpt[:200]}")
    if ctx.recent_events:
        parts.append("recent_events:\n  - " + "\n  - ".join(ctx.recent_events[-10:]))
    parts.append(f"trigger: {ep.trigger}")
    return "\n".join(parts)


def _catalog_block(cat: TaskCatalog) -> str:
    lines = [f"employee: {cat.employee_id} ({cat.employee_role})", "tasks:"]
    for t in cat.tasks:
        kw = f" [keywords: {', '.join(t.typical_keywords)}]" if t.typical_keywords else ""
        apps = f" [apps: {', '.join(t.typical_apps)}]" if t.typical_apps else ""
        lines.append(f"  - {t.id}: {t.label} — {t.description}{apps}{kw}")
    return "\n".join(lines)


def classify_episode(ep: Episode, catalog: TaskCatalog, llm: LLMBackend) -> Episode:
    """Fill ep.task_id / task_confidence / task_classification_reason in place."""
    user = (
        "## Task Catalog\n"
        + _catalog_block(catalog)
        + "\n\n## Episode features\n"
        + _episode_features(ep)
        + "\n\nClassify this episode."
    )
    result = llm.complete_json(SYSTEM_PROMPT, user)
    task_id = str(result.get("task_id", "other"))
    if catalog.get(task_id) is None:
        task_id = "other"
    ep.task_id = task_id
    ep.task_confidence = float(result.get("confidence", 0.0))
    ep.task_classification_reason = str(result.get("reason", ""))
    return ep
