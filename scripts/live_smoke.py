"""Explicit live read-only verification through a fresh MCP stdio process."""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def main():
    checks = []
    params = StdioServerParameters(
        command=str(ROOT / ".venv/bin/canvas-mcp"),
        args=["--env-file", str(ROOT / ".env")],
        cwd="/",
        env={"PATH": "/usr/bin:/bin"},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        async def read_op(operation, path=None, query=None, *, optional=False, cursor=None):
            result = await session.call_tool(
                "canvas_read",
                {
                    "operation": operation,
                    "path": path,
                    "query": query,
                    "cursor": cursor,
                },
            )
            checks.append(
                {"operation": operation, "status": "unavailable" if result.isError else "ok"}
            )
            if result.isError:
                if optional:
                    return None
                raise RuntimeError(f"Required live read failed: {operation}")
            return result.structuredContent

        profile = (await read_op("profile", {"user_id": "self"}))["data"]
        first = await read_op("courses", query={"per_page": 2, "enrollment_state": "active"})
        if first["pagination"]["next_cursor"]:
            second = await read_op("courses", cursor=first["pagination"]["next_cursor"])
            assert {c["id"] for c in first["data"]}.isdisjoint(c["id"] for c in second["data"])
            checks.append({"operation": "pagination", "status": "ok"})
        result = await read_op(
            "courses",
            query={
                "per_page": 100,
                "enrollment_state": "active",
                "include[]": ["term", "total_scores"],
            },
        )
        courses = result["data"]
        while result["pagination"]["next_cursor"]:
            result = await read_op("courses", cursor=result["pagination"]["next_cursor"])
            courses.extend(result["data"])
        courses = [c for c in courses if c.get("name")]
        courses.sort(
            key=lambda c: c.get("term", {}).get("start_at") or c.get("start_at") or "", reverse=True
        )
        selected = assignment = None
        for course in courses[:10]:
            assignments = await read_op(
                "assignments",
                {"course_id": course["id"]},
                {"per_page": 5, "include[]": ["submission"]},
                optional=True,
            )
            if assignments and assignments["data"]:
                selected, assignment = course, assignments["data"][0]
                break
        if selected is None:
            raise RuntimeError("No course with a readable assignment was found.")
        cid, aid = selected["id"], assignment["id"]
        detail = (await read_op("course", {"id": cid}, {"include[]": ["syllabus_body", "term"]}))[
            "data"
        ]
        await read_op("assignment", {"course_id": cid, "id": aid})
        submission = await read_op(
            "submission",
            {
                "course_id": cid,
                "assignment_id": aid,
                "user_id": "self",
            },
            {"include[]": ["submission_comments", "submission_history", "rubric_assessment"]},
        )
        for op in [
            "modules",
            "pages",
            "discussions",
            "assignment_groups",
            "rubrics",
            "sections",
            "tabs",
            "quizzes",
        ]:
            result = await read_op(op, {"course_id": cid}, {"per_page": 5}, optional=True)
            if op == "modules" and result and result["data"]:
                await read_op(
                    "module_items",
                    {"course_id": cid, "module_id": result["data"][0]["id"]},
                    {"per_page": 5},
                )
            if op == "pages" and result and result["data"]:
                await read_op("page", {"course_id": cid, "url_or_id": result["data"][0]["url"]})
        start = datetime.now(UTC).date()
        window = {"start_date": str(start), "end_date": str(start + timedelta(days=7))}
        await read_op("planner_items", query=window, optional=True)
        await read_op(
            "calendar_events", query=window | {"context_codes[]": [f"course_{cid}"]}, optional=True
        )
        await read_op(
            "announcements",
            query={
                "context_codes[]": [f"course_{cid}"],
                "start_date": str(start - timedelta(days=60)),
                "end_date": str(start),
            },
            optional=True,
        )
        await read_op("enrollments", {"user_id": "self"}, {"per_page": 5})
        await read_op("groups", query={"per_page": 5})
        before = await read_op("unread_count")
        conversations = await read_op("conversations", query={"scope": "unread", "per_page": 1})
        if conversations["data"]:
            conversation = await read_op("conversation", {"id": conversations["data"][0]["id"]})
            assert conversation["data"]["workflow_state"] == "unread"
        after = await read_op("unread_count")
        assert before["data"] == after["data"], "Inbox unread count changed during verification."
        checks.append({"operation": "inbox_read_state", "status": "ok"})
        file_id = None
        file_text_sample = None
        for course in [selected] + [c for c in courses[:5] if c != selected]:
            files = await read_op(
                "files",
                {"course_id": course["id"]},
                {
                    "per_page": 10,
                    "content_types[]": ["application/pdf"],
                },
                optional=True,
            )
            if not files:
                continue
            for file in files["data"]:
                if file.get("locked_for_user") or file.get("size", 0) > 25 * 1024 * 1024:
                    continue
                progress = await read_op(
                    "course_progress",
                    {
                        "course_id": course["id"],
                        "user_id": profile["id"],
                    },
                    optional=True,
                )
                result = await session.call_tool(
                    "canvas_read_file", {"file_id": file["id"], "max_chars": 1000}
                )
                if not result.isError:
                    assert result.structuredContent["total_chars"] > 0
                    file_id = file["id"]
                    file_text_sample = result.structuredContent["text"]
                    if progress:
                        updated = await read_op(
                            "course_progress", {"course_id": course["id"], "user_id": profile["id"]}
                        )
                        assert progress["data"] == updated["data"], "Module progress changed."
                        checks.append({"operation": "course_progress_unchanged", "status": "ok"})
                    checks.append({"operation": "file_text", "status": "ok"})
                    break
            if file_id:
                break
        if not file_id:
            raise RuntimeError("Could not verify a readable PDF attachment.")
        blocked = await session.call_tool("canvas_read", {"operation": "update_assignment"})
        assert blocked.isError
        checks.append({"operation": "write_rejected_and_logged", "status": "ok"})
        expected = {
            "course_count": len(courses),
            "course_id": cid,
            "course_name": selected["name"],
            "assignment_id": aid,
            "assignment_name": assignment["name"],
            "due_at": assignment.get("due_at"),
            "profile_time_zone": profile.get("time_zone"),
            "submission_state": submission["data"].get("workflow_state"),
            "syllabus_present": bool(detail.get("syllabus_body")),
            "file_id": file_id,
            "file_text_sample": file_text_sample,
        }
    output = ROOT / ".local"
    output.mkdir(exist_ok=True, mode=0o700)
    for name, data in {
        "live-report.json": {"checked_at": datetime.now(UTC).isoformat(), "checks": checks},
        "live-expected.json": expected,
    }.items():
        path = output / name
        path.write_text(json.dumps(data, indent=2) + "\n")
        path.chmod(0o600)
    print(
        json.dumps(
            {
                "successful_checks": sum(c["status"] == "ok" for c in checks),
                "unavailable_checks": sum(c["status"] == "unavailable" for c in checks),
                "report": ".local/live-report.json",
            }
        )
    )


if __name__ == "__main__":
    os.umask(0o077)
    asyncio.run(main())
