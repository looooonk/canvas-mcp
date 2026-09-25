"""Use the existing ChatGPT login to verify Canvas answers with a small Codex model."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from canvas_mcp.diagnostics import ErrorLog

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-6-luna")
    args = parser.parse_args()
    expected = json.loads((LOCAL / "live-expected.json").read_text())
    config = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    canvas = tomllib.loads(config.read_text())["mcp_servers"]["canvas"]
    work = LOCAL / "codex-check"
    work.mkdir(exist_ok=True)
    properties = {
        "course_count": {"type": "integer"},
        "course_id": {"type": "string"},
        "course_name": {"type": "string"},
        "assignment_id": {"type": "string"},
        "assignment_name": {"type": "string"},
        "due_at": {"type": ["string", "null"]},
        "profile_time_zone": {"type": ["string", "null"]},
        "submission_state": {"type": ["string", "null"]},
        "file_excerpt": {"type": "string"},
    }
    schema = work / "schema.json"
    schema.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            }
        )
    )
    prompt = (
        "Verify this Canvas MCP by using only its MCP tools. Do not read local files or use shell, "
        "web, other MCPs, or subagents. Discover operations and inspect their parameters first. "
        "Retrieve my profile time zone, count ALL accessible named courses with active enrollments "
        "(follow pagination), then read course "
        + expected["course_id"]
        + " and assignment "
        + expected["assignment_id"]
        + " in that course. Read my own submission for that assignment. "
        "Report exact IDs, names, due_at (raw timestamp or null), and submission workflow_state. "
        "Read file "
        + expected["file_id"]
        + " using canvas_read_file with file_id as a JSON integer. Include an exact short excerpt "
        "from its extracted text. Do not guess values. Return the required JSON only."
    )
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--json",
        "-C",
        str(work),
        "--disable",
        "shell_tool",
        "--disable",
        "apps",
        "--disable",
        "multi_agent",
        "-m",
        args.model,
        "-c",
        'model_reasoning_effort="low"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers.canvas.command=" + json.dumps(canvas["command"]),
        "-c",
        "mcp_servers.canvas.args="
        + json.dumps(canvas.get("args", []) + ["--log-dir", str(LOCAL / "verification/logs")]),
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(LOCAL / "codex-answer.json"),
        "-",
    ]
    env = dict(os.environ)
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"):
        env.pop(key, None)
    with (
        (LOCAL / "codex-events.jsonl").open("w") as out,
        (LOCAL / "codex-stderr.log").open("w") as err,
    ):
        result = subprocess.run(
            command, input=prompt, text=True, stdout=out, stderr=err, env=env, timeout=300
        )
    if result.returncode:
        raise SystemExit("Codex verification failed; see ignored .local/codex-stderr.log.")
    answer = json.loads((LOCAL / "codex-answer.json").read_text())
    mismatches = [
        key for key in properties if key != "file_excerpt" and answer.get(key) != expected[key]
    ]
    if mismatches:
        raise SystemExit("Codex answer differed from live API values: " + ", ".join(mismatches))
    excerpt = re.sub(r"\s+", " ", answer.get("file_excerpt", "")).strip()
    sample = re.sub(r"\s+", " ", expected["file_text_sample"]).strip()
    if not excerpt or excerpt not in sample:
        raise SystemExit("Codex attachment excerpt did not match the extracted file text.")
    events = [json.loads(line) for line in (LOCAL / "codex-events.jsonl").read_text().splitlines()]
    calls = [
        e["item"]
        for e in events
        if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "mcp_tool_call"
    ]
    if not calls or any(c.get("server") != "canvas" for c in calls):
        raise SystemExit("Expected successful Canvas MCP calls were not observed.")
    successful = [
        c
        for c in calls
        if c.get("status") == "completed" and not (c.get("result") or {}).get("isError")
    ]
    required = {
        "canvas_find_operations",
        "canvas_describe_operation",
        "canvas_read",
        "canvas_read_file",
    }
    if not required <= {c.get("tool") for c in successful}:
        raise SystemExit("Expected successful tool calls were not observed.")
    report = {
        "model": args.model,
        "matched_fields": len(properties) - 1,
        "mcp_calls": len(calls),
        "result": "verified",
    }
    (LOCAL / "codex-summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        ErrorLog(LOCAL / "verification/logs").record("codex_verification_failure", error)
        raise SystemExit(
            "Codex verification failed; inspect safe verification diagnostics."
        ) from None
