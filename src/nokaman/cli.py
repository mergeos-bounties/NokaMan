from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from nokaman import __version__
from nokaman.config import OUT_DIR, RUNS_DIR
from nokaman.data.coverage import language_skill_coverage
from nokaman.data.loader import list_sample_files, list_rubric_files, load_rubric
from nokaman.eval.metrics import batch_evaluate, placement_test
from nokaman.eval.pipeline import evaluate_demo, evaluate_sample_file, evaluate_text
from nokaman.rubrics.registry import SKILLS, SUPPORTED_LANGUAGES, get_language_meta, load_language_rubric
from nokaman.train.toy_train import train_toy

app = typer.Typer(
    help="NokaMan — multi-language learning ability assessment (runnable).",
    no_args_is_help=True,
)
lang_app = typer.Typer(help="Supported languages")
rubrics_app = typer.Typer(help="Skill rubrics")
eval_app = typer.Typer(help="Evaluate learner ability")
train_app = typer.Typer(help="Training / calibration")
app.add_typer(lang_app, name="languages")
app.add_typer(rubrics_app, name="rubrics")
app.add_typer(eval_app, name="eval")
app.add_typer(train_app, name="train")
console = Console()


def _print_json(data: object) -> None:
    console.print_json(data=data, ensure_ascii=True)


@app.command("version")
def version_cmd() -> None:
    console.print(f"NokaMan {__version__}")
    console.print(f"Languages: {', '.join(sorted(SUPPORTED_LANGUAGES))}")


@app.command("stats")
def stats_cmd() -> None:
    """Sample inventory by language + skill."""
    from collections import Counter

    by_lang: Counter[str] = Counter()
    by_skill: Counter[str] = Counter()
    for path in list_sample_files():
        stem = path.stem
        parts = stem.split("_")
        lang = parts[0] if parts else "?"
        skill = parts[1] if len(parts) > 1 else "?"
        by_lang[lang] += 1
        by_skill[skill] += 1
    _print_json(
        data={
            "version": __version__,
            "n_samples": len(list_sample_files()),
            "by_lang": dict(by_lang),
            "by_skill": dict(by_skill),
            "languages_supported": sorted(SUPPORTED_LANGUAGES),
        }
    )


@app.command("demo")
def demo_cmd(lang: str = typer.Option("en", "--lang", "-l")) -> None:
    """Full multi-skill demo for a language (end-to-end runnable)."""
    result = evaluate_demo(lang)
    _print_json(data=result)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"demo_{lang}.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    console.print(f"[dim]saved[/dim] {path}")


@lang_app.command("list")
def languages_list() -> None:
    table = Table(title="Supported languages")
    table.add_column("Code")
    table.add_column("Name")
    table.add_column("Frameworks")
    for code in sorted(SUPPORTED_LANGUAGES):
        meta = get_language_meta(code)
        table.add_row(code, meta["name"], ", ".join(meta["frameworks"]))
    console.print(table)


@lang_app.command("coverage")
def languages_coverage(json_output: bool = typer.Option(False, "--json")) -> None:
    report = language_skill_coverage()
    if json_output:
        console.print_json(data=report)
        return

    table = Table(title="Language coverage")
    table.add_column("Code")
    table.add_column("Rubric")
    table.add_column("Total", justify="right")
    skill_headers = {
        "vocabulary": "Vocab",
        "grammar": "Gram",
        "reading": "Read",
        "writing": "Write",
        "listening": "Listen",
        "speaking": "Speak",
    }
    for skill in report["skills"]:
        table.add_column(skill_headers.get(skill, skill), justify="right")
    for row in report["languages"]:
        table.add_row(
            str(row["code"]),
            "yes" if row["has_rubric"] else "fallback",
            str(row["total"]),
            *[str(row["skills"].get(skill, 0)) for skill in report["skills"]],
        )
    console.print(table)


@rubrics_app.command("list")
def rubrics_list(lang: Optional[str] = typer.Option(None, "--lang", "-l")) -> None:
    files = list_rubric_files()
    if lang:
        files = [p for p in files if p.stem == lang.strip().lower()]
    if not files:
        console.print("[yellow]No rubrics found[/yellow]")
        raise typer.Exit()
    table = Table(title="Rubrics")
    table.add_column("Language")
    table.add_column("Skills")
    for path in files:
        r = load_rubric(path)
        skills = ", ".join((r.get("skills") or {}).keys())
        table.add_row(str(r.get("language")), skills)
    console.print(table)


@rubrics_app.command("explain")
def rubrics_explain(
    lang: str = typer.Option("en", "--lang", "-l"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        meta = get_language_meta(lang)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    rubric = load_language_rubric(meta["code"])
    skills = rubric.get("skills") or {}
    rows = [
        {
            "skill": skill,
            "weight": float((skills.get(skill) or {}).get("weight", 1.0)),
            "notes": str((skills.get(skill) or {}).get("notes", "")),
        }
        for skill in SKILLS
    ]
    report = {
        "language": meta["code"],
        "name": meta["name"],
        "frameworks": meta["frameworks"],
        "bands": rubric.get("bands") or [],
        "skills": rows,
    }
    if json_output:
        console.print_json(data=report)
        return

    table = Table(title=f"Rubric weights: {meta['name']} ({meta['code']})")
    table.add_column("Skill")
    table.add_column("Weight", justify="right")
    table.add_column("Notes")
    for row in rows:
        table.add_row(row["skill"], f"{row['weight']:g}", row["notes"])
    console.print(table)
    console.print(f"Frameworks: {', '.join(meta['frameworks'])}")
    console.print(f"Bands: {', '.join(report['bands'])}")


@eval_app.command("text")
def eval_text(
    lang: str = typer.Option("en", "--lang", "-l"),
    text: Optional[str] = typer.Option(None, "--text", "-t"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", exists=True, dir_okay=False),
    skill: str = typer.Option("writing", "--skill", "-s"),
) -> None:
    if file is not None:
        result = evaluate_sample_file(file)
    elif text:
        result = evaluate_text(lang, text, skill=skill)
    else:
        console.print("[red]Provide --text or --file[/red]")
        raise typer.Exit(code=1)
    _print_json(data=result)


@eval_app.command("demo")
def eval_demo(lang: str = typer.Option("en", "--lang", "-l")) -> None:
    _print_json(data=evaluate_demo(lang))


@eval_app.command("samples")
def eval_samples() -> None:
    files = list_sample_files()
    if not files:
        console.print("[yellow]No samples[/yellow]")
        raise typer.Exit()
    table = Table(title=f"Samples ({len(files)})")
    table.add_column("File")
    table.add_column("Lang")
    table.add_column("Skill")
    table.add_column("CEFR")
    table.add_column("Score")
    for path in files:
        result = evaluate_sample_file(path)
        table.add_row(
            path.name,
            str(result.get("language")),
            str(result.get("skill")),
            str(result.get("cefr")),
            str(result.get("score")),
        )
    console.print(table)


@eval_app.command("batch")
def eval_batch(
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    table: bool = typer.Option(True, "--table/--json-only"),
) -> None:
    report = batch_evaluate()
    out_path = out or (RUNS_DIR / "batch_eval.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    console.print(
        f"[green]batch[/green] n={report['n_samples']} exact={report['exact_cefr_hit_rate']} "
        f"adjacent={report['adjacent_cefr_hit_rate']}"
    )
    if table and report.get("by_language"):
        t = Table(title="By language")
        t.add_column("Lang")
        t.add_column("n")
        t.add_column("exact")
        t.add_column("adjacent")
        for lang, row in sorted((report.get("by_language") or {}).items()):
            t.add_row(
                str(lang),
                str(row.get("n") or row.get("n_samples") or ""),
                str(row.get("exact_cefr_hit_rate", row.get("exact", ""))),
                str(row.get("adjacent_cefr_hit_rate", row.get("adjacent", ""))),
            )
        console.print(t)
    console.print(f"Report: {out_path}")


@eval_app.command("summary")
def eval_summary() -> None:
    """Compact inventory of samples + batch metrics."""
    files = list_sample_files()
    by_lang: dict[str, int] = {}
    for path in files:
        stem = path.stem
        lang = stem.split("_")[0] if "_" in stem else "?"
        by_lang[lang] = by_lang.get(lang, 0) + 1
    report = batch_evaluate()
    _print_json(
        data={
            "version": __version__,
            "n_samples": len(files),
            "by_lang_files": by_lang,
            "exact_cefr_hit_rate": report.get("exact_cefr_hit_rate"),
            "adjacent_cefr_hit_rate": report.get("adjacent_cefr_hit_rate"),
        }
    )


@eval_app.command("placement")
def eval_placement(
    lang: str = typer.Option("en", "--lang", "-l"),
    answer: list[str] = typer.Option(..., "--answer", "-a", help="Repeat for multiple answers"),
) -> None:
    result = placement_test(lang, answer)
    _print_json(data=result)


@train_app.command("toy")
def train_toy_cmd(epochs: int = typer.Option(3, "--epochs", "-e", min=1, max=50)) -> None:
    report = train_toy(epochs=epochs)
    last = report["history"][-1]["exact_cefr_hit_rate"]
    console.print(f"[green]Calibration complete[/green] exact_cefr_hit_rate={last}")
    console.print(f"Report: {report['report_path']}")


@train_app.command("report")
def train_report() -> None:
    path = Path("data/runs/toy_train_report.json")
    if not path.exists():
        console.print("[yellow]No report yet. Run: nokaman train toy[/yellow]")
        raise typer.Exit(code=1)
    console.print(path.read_text(encoding="utf-8"))


@app.command("gui")
def gui_cmd() -> None:
    """Launch modern Qt desktop demo (pip install -e '.[gui]')."""
    from nokaman.gui.app import main as gui_main

    raise SystemExit(gui_main())


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8767, "--port", min=1, max=65535),
) -> None:
    """Run FastAPI (pip install -e '.[api]')."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print('[red]Install:[/red] pip install -e ".[api]"')
        raise typer.Exit(1) from exc
    console.print(f"Serving http://{host}:{port}/health")
    uvicorn.run("nokaman.api.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    app()
