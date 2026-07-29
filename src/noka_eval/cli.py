import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from noka_eval.exporter import format_evaluations_as_csv


def run_batch_evaluation(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Core batch evaluation processing stub.
    Evaluates submissions and attaches score metrics and teacher feedback fields.
    """
    results = []
    for item in data:
        score = item.get("score", 0.0)
        max_score = item.get("max_score", 100.0)
        results.append({
            "id": item.get("id", ""),
            "student_id": item.get("student_id", ""),
            "score": score,
            "max_score": max_score,
            "status": "PASSED" if score >= (max_score * 0.6) else "NEEDS_REVIEW",
            "feedback": item.get("feedback", ""),
            "criteria": item.get("criteria", {})
        })
    return results


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch Evaluation CLI Tool")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to input JSON evaluation batch file"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "text", "csv"],
        default="json",
        help="Output format for batch evaluation (default: json)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Optional output file destination path"
    )

    parsed_args = parser.parse_args(args)

    raw_input = []
    if parsed_args.input:
        with open(parsed_args.input, "r", encoding="utf-8") as f:
            raw_input = json.load(f)

    results = run_batch_evaluation(raw_input)

    if parsed_args.format == "csv":
        formatted_output = format_evaluations_as_csv(results)
    elif parsed_args.format == "text":
        formatted_output = "\n".join(
            f"ID: {r.get('id')} | Student: {r.get('student_id')} | Score: {r.get('score')}/{r.get('max_score')} | Status: {r.get('status')}"
            for r in results
        )
    else:  # json
        formatted_output = json.dumps(results, indent=2, ensure_ascii=False)

    if parsed_args.output:
        with open(parsed_args.output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
    else:
        sys.stdout.write(formatted_output + ("\n" if not formatted_output.endswith("\n") else ""))

    return 0


if __name__ == "__main__":
    sys.exit(main())
