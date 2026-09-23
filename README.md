# Canvas MCP

A personal, local, read-only Canvas LMS integration for Codex. It provides **140
reviewed API operations** through five discoverable tools, covering most information
available to a student in Canvas. Credentials stay in `.env`; no cloud service,
background daemon, or API billing account is needed.

## Install and keep it working

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and the Codex CLI.

1. Keep this repository at a stable location.
2. Put `CANVAS_BASE_URL` (the HTTPS school origin) and `CANVAS_API_TOKEN` in `.env`.
   See `.env.example`. Existing environment variables take precedence.
3. Run:

   ```sh
   make install
   ```

Installation locks dependencies, protects `.env` with owner-only permissions, backs
up the existing Codex configuration under `.local/config-backups/`, registers the
`canvas` MCP globally, and installs the local pre-commit hook. It leaves other MCP
servers alone. It uses the existing ChatGPT login for optional Codex verification.

Codex starts the server on demand using absolute paths to the installed executable
and `.env`. **The configuration survives computer restarts** and works from other
projects without an activated environment or a terminal in this directory. Start a
new Codex task after installation, or restart the MCP in Codex settings. Nothing
needs to run while Codex is closed.

After pulling updates, run `uv sync --locked`. If this repository moves or the Python
installation changes, run `make install` again. Removing the integration only needs
`codex mcp remove canvas`.

## Ask Codex

- “What assignments are due in the next seven days? Check submission status too.”
- “Find the grading policy in my course syllabi.”
- “Show the feedback and rubric for my latest assignment.”
- “Find the lecture notes linked in this week's modules and summarize them.”
- “Summarize recent announcements and unread inbox messages.”
- “Which requirements in this course's modules are still incomplete?”

The server supplies workflow instructions, API parameter documentation, pagination,
source URLs, and two reference resources (`canvas://guide`, `canvas://operations`).

| Tool | Purpose |
| --- | --- |
| `canvas_find_operations` | Discover operations by keyword or category; empty search lists all |
| `canvas_describe_operation` | Get exact path parameters, allowed filters, notes, and official docs |
| `canvas_read` | Read one page of Canvas JSON; optionally select fields |
| `canvas_read_text` | Read long syllabus/page/description/message fields in chunks with HTML links |
| `canvas_read_file` | Extract PDF, DOCX, PPTX, HTML, and UTF-8 text from a Canvas file ID |

Example tool arguments:

```json
{
  "operation": "courses",
  "query": {"enrollment_state": "active", "include[]": ["term", "total_scores"]}
}
```

```json
{
  "operation": "submission",
  "path": {"course_id": "123", "assignment_id": "456", "user_id": "self"},
  "query": {"include[]": ["submission_comments", "submission_history", "rubric_assessment"]}
}
```

Each read returns `data`, `source_url`, and `pagination`. To continue, pass
`pagination.next_cursor` with the same `operation` and `path`, and omit `query`.
Stop when the cursor is null. `query.per_page` accepts 1–100; the default is 50.
Array parameters keep their `[]` suffix and take JSON arrays. IDs are requested
from Canvas as strings to preserve their full precision.

`canvas_read_text` accepts a dotted `field` such as `body`, `syllabus_body`, or
`messages.0.body`. Text and file results expose `next_offset`; repeat with that
offset to continue. No text is silently truncated. Large JSON results require
smaller pages, selected `fields`, or the text tool.

## Coverage and limits

The [operation catalog](docs/operations.md) covers profile, enrollments, courses,
syllabi, assignments and overrides, submissions and feedback, grade summaries,
assignment groups, rubrics, peer reviews, modules and requirements, pages and
revisions, files and folders, announcements, discussions and replies, inbox,
planner and notes, calendars and appointments, quizzes, groups, people and sections,
learning outcomes, grading periods and policies, favorites, bookmarks, conferences,
collaborations, navigation, and notification preferences.

Canvas remains the authority on permissions. A 403/404 can mean a disabled feature,
locked item, or missing permission; it is never converted to an empty list. New
Quizzes APIs often require instructor access, and Smart Search is optional. Their
student fallback is assignment and module metadata. External LTI tools such as
publisher platforms have their own content and authentication; this server exposes
Canvas's links and metadata without launching them.

Active enrollment can include old courses. Check term dates, explicit date ranges,
submission states, missing/late/excused flags, and the profile time zone. Hidden or
null grades are not zero. The planner alone is not an exhaustive assignment list.

File downloads are limited to 25 MiB. PDF extraction is limited to 300 pages and
reads embedded text, not scans, diagrams, or handwriting. DOCX/PPTX extraction
reads text, not layout or images. Other binary/media formats still have accessible
metadata and Canvas links. UTF-8 text includes CSV, JSON, notebooks, Markdown,
and source code. Downloads and extracted text are held in memory, not saved.

## Read-only guarantees

- Only the checked-in operation allowlist can reach the Canvas API. There is no raw
  URL, endpoint, HTTP method, header, GraphQL, or request-body tool.
- The transport issues GET requests only. It validates path IDs, query keys, array
  shapes, and page sizes; rejects masquerading, token query parameters, method
  overrides, and traversal; and revalidates cursors before requesting another page.
- Conversation reads force `auto_mark_as_read=false`. That setting is not exposed
  for callers to change.
- File downloads force `preview=1` and `download_frd=1` on Canvas and its file-domain
  redirects, avoiding the module-completion action used by ordinary downloads.
  Downloads are restricted to validated file routes and known storage domains;
  the Canvas bearer token is sent only to the configured Canvas origin.
- API redirects are rejected. File redirects have a separate policy and never carry
  API cookies. HTTPS certificate verification stays enabled.
- No quiz attempts, submissions, messages, edits, read-state updates, module
  completion actions, favorites changes, public preview URL generation, student-view
  user creation, or LTI launches are exposed.

Canvas can still record normal API access logs and internal cache activity. This
is a restriction on the MCP's capabilities, not a read-only scope imposed on the
personal token itself. Someone with direct access to `.env` may have broader
permissions. See [the security design](docs/security.md) for details.

## Automatic error logs

Failures are automatically written to **`.local/logs/canvas-mcp.jsonl`**. Each JSON
line records UTC time, process ID, known tool/operation, error type/code, HTTP status
when available, and source filenames/line numbers. Tool validation failures,
rejected requests, API failures, resource failures, and startup/server exceptions
are covered. Logs rotate at 1 MiB with three backups; locking supports concurrent
local server processes.

Logs deliberately omit tokens, arguments, exception messages, URLs, headers,
response bodies, grades, inbox text, and file contents. The files have owner-only
permissions and `.local/` is ignored by Git. If logging itself fails, a short warning
goes to stderr. A process that cannot launch or is forcibly killed cannot write a
log; check Codex's MCP startup status in that case. `--log-dir` overrides the location.

## Development and verification

```sh
make check                  # lint, formatting, tests, staged-secret checks
make live                   # explicit live reads through a fresh MCP process
uv run python scripts/verify_codex.py  # uses ChatGPT subscription; defaults to gpt-5.6-luna
make serve                  # stdio server; it waits for an MCP client, not a web browser
```

The pre-commit hook runs offline checks and prevents staging `.env`, `.local/`, or
the current Canvas token. Dependencies are pinned in `uv.lock`. No GitHub Actions
or publishing setup is required.

`make live` writes a summary to `.local/live-report.json` and private comparison
values to `.local/live-expected.json`. It checks real pagination, content, unread
state, preview file downloads, course progress, and rejected writes. Run it before
`verify_codex.py`, which launches a fresh Codex process with the registered Canvas
command, shell/other app tools disabled, and compares its answers with those values.
The Codex transcript and answer stay in ignored `.local/` files; these contain
private coursework, unlike the redacted automatic error log. Verification must be
explicit and is never run by the pre-commit hook.

See [verification notes](docs/verification.md) for the performed checks. To debug an
authentication failure, update `.env` and restart the MCP. For missing tools, run
`codex mcp get canvas`, then start a fresh Codex task. Permission errors should be
investigated against the same course in Canvas; they do not imply missing data.

## References

- [Official Canvas API](https://developerdocs.instructure.com/services/canvas)
- [Canvas pagination](https://developerdocs.instructure.com/services/canvas/basics/file.pagination)
- [Conversations and automatic read state](https://developerdocs.instructure.com/services/canvas/resources/conversations)
- [Canvas file controller and preview behavior](https://github.com/instructure/canvas-lms/blob/master/app/controllers/files_controller.rb)
- [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
