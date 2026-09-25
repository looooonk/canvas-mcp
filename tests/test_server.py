import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.exceptions import ToolError

from canvas_mcp.catalog import CanvasError
from canvas_mcp.config import Settings
from canvas_mcp.diagnostics import ErrorLog
from canvas_mcp.server import create_server


@pytest.mark.parametrize("file_id", [123, "123"])
async def test_file_ids_are_normalized_before_read(tmp_path, monkeypatch, file_id):
    calls = []

    async def read_file(client, identifier):
        calls.append(identifier)
        return {"filename": "sample.txt", "content-type": "text/plain"}, b"example text"

    monkeypatch.setattr("canvas_mcp.server.read_file", read_file)
    server = create_server(Settings("https://canvas.example.edu", "secret"), tmp_path)
    monkeypatch.setattr(
        server,
        "get_context",
        lambda: SimpleNamespace(request_context=SimpleNamespace(lifespan_context=None)),
    )
    _, result = await server.call_tool("canvas_read_file", {"file_id": file_id})
    assert calls == ["123"]
    assert result["file_id"] == "123" and result["text"] == "example text"


@pytest.mark.parametrize("file_id", [True, False, 1.5, -1, 0, 10**30, "../123", "1\n", {}])
async def test_invalid_file_ids_never_read(tmp_path, monkeypatch, file_id):
    async def unexpected_read(*args):
        pytest.fail("Invalid file IDs must be rejected before reading")

    monkeypatch.setattr("canvas_mcp.server.read_file", unexpected_read)
    server = create_server(Settings("https://canvas.example.edu", "secret"), tmp_path)
    with pytest.raises(ToolError, match="file_id"):
        await server.call_tool("canvas_read_file", {"file_id": file_id})


async def test_all_tools_are_read_only_and_errors_are_logged(tmp_path):
    server = create_server(Settings("https://canvas.example.edu", "private-token"), tmp_path)
    tools = await server.list_tools()
    assert len(tools) == 5
    assert all(t.annotations.readOnlyHint and not t.annotations.destructiveHint for t in tools)
    with pytest.raises(ToolError):
        await server.call_tool("canvas_describe_operation", {"operation": "private-token"})
    record = json.loads((tmp_path / "canvas-mcp.jsonl").read_text())
    assert record["event"] == "tool_failure" and record["operation"] is None
    assert "private-token" not in (tmp_path / "canvas-mcp.jsonl").read_text()


async def test_validation_errors_are_logged(tmp_path):
    server = create_server(Settings("https://canvas.example.edu", "secret"), tmp_path)
    with pytest.raises(ToolError):
        await server.call_tool("canvas_read_file", {"file_id": "1", "offset": -1})
    assert (tmp_path / "canvas-mcp.jsonl").exists()


def test_log_rotation_redaction_permissions_and_http_status(tmp_path):
    log = ErrorLog(tmp_path, max_bytes=1, backups=2)
    for _ in range(5):
        log.record(
            "tool_failure",
            CanvasError("secret-grade-and-token", code="http_error", http_status=403),
            operation="courses",
            tool="canvas_read",
        )
    assert len(list(tmp_path.glob("*.jsonl*"))) == 3
    raw = (tmp_path / "canvas-mcp.jsonl").read_text()
    assert "secret-grade-and-token" not in raw
    assert json.loads(raw)["http_status"] == 403
    assert (tmp_path / "canvas-mcp.jsonl").stat().st_mode & 0o777 == 0o600


async def test_real_stdio_handshake_discovery_and_rejection(tmp_path):
    env = tmp_path / ".env"
    env.write_text("CANVAS_BASE_URL=https://canvas.example.edu\nCANVAS_API_TOKEN=fake-token\n")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "canvas_mcp.server", "--env-file", str(env)],
        cwd=str(Path(__file__).resolve().parents[1]),
        env={k: v for k, v in os.environ.items() if not k.startswith("CANVAS_")},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        init = await session.initialize()
        assert "Read-only Canvas" in init.instructions
        listed = await session.list_tools()
        assert len(listed.tools) == 5
        result = await session.call_tool("canvas_describe_operation", {"operation": "conversation"})
        assert not result.isError
        assert result.structuredContent["fixed_query"] == {"auto_mark_as_read": False}
        rejected = await session.call_tool(
            "canvas_read",
            {
                "operation": "conversation",
                "path": {"id": "1"},
                "query": {"auto_mark_as_read": True},
            },
        )
        assert rejected.isError
        resources = await session.list_resources()
        assert len(resources.resources) == 2
    assert (tmp_path / ".local/logs/canvas-mcp.jsonl").exists()
