"""L3 step 2 — Counterfactual dialogue.

Phase 1: CLI 实现, 选择题为主, 开放题兜底。
触发时机: 由 `skill-harvester review` 命令在用户主动调用时跑, 不打断工作。

为什么优先选择题: 见 design v2 §4.5 (缓解事后合理化)
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .llm import LLMBackend
from .models import DialogueTurn, Episode, TaskCatalog


SYSTEM_PROMPT_QUESTIONS = """You are an expert cognitive task analyst running a debrief.

Given an episode's classified task and any tacit signals (pauses, undos, lookups),
generate 1-3 short, concrete questions to externalize the employee's hidden decision conditions.

Prefer multiple-choice questions (give 3-4 candidate answers) over open questions.
The candidates should be plausible, distinct, and grounded in the episode features.
Always include an "other / write in" option as the last choice.

Respond with JSON:
{
  "questions": [
    {
      "question_type": "decision_choice" | "counterfactual" | "knowledge_gap" | "comparison" | "open",
      "question": "...",
      "choices": ["A. ...", "B. ...", "C. ...", "D. other (write in)"]   // empty list if open
    }
  ]
}
"""


def _episode_summary(ep: Episode, catalog: TaskCatalog) -> str:
    task = catalog.get(ep.task_id) if ep.task_id else None
    task_label = task.label if task else "(unknown)"
    return (
        f"task: {ep.task_id} — {task_label}\n"
        f"app: {ep.context.active_app}\n"
        f"window: {ep.context.window_title}\n"
        f"trigger: {ep.trigger}\n"
        f"pauses_ms: {ep.tacit_signals.pauses_ms}\n"
        f"undo_count: {ep.tacit_signals.undo_count}\n"
        f"external_lookups: {ep.tacit_signals.external_lookups}\n"
    )


def generate_questions(ep: Episode, catalog: TaskCatalog, llm: LLMBackend) -> list[dict]:
    user = "## Episode\n" + _episode_summary(ep, catalog)
    result = llm.complete_json(SYSTEM_PROMPT_QUESTIONS, user)
    return result.get("questions", []) or []


# ----------------------------------------------------------------------------
# CLI review flow
# ----------------------------------------------------------------------------

def review_episode_cli(
    ep: Episode,
    catalog: TaskCatalog,
    llm: LLMBackend,
    console: Optional[Console] = None,
) -> Episode:
    """Interactive review for one episode. Mutates ep in place and returns it."""
    console = console or Console()

    # Step A: confirm task classification (always ask in Phase 1)
    task = catalog.get(ep.task_id) if ep.task_id else None
    task_label = task.label if task else "(unknown)"
    console.print(
        Panel(
            f"[bold]Episode[/bold] {ep.episode_id}\n"
            f"[bold]App[/bold]: {ep.context.active_app}  |  "
            f"[bold]Window[/bold]: {ep.context.window_title}\n"
            f"[bold]Trigger[/bold]: {ep.trigger}\n\n"
            f"系统猜测的任务: [cyan]{ep.task_id}[/cyan] — {task_label}  "
            f"(置信度 {ep.task_confidence:.2f})\n"
            f"理由: {ep.task_classification_reason}",
            title="Goal Classification",
        )
    )

    confirm_choices = [t.id for t in catalog.tasks]
    chosen = Prompt.ask(
        "正确的 task_id 是?",
        choices=confirm_choices,
        default=ep.task_id or "other",
    )
    if chosen != ep.task_id:
        ep.dialogue.append(
            DialogueTurn(
                question_type="goal_confirm",
                question=f"系统猜测 task={ep.task_id} (conf={ep.task_confidence:.2f})",
                answer=f"corrected_to={chosen}",
            )
        )
        ep.task_id = chosen
    else:
        ep.dialogue.append(
            DialogueTurn(
                question_type="goal_confirm",
                question=f"系统猜测 task={ep.task_id}",
                answer="confirmed",
            )
        )

    # Step B: counterfactual questions
    questions = generate_questions(ep, catalog, llm)
    if not questions:
        console.print("[yellow]LLM did not generate counterfactual questions; skipping.[/yellow]")
    for q in questions:
        qtext = q.get("question", "")
        qtype = q.get("question_type", "open")
        choices = q.get("choices") or []
        console.print(Panel(qtext, title=f"Q ({qtype})"))
        if choices:
            for c in choices:
                console.print(f"  {c}")
            answer = Prompt.ask("你的回答 (输入字母, 选 'other' 时可补一句话)")
        else:
            answer = Prompt.ask("你的回答")
        ep.dialogue.append(
            DialogueTurn(question_type=qtype, question=qtext, answer=answer)
        )

    ep.review_complete = True
    return ep
