"""score CLI command for NokaMan — rich table output for sample evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from nokaman import __version__
from nokaman.eval.pipeline import evaluate_sample_file, evaluate_text
from nokaman.data.loader import list_sample_files

console = Console()


def score_cmd(
    sample: Optional[Path] = typer.Option(
        None, "--sample", "-s", exists=True, dir_okay=False,
        help="Path to a sample JSON file to score.",
    ),
    text: Optional[str] = typer.Option(
        None, "--text", "-t",
        help="Inline text to score (requires --lang and --skill).",
    ),
    lang: str = typer.Option("en", "--lang", "-l"),
    skill: str = typer.Option("writing", "--skill", "-k"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich table."),
) -> None:
    """Score a sample file or inline text and print a rich dimension table.

    Examples:
        nokaman score --sample data/samples/en_writing_b1.json
        nokaman score --text "I goes to school" --lang en --skill writing
        nokaman score --sample data/samples/en_writing_b1.json --json
    """
    if sample is not None:
        result = evaluate_sample_file(sample)
    elif text:
        result = evaluate_text(lang, text, skill=skill)
    else:
        console.print("[red]Provide --sample or --text[/red]")
        raise typer.Exit(code=1)

    if json_output:
        console.print_json(data=result)
        return

    # Rich table output
    table = Table(title=f"NokaMan Score — {result.get('language', lang)} / {result.get('skill', skill)}", show_lines=True)
    table.add_column("Dimension", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right", style="green")
    table.add_column("Band", style="yellow")
    table.add_column("Notes", style="dim")

    dimensions = result.get("dimensions") or result.get("scores") or {}
    if isinstance(dimensions, dict):
        for dim_name, dim_val in dimensions.items():
            if isinstance(dim_val, dict):
                score = dim_val.get("score", dim_val.get("value", "—"))
                band = dim_val.get("band", dim_val.get("level", ""))
                notes = dim_val.get("note", dim_val.get("feedback", ""))[:60]
            else:
                score = dim_val
                band = ""
                notes = ""
            table.add_row(str(dim_name), str(score), str(band), str(notes))
    elif isinstance(dimensions, list):
        for dim in dimensions:
            if isinstance(dim, dict):
                table.add_row(
                    str(dim.get("name", dim.get("dimension", "?"))),
                    str(dim.get("score", dim.get("value", "—"))),
                    str(dim.get("band", dim.get("level", ""))),
                    str(dim.get("note", dim.get("feedback", "")))[:60],
                )

    # Summary row
    overall = result.get("score", result.get("overall", "—"))
    cefr = result.get("cefr", "")
    table.add_row("[bold]Overall[/bold]", f"[bold green]{overall}[/bold green]", f"[bold yellow]{cefr}[/bold yellow]", "")

    console.print(table)

    if sample:
        console.print(f"\n[dim]Sample: {sample}[/dim]")
    console.print(f"[dim]NokaMan v{__version__}[/dim]")


def register_score(app: typer.Typer) -> None:
    """Register the score command on a Typer app."""
    app.command("score")(score_cmd)
