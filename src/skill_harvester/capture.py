"""L1 (Sparse Sensor) + L2 (Episode Builder) — Phase 1 最笨版本.

设计取舍 (见 design v2 §6 Phase 1):
- 不做系统级 hook、不做 AX Tree、不算 surprisal
- 只做一件事: 全局热键 Ctrl+Alt+M, 按下时:
    1. 截一张当前屏幕
    2. 抓 active app + window title (best effort, 跨平台优雅退化)
    3. 创建一条 Episode 写入 store
- pynput / mss 是可选依赖, 缺失时 capture 退化为"键盘 Enter 触发"模式,
  让 Phase 0 验证完全可以脱离系统级权限跑

为什么不直接用 OS 录屏: 见 design §2.1
"""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Callable, Optional

from .models import Episode, EpisodeContext, TacitSignals
from .storage import Store


def _now_id() -> str:
    return "ep_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]


# ---------------------------------------------------------------------------
# Snapshot adapter — best effort, gracefully degrades
# ---------------------------------------------------------------------------

def _take_screenshot(out_dir: Path, episode_id: str) -> Optional[str]:
    try:
        import mss  # type: ignore
    except ImportError:
        return None
    out_path = out_dir / f"{episode_id}.png"
    with mss.mss() as sct:
        sct.shot(mon=-1, output=str(out_path))
    return str(out_path)


def _active_window_info() -> tuple[str, str]:
    """Return (active_app, window_title). Empty strings if unavailable.

    Phase 1: 不为这件事引入重型跨平台依赖. 缺信息没关系, L3 step1 会用
    fallback 路径让员工自己确认 task。
    """
    try:
        import platform
        if platform.system() == "Darwin":
            # AppleScript path; lightweight
            import subprocess
            script = (
                'tell application "System Events" to '
                'get {name, title of front window} of (first application process whose frontmost is true)'
            )
            out = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            if "," in out:
                app, _, title = out.partition(",")
                return app.strip(), title.strip()
    except Exception:
        pass
    return "", ""


# ---------------------------------------------------------------------------
# Episode builder
# ---------------------------------------------------------------------------

class CaptureService:
    """Glue between hotkey trigger and Store. L2 in v2's six-layer model.

    每次 trigger() 调用都会:
      1. 截屏 (best effort)
      2. 抓活动窗口
      3. 构造一条最小化 Episode (无 task_id, 无 dialogue)
      4. 写盘
    """

    def __init__(self, store: Store):
        self.store = store

    def trigger(self, trigger_reason: str = "hotkey") -> Episode:
        episode_id = _now_id()
        snapshot_path = _take_screenshot(self.store.snapshots_dir, episode_id)
        app, title = _active_window_info()
        ep = Episode(
            episode_id=episode_id,
            ts=dt.datetime.now(),
            trigger=trigger_reason,
            snapshot_path=snapshot_path,
            context=EpisodeContext(
                active_app=app,
                window_title=title,
                recent_events=[],
            ),
            tacit_signals=TacitSignals(),
        )
        self.store.save_episode(ep)
        return ep


# ---------------------------------------------------------------------------
# Hotkey loop (optional dependency)
# ---------------------------------------------------------------------------

def run_hotkey_loop(service: CaptureService, on_capture: Callable[[Episode], None]) -> None:
    """Block on global hotkey Ctrl+Alt+M. Falls back to ENTER prompt if pynput missing."""
    try:
        from pynput import keyboard  # type: ignore
    except ImportError:
        _run_enter_loop(service, on_capture)
        return

    def _on_activate():
        ep = service.trigger("hotkey")
        on_capture(ep)

    with keyboard.GlobalHotKeys({"<ctrl>+<alt>+m": _on_activate}) as h:
        h.join()


def _run_enter_loop(service: CaptureService, on_capture: Callable[[Episode], None]) -> None:
    print("[fallback mode] pynput not installed — press ENTER to capture, Ctrl+C to quit.")
    try:
        while True:
            input()
            ep = service.trigger("manual_enter")
            on_capture(ep)
    except (KeyboardInterrupt, EOFError):
        return
