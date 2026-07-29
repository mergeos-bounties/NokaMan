import csv
import io
import json
from typing import Any, Dict, List, Optional


def format_evaluations_as_csv(
    evaluations: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None
) -> str:
    """
    Formats a list of batch evaluation dictionaries into a CSV string.

    Handles boundary conditions:
    - Empty evaluation list
    - Nested score breakdowns (flattened or JSON-serialized)
    - Multi-line text and special characters escaping
    """
    if not evaluations:
        if fieldnames:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            return output.getvalue()
        return ""

    # Flatten nested dictionaries or criteria breakdowns for standard tabular view
    processed_records: List[Dict[str, Any]] = []
    dynamic_keys = set()

    for item in evaluations:
        record: Dict[str, Any] = {}
        for k, v in item.items():
            if isinstance(v, dict):
                # Represent sub-dictionaries as serialized JSON strings or flattened keys
                record[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, (list, tuple)):
                record[k] = json.dumps(v, ensure_ascii=False)
            else:
                record[k] = v if v is not None else ""
            dynamic_keys.add(k)
        processed_records.append(record)

    # Determine final standard field ordering if not provided
    if not fieldnames:
        # Standard default field order prioritized for teacher workflows
        preferred_order = ["id", "student_id", "submission_id", "score", "max_score", "status", "feedback", "timestamp"]
        fieldnames = [k for k in preferred_order if k in dynamic_keys]
        for k in sorted(dynamic_keys):
            if k not in fieldnames:
                fieldnames.append(k)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(processed_records)

    return output.getvalue()
