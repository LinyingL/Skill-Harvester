"""Episode + Production persistence. JSONL for append-only simplicity.

文件布局:
  ~/.skill-harvester/
    task_list.yaml          # L0
    episodes/<id>.json      # one file per episode (snapshots referenced by path)
    productions.jsonl       # L4 output, append-only
    skills/pending/*.md     # L5 output
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

import yaml

from .models import Episode, Production, TaskCatalog


def default_root() -> Path:
    return Path(os.environ.get("SKILL_HARVESTER_HOME", Path.home() / ".skill-harvester"))


class Store:
    def __init__(self, root: Path | None = None):
        self.root = root or default_root()
        self.episodes_dir = self.root / "episodes"
        self.snapshots_dir = self.root / "snapshots"
        self.skills_dir = self.root / "skills" / "pending"
        self.productions_path = self.root / "productions.jsonl"
        self.task_list_path = self.root / "task_list.yaml"

        for d in (self.episodes_dir, self.snapshots_dir, self.skills_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---- L0 ----
    def load_task_catalog(self) -> TaskCatalog:
        if not self.task_list_path.exists():
            raise FileNotFoundError(
                f"Task catalog not found at {self.task_list_path}. "
                f"Copy examples/task_list.example.yaml there and edit it."
            )
        data = yaml.safe_load(self.task_list_path.read_text())
        cat = TaskCatalog.model_validate(data)
        problems = cat.validate_shape()
        if problems:
            raise ValueError(f"Task catalog invalid: {problems}")
        return cat

    # ---- Episodes ----
    def save_episode(self, ep: Episode) -> Path:
        path = self.episodes_dir / f"{ep.episode_id}.json"
        path.write_text(ep.model_dump_json(indent=2))
        return path

    def load_episode(self, episode_id: str) -> Episode:
        path = self.episodes_dir / f"{episode_id}.json"
        return Episode.model_validate_json(path.read_text())

    def iter_episodes(self) -> Iterator[Episode]:
        for path in sorted(self.episodes_dir.glob("*.json")):
            yield Episode.model_validate_json(path.read_text())

    def episodes_pending_review(self) -> list[Episode]:
        return [e for e in self.iter_episodes() if not e.review_complete]

    # ---- Productions ----
    def append_production(self, p: Production) -> None:
        with self.productions_path.open("a") as f:
            f.write(p.model_dump_json() + "\n")

    def iter_productions(self) -> Iterator[Production]:
        if not self.productions_path.exists():
            return
        for line in self.productions_path.read_text().splitlines():
            if line.strip():
                yield Production.model_validate_json(line)

    def reset_productions(self) -> None:
        if self.productions_path.exists():
            self.productions_path.unlink()

    # ---- Skills (L5 output) ----
    def write_skill(self, task_id: str, content: str) -> Path:
        path = self.skills_dir / f"{task_id}.md"
        path.write_text(content)
        return path
