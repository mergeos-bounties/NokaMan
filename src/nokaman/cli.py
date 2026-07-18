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
from nokaman.data.loader import list_sample_files, list_rubric_files, load_rubric, load_sample, list_placement_files, load_placement_pack
from nokaman.eval.metrics import _compute_band_accuracy_metrics, batch_evaluate, placement_test
from nokaman.eval.pipeline import evaluate_demo, evaluate_sample_file, evaluate_text
from nokaman.eval.session import SessionManager
from nokaman.models.cefr import cefr_rank
from nokaman.rubrics.registry import (
    SKILLS,
    SUPPORTED_LANGUAGES,
    get_language_meta,
    load_language_rubric,
)
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
session_app = typer.Typer(help="Adaptive quiz session (state machine)")
app.add_typer(session_app, name="session")
app.add_typer(train_app, name="train")
placement_app = typer.Typer(help="Placement test packs")
app.add_typer(placement_app, name="placement")
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


@eval_app.command("report")
def eval_report(
    table: bool = typer.Option(True, "--table/--no-table"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Eval metrics report: band accuracy, adjacent accuracy, MAE on score."""
    from rich.progress import track

    files = list_sample_files()
    if not files:
        console.print("[yellow]No samples found[/yellow]")
        raise typer.Exit()

    rows = []
    for path in track(files, description="Evaluating..."):
        sample = load_sample(path)
        result = evaluate_sample_file(path)
        cefr_pred = str(result.get("cefr") or "").upper()
        cefr_exp = str(sample.get("expected_cefr") or "").upper()
        dist = None
        if cefr_exp:
            dist = abs(cefr_rank(cefr_pred) - cefr_rank(cefr_exp))
        rows.append(
            {
                "file": path.name,
                "language": result.get("language"),
                "skill": result.get("skill"),
                "score": result.get("score"),
                "cefr": result.get("cefr"),
                "expected_cefr": sample.get("expected_cefr"),
                "distance": dist,
            }
        )

    # Compute aggregate metrics
    metrics = _compute_band_accuracy_metrics(rows)

    report_data = {
        "version": __version__,
        "n_samples": len(files),
        "n_labeled": metrics["n_labeled"],
        "exact_cefr_hit_rate": metrics["exact_cefr_hit_rate"],
        "adjacent_cefr_hit_rate": metrics["adjacent_cefr_hit_rate"],
        "mae_on_score": metrics["mae_on_score"],
        "by_language": {},
    }

    # Per-language breakdown
    by_lang: dict[str, list] = {}
    for row in rows:
        lang = str(row.get("language") or "?")
        by_lang.setdefault(lang, []).append(row)

    for lang, lang_rows in sorted(by_lang.items()):
        lang_metrics = _compute_band_accuracy_metrics(lang_rows)
        report_data["by_language"][lang] = lang_metrics

    if json_output:
        _print_json(data=report_data)
        return

    # Pretty table output
    overall_table = Table(title="NokaMan Eval Report — Overall")
    overall_table.add_column("Metric", style="bold")
    overall_table.add_column("Value", justify="right")
    overall_table.add_row("Samples", str(len(files)))
    overall_table.add_row("Labeled", str(metrics["n_labeled"]))
    exact_rate = metrics["exact_cefr_hit_rate"]
    overall_table.add_row(
        "Exact CEFR Hit Rate",
        f"{exact_rate:.1%}" if exact_rate is not None else "N/A",
    )
    adj_rate = metrics["adjacent_cefr_hit_rate"]
    overall_table.add_row(
        "Adjacent CEFR Hit Rate",
        f"{adj_rate:.1%}" if adj_rate is not None else "N/A",
    )
    mae = metrics["mae_on_score"]
    overall_table.add_row(
        "MAE (CEFR rank)",
        f"{mae:.4f}" if mae is not None else "N/A",
    )
    console.print(overall_table)

    if report_data["by_language"]:
        lang_table = Table(title="By Language")
        lang_table.add_column("Language", style="bold")
        lang_table.add_column("n", justify="right")
        lang_table.add_column("Labeled", justify="right")
        lang_table.add_column("Exact", justify="right")
        lang_table.add_column("Adjacent", justify="right")
        lang_table.add_column("MAE", justify="right")
        for lang, m in sorted(report_data["by_language"].items()):
            lang_table.add_row(
                str(lang),
                str(len(by_lang.get(lang, []))),
                str(m["n_labeled"]),
                f"{m['exact_cefr_hit_rate']:.1%}" if m["exact_cefr_hit_rate"] is not None else "—",
                f"{m['adjacent_cefr_hit_rate']:.1%}" if m["adjacent_cefr_hit_rate"] is not None else "—",
                f"{m['mae_on_score']:.4f}" if m["mae_on_score"] is not None else "—",
            )
        console.print(lang_table)


@eval_app.command("placement")
def eval_placement(
    lang: str = typer.Option("en", "--lang", "-l"),
    answer: list[str] = typer.Option(..., "--answer", "-a", help="Repeat for multiple answers"),
) -> None:
    result = placement_test(lang, answer)
    _print_json(data=result)


@train_app.command("toy")
def train_toy_cmd(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        dir_okay=False,
        help="YAML/JSON calibration config.",
    ),
    epochs: int | None = typer.Option(None, "--epochs", "-e", min=1, max=50),
    seed: int | None = typer.Option(None, "--seed", min=0),
    run_id: str | None = typer.Option(None, "--run-id"),
    resume: bool | None = typer.Option(None, "--resume/--no-resume"),
) -> None:
    report = train_toy(
        epochs=epochs,
        config_path=config,
        seed=seed,
        run_id=run_id,
        resume=resume,
    )
    last = report["history"][-1]["exact_cefr_hit_rate"]
    console.print(f"[green]Calibration complete[/green] exact_cefr_hit_rate={last}")
    if report.get("resumed"):
        console.print(f"[dim]resumed[/dim] {report['run_id']}")
    console.print(f"Report: {report['report_path']}")
    console.print(f"Dashboard: {report['dashboard_path']}")


@train_app.command("report")
def train_report(run_id: str | None = typer.Option(None, "--run-id")) -> None:
    path = RUNS_DIR / "toy_train_report.json"
    if run_id:
        path = RUNS_DIR / run_id / "toy_train_report.json"
    elif not path.exists():
        reports = sorted(
            RUNS_DIR.glob("*/toy_train_report.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if reports:
            path = reports[0]
    if not path.exists():
        console.print("[yellow]No report yet. Run: nokaman train toy[/yellow]")
        raise typer.Exit(code=1)
    console.print(path.read_text(encoding="utf-8"))


# ── session commands ─────────────────────────────────────────


@session_app.command("start")
def session_start(
    lang: str = typer.Option("en", "--lang", "-l"),
) -> None:
    """Start a new adaptive quiz session."""
    mgr = SessionManager(language=lang)
    result = mgr.start()
    _print_json(data=result)


@session_app.command("answer")
def session_answer(
    session_id: str = typer.Option(..., "--session-id", "-sid"),
    lang: str = typer.Option("en", "--lang", "-l"),
    text: str = typer.Option(..., "--text", "-t"),
) -> None:
    """Submit an answer to an active session."""
    mgr = SessionManager(language=lang, session_id=session_id)
    result = mgr.submit_answer(text)
    _print_json(data=result)


@session_app.command("snapshot")
def session_snapshot(
    session_id: str = typer.Option(..., "--session-id", "-sid"),
    lang: str = typer.Option("en", "--lang", "-l"),
) -> None:
    """Get current session snapshot without submitting an answer."""
    mgr = SessionManager(language=lang, session_id=session_id)
    _print_json(data=mgr.snapshot())


@session_app.command("end")
def session_end(
    session_id: str = typer.Option(..., "--session-id", "-sid"),
    lang: str = typer.Option("en", "--lang", "-l"),
) -> None:
    """Manually end an active session."""
    mgr = SessionManager(language=lang, session_id=session_id)
    result = mgr.end()
    _print_json(data=result)


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


# ── placement commands ─────────────────────────────────────────


@placement_app.command("list")
def placement_list() -> None:
    """List available placement test packs."""
    files = list_placement_files()
    if not files:
        console.print("[yellow]No placement packs found[/yellow]")
        raise typer.Exit()
    table = Table(title="Placement Test Packs")
    table.add_column("ID")
    table.add_column("Language")
    table.add_column("Prompts")
    for path in files:
        pack = load_placement_pack(path)
        table.add_row(str(pack.get("id")), str(pack.get("language")), str(len(pack.get("prompts", []))))
    console.print(table)


@placement_app.command("show")
def placement_show(
    pack_id: str = typer.Argument(..., help="Placement pack ID (e.g., en_placement)"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show details of a placement test pack."""
    files = list_placement_files()
    pack_path = None
    for path in files:
        if path.stem == pack_id:
            pack_path = path
            break
    if not pack_path:
        console.print(f"[red]Pack '{pack_id}' not found[/red]")
        raise typer.Exit(code=1)
    
    pack = load_placement_pack(pack_path)
    if json_output:
        _print_json(data=pack)
        return
    
    console.print(f"[bold]{pack.get('id')}[/bold] ({pack.get('language')})")
    console.print(f"Skill: {pack.get('skill')}")
    console.print(f"Prompts: {len(pack.get('prompts', []))}")
    
    if pack.get('prompts'):
        table = Table(title="Prompts")
        table.add_column("ID")
        table.add_column("Text")
        table.add_column("CEFR")
        for prompt in pack.get('prompts', [])[:10]:
            table.add_row(str(prompt.get('id')), str(prompt.get('text')[:60]), str(prompt.get('cefr')))
        console.print(table)


@placement_app.command("run")
def placement_run(
    pack_id: str = typer.Argument(..., help="Placement pack ID (e.g., en_placement)"),
    answers: list[str] = typer.Argument(..., help="Answer text for each prompt"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run a placement test with provided answers."""
    files = list_placement_files()
    pack_path = None
    for path in files:
        if path.stem == pack_id:
            pack_path = path
            break
    if not pack_path:
        console.print(f"[red]Pack '{pack_id}' not found[/red]")
        raise typer.Exit(code=1)
    
    pack = load_placement_pack(pack_path)
    language = pack.get('language', 'en')
    
    if len(answers) != len(pack.get('prompts', [])):
        console.print(f"[yellow]Warning: Expected {len(pack.get('prompts', []))} answers, got {len(answers)}[/yellow]")
    
    result = placement_test(language, answers)
    
    if json_output:
        _print_json(data=result)
        return
    
    console.print(f"[bold]Placement Test Results[/bold]")
    console.print(f"Language: {result.get('language')}")
    console.print(f"Items: {result.get('n_items')}")
    console.print(f"Overall Score: {result.get('overall')}")
    console.print(f"CEFR Level: {result.get('cefr')}")
    
    if result.get('items'):
        table = Table(title="Item Details")
        table.add_column("Item")
        table.add_column("Text")
        table.add_column("Score")
        table.add_column("CEFR")
        for item in result.get('items', [])[:10]:
            table.add_row(
                str(item.get('item')),
                str(item.get('text')[:50]),
                str(item.get('overall')),
                str(item.get('cefr'))
            )
        console.print(table)
    
    console.print(f"[dim]Ready for UI: {result.get('ready_for_ui')}[/dim]")
@eval_app.command("score")
def eval_score(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Path to sample JSON file"),
    table: bool = typer.Option(True, "--table/--no-table", help="Show rich table output"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Score a single sample and display detailed dimension table."""
    from nokaman.data.loader import load_sample
    from nokaman.eval.pipeline import evaluate_sample_file
    from nokaman.rubrics.speaking_fluency import score_speaking_fluency

    sample = load_sample(path)
    skill = str(sample.get("skill") or "writing").lower()
    
    # For speaking samples with fluency observations, compute detailed dimensions
    if skill == "speaking":
        fluency_observations = sample.get("fluency_observations") or {}
        if fluency_observations:
            # Score using the speaking fluency rubric
            result = score_speaking_fluency(
                str(sample.get("text") or ""),
                duration_seconds=float(fluency_observations.get("duration_seconds")) if fluency_observations.get("duration_seconds") else None,
                pause_count=int(fluency_observations.get("pause_count")) if fluency_observations.get("pause_count") else None,
                filler_count=int(fluency_observations.get("filler_count")) if fluency_observations.get("filler_count") else None,
            )
            result.update({
                "language": sample.get("language"),
                "skill": "speaking",
                "cefr": sample.get("cefr"),
                "expected_cefr": sample.get("expected_cefr"),
            })
        else:
            # Fallback to regular evaluation
            result = evaluate_sample_file(path)
    else:
        result = evaluate_sample_file(path)

    if json_output:
        _print_json(data=result)
        return

    # Display rich table for speaking samples with dimensions
    if skill == "speaking" and result.get("dimensions"):
        from rich.table import Table
        dimensions = result.get("dimensions") or {}
        observations = result.get("observations") or {}
        limitations = result.get("limitations") or []

        table_obj = Table(title=f"Score Details: {path.name}")
        table_obj.add_column("Dimension", style="bold")
        table_obj.add_column("Score", style="cyan")
        table_obj.add_column("Weight", style="magenta")
        table_obj.add_column("Observation", style="green")

        # Add overall score
        table_obj.add_row(
            "Overall Score",
            str(result.get("score", "N/A")),
            "1.00",
            "Weighted average of all dimensions"
        )

        # Add dimension scores
        weights = {
            "pace": 0.30,
            "continuity": 0.30,
            "filler_control": 0.20,
            "phrase_length": 0.20,
        }
        
        for dim_name in sorted(dimensions.keys()):
            dim_score = dimensions.get(dim_name)
            weight = weights.get(dim_name, 0.0)
            obs_val = str(observations.get(dim_name) or "")
            table_obj.add_row(
                dim_name.replace("_", " ").title(),
                str(dim_score),
                f"{weight:.2f}",
                obs_val
            )

        console.print(table_obj)
        
        # Show limitations if present
        if limitations:
            console.print("\n[dim]Limitations:[/dim]")
            for lim in limitations:
                console.print(f"  • {lim}")
    else:
        # For non-speaking samples or JSON output, just print the result
        _print_json(data=result)


