"""Core data models for all six layers (L0-L5).

Schema 设计原则:
- L0 TaskCatalog: 员工陈述性自述, 系统的元数据基座
- Episode: 移除了 v1 的 goal_hint (循环依赖根源), goal 由 L3 step1 填写
- Production: 意图层 (intent) + 执行层 (execution) 双层, 让 UI 漂移时只需重写 execution
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# L0 — Task Catalog
# ============================================================================

class TaskItem(BaseModel):
    """One concrete daily task. MUST be in 动词+具体宾语 form."""
    id: str
    label: str
    description: str = ""
    typical_apps: list[str] = Field(default_factory=list)
    typical_keywords: list[str] = Field(default_factory=list)


class TaskCatalog(BaseModel):
    """L0 — the employee's self-described daily task list.

    Hard rules enforced by validation:
      - 5 <= len(tasks) <= 15 (excluding the 'other' fallback)
      - MUST contain a task with id == 'other' as fallback
    """
    employee_id: str
    employee_role: str = ""
    tasks: list[TaskItem]

    def get(self, task_id: str) -> Optional[TaskItem]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def validate_shape(self) -> list[str]:
        """Return list of human-readable problems. Empty list = valid."""
        problems: list[str] = []
        ids = [t.id for t in self.tasks]
        if "other" not in ids:
            problems.append("missing fallback task with id='other'")
        non_other = [t for t in self.tasks if t.id != "other"]
        if len(non_other) < 5:
            problems.append(f"only {len(non_other)} real tasks, need >= 5")
        if len(non_other) > 15:
            problems.append(f"{len(non_other)} real tasks, need <= 15 (split into roles)")
        if len(ids) != len(set(ids)):
            problems.append("duplicate task ids")
        return problems


# ============================================================================
# L1/L2 — Episode
# ============================================================================

class TacitSignals(BaseModel):
    """The 'physical traces' of tacit knowledge surfacing into working memory."""
    pauses_ms: list[int] = Field(default_factory=list)
    undo_count: int = 0
    external_lookups: list[str] = Field(default_factory=list)
    window_switches: int = 0


class EpisodeContext(BaseModel):
    """Lightweight textual features used by the L3 classifier.

    截图路径单独存, 不进 LLM prompt (Phase 1 暂不用多模态)。
    """
    active_app: str = ""
    window_title: str = ""
    url: Optional[str] = None
    clipboard_excerpt: str = ""
    recent_events: list[str] = Field(default_factory=list)


class MetadataPoint(BaseModel):
    """v3: 单条 long-window metadata. 无截图无像素, 仅 < 200 bytes.

    用途见 design v3 §4.3.3 — 把因果窗口从 30s 扩到 15min, 让 L3 能问
    "3 分钟前你看的那封邮件是不是和现在的判断有关"。
    """
    ts: datetime
    app: str = ""
    window_template: str = ""  # 数字/ID 已被归一化, e.g. "Re: Order #N refund"
    url: Optional[str] = None
    event: str = ""  # open / focus / click / pause / undo / ...


TriggerKind = Literal["hotkey", "long_pause", "undo_burst", "routine_confirmation", "manual_enter"]


class DialogueTurn(BaseModel):
    question: str
    answer: str
    question_type: Literal[
        "goal_confirm",
        "decision_choice",
        "counterfactual",
        "knowledge_gap",
        "comparison",
        "rule_statement",  # v3: for routine-triggered episodes
        "one_line_quick",  # v3: immediate-tier 一句话快问
        "open",
    ]
    # v3: which L3 tier produced this turn
    tier: Literal["immediate", "close_window", "deferred"] = "deferred"


class Episode(BaseModel):
    """L2 output. The unit of work for the rest of the pipeline."""
    episode_id: str
    ts: datetime
    trigger: str  # see TriggerKind
    duration_s: float = 0.0
    snapshot_path: Optional[str] = None
    context: EpisodeContext

    # v3: long-window metadata buffer for causal-chain reconstruction (§4.3.3)
    recent_metadata: list[MetadataPoint] = Field(default_factory=list)

    # v3: filled when this episode came from L1 sensor B (frequency accumulator).
    # routine episodes use a different L3 question template (rule-statement, not
    # counterfactual recall). See design v3 §4.5.2.
    routine_signature: Optional[str] = None
    routine_observed_count: int = 0

    tacit_signals: TacitSignals = Field(default_factory=TacitSignals)

    # filled by L3 step 1
    task_id: Optional[str] = None
    task_confidence: Optional[float] = None
    task_classification_reason: Optional[str] = None

    # filled by L3 step 2
    dialogue: list[DialogueTurn] = Field(default_factory=list)

    # set to True only after both L3 steps complete
    review_complete: bool = False


# ============================================================================
# L4 — Production (intent / execution split)
# ============================================================================

class ProductionIntent(BaseModel):
    """业务规则 — 与 UI 无关, 是 L4 归纳的核心成果。"""
    goal: str
    conditions: list[str]
    business_action: str
    rationale: str = ""


class ProductionExecution(BaseModel):
    """工具调用映射 — UI 改版时可被 self-heal 重写, 不影响 intent。"""
    tool: str = ""
    args: dict[str, Any] = Field(default_factory=dict)
    fallback_tool: str = ""
    fallback_hint: str = ""


class Production(BaseModel):
    id: str
    task_id: str
    intent: ProductionIntent
    execution: ProductionExecution = Field(default_factory=ProductionExecution)
    utility: float = 0.0  # successes / total matches
    source_episodes: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"
