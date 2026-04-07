"""Command line entry. Five subcommands map 1:1 to the design layers.

  skill-harvester init       — copy the example task list
  skill-harvester capture    — L1+L2: hotkey loop
  skill-harvester review     — L3:    classify pending episodes + counterfactual dialogue
  skill-harvester induce     — L4:    induce productions from reviewed episodes
  skill-harvester compile    — L5:    emit SKILL.md to skills/pending/
  skill-harvester status     — show how many episodes / productions / skills exist
"""

from __future__ import annotations

import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .capture import CaptureService, run_hotkey_loop
from .classifier import classify_episode
from .compiler import compile_skill_md, group_by_task
from .dialogue import review_episode_cli
from .inducer import induce_all
from .llm import get_backend
from .storage import Store

console = Console()


@click.group()
def main() -> None:
    """Skill Harvester — extract IF-THEN rules from real workflows."""


@main.command()
def init() -> None:
    """Copy the example task list into ~/.skill-harvester/."""
    store = Store()
    if store.task_list_path.exists():
        console.print(f"[yellow]Task list already exists at {store.task_list_path}[/yellow]")
        return
    example = Path(__file__).parent.parent.parent / "examples" / "task_list.example.yaml"
    if not example.exists():
        console.print(f"[red]Example file missing: {example}[/red]")
        return
    shutil.copy(example, store.task_list_path)
    console.print(f"[green]Wrote {store.task_list_path}. Edit it before running capture.[/green]")


@main.command()
def capture() -> None:
    """L1+L2: start the hotkey loop. Press Ctrl+Alt+M to mark a hard moment."""
    store = Store()
    store.load_task_catalog()  # validate L0 exists before we start
    service = CaptureService(store)
    console.print("[green]Capture loop running. Hotkey: Ctrl+Alt+M (or ENTER fallback).[/green]")

    def _on_capture(ep):
        console.print(
            f"  [cyan]captured[/cyan] {ep.episode_id}  "
            f"app=[bold]{ep.context.active_app or '?'}[/bold]  "
            f"window=[bold]{ep.context.window_title or '?'}[/bold]"
        )

    run_hotkey_loop(service, _on_capture)


@main.command()
def review() -> None:
    """L3: classify pending episodes and run counterfactual dialogue."""
    store = Store()
    catalog = store.load_task_catalog()
    llm = get_backend()
    pending = store.episodes_pending_review()
    if not pending:
        console.print("[yellow]No episodes pending review.[/yellow]")
        return
    console.print(f"[green]{len(pending)} episodes pending. LLM backend = {llm.name}[/green]")
    for ep in pending:
        classify_episode(ep, catalog, llm)
        review_episode_cli(ep, catalog, llm, console=console)
        store.save_episode(ep)
        console.print(f"[green]Saved {ep.episode_id}.[/green]\n")


@main.command()
def induce() -> None:
    """L4: induce productions from all reviewed episodes."""
    store = Store()
    catalog = store.load_task_catalog()
    llm = get_backend()
    episodes = list(store.iter_episodes())
    reviewed = [e for e in episodes if e.review_complete]
    console.print(f"[green]{len(reviewed)}/{len(episodes)} episodes are reviewed.[/green]")
    productions = induce_all(reviewed, catalog, llm)
    store.reset_productions()
    for p in productions:
        store.append_production(p)
    console.print(f"[green]Induced {len(productions)} productions → {store.productions_path}[/green]")


@main.command()
def compile() -> None:  # noqa: A001 - matches subcommand name
    """L5: compile productions into SKILL.md drafts in skills/pending/."""
    store = Store()
    catalog = store.load_task_catalog()
    productions = list(store.iter_productions())
    if not productions:
        console.print("[yellow]No productions found. Run `skill-harvester induce` first.[/yellow]")
        return
    by_task = group_by_task(productions)
    for task_id, ps in by_task.items():
        md = compile_skill_md(task_id, ps, catalog)
        path = store.write_skill(task_id, md)
        console.print(f"[green]Wrote {path}[/green]")


@main.command()
def status() -> None:
    """Print pipeline counts at every layer."""
    store = Store()
    try:
        catalog = store.load_task_catalog()
        l0 = f"{len(catalog.tasks)} tasks (employee={catalog.employee_id})"
    except Exception as e:
        l0 = f"[red]{e}[/red]"
    episodes = list(store.iter_episodes())
    reviewed = [e for e in episodes if e.review_complete]
    productions = list(store.iter_productions())
    skills = list(store.skills_dir.glob("*.md"))

    t = Table(title="Skill Harvester pipeline status")
    t.add_column("Layer")
    t.add_column("Count / Status")
    t.add_row("L0  Task Catalog", l0)
    t.add_row("L2  Episodes (total)", str(len(episodes)))
    t.add_row("L3  Episodes (reviewed)", str(len(reviewed)))
    t.add_row("L4  Productions", str(len(productions)))
    t.add_row("L5  Skill drafts", str(len(skills)))
    console.print(t)


if __name__ == "__main__":
    main()
