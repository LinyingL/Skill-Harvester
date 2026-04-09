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

    # filled by L3 step 3 (v4.1: voluntary, may stay "unknown")
    # see design v4.1 §4.3 — step 3 与 step 2 同时呈现, 员工可跳过
    epistemic_load: Literal["low", "medium", "high", "unknown"] = "unknown"

    # set to True only after both L3 steps complete
    review_complete: bool = False


# ============================================================================
# L4 — Conditions (v4.1: trigger / decision split, see design §4.5)
# ============================================================================
#
# v4.1 关键变化: conditions 从 list[str] 拆成 trigger / decision 两段
# - trigger: 决定规则何时被尝试匹配, 必须至少 1 个 observable=True
# - decision: 决定 business_action 的判断条件, 可以全部 non-observable
# 总条件数 (trigger + decision) <= 5 (MDL 上限)
#
# observability 是标注属性, 不是分类标签 — 同一字段在不同上下文可观测性不同。

ConditionKind = Literal["observable", "declared", "organizational"]


class TriggerCondition(BaseModel):
    """规则的触发条件 — 必须至少 1 个 observable=True 才能被匹配。"""
    field: str  # e.g. "active_app", "active_window_template"
    op: Literal["equals", "contains", "matches", "less_than", "greater_than", "in"]
    value: Any
    observable: bool = True  # trigger 段几乎总是 True; False 则规则不可匹配 → reject
    source: str = ""  # e.g. "window_focus", "window_title", "url_pattern"


class DecisionCondition(BaseModel):
    """规则的判断条件 — 可以是 observable / declared / organizational 的任意混合。

    declared / organizational 必须有 source (source_dialogue 或 source_doc), 否则 reject。
    """
    # observable 路径
    field: Optional[str] = None
    op: Optional[Literal["equals", "contains", "matches", "less_than", "greater_than", "in"]] = None
    value: Optional[Any] = None
    unit: Optional[str] = None  # e.g. "EUR", "ms"

    # 非 observable 路径
    text: Optional[str] = None  # 自然语言描述, 当 kind != observable 时使用

    observable: bool = True
    kind: ConditionKind = "observable"

    source: str = ""  # observable 时: 数据源 (e.g. "erp_dom")
    source_dialogue: Optional[str] = None  # declared 时: 来自哪条 episode 的对话
    source_doc: Optional[str] = None  # organizational 时: 来自哪份文档


class Conditions(BaseModel):
    """v4.1: trigger / decision 两段 schema。

    硬约束 (由 inducer / consistency_checker 验证, models 层不强制):
      1. trigger 段必须至少 1 个 observable=True
      2. decision 段无 observability 要求
      3. len(trigger) + len(decision) <= 5
      4. declared / organizational 条件必须有 source_dialogue 或 source_doc
    """
    trigger: list[TriggerCondition] = Field(default_factory=list)
    decision: list[DecisionCondition] = Field(default_factory=list)


# ============================================================================
# L4 — Production (intent / execution split)
# ============================================================================

class ProductionIntent(BaseModel):
    """业务规则 — 与 UI 无关, 是 L4 归纳的核心成果。

    v4.1: conditions 从 list[str] 改为 Conditions (trigger/decision 两段)。
    """
    goal: str
    conditions: Conditions
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

    # v4.1 §4.6: 二维矩阵输出状态 (verification × epistemic)
    # - verified_auto:           verification ok + epistemic low/medium → 自动执行
    # - verified_reminder_only:  verification ok + epistemic high → "知道是对的, 但故意不自动化"
    # - hypothesis:              verification low/insufficient, 或 epistemic unknown
    # - unlabeled:               episode 的 epistemic_load 还没标 → 待回 L3 step 3
    status: Literal[
        "verified_auto",
        "verified_reminder_only",
        "hypothesis",
        "unlabeled",
    ] = "hypothesis"

    # v4.1 §4.4: L4.5 consistency check 输出
    # None = N < 9 透明态 (insufficient_sample, L4.5 不评分)
    consistency_score: Optional[float] = None
