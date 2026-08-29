"""
Workflow Functions
==================

Deterministic building blocks for Studio-built workflows, registered in the
Studio registry's `functions` slot (app/registry.py). Each function is a step
executor: the runtime calls it as `func(step_input)` with a `StepInput`, and it
returns a string (the step's content) or a `StepOutput`.
"""

import csv
import io
import json
import re
from typing import Any

from agno.media import File
from agno.workflow import StepInput, StepOutput
from pydantic import BaseModel

_URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+")
_TABLE_ROW_CAP = 50
_ERROR_PREFIX = "Error: "


def _error(message: str) -> str:
    return f"{_ERROR_PREFIX}{message}"


def _step_text(step_input: StepInput) -> str:
    content = step_input.previous_step_content
    if content is None:
        return step_input.get_input_as_string() or ""
    if isinstance(content, BaseModel):
        return content.model_dump_json(indent=2, exclude_none=True)
    if isinstance(content, (dict, list)):
        return json.dumps(content, indent=2, default=str, ensure_ascii=False)
    return str(content)


_NO_JSON = object()


def _json_payload(text: str) -> Any:
    decoder = json.JSONDecoder()
    best_span, best_value, skip_until = 0, _NO_JSON, 0
    for match in re.finditer(r"[\[{]", text):
        start = match.start()
        if start < skip_until:
            continue
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if end - start > best_span:
            best_span, best_value = end - start, value
        skip_until = end
    return best_value


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _table_cell(cell: str) -> str:
    return cell.strip().replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def extract_json(step_input: StepInput) -> str:
    text = _step_text(step_input)
    if text.startswith(_ERROR_PREFIX):
        return text
    value = _json_payload(text)
    if value is _NO_JSON:
        return _error("no valid JSON object or array in the previous step's output")
    return json.dumps(value, indent=2, ensure_ascii=False)


def extract_urls(step_input: StepInput) -> str:
    text = _step_text(step_input)
    if text.startswith(_ERROR_PREFIX):
        return text
    urls = dict.fromkeys(url.rstrip(".,;:!?`*") for url in _URL_PATTERN.findall(text))
    if not urls:
        return _error("no URLs in the previous step's output")
    return "\n".join(urls)


def json_to_csv(step_input: StepInput) -> StepOutput:
    text = _step_text(step_input)
    if text.startswith(_ERROR_PREFIX):
        return StepOutput(content=text)
    value = _json_payload(text)
    if isinstance(value, dict):
        arrays = [item for item in value.values() if isinstance(item, list)]
        if len(arrays) == 1:
            value = arrays[0]
    if value is _NO_JSON or not isinstance(value, list) or not value or not all(isinstance(r, dict) for r in value):
        return StepOutput(content=_error("expected a JSON array of objects in the previous step's output"))
    header: list[str] = []
    for row in value:
        for key in row:
            if key not in header:
                header.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    for row in value:
        writer.writerow({key: _cell(row.get(key)) for key in header})
    data = buffer.getvalue()
    return StepOutput(
        content=data,
        files=[File(content=data.encode(), mime_type="text/csv", filename="data.csv")],
    )


def csv_to_markdown_table(step_input: StepInput) -> str:
    text = _step_text(step_input)
    if text.startswith(_ERROR_PREFIX):
        return text
    rows = [row for row in csv.reader(io.StringIO(text)) if row]
    if len(rows) < 2:
        return _error("expected CSV with a header row and at least one data row")

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(_table_cell(cell) for cell in cells) + " |"

    header, data = rows[0], rows[1:]
    lines = [line(header), "| " + " | ".join("---" for _ in header) + " |"]
    lines += [line(row) for row in data[:_TABLE_ROW_CAP]]
    if len(data) > _TABLE_ROW_CAP:
        lines.append(f"… {len(data) - _TABLE_ROW_CAP} more rows")
    return "\n".join(lines)


def content_to_file(step_input: StepInput) -> StepOutput:
    text = _step_text(step_input)
    if text.startswith(_ERROR_PREFIX):
        return StepOutput(content=text)
    if not text.strip():
        return StepOutput(content=_error("previous step produced no content to save"))
    return StepOutput(
        content=text,
        files=[File(content=text.encode(), mime_type="text/markdown", filename="output.md")],
    )
