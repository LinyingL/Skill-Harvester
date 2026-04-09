"""L1 sensor B — Frequency accumulator (v3, Phase 1.5 stub).

为什么有这个文件: design v3 §4.3.2 + CHANGELOG v3 批评 1 的回应。

核心思想:
  surprisal 触发器看不见"已经完全压实的产生式"(心流状态, 0 停顿)。
  那是企业最想自动化的那一类。
  本模块用一个指数衰减计数器, 当某个 (app, window_template, action_signature)
  三元组在窗口期内累积 >= N 次时, 触发一条 routine_confirmation episode。

Phase 1.5 实现状态:
  - 计数器是真的(内存 dict + JSON 持久化)
  - window_template 归一化是最朴素的"数字替换为 #N"
  - action_signature 用 hash(recent_events tuple)
  - 还没接进 capture loop, 需要 Phase 2 的工作把它和系统事件流串起来
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ----------------------------------------------------------------------------
# Tunables (Phase 0 必须实测校准, 见 CHANGELOG v3 留下的坑 #1)
# ----------------------------------------------------------------------------

DEFAULT_THRESHOLD_N = 10           # 7 天内累积多少次才算 routine
DEFAULT_WINDOW_DAYS = 7
DEFAULT_COOLDOWN_DAYS = 30         # 一旦触发, 同模式 30 天内不再触发
DEFAULT_DECAY_HALFLIFE_DAYS = 14   # 计数指数衰减半衰期


# ----------------------------------------------------------------------------
# Window title normalization
# ----------------------------------------------------------------------------

_DIGIT_RE = re.compile(r"\d+")
_HEX_ID_RE = re.compile(r"\b[0-9a-f]{8,}\b", re.IGNORECASE)


def normalize_window(title: str) -> str:
    """e.g. 'Re: Order #4471 refund' → 'Re: Order #N refund'

    最朴素的归一化: 数字 → N, 长 hex ID → ID。Phase 2 应按目标 app 写
    专用规则; 中文窗口标题需要单独处理。
    """
    if not title:
        return ""
    s = _HEX_ID_RE.sub("ID", title)
    s = _DIGIT_RE.sub("N", s)
    return s.strip()


def action_signature(events: list[str]) -> str:
    """Hash a sequence of event names. Order matters."""
    h = hashlib.sha1("|".join(events).encode("utf-8")).hexdigest()
    return h[:12]


# ----------------------------------------------------------------------------
# Detector
# ----------------------------------------------------------------------------

@dataclass
class RoutineRecord:
    key: str            # f"{app}::{window_template}::{action_sig}"
    app: str
    window_template: str
    action_sig: str
    count: float = 0.0
    last_seen: Optional[datetime] = None
    last_triggered: Optional[datetime] = None  # cooldown anchor


@dataclass
class RoutineDetector:
    threshold_n: int = DEFAULT_THRESHOLD_N
    window_days: int = DEFAULT_WINDOW_DAYS
    cooldown_days: int = DEFAULT_COOLDOWN_DAYS
    halflife_days: float = DEFAULT_DECAY_HALFLIFE_DAYS
    records: dict[str, RoutineRecord] = field(default_factory=dict)

    # ---- core ----

    def observe(
        self,
        app: str,
        window_title: str,
        events: list[str],
        now: Optional[datetime] = None,
    ) -> Optional[RoutineRecord]:
        """Record one execution. Return a record iff it just crossed the threshold
        and is not in cooldown — caller should then build a routine_confirmation
        episode out of it.
        """
        now = now or datetime.now()
        wt = normalize_window(window_title)
        sig = action_signature(events)
        key = f"{app}::{wt}::{sig}"
        rec = self.records.get(key)
        if rec is None:
            rec = RoutineRecord(key=key, app=app, window_template=wt, action_sig=sig)
            self.records[key] = rec

        # exponential decay then +1
        if rec.last_seen is not None:
            dt_days = (now - rec.last_seen).total_seconds() / 86400
            decay = 0.5 ** (dt_days / self.halflife_days)
            rec.count *= decay
        rec.count += 1.0
        rec.last_seen = now

        # cooldown check
        if rec.last_triggered is not None:
            since = (now - rec.last_triggered).days
            if since < self.cooldown_days:
                return None

        # 0.05 epsilon: tolerate decay-induced rounding when calls cluster in time.
        # Real-world threshold of ~10 dwarfs this slack.
        if rec.count >= self.threshold_n - 0.05:
            rec.last_triggered = now
            return rec
        return None

    # ---- persistence ----

    def to_json(self) -> str:
        def _dump(r: RoutineRecord) -> dict:
            return {
                "key": r.key,
                "app": r.app,
                "window_template": r.window_template,
                "action_sig": r.action_sig,
                "count": r.count,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
            }
        return json.dumps([_dump(r) for r in self.records.values()], indent=2)

    @classmethod
    def from_json(cls, text: str) -> "RoutineDetector":
        d = cls()
        for item in json.loads(text):
            r = RoutineRecord(
                key=item["key"],
                app=item["app"],
                window_template=item["window_template"],
                action_sig=item["action_sig"],
                count=item["count"],
                last_seen=datetime.fromisoformat(item["last_seen"]) if item["last_seen"] else None,
                last_triggered=datetime.fromisoformat(item["last_triggered"]) if item["last_triggered"] else None,
            )
            d.records[r.key] = r
        return d

    def save(self, path: Path) -> None:
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "RoutineDetector":
        if not path.exists():
            return cls()
        return cls.from_json(path.read_text())
