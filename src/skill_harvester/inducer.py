"""L4 — Production Inducer.

Phase 1 实现策略:
- 按 task_id 分组 (L0 task_id 已经是受控词汇表, 不需要 embedding 聚类)
- 每个 task 内, 把所有 reviewed episode 的特征 + dialogue 喂给 LLM
- LLM 输出候选 productions (intent + execution 双层)
- MDL 评估暂时退化为"按 utility 排序 + 去重"

设计依据: design v2 §4.6
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .llm import LLMBackend
from .models import (
    Episode,
    Production,
    ProductionExecution,
    ProductionIntent,
    TaskCatalog,
)


SYSTEM_PROMPT = """You are a production-rule inducer in the ACT-R tradition.

You will be given a batch of work episodes for a single task type, each with the
employee's externalized reasoning (collected via post-hoc counterfactual dialogue).

Your job is to induce a small set of IF-THEN production rules that explain the
employee's behavior. Follow these rules:

1. Split intent from execution. Intent describes the business decision and its
   conditions. Execution describes the concrete tool/UI action.
2. Conditions must be concrete (e.g., "order_amount < 50 EUR"), not vague
   (e.g., "small order").
3. Prefer fewer, broader rules over many narrow ones (Occam / MDL).
4. If two episodes are nearly identical but the employee acted differently,
   that is a SPLIT — find what discriminates them and put it in conditions.
5. Skip rules you cannot ground in at least 2 episodes (mark single-episode
   rules with confidence "low").

Respond with JSON:
{
  "productions": [
    {
      "intent": {
        "goal": "...",
        "conditions": ["...", "..."],
        "business_action": "...",
        "rationale": "..."
      },
      "execution": {
        "tool": "...",
        "args": {...},
        "fallback_tool": "...",
        "fallback_hint": "..."
      },
      "utility": 0.0-1.0,
      "source_episode_ids": ["...", "..."],
      "confidence": "low" | "medium" | "high"
    }
  ]
}
"""


def _episode_block(ep: Episode) -> str:
    lines = [
        f"### {ep.episode_id}",
        f"app: {ep.context.active_app}  window: {ep.context.window_title}",
        f"trigger: {ep.trigger}",
    ]
    if ep.tacit_signals.pauses_ms:
        lines.append(f"pauses_ms: {ep.tacit_signals.pauses_ms}")
    if ep.tacit_signals.undo_count:
        lines.append(f"undo_count: {ep.tacit_signals.undo_count}")
    if ep.tacit_signals.external_lookups:
        lines.append(f"external_lookups: {ep.tacit_signals.external_lookups}")
    if ep.dialogue:
        lines.append("dialogue:")
        for d in ep.dialogue:
            lines.append(f"  - Q ({d.question_type}): {d.question}")
            lines.append(f"    A: {d.answer}")
    return "\n".join(lines)


def induce_for_task(
    task_id: str,
    episodes: list[Episode],
    catalog: TaskCatalog,
    llm: LLMBackend,
) -> list[Production]:
    if not episodes:
        return []
    task = catalog.get(task_id)
    task_label = task.label if task else task_id
    user = (
        f"## Task: {task_id} — {task_label}\n"
        f"{len(episodes)} episodes attached.\n\n"
        + "\n\n".join(_episode_block(e) for e in episodes)
        + "\n\nInduce production rules now."
    )
    result = llm.complete_json(SYSTEM_PROMPT, user)
    raw = result.get("productions", []) or []

    out: list[Production] = []
    for i, p in enumerate(raw):
        intent_raw = p.get("intent", {}) or {}
        exec_raw = p.get("execution", {}) or {}
        try:
            intent = ProductionIntent(
                goal=str(intent_raw.get("goal", task_id)),
                conditions=[str(c) for c in (intent_raw.get("conditions") or [])],
                business_action=str(intent_raw.get("business_action", "")),
                rationale=str(intent_raw.get("rationale", "")),
            )
        except Exception:
            continue
        execution = ProductionExecution(
            tool=str(exec_raw.get("tool", "")),
            args=exec_raw.get("args") or {},
            fallback_tool=str(exec_raw.get("fallback_tool", "")),
            fallback_hint=str(exec_raw.get("fallback_hint", "")),
        )
        confidence = str(p.get("confidence", "low"))
        if confidence not in ("low", "medium", "high"):
            confidence = "low"
        out.append(
            Production(
                id=f"{task_id}_rule_{i+1}",
                task_id=task_id,
                intent=intent,
                execution=execution,
                utility=float(p.get("utility", 0.0)),
                source_episodes=[str(s) for s in (p.get("source_episode_ids") or [])],
                confidence=confidence,  # type: ignore[arg-type]
            )
        )
    return out


def induce_all(
    episodes: Iterable[Episode],
    catalog: TaskCatalog,
    llm: LLMBackend,
) -> list[Production]:
    """Group reviewed episodes by task_id and induce productions for each."""
    by_task: dict[str, list[Episode]] = defaultdict(list)
    for ep in episodes:
        if ep.review_complete and ep.task_id and ep.task_id != "other":
            by_task[ep.task_id].append(ep)

    productions: list[Production] = []
    for task_id, eps in by_task.items():
        productions.extend(induce_for_task(task_id, eps, catalog, llm))
    return productions
