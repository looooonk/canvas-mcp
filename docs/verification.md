# Verification

Verified locally on September 22, 2026 (America/New_York; September 23 UTC).
No token, course names, grades, messages, or file contents are included here.

## Offline and protocol checks

`make check` passes **212 tests**, plus lint and formatting checks. Tests cover:

- Every catalog route's path construction and prohibited query keys.
- Traversal, route injection, method overrides, impersonation, and token parameters.
- Conversation reads forcing `auto_mark_as_read=false`.
- Pagination, repeated array parameters, forged cursors, and hostile next links.
- API redirects, HTTP failures, retries, and compressed responses.
- HTTPS origin validation and keeping tokens out of representations and results.
- File redirect chains, shard-prefixed IDs, preserving preview mode at each Canvas
  hop, stripping authorization and cookies at storage hosts, and unsafe URLs.
- HTML/text extraction, Office extraction, text continuation, and unsupported files.
- MCP initialization, tool discovery, structured output, resources, and write rejection.
- Read-only tool annotations and automatic error logs, including validation failures,
  HTTP status fields, rotation, private permissions, and absence of secret messages.

## Live Canvas through MCP

`scripts/live_smoke.py` starts a new server using an absolute executable/env path,
working directory `/`, and a minimal PATH. This confirms startup does not depend on
an activated shell or the repository being the current directory. Registration is
in the persistent global Codex configuration; no real machine reboot was performed.

The latest run reports **28 successful checks** and **5 unavailable checks**. It
reads profile, all accessible named active courses, assignment details, own submission
and feedback, modules and module items, assignment groups, sections, navigation,
planner, calendar, announcements, enrollments, groups, inbox counts, and a PDF file.
It also exercises actual pagination and rejects an unsupported write operation.

The unread inbox count was unchanged across verification. File text was extracted
successfully through the school's real redirect chain.

Unavailable checks in the sampled courses were pages (404), rubrics (403), quizzes
(404), one course's file listing (403), and course progress (400). A different course
provided the readable PDF. Canvas explained that the sampled file course did not
provide module-based completion progress (or an applicable student enrollment), so
**a live before/after progress comparison could not be performed**. The preview
protection is verified against Canvas source and mocked redirect-chain tests. No
claim is made that every endpoint is usable for every course or school feature.

Verification failures now produce redacted records in
`.local/verification/logs/canvas-mcp.jsonl`, including HTTP statuses. Historical
operational logs are retained unchanged. Raw verification artifacts
are separate, private, ignored files under `.local/`.

## Independent Codex session

The existing ChatGPT subscription login was used for a fresh, ephemeral CLI session.
Its Canvas command and arguments were read from the installed Codex configuration.
Other app tools, shell tools, and subagents were disabled for the check.

**GPT-6 Luna made 13 Canvas MCP calls**, discovered and described operations,
retrieved data, and returned eight fields that exactly matched the live MCP values:
course count, course ID/name, assignment ID/name, raw due timestamp, profile time
zone, and submission state. Its file excerpt also matched extracted text after
whitespace normalization. The verifier checks these values programmatically.

The September 25, 2026 check used GPT-6 Luna with the installed Canvas command,
including an integer file ID. The script defaults to `gpt-6-luna`; `--model` can
select another supported model. No OpenAI API key was needed.

## Reproduce

```sh
make install
make check
make live
uv run python scripts/verify_codex.py
```

Live checks are explicit and are never run by the Git hook. The hook runs offline
checks and rejects staged private artifacts or the current Canvas token. There is
no GitHub Actions workflow.

## Diagnostic isolation

Both verification scripts pass `--log-dir .local/verification/logs` as an absolute
path to the MCP process. Deliberately invalid requests and live verification errors
stay there; normal Codex sessions continue to use `.local/logs/`. Historical logs
are not rewritten. Run the Codex check with `--model gpt-6-luna`.
