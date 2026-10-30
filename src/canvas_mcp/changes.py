from canvas_mcp.catalog import CanvasError
from canvas_mcp.changefeed import FeedError, record, selected


class CanvasChanges:
    errors = (CanvasError, FeedError)
    coverage = (
        "Course assignments/deadlines, your submissions/grades/feedback, "
        "page bodies, and file metadata."
    )

    async def authorize(self, client, course):
        data = (await client.read("course", {"id": course}))["data"]
        if not isinstance(data, dict) or str(data.get("id")) != course:
            raise FeedError("Course membership could not be verified.")
        return sorted({str(e.get("type")) for e in data.get("enrollments", [])})

    def tasks(self, course, role):
        return [
            {"source": name, "cursor": None}
            for name in ("assignments", "student_submissions", "pages", "files")
        ]

    async def collect(self, client, course, task):
        name = task["source"]
        queries = {
            "assignments": {"include[]": ["all_dates"]},
            "student_submissions": {
                "student_ids[]": ["self"],
                "include[]": ["submission_comments", "rubric_assessment"],
            },
            "pages": {"include[]": ["body"], "sort": "created_at", "order": "asc"},
            "files": {"sort": "created_at", "order": "asc"},
        }
        result = await client.read(
            name,
            {"course_id": course},
            None if task["cursor"] else queries[name] | {"per_page": 50},
            task["cursor"],
        )
        rows = result["data"]
        if not isinstance(rows, list):
            raise FeedError("Canvas change source returned an unexpected shape.")
        base = client.settings.base_url + f"/courses/{course}"
        records = []
        for row in rows:
            if not isinstance(row, dict):
                raise FeedError("Canvas change source has an invalid record.")
            identifier = row.get("page_id" if name == "pages" else "id")
            if name == "student_submissions":
                identifier = row.get("assignment_id")
            if identifier is None:
                raise FeedError("Canvas change source is missing a stable identifier.")
            if name == "assignments":
                fields = selected(
                    row,
                    (
                        "name description due_at unlock_at lock_at all_dates "
                        "points_possible published submission_types"
                    ),
                )
                kind, url = "assignment", f"{base}/assignments/{identifier}"
            elif name == "student_submissions":
                fields = selected(
                    row,
                    (
                        "assignment_id score grade workflow_state submitted_at graded_at "
                        "late missing excused attempt submission_comments "
                        "rubric_assessment"
                    ),
                )
                kind, url = "submission", f"{base}/assignments/{identifier}/submissions/self"
            elif name == "pages":
                fields = selected(
                    row, "title body published front_page locked_for_user block_editor_attributes"
                )
                kind, url = "page", f"{base}/pages/{row.get('url', identifier)}"
            else:
                fields = selected(
                    row,
                    (
                        "display_name filename size content-type updated_at "
                        "locked_for_user hidden locked"
                    ),
                )
                kind, url = "file", f"{base}/files/{identifier}"
            records.append(
                record(
                    kind,
                    identifier,
                    row.get("name")
                    or row.get("title")
                    or row.get("display_name")
                    or f"{kind} {identifier}",
                    url,
                    fields,
                )
            )
        next_cursor = result["pagination"]["next_cursor"]
        return records, ([task | {"cursor": next_cursor}] if next_cursor else [])
