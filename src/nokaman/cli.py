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
from nokaman.eval.session import SessionManager
from nokaman.eval.asr_scorer import score_asr_transcript, score_asr_transcript_text
from nokaman.eval.llm_grader import create_llm_grader, LLMRubricGrader
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
def eval_samples(
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter by language code (e.g., en, de)"),
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Filter by skill (e.g., writing, speaking)"),
) -> None:
    """List samples with optional language and skill filters."""
    files = list_sample_files()
    if not files:
        console.print("[yellow]No samples[/yellow]")
        raise typer.Exit()

    filtered_files = []
    for path in files:
        from nokaman.data.loader import load_sample
        sample = load_sample(path)
        sample_lang = str(sample.get("language") or "").lower()
        sample_skill = str(sample.get("skill") or "").lower()

        if language and sample_lang != language.lower():
            continue
        if skill and sample_skill != skill.lower():
            continue

        filtered_files.append(path)

    if not filtered_files:
        console.print(f"[yellow]No samples matching filters (language={language}, skill={skill})[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Samples ({len(filtered_files)})")
    table.add_column("File")
    table.add_column("Lang")
    table.add_column("Skill")
    table.add_column("CEFR")
    table.add_column("Score")
    for path in filtered_files:
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
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, csv"),
) -> None:
    report = batch_evaluate()

    # Determine output path and format
    if out:
        out_path = out
    else:
        ext = "csv" if format == "csv" else "json"
        out_path = RUNS_DIR / f"batch_eval.{ext}"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "csv":
        # Write CSV format
        import csv
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["language", "n_samples", "exact_cefr_hit_rate", "adjacent_cefr_hit_rate", "mae_score"])
            # Overall
            writer.writerow([
                "overall",
                report.get("n_samples", 0),
                report.get("exact_cefr_hit_rate", ""),
                report.get("adjacent_cefr_hit_rate", ""),
                report.get("mae_score", ""),
            ])
            # By language
            for lang, row in sorted((report.get("by_language") or {}).items()):
                writer.writerow([
                    lang,
                    row.get("n") or row.get("n_samples") or "",
                    row.get("exact_cefr_hit_rate", row.get("exact", "")),
                    row.get("adjacent_cefr_hit_rate", row.get("adjacent", "")),
                    row.get("mae_score", ""),
                ])
        console.print(f"[green]CSV report saved[/green]: {out_path}")
    else:
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


@eval_app.command("asr")
def eval_asr(
    transcript: Path = typer.Option(..., "--transcript", "-t", exists=True, dir_okay=False, help="ASR transcript JSON file"),
    lang: str = typer.Option("en", "--lang", "-l"),
    skill: str = typer.Option("speaking", "--skill", "-s"),
) -> None:
    """Score speaking from ASR transcript JSON file."""
    result = score_asr_transcript(transcript, lang, skill)
    _print_json(data=result)


@eval_app.command("asr-text")
def eval_asr_text(
    text: str = typer.Option(..., "--text", help="Transcript text"),
    lang: str = typer.Option("en", "--lang", "-l"),
    duration: float = typer.Option(0.0, "--duration", "-d", help="Duration in seconds"),
    confidence: float = typer.Option(1.0, "--confidence", "-c", help="ASR confidence 0-1"),
) -> None:
    """Score speaking from raw transcript text."""
    result = score_asr_transcript_text(text, lang, duration, confidence)
    _print_json(data=result)


@eval_app.command("llm-grade")
def eval_llm_grade(
    text: str = typer.Option(..., "--text", "-t", help="Text to grade"),
    lang: str = typer.Option("en", "--lang", "-l"),
    skill: str = typer.Option("writing", "--skill", "-s"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="LLM API key (or set LLM_API_KEY)"),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="LLM API URL"),
    model: str = typer.Option("gpt-4o-mini", "--model", help="LLM model name"),
) -> None:
    """Grade text using optional LLM rubric grader (requires httpx extra)."""
    grader = LLMRubricGrader(language=lang, api_key=api_key, api_url=api_url, model=model)
    if not grader.is_available():
        console.print("[red]LLM grader not available. Install httpx: pip install httpx[/red]")
        console.print("[dim]Set ENABLE_LLM_GRADER=true and LLM_API_KEY env vars[/dim]")
        raise typer.Exit(code=1)
    result = grader.score_text(text, skill)
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
