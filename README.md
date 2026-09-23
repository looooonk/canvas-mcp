# Canvas MCP

A personal, local MCP server that lets Codex read Canvas LMS. It uses an explicit
allowlist of student-facing API operations and never exposes Canvas writes.

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and Codex. Authentication
stays in the ignored `.env` file; start from `.env.example` when needed.

```sh
uv sync --locked
```

Source documentation: [Canvas REST API](https://developerdocs.instructure.com/services/canvas)
and [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
