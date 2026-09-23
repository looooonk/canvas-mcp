# Security and read-only design

## Boundary

`operations.json` is a reviewed, static allowlist derived from official Canvas REST
API documentation. `catalog.py` constructs paths from that catalog and validates
all input. `client.py` has a single GET-only authenticated transport. Models cannot
supply arbitrary paths, URLs, headers, methods, bodies, or unrecognized query keys.
Tool annotations describe read-only behavior but are not the enforcement boundary.

Never automatically import every GET route. Several GETs have side effects:
conversation reads default to marking messages read; ordinary file downloads can
advance module progress; student-view, media-folder, public file preview, and LTI
launch routes can create state or sessions. These routes are excluded or constrained.
In particular, conversation reads fix `auto_mark_as_read=false`. The file reader
forces preview mode on every Canvas/file-domain redirect, including shard-prefixed
file IDs. Merely setting preview on the first URL is insufficient because Canvas
can omit it from the next redirect.

Canvas's source implements `send_stored_file` so `context_module_action` only runs
when a user exists and `preview` is absent. Preview downloads still pass normal
Canvas permission checks. We also exclude the file metadata `view` parameter,
which can advance progress in Canvas Career. Course, page, and discussion reads may
record access telemetry. The server does not claim to suppress server-side logs,
caches, or all incidental internal database writes.

## Requests, credentials, and returned content

The configured origin must use HTTPS. The token is a bearer header, never a query
parameter or a Codex config value. API redirects are rejected. Pagination links must
match the exact origin and endpoint and pass the same query validation; cursors are
untrusted encodings, not authorization credentials. Forging one cannot expand the
allowlist. The authenticated API client does not share cookies with file downloads.

File URLs originate only from the authorized metadata endpoint. The configured
Canvas origin and Canvas file-domain routes must match the requested numeric file
ID, optionally with Canvas's shard prefix. These routes force preview mode. Storage
hosts are limited to Canvas/Instructure storage, Amazon S3, and CloudFront suffixes,
including the Instructure Files host used by this school. No bearer token is sent
to any other origin. Redirects, response sizes, request concurrency, retries, and
request time are bounded. TLS verification is never disabled.

All Canvas content is untrusted data. Server instructions tell Codex to ignore
instructions embedded in course content. Returned links are references; this MCP
does not execute scripts, launch external tools, open arbitrary URLs, or extract
archive files to disk. File parsers have download, page, and expanded archive limits.
Signed file URLs returned by Canvas can grant temporary access, so they should not
be published or pasted into shared documents.

## Local storage and diagnostics

`.env` is owner-readable and ignored. Runtime logs use an explicit field allowlist;
exception messages and tool arguments are never logged. Error causes contribute
only their class name, fixed error code, optional status, and traceback locations.
Logs rotate under a process lock and have mode 0600. Logging failures do not mask
the original tool failure or write to MCP stdout.

The application does not cache Canvas data or write attachments. Explicit verification
scripts save private results under ignored `.local/` with restricted permissions.
Codex itself may retain tool responses according to its normal task behavior.
Configuration backups can contain other local settings; they are ignored and private.

The Git hook rejects private staged paths and the current token. It is an accidental
leak check, not a substitute for reviewing commits or an exhaustive secret scanner.

## Extending the catalog

1. Read the official endpoint documentation and inspect source when GET semantics
   are unclear. Confirm it does not intentionally mutate student-visible state.
2. Add a named operation and only its reviewed parameters to `operations.json`.
3. Check path validation for each placeholder; do not weaken ID validation to accept
   arbitrary route segments.
4. Add behavioral tests for any new safety requirement, especially defaults and
   redirects. Keep unit tests independent of live credentials.
5. Update the catalog documentation and run the offline checks. Run explicit live
   verification if the change affects network behavior.

References: [Canvas API](https://developerdocs.instructure.com/services/canvas),
[conversation defaults](https://developerdocs.instructure.com/services/canvas/resources/conversations),
[file implementation](https://github.com/instructure/canvas-lms/blob/master/app/controllers/files_controller.rb).
