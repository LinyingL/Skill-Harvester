"""L3 three-tier dialogue framework (v3, Phase 1.5 stub).

为什么有这个文件: design v3 §4.5 + CHANGELOG v3 批评 2 的回应。

时延档:
  - immediate (0-30s)   一句话快问. 自愿触发, 不打扰. 目标: 抓瞬时记忆.
  - close_window (几分钟) 选择题追问. 鼠标静止 30s 时弹. 目标: 短期记忆 + 辅助回忆.
  - deferred (当晚)       对比追问. skill-harvester review 命令. 目标: 规律记忆.

追问路径(v3 两条):
  - counterfactual: 来自 surprisal 触发的 episode → "你刚才在权衡什么?"
  - rule_statement: 来自 routine 触发的 episode → "你按照什么规则判断?"
  routine_signature 字段决定走哪条路径。

Phase 1.5 实现状态:
  - immediate 层只有一个 CLI prompt 函数, 没有系统级红点托盘
  - close_window 层是占位, 真正实现需要 idle detector
  - deferred 层复用 v2 的 dialogue.review_episode_cli (没动)
  - 和 capture loop 还没串起来
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .llm import LLMBackend
from .models import DialogueTurn, Episode, TaskCatalog


# ----------------------------------------------------------------------------
# Tier 1: immediate (0-30s 一句话快问)
# ----------------------------------------------------------------------------

def immediate_one_line(ep: Episode, console: Optional[Console] = None) -> Episode:
    """触发后 0-30s 内调用. 只问一个问题, 一句话或一个 ENTER 跳过.

    Hard rule: 如果员工在 5 秒内没有响应, 自动跳过, 不打扰。
    Phase 1.5: 这里只是阻塞 input(); 真实使用需要系统级非阻塞热键托盘。
    """
    console = console or Console()
    console.print(
        Panel(
            "[bold]刚才那一下, 在想什么?[/bold]\n"
            "(一句话即可, 直接回车跳过 — 不强求)",
            title=f"⚡ immediate · {ep.episode_id}",
            border_style="yellow",
        )
    )
    answer = Prompt.ask("", default="").strip()
    if answer:
        ep.dialogue.append(
            DialogueTurn(
                question_type="one_line_quick",
                tier="immediate",
                question="刚才那一下在想什么?",
                answer=answer,
            )
        )
    return ep


# ----------------------------------------------------------------------------
# Tier 2: close_window (几分钟内, 选择题追问)
# ----------------------------------------------------------------------------

def close_window_choices(ep: Episode, catalog: TaskCatalog, llm: LLMBackend) -> Episode:
    """鼠标静止 30s 触发. 复用 v2 dialogue 的选择题路径, 但 tier 标记不同。

    Phase 1.5: 这里只是 stub, 真正接入需要一个 idle detector daemon。
    实际实现先沿用 v2 的 dialogue.review_episode_cli, tier 改成 close_window。
    """
    from .dialogue import generate_questions
    console = Console()
    questions = generate_questions(ep, catalog, llm)
    for q in questions:
        qtext = q.get("question", "")
        choices = q.get("choices") or []
        console.print(Panel(qtext, title="close_window Q"))
        for c in choices:
            console.print(f"  {c}")
        answer = Prompt.ask("回答 (字母或一句话)")
        ep.dialogue.append(
            DialogueTurn(
                question_type="decision_choice",
                tier="close_window",
                question=qtext,
                answer=answer,
            )
        )
    return ep


# ----------------------------------------------------------------------------
# Tier 3: deferred (当晚, 对比追问 / 规则陈述)
# ----------------------------------------------------------------------------

def deferred_review(ep: Episode, catalog: TaskCatalog, llm: LLMBackend) -> Episode:
    """skill-harvester review 命令调用. 根据 episode 来源选追问路径:

      - 普通 surprisal episode → 反事实 / 对比追问 (沿用 v2 流程)
      - routine_confirmation episode → 规则陈述追问 (v3 新)
    """
    if ep.routine_signature:
        return _routine_rule_statement(ep, catalog, llm)
    # 默认: 沿用 v2 的反事实流程
    from .dialogue import review_episode_cli
    return review_episode_cli(ep, catalog, llm)


def _routine_rule_statement(ep: Episode, catalog: TaskCatalog, llm: LLMBackend) -> Episode:
    console = Console()
    task = catalog.get(ep.task_id) if ep.task_id else None
    task_label = task.label if task else "(unknown)"
    console.print(
        Panel(
            f"我注意到你最近做了 [bold]{ep.routine_observed_count}[/bold] 次很相似的"
            f"[cyan]'{task_label}'[/cyan]操作, 几乎都很流畅。\n\n"
            f"能用一句话说说, 你判断'可以这样直接处理'的标准是什么?\n"
            f"[dim](这种问题不需要回忆某个具体瞬间, 只需要描述你的固定做法)[/dim]",
            title=f"📜 routine · {ep.episode_id}",
            border_style="green",
        )
    )
    answer = Prompt.ask("回答")
    ep.dialogue.append(
        DialogueTurn(
            question_type="rule_statement",
            tier="deferred",
            question=f"针对 {ep.routine_observed_count} 次重复的 routine, 你的判断标准?",
            answer=answer,
        )
    )
    ep.review_complete = True
    return ep
